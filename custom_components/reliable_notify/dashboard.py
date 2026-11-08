"""Admin-only WebSocket status for an interactive Lovelace card.

The card never receives notification bodies or provider credentials.
"""
from __future__ import annotations

import voluptuous as vol
from homeassistant.components import websocket_api

from .const import DOMAIN
from .retry import validate_policies
from .retention import validate_retention
from .smart import validate_quiet_hours
from .i18n import text as i18n_text
from .routing import (display_name, merge_routes, validate_config, valid_label,
                      ROUTE_KINDS, MAX_LABEL)


def register_dashboard(hass):
    @websocket_api.websocket_command({vol.Required("type"): "reliable_notify/dashboard", vol.Optional("limit", default=50): vol.All(vol.Coerce(int), vol.Range(min=1, max=100))})
    @websocket_api.async_response
    async def get_dashboard(hass, connection, msg):
        if not connection.user.is_admin:
            connection.send_error(msg['id'], 'unauthorized', 'Administrator required')
            return
        managers = hass.data.get(DOMAIN, {})
        if not managers:
            connection.send_error(msg['id'], 'not_loaded', 'Reliable Notify not loaded')
            return
        manager = next(iter(managers.values()))
        count, dead, metrics, recent, dead_recent, history, staged = await __import__('asyncio').gather(
            manager.store.count(), manager.store.dead_count(), manager.store.metrics(),
            manager.store.recent(msg['limit']), manager.store.recent(msg['limit'], dead=True),
            manager.store.history(msg['limit']), manager.store.staged(msg['limit']),
        )
        connection.send_result(msg['id'], {
            'count': count, 'dead': dead, 'metrics': metrics,
            'queue': recent, 'dead_letters': dead_recent, 'history': history,
            'staged': staged, 'staged_count': len(staged),
            'recipient_names': sorted(manager.routes['recipients']),
            'persons': sorted(manager.routes.get('persons', {})),
            'labels': dict(manager.routes.get('labels', {})),
            'policies': manager.policies, 'retention': manager.archive_retention, 'storage': await manager.storage_status(),
            'acknowledgements': await manager.store.active_acknowledgements(), 'maintenance': manager.maintenance_info,
            'smart': {'quiet_hours':manager.quiet_hours,
                      'rate_limit_per_minute':int(manager.settings.get('rate_limit_per_minute',10)),
                      'digest_window_seconds':int(manager.settings.get('digest_window_seconds',300))},
        })

    @websocket_api.websocket_command({
        vol.Required('type'): 'reliable_notify/set_retry_policies',
        vol.Required('policies'): dict,
    })
    @websocket_api.async_response
    async def set_policies(hass, connection, msg):
        if not connection.user.is_admin:
            connection.send_error(msg['id'], 'unauthorized', 'Administrator required')
            return
        manager = next(iter(hass.data.get(DOMAIN, {}).values()), None)
        if manager is None:
            connection.send_error(msg['id'], 'not_loaded', 'Reliable Notify not loaded')
            return
        try:
            policies = validate_policies(msg['policies'])
        except ValueError as err:
            connection.send_error(msg['id'], 'invalid_policy', str(err))
            return
        hass.config_entries.async_update_entry(manager.entry, options={
            **manager.entry.options, 'retry_policies': policies,
        })
        connection.send_result(msg['id'], {'saved': True})

    @websocket_api.websocket_command({vol.Required('type'): 'reliable_notify/send_staged',
                                       vol.Required('id'): vol.All(vol.Coerce(int), vol.Range(min=1)),
                                       vol.Required('recipient'): str})
    @websocket_api.async_response
    async def send_staged(hass, connection, msg):
        if not connection.user.is_admin:
            connection.send_error(msg['id'], 'unauthorized', 'Administrator required')
            return
        manager = next(iter(hass.data.get(DOMAIN, {}).values()), None)
        if manager is None:
            connection.send_error(msg['id'], 'not_loaded', 'Reliable Notify not loaded')
            return
        recipient = manager.routes['recipients'].get(msg['recipient'])
        if not recipient:
            connection.send_error(msg['id'], 'invalid_recipient', 'Select a configured individual recipient')
            return
        from .routing import valid_action
        action = recipient.get('action', 'notify.send_message')
        if not valid_action(action):
            connection.send_error(msg['id'], 'invalid_action', 'Invalid recipient action')
            return
        target = recipient.get('target_entity', '') if action in ('notify.send_message','smtp.send_message') else msg['recipient']
        updated = await manager.store.assign_staged(msg['id'], action, target, recipient.get('data', {}))
        if not updated:
            connection.send_error(msg['id'], 'not_found', 'Staged message no longer available')
            return
        manager.wakeup.set()
        connection.send_result(msg['id'], {'assigned': True})


    @websocket_api.websocket_command({
        vol.Required('type'): 'reliable_notify/archive',
        vol.Optional('limit', default=50): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
        vol.Optional('search', default=''): vol.All(str, vol.Length(max=200)),
    })
    @websocket_api.async_response
    async def archive_search(hass, connection, msg):
        if not connection.user.is_admin:
            connection.send_error(msg['id'], 'unauthorized', 'Administrator required')
            return
        manager = next(iter(hass.data.get(DOMAIN, {}).values()), None)
        if manager is None:
            connection.send_error(msg['id'], 'not_loaded', 'Reliable Notify not loaded')
            return
        rows = await manager.store.archive_list(msg['limit'], msg['search'])
        connection.send_result(msg['id'], {'items': rows})

    @websocket_api.websocket_command({
        vol.Required('type'): 'reliable_notify/archive_detail',
        vol.Required('message_id'): vol.All(vol.Coerce(int), vol.Range(min=1)),
    })
    @websocket_api.async_response
    async def archive_detail(hass, connection, msg):
        if not connection.user.is_admin:
            connection.send_error(msg['id'], 'unauthorized', 'Administrator required')
            return
        manager = next(iter(hass.data.get(DOMAIN, {}).values()), None)
        if manager is None:
            connection.send_error(msg['id'], 'not_loaded', 'Reliable Notify not loaded')
            return
        item = await manager.store.archive_detail(msg['message_id'])
        if item is None:
            connection.send_error(msg['id'], 'not_found', 'Message not in archive')
            return
        connection.send_result(msg['id'], item)

    @websocket_api.websocket_command({
        vol.Required('type'): 'reliable_notify/set_archive_retention',
        vol.Required('retention'): dict,
    })
    @websocket_api.async_response
    async def set_retention(hass, connection, msg):
        if not connection.user.is_admin:
            connection.send_error(msg['id'], 'unauthorized', 'Administrator required')
            return
        manager = next(iter(hass.data.get(DOMAIN, {}).values()), None)
        if manager is None:
            connection.send_error(msg['id'], 'not_loaded', 'Reliable Notify not loaded')
            return
        try:
            configured = validate_retention(msg['retention'])
        except ValueError as err:
            connection.send_error(msg['id'], 'invalid_retention', str(err))
            return
        hass.config_entries.async_update_entry(manager.entry, options={
            **manager.entry.options, 'archive_retention': configured,
        })
        connection.send_result(msg['id'], {'saved': True})

    @websocket_api.websocket_command({
        vol.Required('type'): 'reliable_notify/acknowledge',
        vol.Required('key'): str,
    })
    @websocket_api.async_response
    async def acknowledge_command(hass, connection, msg):
        if not connection.user.is_admin:
            connection.send_error(msg['id'], 'unauthorized', 'Administrator required')
            return
        manager=next(iter(hass.data.get(DOMAIN, {}).values()),None)
        if manager is None:
            connection.send_error(msg['id'], 'not_loaded', 'Reliable Notify not loaded')
            return
        changed=await manager.store.acknowledgement(msg['key'], connection.user.name or 'admin')
        connection.send_result(msg['id'], {'acknowledged':bool(changed)})

    @websocket_api.websocket_command({
        vol.Required('type'): 'reliable_notify/set_smart_settings',
        vol.Required('quiet_hours'): dict,
        vol.Required('rate_limit_per_minute'): vol.All(vol.Coerce(int),vol.Range(min=1,max=1000)),
        vol.Required('digest_window_seconds'): vol.All(vol.Coerce(int),vol.Range(min=10,max=3600)),
    })
    @websocket_api.async_response
    async def set_smart(hass,connection,msg):
        if not connection.user.is_admin:
            connection.send_error(msg['id'],'unauthorized','Administrator required')
            return
        manager=next(iter(hass.data.get(DOMAIN,{}).values()),None)
        if manager is None:
            connection.send_error(msg['id'],'not_loaded','Reliable Notify not loaded')
            return
        try:
            policy=validate_quiet_hours(msg['quiet_hours'])
        except ValueError as err:
            connection.send_error(msg['id'],'invalid_policy',str(err))
            return
        hass.config_entries.async_update_entry(manager.entry,options={
            **manager.entry.options,
            'quiet_hours':policy,
            'rate_limit_per_minute':msg['rate_limit_per_minute'],
            'digest_window_seconds':msg['digest_window_seconds'],
        })
        connection.send_result(msg['id'],{'saved':True})

    @websocket_api.websocket_command({
        vol.Required("type"): "reliable_notify/simulate",
        vol.Required("notification"): dict,
    })
    @websocket_api.async_response
    async def dry_run(hass,connection,msg):
        if not connection.user.is_admin:
            connection.send_error(msg['id'],"unauthorized","Administrator required")
            return
        manager=next(iter(hass.data.get(DOMAIN,{}).values()),None)
        if manager is None:
            connection.send_error(msg["id"],"not_loaded","Integration unavailable")
            return
        try:
            result=manager.preview(msg["notification"])
        except (ValueError,TypeError,KeyError) as err:
            connection.send_error(msg['id'],"invalid_input",str(err))
            return
        connection.send_result(msg["id"],result)

    @websocket_api.websocket_command({
        vol.Required("type"): "reliable_notify/admin_inventory",
    })
    @websocket_api.async_response
    async def admin_inventory(hass,connection,msg):
        if not connection.user.is_admin:
            connection.send_error(msg['id'],"unauthorized","Administrator required")
            return
        manager=next(iter(hass.data.get(DOMAIN,{}).values()),None)
        if manager is None:
            connection.send_error(msg["id"],"not_loaded","Integration unavailable")
            return
        services=hass.services.async_services()
        phones=sorted("notify."+name for name in services.get("notify",{})
                      if name.startswith("mobile_app_"))
        # Never expose per-recipient transport credentials/chat IDs.
        routes=manager.routes
        recipients={name:{"action":record.get("action","notify.send_message"),
                          "target_entity":record.get("target_entity","")}
                    for name,record in routes.get("recipients",{}).items()}
        connection.send_result(msg["id"],{
            "companion_actions":phones,
            "people":sorted(hass.states.async_entity_ids("person")),
            "notify_entities":sorted(hass.states.async_entity_ids("notify")),
            "routes":{"recipients":recipients,"groups":routes.get("groups",{}),
                      "persons":routes.get("persons",{})},
            # Display names only; routing keeps using the internal aliases.
            "labels":dict(routes.get("labels",{})),
            "options_routes":{"recipients":sorted(manager.entry.options.get("routes",{}).get("recipients",{})),
                             "groups":sorted(manager.entry.options.get("routes",{}).get("groups",{})),
                             "persons":sorted(manager.entry.options.get("routes",{}).get("persons",{}))},
        })

    @websocket_api.websocket_command({
        vol.Required("type"): "reliable_notify/route_definition",
        vol.Required("category"): vol.In(("recipients", "groups", "persons")),
        vol.Required("name"): str,
    })
    @websocket_api.async_response
    async def route_definition(hass, connection, msg):
        # Full transport settings are fetched only for an explicit admin edit.
        # The inventory and diagnostics remain redacted.
        if not connection.user.is_admin:
            connection.send_error(msg["id"], "unauthorized", "Administrator required")
            return
        manager = next(iter(hass.data.get(DOMAIN, {}).values()), None)
        if manager is None:
            connection.send_error(msg["id"], "not_loaded", "Integration unavailable")
            return
        definition = manager.routes.get(msg["category"], {}).get(msg["name"])
        if definition is None:
            connection.send_error(msg["id"], "not_found", "Route unavailable")
            return
        connection.send_result(msg["id"], {"definition": definition})

    @websocket_api.websocket_command({
        vol.Required("type"): "reliable_notify/test_route",
        vol.Required("category"): vol.In(("recipients", "groups", "persons")),
        vol.Required("name"): str,
        vol.Optional("language", default="en"): vol.In(("de", "en")),
    })
    @websocket_api.async_response
    async def test_route(hass, connection, msg):
        """Queue an explicit, real test through the normal delivery pipeline."""
        if not connection.user.is_admin:
            connection.send_error(msg["id"], "unauthorized", "Administrator required")
            return
        manager = next(iter(hass.data.get(DOMAIN, {}).values()), None)
        if manager is None:
            connection.send_error(msg["id"], "not_loaded", "Integration unavailable")
            return
        name = msg["name"]
        if name not in manager.routes.get(msg["category"], {}):
            connection.send_error(msg["id"], "not_found", "Save the target before testing it")
            return
        language = msg.get("language", "en")
        notification = {
            "recipients": [name], "priority": "info", "strategy": "always",
            "title": i18n_text(language, "test_title"),
            "message": i18n_text(language, "test_message", name=display_name(manager.routes, name)),
            "message_type": "test", "archive_days": 1, "ttl": 86400,
        }
        try:
            scheduled = manager.preview(notification).get("not_before")
            ids = await manager.enqueue(notification)
        except Exception:
            # Transport settings can contain secrets; do not echo exception payloads.
            connection.send_error(msg["id"], "test_failed", "Could not queue test; check target configuration and diagnostics")
            return
        connection.send_result(msg["id"], {"ids": ids, "not_before": scheduled})

    @websocket_api.websocket_command({
        vol.Required("type"): "reliable_notify/set_route",
        vol.Required("category"): vol.In(("recipients","groups","persons")),
        vol.Required("name"): vol.Match(r"^[a-z][a-z0-9_]{0,63}$", msg="Invalid internal name: use 1–64 lowercase letters, digits or underscores; start with a letter. Example: rn_kw_telegram (not RN-KW-Telegram)."),
        vol.Optional("definition"): object,
        # Optional human-readable name (Klarname); empty removes it.
        vol.Optional("label"): vol.Any(None, str),
        vol.Optional("delete",default=False): bool,
    })
    @websocket_api.async_response
    async def set_route(hass,connection,msg):
        if not connection.user.is_admin:
            connection.send_error(msg["id"],"unauthorized","Administrator required")
            return
        manager=next(iter(hass.data.get(DOMAIN,{}).values()),None)
        if manager is None:
            connection.send_error(msg["id"],"not_loaded","Integration unavailable")
            return
        category,name=msg["category"],msg["name"]
        old=manager.entry.options.get("routes",{})
        updated={kind:dict(old.get(kind,{}))
                 for kind in ROUTE_KINDS}
        labels=dict(old.get("labels",{}))
        if msg["delete"]:
            if name not in updated[category]:
                connection.send_error(msg["id"],"not_managed","Only UI-managed entries may be deleted")
                return
            updated[category].pop(name)
            labels.pop(name,None)
        else:
            if "definition" not in msg:
                connection.send_error(msg["id"],"bad_input","Missing route definition")
                return
            updated[category][name]=msg["definition"]
            if "label" in msg:
                label=(msg["label"] or "").strip()
                if label and not valid_label(label):
                    connection.send_error(msg["id"],"invalid_label",
                        f"Display name: 1-{MAX_LABEL} characters, no control characters")
                    return
                if label and label!=name:
                    labels[name]=label
                else:
                    labels.pop(name,None)
        from . import _load_routes
        file_routes=await __import__("asyncio").to_thread(_load_routes,manager.route_path)
        merged=merge_routes(file_routes,{**updated,"labels":labels})
        try:
            validate_config(merged)
        except (TypeError,ValueError) as err:
            connection.send_error(msg["id"],"invalid_route",str(err))
            return
        stored={**updated}
        if labels:
            stored["labels"]=labels
        hass.config_entries.async_update_entry(manager.entry,options={
            **manager.entry.options,"routes":stored,
        })
        connection.send_result(msg["id"],{"saved":True})

    @websocket_api.websocket_command({
        vol.Required("type"): "reliable_notify/settings_v2",
        vol.Optional("test_mode"): vol.In(("off","stage")),
        vol.Optional("test_recipients"): [str],
        vol.Optional("transport_logging"): dict,
    })
    @websocket_api.async_response
    async def settings_v2(hass,connection,msg):
        if not connection.user.is_admin:
            connection.send_error(msg["id"],"unauthorized","Administrator required")
            return
        manager=next(iter(hass.data.get(DOMAIN,{}).values()),None)
        if manager is None:
            connection.send_error(msg["id"],"not_loaded","Integration unavailable")
            return
        from .logging_utils import validate_transport_logging
        opts=dict(manager.entry.options)
        if "test_mode" in msg:opts["test_mode"]=msg["test_mode"]
        if "test_recipients" in msg:
            if len(msg["test_recipients"])>100 or any(len(x)>100 for x in msg["test_recipients"]):
                connection.send_error(msg["id"],"invalid_input","Too many test recipients")
                return
            opts["test_recipients"]=msg["test_recipients"]
        if "transport_logging" in msg:
            try:opts["transport_logging"]=validate_transport_logging(msg["transport_logging"])
            except ValueError as err:
                connection.send_error(msg["id"],"invalid_input",str(err))
                return
        hass.config_entries.async_update_entry(manager.entry,options=opts)
        connection.send_result(msg["id"],{"saved":True})

    @websocket_api.websocket_command({
        vol.Required("type"): "reliable_notify/incident_action",
        vol.Required("key"): vol.All(str,vol.Length(min=1,max=128)),
        vol.Required("action"): vol.In(("ack","snooze","escalate")),
    })
    @websocket_api.async_response
    async def incident_action(hass,connection,msg):
        if not connection.user.is_admin:
            connection.send_error(msg["id"],"unauthorized","Administrator required")
            return
        manager=next(iter(hass.data.get(DOMAIN,{}).values()),None)
        if manager is None:
            connection.send_error(msg["id"],"not_loaded","Integration unavailable")
            return
        changed=await manager.store.act_on_incident(
            msg["key"],msg["action"],connection.user.name or "HA admin")
        if changed:
            manager.hass.bus.async_fire("reliable_notify_updated",{"kind":"incident"})
        connection.send_result(msg["id"],{"changed":bool(changed)})

    @websocket_api.websocket_command({
        vol.Required("type"): "reliable_notify/statistics",
        vol.Optional("days",default=7): vol.All(vol.Coerce(int),vol.Range(min=1,max=30)),
    })
    @websocket_api.async_response
    async def statistics(hass,connection,msg):
        if not connection.user.is_admin:
            connection.send_error(msg["id"],"unauthorized","Administrator required")
            return
        manager=next(iter(hass.data.get(DOMAIN,{}).values()),None)
        if manager is None:
            connection.send_error(msg["id"],"not_loaded","Integration unavailable")
            return
        stats=await manager.store.statistics(msg["days"])
        storage=await manager.storage_status()
        connection.send_result(msg["id"],{
            **stats,"storage":storage,"maintenance":manager.maintenance_info,
            "test_mode":manager.settings.get("test_mode","off"),
            "test_recipients":manager.settings.get("test_recipients",[]),
            "transport_logging":manager.settings.get("transport_logging",{}),
            "version":"3.1.0",
            "daily_trends":await manager.store.long_term_statistics(365),
        })

    @websocket_api.websocket_command({vol.Required("type"): "reliable_notify/migration_scan"})
    @websocket_api.async_response
    async def migration_scan_command(hass, connection, msg):
        if not connection.user.is_admin:
            connection.send_error(msg["id"], "unauthorized", "Administrator required")
            return
        manager=next(iter(hass.data.get(DOMAIN,{}).values()),None)
        if manager is None:
            connection.send_error(msg["id"], "not_loaded", "Integration unavailable")
            return
        from .migration_scan import scan_automation_files
        report=await scan_automation_files(hass.config.config_dir,manager.routes)
        connection.send_result(msg["id"],report)

    @websocket_api.websocket_command({
        vol.Required("type"): "reliable_notify/templates",
    })
    @websocket_api.async_response
    async def list_templates(hass,connection,msg):
        if not connection.user.is_admin:
            connection.send_error(msg["id"],"unauthorized","Administrator required")
            return
        manager=next(iter(hass.data.get(DOMAIN,{}).values()),None)
        if manager is None:
            connection.send_error(msg["id"],"not_loaded","Integration unavailable")
            return
        from .templates import validate_templates
        connection.send_result(msg["id"],
            {"templates":validate_templates(manager.settings.get("notification_templates",{}))})

    @websocket_api.websocket_command({
        vol.Required("type"): "reliable_notify/set_templates",
        vol.Required("templates"): dict,
    })
    @websocket_api.async_response
    async def save_templates(hass,connection,msg):
        if not connection.user.is_admin:
            connection.send_error(msg["id"],"unauthorized","Administrator required")
            return
        manager=next(iter(hass.data.get(DOMAIN,{}).values()),None)
        if manager is None:
            connection.send_error(msg["id"],"not_loaded","Integration unavailable")
            return
        from .templates import validate_templates
        try:
            validated=validate_templates(msg["templates"])
        except ValueError as err:
            connection.send_error(msg["id"],"invalid_templates",str(err))
            return
        hass.config_entries.async_update_entry(manager.entry,options={
            **manager.entry.options,"notification_templates":validated})
        connection.send_result(msg["id"],{"saved":True})

    @websocket_api.websocket_command({vol.Required("type"): "reliable_notify/profiles"})
    @websocket_api.async_response
    async def list_profiles(hass,connection,msg):
        if not connection.user.is_admin:
            connection.send_error(msg["id"],"unauthorized","Administrator required")
            return
        manager=next(iter(hass.data.get(DOMAIN,{}).values()),None)
        if manager is None:
            connection.send_error(msg["id"],"not_loaded","Integration unavailable")
            return
        from .profiles import validate_profiles, DEFAULT
        connection.send_result(msg["id"],{
            "profiles":validate_profiles(manager.settings.get("notification_profiles",DEFAULT)),
            "external_api_enabled":manager.settings.get("external_api_enabled",False),
            "external_api_recipients":manager.settings.get("external_api_recipients",[]),
            "external_api_rate":manager.settings.get("external_api_rate",30),
        })

    @websocket_api.websocket_command({
        vol.Required("type"): "reliable_notify/set_profiles",
        vol.Required("profiles"): dict,
    })
    @websocket_api.async_response
    async def set_profiles(hass,connection,msg):
        if not connection.user.is_admin:
            connection.send_error(msg["id"],"unauthorized","Administrator required")
            return
        manager=next(iter(hass.data.get(DOMAIN,{}).values()),None)
        if manager is None:
            connection.send_error(msg["id"],"not_loaded","Integration unavailable")
            return
        from .profiles import validate_profiles
        try:
            validated=validate_profiles(msg["profiles"])
        except ValueError as err:
            connection.send_error(msg["id"],"invalid_profiles",str(err))
            return
        hass.config_entries.async_update_entry(manager.entry,options={
            **manager.entry.options,"notification_profiles":validated,
        })
        connection.send_result(msg["id"],{"saved":True})

    @websocket_api.websocket_command({
        vol.Required("type"): "reliable_notify/set_external_api",
        vol.Required("enabled"): bool,
        vol.Required("recipients"): [str],
        vol.Required("rate"): vol.All(vol.Coerce(int),vol.Range(min=1,max=60)),
    })
    @websocket_api.async_response
    async def set_external_api(hass,connection,msg):
        if not connection.user.is_admin:
            connection.send_error(msg["id"],"unauthorized","Administrator required")
            return
        manager=next(iter(hass.data.get(DOMAIN,{}).values()),None)
        if manager is None:
            connection.send_error(msg["id"],"not_loaded","Integration unavailable")
            return
        allowed=(set(manager.routes.get("recipients",{})) |
                 set(manager.routes.get("groups",{})) |
                 set(manager.routes.get("persons",{})))
        if len(msg["recipients"])>50 or any(n not in allowed for n in msg["recipients"]):
            connection.send_error(msg["id"],"invalid_recipients","Invalid route allowlist")
            return
        hass.config_entries.async_update_entry(manager.entry,options={
            **manager.entry.options,
            "external_api_enabled":msg["enabled"],
            "external_api_recipients":msg["recipients"],
            "external_api_rate":msg["rate"],
        })
        connection.send_result(msg["id"],{"saved":True})

    @websocket_api.websocket_command({
        vol.Required("type"): "reliable_notify/migration_apply",
        vol.Required("file"): str,
        vol.Required("sha256"): vol.Match(r"^[a-f0-9]{64}$"),
        vol.Required("path"): str,
        vol.Required("confirmation"): vol.In(("APPLY_SINGLE_CHANGE",)),
    })
    @websocket_api.async_response
    async def apply_migration(hass,connection,msg):
        if not connection.user.is_admin:
            connection.send_error(msg["id"],"unauthorized","Administrator required")
            return
        manager=next(iter(hass.data.get(DOMAIN,{}).values()),None)
        if manager is None:
            connection.send_error(msg["id"],"not_loaded","Integration unavailable")
            return
        from .migration_apply import apply_single_package_change, MigrationError
        try:
            result=await apply_single_package_change(
                hass.config.config_dir,msg["file"],msg["sha256"],
                msg["path"],manager.routes,msg["confirmation"])
        except MigrationError as err:
            # The message is a stable code; the panel shows it in German or English.
            connection.send_error(msg["id"],"migration_failed",err.code)
            return
        except (ValueError,TypeError,KeyError,OSError) as err:
            connection.send_error(msg["id"],"migration_failed",type(err).__name__)
            return
        connection.send_result(msg["id"],result)

    websocket_api.async_register_command(hass, get_dashboard)
    websocket_api.async_register_command(hass, apply_migration)
    websocket_api.async_register_command(hass, list_profiles)
    websocket_api.async_register_command(hass, set_profiles)
    websocket_api.async_register_command(hass, set_external_api)
    websocket_api.async_register_command(hass, list_templates)
    websocket_api.async_register_command(hass, save_templates)
    websocket_api.async_register_command(hass, migration_scan_command)
    websocket_api.async_register_command(hass, dry_run)
    websocket_api.async_register_command(hass, admin_inventory)
    websocket_api.async_register_command(hass, test_route)
    websocket_api.async_register_command(hass, set_route)
    websocket_api.async_register_command(hass, route_definition)
    websocket_api.async_register_command(hass, settings_v2)
    websocket_api.async_register_command(hass, incident_action)
    websocket_api.async_register_command(hass, statistics)
    websocket_api.async_register_command(hass, set_smart)
    websocket_api.async_register_command(hass, acknowledge_command)
    websocket_api.async_register_command(hass, set_retention)
    websocket_api.async_register_command(hass, archive_search)
    websocket_api.async_register_command(hass, archive_detail)
    websocket_api.async_register_command(hass, send_staged)
    websocket_api.async_register_command(hass, set_policies)
