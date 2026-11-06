"""Reliable Notify: durable multi-recipient delivery via HA actions."""
from __future__ import annotations

import asyncio
import logging
import json
import time
import os
import secrets
from pathlib import Path

import voluptuous as vol
from homeassistant.util.yaml import load_yaml
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.components.http import StaticPathConfig
from homeassistant.components import panel_custom, frontend

from .const import CONF_INTERVAL, CONF_TARGET, DEFAULT_INTERVAL, DOMAIN, MAX_QUEUE
from .routing import resolve, validate_config, valid_action
from .notify_compat import async_register_compat, async_unregister_compat
from .templates import validate_templates, validate_parameters
from .profiles import DEFAULT as DEFAULT_PROFILES, validate_profiles, resolve_profile
from .api import ReliableNotifyAPIView
from .store import QueueStore
from .transport import create_payload
from .media import snapshot_file, cleanup_media, snapshot_attachments, free_disk_bytes
from .retry import classify_error, validate_policies, DEFAULT_POLICIES
from .retention import validate_retention, retention_for_message, DEFAULT_RETENTION
from .dashboard import register_dashboard
from .acknowledgement import validate_acknowledgement
from .lifecycle import notification_tag
from .smart import DEFAULT_QUIET_HOURS, validate_quiet_hours, next_allowed_timestamp
from .simulation import simulate
from .callbacks import make_token, read_token
from .logging_utils import validate_transport_logging, transport_for
from .native_transport import NATIVE_ACTIONS, native_public_payload, async_deliver_native

LANES = ("telegram", "smtp", "notify", "notify")

_LOGGER = logging.getLogger(__name__)

ENQUEUE_SCHEMA = vol.Schema({
    vol.Required("message"): cv.string,
    vol.Optional("title"): cv.string,
    vol.Optional("recipients"): vol.Any(cv.string, [cv.string]),
    vol.Optional("media", default="text"): vol.In(("text", "photo")),
    vol.Optional("target_entity"): cv.string,
    vol.Optional("action"): cv.string,
    vol.Optional("data", default={}): dict,
    vol.Optional("priority"): vol.In(("info", "warning", "critical")),
    vol.Optional("message_type"): vol.Match(r"^[a-z][a-z0-9_]{0,63}$"),
    vol.Optional("profile"): vol.Match(r"^[a-z][a-z0-9_]{0,63}$"),
    vol.Optional("archive"): vol.In(("keep", "delete_after_send")),
    vol.Optional("archive_days"): vol.All(vol.Coerce(int), vol.Range(min=0, max=365)),
    vol.Optional("ttl"): vol.All(vol.Coerce(int), vol.Range(min=0)),
    vol.Optional("dedup_key"): cv.string,
    vol.Optional("strategy"): vol.In(("always", "replace", "digest")),
    vol.Optional("acknowledgement"): dict,
    vol.Optional("test_mode"): vol.In(("off","stage")),
    vol.Optional("only_if"): vol.Schema({
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("state"): cv.string,
    }),
})
JOB_SCHEMA = vol.Schema({vol.Required("id"): vol.All(vol.Coerce(int),vol.Range(min=1)),
                         vol.Optional("dead", default=False): cv.boolean})
ACK_SCHEMA = vol.Schema({
    vol.Required("dedup_key"): cv.string,
    vol.Optional("by", default="manual"): cv.string,
})
UPDATE_SCHEMA = ENQUEUE_SCHEMA.extend({vol.Required("dedup_key"): cv.string})
DISMISS_SCHEMA = vol.Schema({
    vol.Required("dedup_key"): cv.string,
    vol.Required("recipients"): vol.Any(cv.string,[cv.string]),
})
CANCEL_SCHEMA = vol.Schema({vol.Required("dedup_key"): cv.string, vol.Optional("target_entity"): cv.string})


def _load_routes(path):
    file = Path(path)
    if not file.exists():
        return {"recipients": {}, "groups": {}, "persons": {}}
    raw = load_yaml(file) or {}
    return validate_config(raw)


class ReliableNotifyManager:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass, self.entry = hass, entry
        self.store = QueueStore(hass.config.path(".storage", "reliable_notify.db"))
        self.route_path = hass.config.path("reliable_notify_routes.yaml")
        self.routes = {"recipients": {}, "groups": {}, "persons": {}}
        self.wakeup = asyncio.Event()
        self.tasks = []
        self.stopping = False
        self._enqueue_lock = asyncio.Lock()
        self.last_error = None
        self.maintenance_info = {}
        self.backup_info = {}
        self.min_free_bytes = 100 * 1024 * 1024
        self.callback_secret = None
        self._event_unsubscribers = []

    @property
    def settings(self):
        return {**self.entry.data, **self.entry.options}

    @property
    def quiet_hours(self):
        return validate_quiet_hours(self.settings.get('quiet_hours', DEFAULT_QUIET_HOURS))

    @property
    def archive_retention(self):
        return validate_retention(self.settings.get('archive_retention', DEFAULT_RETENTION))

    @property
    def policies(self):
        return validate_policies(self.settings.get('retry_policies', DEFAULT_POLICIES))

    async def storage_status(self):
        try:
            free = await asyncio.to_thread(free_disk_bytes, '/media/reliable_notify')
        except OSError:
            free = None
        return {'free_bytes': free, 'minimum_free_bytes': self.min_free_bytes,
                'healthy': free is not None and free >= self.min_free_bytes}

    async def reload_routes(self):
        # UI-defined routes override YAML names; invalid reload leaves previous mapping intact.
        file_routes = await asyncio.to_thread(_load_routes, self.route_path)
        ui_routes = self.entry.options.get("routes", {"recipients": {}, "groups": {}})
        self.routes = validate_config({
            "recipients": {**file_routes["recipients"], **ui_routes.get("recipients", {})},
            "groups": {**file_routes["groups"], **ui_routes.get("groups", {})},
            "persons": {**file_routes.get("persons",{}), **ui_routes.get("persons",{})},
        })
        _LOGGER.info("Reliable Notify: %s recipients and %s groups loaded",
                     len(self.routes["recipients"]), len(self.routes["groups"]))

    async def start(self):
        await self.reload_routes()
        self.callback_secret = await asyncio.to_thread(self._load_callback_secret)
        self._event_unsubscribers = [
            self.hass.bus.async_listen('telegram_callback', self._on_telegram_action),
            self.hass.bus.async_listen('telegram_sent', self._on_telegram_sent),
            self.hass.bus.async_listen('mobile_app_notification_action', self._on_mobile_action),
        ]
        # Dedicated Telegram worker; two independently operating general notify workers.
        for index, lane in enumerate(LANES):
            self.tasks.append(self.hass.async_create_task(self.worker(index, lane), eager_start=False))
        self.tasks.append(self.hass.async_create_task(self.media_cleanup_loop(), eager_start=False))
        self.tasks.append(self.hass.async_create_task(self.maintenance_loop(), eager_start=False))
        self.tasks.append(self.hass.async_create_task(self.backup_loop(), eager_start=False))
        self.tasks.append(self.hass.async_create_task(self.escalation_loop(), eager_start=False))

    async def stop(self):
        self.stopping = True
        for unsubscribe in self._event_unsubscribers:
            unsubscribe()
        self._event_unsubscribers.clear()
        self.wakeup.set()
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()

    def _load_callback_secret(self):
        path = Path(self.hass.config.path(".storage","reliable_notify_callback_secret"))
        path.parent.mkdir(parents=True,exist_ok=True)
        try:
            fd = os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            try:
                with os.fdopen(fd,"w",encoding="ascii") as file:
                    file.write(secrets.token_hex(32))
            except Exception:
                path.unlink(missing_ok=True)
                raise
        except FileExistsError:
            pass
        return path.read_text(encoding="ascii").strip()

    async def _process_action(self, raw, origin):
        token=read_token(self.callback_secret,raw)
        if token is None:
            return False
        identity,action=token
        key=await self.store.incident_key_from_action_id(identity)
        if key is None:
            return False
        result=await self.store.act_on_incident(key,action,origin)
        if result:
            self.hass.bus.async_fire("reliable_notify_updated", {"kind":"acknowledgement"})
        return bool(result)

    async def _telegram_feedback(self,event,raw,actor):
        try:
            if read_token(self.callback_secret,raw) is None:
                return  # Never intercept other Telegram bot callbacks.
            applied=await self._process_action(raw,actor)
            query_id=event.data.get("id")
            if not query_id or not self.hass.services.has_service("telegram_bot","answer_callback_query"):
                return
            payload={"callback_query_id":str(query_id),
                     "message":"Aktion übernommen" if applied else "Bereits bearbeitet oder ungültig"}
            config_id=event.data.get("config_entry_id")
            if config_id:
                payload["config_entry_id"]=config_id
            await self.hass.services.async_call(
                "telegram_bot","answer_callback_query",payload,blocking=True)
        except Exception:
            _LOGGER.warning("Reliable Notify: unable to process Telegram action feedback")

    def _on_telegram_sent(self,event):
        # Only record messages carrying our own outgoing queue tag.
        # Telegram integration emits telegram_sent with chat/message IDs.
        tag=event.data.get("message_tag")
        if not isinstance(tag,str) or not tag.startswith("rn_"):
            return
        identifier=tag[3:]
        if not identifier.isdecimal():
            return
        async def save():
            try:
                await self.store.record_telegram_receipt(
                    int(identifier),event.data.get("chat_id"),
                    event.data.get("message_id"))
            except Exception:
                _LOGGER.warning("Reliable Notify could not save Telegram receipt")
        self.hass.async_create_task(save())

    def _on_telegram_action(self,event):
        raw=event.data.get("data") or event.data.get("command")
        actor="telegram:" + str(event.data.get("user_id","unknown"))
        self.hass.async_create_task(self._telegram_feedback(event,raw,actor))

    def _on_mobile_action(self,event):
        raw=event.data.get("action")
        actor="companion:" + str(event.context.user_id or "unknown")
        self.hass.async_create_task(self._process_action(raw,actor))

    def _action_payload(self,action,payload,key):
        """Opt-in signed actionable buttons; do not overwrite caller buttons."""
        if not self.callback_secret:
            raise ValueError("callback secret unavailable")
        prepared=dict(payload)
        tokens={name:make_token(self.callback_secret,key,name)
                for name in ("ack","snooze","escalate")}
        if action.startswith("notify.mobile_app_"):
            native=dict(prepared.get("data") or {})
            native.setdefault("actions",[
                {"action":tokens["ack"],"title":"Bestätigen"},
                {"action":tokens["snooze"],"title":"15 Min. später"},
                {"action":tokens["escalate"],"title":"Eskalieren"},
            ])
            prepared["data"]=native
        elif action=="telegram_bot.send_message":
            prepared.setdefault("inline_keyboard",[
                "Bestätigen:"+tokens["ack"]+", 15 Min. später:"+tokens["snooze"],
                "Eskalieren:"+tokens["escalate"],
            ])
        return prepared

    def preview(self,data):
        data=resolve_profile(data,self.settings.get("notification_profiles",DEFAULT_PROFILES))
        return simulate({
            "quiet_hours":self.quiet_hours,
            "archive_retention":self.archive_retention,
            "default_notify":self.settings.get(CONF_TARGET),
        },self.routes,data,now=time.time(),timezone=self.hass.config.time_zone)

    async def enqueue(self, data):
        data=resolve_profile(data,self.settings.get("notification_profiles",DEFAULT_PROFILES))
        try:
            extra = data.get("data") or {}
            if not isinstance(extra, dict) or any(k in extra for k in ("message", "title", "entity_id")):
                raise ValueError("data must be a mapping and cannot override message/title/entity_id")
            recipients = data.get("recipients")
            if recipients:
                if data.get("action") or data.get("target_entity"):
                    raise ValueError("use either recipients or action/target_entity")
                names = [recipients] if isinstance(recipients, str) else recipients
                presence={}
                for spec in self.routes.get("persons",{}).values():
                    entity=spec.get("entity")
                    if entity:
                        state=self.hass.states.get(entity)
                        presence[entity]=state.state if state is not None else "unknown"
                targets = resolve(self.routes, names, priority=data.get("priority","info"),
                                  presence=presence)
            else:
                # No default and no explicitly addressed recipient: persist for review,
                # never guess a mobile/Telegram destination.
                target_entity = data.get("target_entity") or self.settings.get(CONF_TARGET)
                action = data.get("action") or ("notify.send_message" if target_entity else "reliable_notify.staged")
                targets = [("", {"action": action,
                    "target_entity": target_entity or "", "data": {}})]
            ack_plan = validate_acknowledgement(data.get('acknowledgement'), data.get('dedup_key'))
            if ack_plan:
                for step in ack_plan['steps']:
                    resolve(self.routes, step['recipients'])
            jobs = []
            for name, rec in targets:
                action = rec.get("action", "notify.send_message")
                if data.get("media") == "photo" and action == "telegram_bot.send_message":
                    action = "telegram_bot.send_photo"
                if action != "reliable_notify.staged" and not valid_action(action):
                    raise ValueError(f"unsupported action: {action}")
                target = rec.get("target_entity", "") if action in ("notify.send_message", "smtp.send_message") else ("(staged)" if action == "reliable_notify.staged" else name or action)
                if action in ("notify.send_message", "smtp.send_message") and not str(target).startswith("notify."):
                    raise ValueError("notify.send_message requires a notify entity")
                if action in NATIVE_ACTIONS:
                    if not name:
                        raise ValueError("native transports require a named recipient")
                    payload=native_public_payload(action,rec.get("data",{}),extra)
                else:
                    payload = {**rec.get("data", {}), **extra}
                if ack_plan is not None:
                    payload=self._action_payload(action,payload,ack_plan["key"])
                if data.get("only_if"):
                    payload["__rn_condition"]=dict(data["only_if"])
                if any(k in payload for k in ("message", "title", "entity_id")):
                    raise ValueError("transport data may not override message/title/entity_id")
                if action.startswith("telegram_bot.") and not any(k in payload for k in ("chat_id", "entity_id", "config_entry_id")):
                    raise ValueError("Telegram bot requires data.chat_id, data.entity_id or data.config_entry_id")
                if action == "telegram_bot.send_photo" and not any(k in payload for k in ("file", "url")):
                    raise ValueError("Telegram photo requires data.file or data.url")
                days = retention_for_message(data, self.archive_retention)
                jobs.append(dict(message=data["message"], title=data.get("title"),
                    target=target, route_name=name, action=action, payload=payload,
                    priority=data.get("priority", "info"), ttl=data.get("ttl", 0),
                    dedup_key=data.get("dedup_key"), strategy=data.get("strategy", "always"),
                    archive_url=self.settings.get('archive_url') or None,
                    archive_days=days,
                    message_type=data.get('message_type') or data.get('priority', 'info')))
            stage_all = data.get("test_mode")=="stage"
            configured_test = self.settings.get("test_mode","off")=="stage"
            test_targets = set(self.settings.get("test_recipients",[]))
            for job in jobs:
                if stage_all or (configured_test and (
                    not test_targets or job["target"] in test_targets
                    or job.get("route_name") in test_targets)):
                    job["action"]="reliable_notify.staged"
                    job["target"]="(test-mode)"
                    job["payload"]={}
                    job["archive_url"]=None
            if data.get("strategy")=="digest" and (
                data.get("media","text")!="text" or "file" in extra or
                "attachments" in extra or "media_source" in extra
            ):
                raise ValueError("digest is only supported for text notifications without file attachments")
            if ack_plan and data.get("strategy")=="digest":
                raise ValueError("digest is incompatible with acknowledgements")
            for job in jobs:
                job["not_before"]=next_allowed_timestamp(
                    time.time(),job["priority"],self.quiet_hours,self.hass.config.time_zone)
                if job.get("strategy")=="digest":
                    if not job.get("dedup_key"):
                        raise ValueError("digest requires dedup_key")
                    job["digest_window_seconds"]=int(self.settings.get("digest_window_seconds",300))
            if any(job["action"]=="reliable_notify.staged" for job in jobs):
                ack_plan=None  # Test/staged messages must never escalate.
            if jobs and ack_plan:
                jobs[0]['ack_plan'] = ack_plan
            snapshots = []
            try:
                # A queued photo must not depend on a rotating camera snapshot file.
                async with self._enqueue_lock:
                    free = await asyncio.to_thread(free_disk_bytes, self.store.path.parent)
                    if free < self.min_free_bytes:
                        raise OSError('Insufficient free disk space for reliable queue')
                    for job in jobs:
                        media_paths = []
                        if job["action"] == "telegram_bot.send_photo" and job["payload"].get("file"):
                            local = job["payload"]["file"]
                            if await asyncio.to_thread(free_disk_bytes, '/media/reliable_notify') < self.min_free_bytes + Path(local).stat().st_size:
                                raise OSError('Insufficient free space for Telegram photo')
                            new_path = await asyncio.to_thread(snapshot_file, local,
                                "/media/reliable_notify", 200 * 1024 * 1024)
                            snapshots.append(new_path)
                            media_paths.append(new_path)
                            job["payload"]["file"] = new_path
                            job["media_path"] = new_path
                        if job["action"] == "smtp.send_message":
                            modified, attached = await asyncio.to_thread(
                                snapshot_attachments, job['payload'], '/media/reliable_notify',
                                min_free_bytes=self.min_free_bytes)
                            job['payload'] = modified
                            snapshots.extend(attached)
                            media_paths.extend(attached)
                        job['media_paths'] = media_paths
                    result = await self.store.enqueue_many(jobs, MAX_QUEUE)
            except Exception:
                for path in snapshots:
                    await asyncio.to_thread(Path(path).unlink, missing_ok=True)
                raise
        except Exception as err:
            raise HomeAssistantError(f"Reliable Notify could not persist notification: {err}") from err
        self.wakeup.set()
        self.hass.bus.async_fire("reliable_notify_updated", {"kind":"queued"})
        return result

    async def _deliver(self, item):
        try:
            saved_payload=json.loads(item.get("payload_json") or "{}")
        except (TypeError,ValueError):
            raise ValueError("persisted transport payload is not JSON")
        requirement=saved_payload.pop("__rn_condition",None)
        if requirement:
            state=self.hass.states.get(requirement["entity_id"])
            if state is None or state.state!=requirement["state"]:
                return False   # stale: never send an obsolete window/door alarm
        item={**item,"payload_json":json.dumps(saved_payload)}
        if item["action"] in NATIVE_ACTIONS:
            record=self.routes.get("recipients",{}).get(item["target"])
            if not record or record.get("action")!=item["action"]:
                raise ValueError("configured native transport recipient no longer exists")
            await async_deliver_native(self.hass,item["action"],record,item)
            return True
        (domain, service), payload = create_payload(item)
        if item["action"]=="telegram_bot.send_message":
            payload.setdefault("message_tag",f"rn_{item['id']}")
        if not self.hass.services.has_service(domain, service):
            raise HomeAssistantError(f"Service unavailable: {domain}.{service}")
        target = {"entity_id": item["target"]} if item["action"] in ("notify.send_message", "smtp.send_message") else None
        await asyncio.wait_for(
            self.hass.services.async_call(domain, service, payload, blocking=True, target=target),
            timeout=35)
        return True

    async def media_cleanup_loop(self):
        while not self.stopping:
            try:
                await asyncio.sleep(300)
                used = await self.store.pending_media_paths()
                await asyncio.to_thread(cleanup_media,
                    "/media/reliable_notify", used)
            except asyncio.CancelledError:
                raise
            except Exception:
                _LOGGER.exception("Reliable Notify media cleanup error")

    async def maintenance_loop(self):
        # Keep database maintenance independent from notification workers.
        while not self.stopping:
            try:
                await asyncio.sleep(60 if not self.maintenance_info else 86400)
                days=int(self.settings.get("dead_letter_days",30))
                self.maintenance_info=await self.store.maintenance(days)
                if self.maintenance_info["integrity"]!="ok":
                    _LOGGER.error("Reliable Notify database integrity check failed")
            except asyncio.CancelledError:
                raise
            except Exception:
                _LOGGER.exception("Reliable Notify maintenance failed")

    async def create_backup(self):
        if not self.settings.get("backup_enabled",True):
            raise ValueError("Reliable Notify backup disabled in settings")
        directory=self.hass.config.path(".storage","reliable_notify_backups")
        self.backup_info=await self.store.online_backup(
            directory,keep=int(self.settings.get("backup_keep",3)),
            min_free_bytes=self.min_free_bytes)
        self.backup_info["created_at"]=time.time()
        self.hass.bus.async_fire("reliable_notify_updated",{"kind":"backup"})
        return self.backup_info

    async def backup_loop(self):
        while not self.stopping:
            try:
                await asyncio.sleep(60 if not self.backup_info else 7*86400)
                if self.settings.get("backup_enabled",True):
                    await self.create_backup()
            except asyncio.CancelledError:
                raise
            except Exception:
                _LOGGER.exception("Reliable Notify online backup failed")

    async def escalation_loop(self):
        while not self.stopping:
            try:
                await asyncio.sleep(15)
                for job in await self.store.due_escalations():
                    # Validate and prepare all routes before the transaction.
                    routes=resolve(self.routes,job["step"]["recipients"],
                                   priority=job["priority"])
                    prepared=[]
                    for name,rec in routes:
                        action=rec.get("action","notify.send_message")
                        if not valid_action(action) or action=="telegram_bot.send_photo":
                            raise ValueError("escalation only supports text transports")
                        item=dict(rec)
                        data=rec.get("data",{})
                        if action in NATIVE_ACTIONS:
                            data=native_public_payload(action,data,{})
                        else:
                            data=self._action_payload(action,data,job["ack_key"])
                        item["data"]=data
                        prepared.append((name,item))
                    # Both message insertion and step advancement commit together.
                    inserted=await self.store.enqueue_escalation_atomic(
                        job["ack_key"],job["step_index"],prepared,MAX_QUEUE)
                    if inserted:
                        self.wakeup.set()
                        self.hass.bus.async_fire("reliable_notify_updated", {"kind":"escalation"})
            except asyncio.CancelledError:
                raise
            except Exception:
                _LOGGER.exception("Reliable Notify escalation processing failed")

    async def worker(self, index, lane):
        while not self.stopping:
            interval = self.settings.get(CONF_INTERVAL, DEFAULT_INTERVAL)
            try:
                item = await self.store.claim_due(lease_seconds=90, lane=lane,
                    rate_limit_per_minute=int(self.settings.get("rate_limit_per_minute",10)))
                if item:
                    try:
                        delivered=await self._deliver(item)
                    except asyncio.CancelledError:
                        raise
                    except Exception as err:
                        self.last_error = f"{item['action']}: {classify_error(err).kind}"
                        classification = classify_error(err)
                        policy = self.policies[item['priority']]
                        # Provider error messages may contain secrets; keep logs generic.
                        log_policy=validate_transport_logging(
                            self.settings.get("transport_logging",{}))
                        channel=transport_for(item["action"])
                        levels={"error":logging.ERROR,"warning":logging.WARNING,
                                "info":logging.INFO,"debug":logging.DEBUG}
                        if log_policy[channel]!="off":
                            _LOGGER.log(levels[log_policy[channel]],
                                        "Reliable Notify #%s transport=%s category=%s",
                                        item["id"],channel,classification.kind)
                        await self.store.failed(item["id"], item["attempts"] + 1,
                                                f"{type(err).__name__}: {classification.kind}",
                                                policy['base_seconds'],
                                                max_attempts=policy['max_attempts'] or None,
                                                permanent=not classification.retryable,
                                                max_delay=policy['max_delay'],
                                                retry_after=classification.retry_after,
                                                category=classification.kind)
                    else:
                        if delivered:
                            await self.store.succeeded(item["id"])
                        else:
                            await self.store.suppress(item["id"])
                        channel=transport_for(item["action"])
                        level=validate_transport_logging(
                            self.settings.get("transport_logging",{}))[channel]
                        if delivered and level in ("debug","info"):
                            _LOGGER.log(logging.DEBUG if level=="debug" else logging.INFO,
                                        "Reliable Notify #%s accepted by transport=%s",
                                        item["id"],channel)
                    self.hass.bus.async_fire("reliable_notify_updated", {"kind":"delivery"})
                    await asyncio.sleep(0)
                    continue
                # Avoid lost wake-up across multiple workers: bounded poll interval.
                self.wakeup.clear()
                try:
                    await asyncio.wait_for(self.wakeup.wait(), timeout=min(interval, 10))
                except asyncio.TimeoutError:
                    pass
            except asyncio.CancelledError:
                raise
            except Exception:
                _LOGGER.exception("Reliable Notify worker %s failed", index)
                await asyncio.sleep(interval)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    manager = ReliableNotifyManager(hass, entry)
    await manager.start()
    if not hass.data.get('reliable_notify_dashboard_registered'):
        register_dashboard(hass)
        await hass.http.async_register_static_paths([
            StaticPathConfig('/reliable_notify/reliable-notify-card.js',
                str(Path(__file__).parent / 'reliable-notify-card.js'), False),
            StaticPathConfig('/reliable_notify/reliable-notify-panel.js',
                str(Path(__file__).parent / 'reliable-notify-panel.js'), False),
        ])
        hass.data['reliable_notify_dashboard_registered'] = True
    if not hass.data.get("reliable_notify_external_api_registered"):
        hass.http.register_view(ReliableNotifyAPIView(hass))
        hass.data["reliable_notify_external_api_registered"]=True
    if not hass.data.get("reliable_notify_panel_registered"):
        await panel_custom.async_register_panel(
            hass, webcomponent_name="reliable-notify-panel",
            frontend_url_path="reliable-notify",
            sidebar_title="Reliable Notify", sidebar_icon="mdi:bell-check",
            module_url="/reliable_notify/reliable-notify-panel.js?v=3.1.1",
            require_admin=True)
        hass.data["reliable_notify_panel_registered"] = True
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = manager

    async def enqueue(call: ServiceCall):
        await manager.enqueue(call.data)

    async def telegram_lifecycle(call: ServiceCall):
        """Edit/delete an already-sent Telegram message at a configured route.

        This is an explicit provider operation; it does not claim queued retries.
        """
        route_name=call.data["recipient"]
        route=manager.routes.get("recipients",{}).get(route_name)
        if not route or route.get("action")!="telegram_bot.send_message":
            raise HomeAssistantError("Telegram recipient is not configured")
        allowed=route.get("data",{}).get("chat_id")
        if isinstance(allowed,list):
            allowed={int(item) for item in allowed}
        elif allowed is not None:
            allowed={int(allowed)}
        else:
            raise HomeAssistantError("Recipient requires explicit Telegram chat ID")
        receipts=await manager.store.telegram_receipts(call.data["dedup_key"])
        matches=[r for r in receipts if r["chat_id"] in allowed]
        if not matches:
            raise HomeAssistantError("No matching sent Telegram message found")
        operation=call.data["operation"]
        payload_data={"message_id":matches[0]["message_id"],
                      "chat_id":matches[0]["chat_id"]}
        configured_id=route.get("data",{}).get("config_entry_id")
        if configured_id:
            payload_data["config_entry_id"]=configured_id
        if operation=="edit":
            payload_data["message"]=call.data["message"]
        action="edit_message" if operation=="edit" else "delete_message"
        await hass.services.async_call("telegram_bot",action,payload_data,blocking=True)
        if operation=="delete":
            await manager.store.telegram_receipt_deleted(
                payload_data["chat_id"],payload_data["message_id"])

    async def send_template(call: ServiceCall):
        from homeassistant.helpers.template import Template
        templates=validate_templates(manager.settings.get("notification_templates",{}))
        name=call.data["template"]
        definition=templates.get(name)
        if definition is None:
            raise HomeAssistantError("Unknown Reliable Notify template")
        variables=validate_parameters(call.data.get("variables",{}))
        message=Template(definition["message"],hass).async_render(
            variables,parse_result=False)
        title=Template(definition.get("title",""),hass).async_render(
            variables,parse_result=False)
        if not isinstance(message,str) or len(message)>16384:
            raise HomeAssistantError("Rendered notification exceeds 16384 characters")
        payload={**definition,"message":message,"title":title}
        payload.update({key:call.data[key] for key in (
            "recipients","priority","dedup_key","archive","archive_days",
            "message_type","test_mode","profile") if key in call.data})
        await manager.enqueue(payload)

    async def simulate_action(call: ServiceCall):
        """Read-only preview for HA automations; never persist or send."""
        return manager.preview(call.data)

    async def create_backup(call: ServiceCall):
        return await manager.create_backup()

    async def retry(call: ServiceCall):
        await manager.store.retry_all()
        manager.wakeup.set()

    async def retry_dead(call: ServiceCall):
        await manager.store.retry_dead()
        manager.wakeup.set()

    async def clear(call: ServiceCall):
        await manager.store.clear()

    async def retry_one(call: ServiceCall):
        if not await manager.store.retry_one(call.data["id"],call.data.get("dead",False)):
            raise HomeAssistantError("Message missing, expired or currently leased")
        manager.wakeup.set()

    async def delete_one(call: ServiceCall):
        if not await manager.store.delete_one(call.data["id"],call.data.get("dead",False)):
            raise HomeAssistantError("Message missing or currently leased")

    async def update_message(call: ServiceCall):
        await manager.enqueue({**call.data,"strategy":"replace"})

    async def dismiss(call: ServiceCall):
        key=call.data["dedup_key"]
        names=call.data["recipients"]
        destinations=resolve(manager.routes,[names] if isinstance(names,str) else names,priority="info")
        mobile=[entry for _,entry in destinations if entry.get("action","").startswith("notify.mobile_app_")]
        if not mobile:
            raise HomeAssistantError("dismiss requires at least one Companion App recipient")
        await manager.store.cancel(key)
        for destination in mobile:
            await manager.enqueue({
                "message":"clear_notification",
                "action":destination["action"],
                "priority":"info",
                "archive":"delete_after_send",
                "data":{"data":{"tag":notification_tag(key)}},
            })

    async def acknowledge(call: ServiceCall):
        changed = await manager.store.acknowledgement(call.data["dedup_key"],call.data.get("by","manual"))
        if not changed:
            raise HomeAssistantError("Acknowledgement key not found or already acknowledged")

    async def cancel(call: ServiceCall):
        await manager.store.cancel(call.data["dedup_key"], call.data.get("target_entity"))

    async def reload_routes(call: ServiceCall):
        try:
            # Reload all platforms; ensure entities and service aliases track routes.
            await hass.config_entries.async_reload(entry.entry_id)
        except Exception as err:
            raise HomeAssistantError(f"Invalid routing configuration: {err}") from err

    TELEGRAM_LIFECYCLE_SCHEMA = vol.Schema({
        vol.Required("recipient"): cv.string,
        vol.Required("dedup_key"): cv.string,
        vol.Required("operation"): vol.In(("edit","delete")),
        vol.Optional("message"): cv.string,
    })
    TEMPLATE_SEND_SCHEMA = vol.Schema({
        vol.Required("template"): cv.string,
        vol.Optional("variables",default={}): dict,
        vol.Optional("recipients"): vol.Any(cv.string,[cv.string]),
        vol.Optional("priority"): vol.In(("info","warning","critical")),
        vol.Optional("dedup_key"): cv.string,
        vol.Optional("profile"): cv.string,
        vol.Optional("message_type"): cv.string,
        vol.Optional("archive"): vol.In(("keep","delete_after_send")),
        vol.Optional("archive_days"): vol.All(vol.Coerce(int),vol.Range(min=0,max=365)),
        vol.Optional("test_mode"): vol.In(("off","stage")),
    })
    for name, fn, schema in (
        ("enqueue", enqueue, ENQUEUE_SCHEMA),
        ("send_template", send_template, TEMPLATE_SEND_SCHEMA),
        ("telegram_lifecycle", telegram_lifecycle, TELEGRAM_LIFECYCLE_SCHEMA),
        ("retry_all", retry, None),
        ("retry_dead", retry_dead, None), ("clear_queue", clear, None),
        ("cancel", cancel, CANCEL_SCHEMA), ("acknowledge", acknowledge, ACK_SCHEMA),
        ("update", update_message, UPDATE_SCHEMA), ("dismiss", dismiss, DISMISS_SCHEMA),
        ("reload_routes", reload_routes, None),
        ("retry_one", retry_one, JOB_SCHEMA), ("delete_one", delete_one, JOB_SCHEMA),
    ):
        hass.services.async_register(DOMAIN, name, fn, schema=schema)
    hass.services.async_register(
        DOMAIN,"simulate",simulate_action,schema=ENQUEUE_SCHEMA,
        supports_response=SupportsResponse.ONLY)
    from homeassistant.helpers.service import async_register_admin_service
    async_register_admin_service(
        hass,DOMAIN,"backup",create_backup,schema=vol.Schema({}),
        supports_response=SupportsResponse.ONLY)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "button", "notify"])
    manager.compat_notify_services = await async_register_compat(hass, manager)
    entry.async_on_unload(entry.add_update_listener(_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    if not await hass.config_entries.async_unload_platforms(entry, ['sensor', 'button', 'notify']):
        return False
    manager = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if manager is not None:
        async_unregister_compat(hass, getattr(manager, 'compat_notify_services', []))
        await manager.stop()
    # WebSocket endpoints are HA-lifetime registrations; panel can be re-added on reload.
    if not hass.data.get(DOMAIN):
        frontend.async_remove_panel(hass,"reliable-notify",warn_if_unknown=False)
        hass.data.pop('reliable_notify_panel_registered',None)
        for service in ('enqueue', 'retry_all', 'retry_dead', 'clear_queue', 'cancel',
                        'reload_routes', 'retry_one', 'delete_one', 'acknowledge', 'update', 'dismiss', 'simulate', 'backup', 'send_template', 'telegram_lifecycle'):
            hass.services.async_remove(DOMAIN, service)
    return True


async def _reload_entry(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


