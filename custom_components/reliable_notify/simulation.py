"""Pure policy preview; never opens a transport connection."""
from __future__ import annotations
from datetime import datetime
from .routing import resolve
from .retention import retention_for_message
from .smart import next_allowed_timestamp


def simulate(settings, routes, data, *, now, timezone):
    """Explain route and scheduling decisions without touching SQLite."""
    priority=data.get("priority","info")
    recipients=data.get("recipients") or []
    names=[recipients] if isinstance(recipients,str) else list(recipients)
    resolved=resolve(routes,names,priority=priority) if names else []
    target_names=[{"recipient":name,"action":route.get("action","notify.send_message")}
                  for name,route in resolved]
    not_before=next_allowed_timestamp(
        now,priority,settings.get("quiet_hours",{}),timezone)
    archive_days=retention_for_message(
        data,settings.get("archive_retention",{}))
    return {"mode":"dry_run","priority":priority,"recipients":target_names,
            "staged":not bool(names) and not settings.get("default_notify"),
            "not_before":not_before,"scheduled":not_before>now,
            "archive_days":archive_days,"would_enqueue":len(target_names),
            "would_send":False,"timestamp":datetime.fromtimestamp(now).isoformat()}
