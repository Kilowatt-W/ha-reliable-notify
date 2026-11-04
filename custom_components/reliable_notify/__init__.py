"""Reliable Notify: durable multi-recipient delivery via HA actions."""
from __future__ import annotations

import asyncio
import logging
import json
from pathlib import Path

import voluptuous as vol
import yaml
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.components.http import StaticPathConfig

from .const import CONF_INTERVAL, CONF_TARGET, DEFAULT_INTERVAL, DOMAIN, MAX_QUEUE
from .routing import resolve, validate_config, valid_action
from .store import QueueStore
from .transport import create_payload
from .media import snapshot_file, cleanup_media, snapshot_attachments, free_disk_bytes
from .retry import classify_error, validate_policies, DEFAULT_POLICIES
from .dashboard import register_dashboard

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
    vol.Optional("priority", default="info"): vol.In(("info", "warning", "critical")),
    vol.Optional("ttl", default=0): vol.All(vol.Coerce(int), vol.Range(min=0)),
    vol.Optional("dedup_key"): cv.string,
    vol.Optional("strategy", default="always"): vol.In(("always", "replace")),
})
JOB_SCHEMA = vol.Schema({vol.Required("id"): vol.All(vol.Coerce(int),vol.Range(min=1)),
                         vol.Optional("dead", default=False): cv.boolean})
CANCEL_SCHEMA = vol.Schema({vol.Required("dedup_key"): cv.string, vol.Optional("target_entity"): cv.string})


def _load_routes(path):
    file = Path(path)
    if not file.exists():
        return {"recipients": {}, "groups": {}}
    with file.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    return validate_config(raw)


class ReliableNotifyManager:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass, self.entry = hass, entry
        self.store = QueueStore(hass.config.path(".storage", "reliable_notify.db"))
        self.route_path = hass.config.path("reliable_notify_routes.yaml")
        self.routes = {"recipients": {}, "groups": {}}
        self.wakeup = asyncio.Event()
        self.tasks = []
        self.stopping = False
        self._enqueue_lock = asyncio.Lock()
        self.last_error = None
        self.min_free_bytes = 100 * 1024 * 1024

    @property
    def settings(self):
        return {**self.entry.data, **self.entry.options}

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
        })
        _LOGGER.info("Reliable Notify: %s recipients and %s groups loaded",
                     len(self.routes["recipients"]), len(self.routes["groups"]))

    async def start(self):
        await self.reload_routes()
        # Dedicated Telegram worker; two independently operating general notify workers.
        for index, lane in enumerate(LANES):
            self.tasks.append(self.hass.async_create_task(self.worker(index, lane), eager_start=False))
        self.tasks.append(self.hass.async_create_task(self.media_cleanup_loop(), eager_start=False))

    async def stop(self):
        self.stopping = True
        self.wakeup.set()
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()

    async def enqueue(self, data):
        try:
            extra = data.get("data") or {}
            if not isinstance(extra, dict) or any(k in extra for k in ("message", "title", "entity_id")):
                raise ValueError("data must be a mapping and cannot override message/title/entity_id")
            recipients = data.get("recipients")
            if recipients:
                if data.get("action") or data.get("target_entity"):
                    raise ValueError("use either recipients or action/target_entity")
                names = [recipients] if isinstance(recipients, str) else recipients
                targets = resolve(self.routes, names)
            else:
                # No default and no explicitly addressed recipient: persist for review,
                # never guess a mobile/Telegram destination.
                target_entity = data.get("target_entity") or self.settings.get(CONF_TARGET)
                action = data.get("action") or ("notify.send_message" if target_entity else "reliable_notify.staged")
                targets = [("", {"action": action,
                    "target_entity": target_entity or "", "data": {}})]
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
                payload = {**rec.get("data", {}), **extra}
                if any(k in payload for k in ("message", "title", "entity_id")):
                    raise ValueError("transport data may not override message/title/entity_id")
                if action.startswith("telegram_bot.") and not any(k in payload for k in ("chat_id", "entity_id", "config_entry_id")):
                    raise ValueError("Telegram bot requires data.chat_id, data.entity_id or data.config_entry_id")
                if action == "telegram_bot.send_photo" and not any(k in payload for k in ("file", "url")):
                    raise ValueError("Telegram photo requires data.file or data.url")
                jobs.append(dict(message=data["message"], title=data.get("title"),
                    target=target, action=action, payload=payload,
                    priority=data.get("priority", "info"), ttl=data.get("ttl", 0),
                    dedup_key=data.get("dedup_key"), strategy=data.get("strategy", "always"),
                    archive_url=self.settings.get("archive_url") or None))
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
        return result

    async def _deliver(self, item):
        (domain, service), payload = create_payload(item)
        if not self.hass.services.has_service(domain, service):
            raise HomeAssistantError(f"Service unavailable: {domain}.{service}")
        target = {"entity_id": item["target"]} if item["action"] in ("notify.send_message", "smtp.send_message") else None
        await asyncio.wait_for(
            self.hass.services.async_call(domain, service, payload, blocking=True, target=target),
            timeout=35)

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

    async def worker(self, index, lane):
        while not self.stopping:
            interval = self.settings.get(CONF_INTERVAL, DEFAULT_INTERVAL)
            try:
                item = await self.store.claim_due(lease_seconds=90, lane=lane)
                if item:
                    try:
                        await self._deliver(item)
                    except asyncio.CancelledError:
                        raise
                    except Exception as err:
                        self.last_error = f"{item['action']}: {classify_error(err).kind}"
                        classification = classify_error(err)
                        policy = self.policies[item['priority']]
                        # Provider error messages may contain secrets; keep logs generic.
                        _LOGGER.warning("Reliable Notify #%s %s failed (%s)",
                                        item["id"], item['action'], classification.kind)
                        await self.store.failed(item["id"], item["attempts"] + 1,
                                                f"{type(err).__name__}: {classification.kind}",
                                                policy['base_seconds'],
                                                max_attempts=policy['max_attempts'] or None,
                                                permanent=not classification.retryable,
                                                max_delay=policy['max_delay'],
                                                retry_after=classification.retry_after,
                                                category=classification.kind)
                    else:
                        await self.store.succeeded(item["id"])
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
                str(Path(__file__).parent / 'reliable-notify-card.js'), False)
        ])
        hass.data['reliable_notify_dashboard_registered'] = True
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = manager

    async def enqueue(call: ServiceCall):
        await manager.enqueue(call.data)

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

    async def cancel(call: ServiceCall):
        await manager.store.cancel(call.data["dedup_key"], call.data.get("target_entity"))

    async def reload_routes(call: ServiceCall):
        try:
            await manager.reload_routes()
        except Exception as err:
            raise HomeAssistantError(f"Invalid routing configuration: {err}") from err

    for name, fn, schema in (
        ("enqueue", enqueue, ENQUEUE_SCHEMA), ("retry_all", retry, None),
        ("retry_dead", retry_dead, None), ("clear_queue", clear, None),
        ("cancel", cancel, CANCEL_SCHEMA), ("reload_routes", reload_routes, None),
        ("retry_one", retry_one, JOB_SCHEMA), ("delete_one", delete_one, JOB_SCHEMA),
    ):
        hass.services.async_register(DOMAIN, name, fn, schema=schema)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "button"])
    entry.async_on_unload(entry.add_update_listener(_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    if not await hass.config_entries.async_unload_platforms(entry, ['sensor', 'button']):
        return False
    manager = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if manager is not None:
        await manager.stop()
    # Handlers and static assets are registered once per HA lifetime.
    if not hass.data.get(DOMAIN):
        for service in ('enqueue', 'retry_all', 'retry_dead', 'clear_queue', 'cancel',
                        'reload_routes', 'retry_one', 'delete_one'):
            hass.services.async_remove(DOMAIN, service)
    return True


async def _reload_entry(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


