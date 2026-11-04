"""Predict routing and scheduling without DB writes or transport side effects."""
from __future__ import annotations
from datetime import datetime
from .routing import resolve, valid_action
from .retention import retention_for_message
from .smart import next_allowed_timestamp


def simulate(settings, routes, data, *, now, timezone):
    if not isinstance(data,dict) or not isinstance(data.get("message"),str):
        raise ValueError("simulation requires a message")
    priority=data.get("priority","info")
    if priority not in ("info","warning","critical"):
        raise ValueError("invalid priority")
    recipients=data.get("recipients") or []
    names=[recipients] if isinstance(recipients,str) else list(recipients)
    if names and (data.get("action") or data.get("target_entity")):
        raise ValueError("recipients cannot be combined with direct action/target")
    staged=False
    if names:
        resolved=resolve(routes,names,priority=priority)
        targets=[{"recipient":name,"action":record.get("action","notify.send_message")}
                 for name,record in resolved]
    elif data.get("action"):
        action=data["action"]
        if not valid_action(action):
            raise ValueError("invalid direct transport action")
        targets=[{"recipient":data.get("target_entity","(direct)"),"action":action}]
    elif data.get("target_entity") or settings.get("default_notify"):
        targets=[{"recipient":data.get("target_entity") or settings["default_notify"],
                  "action":"notify.send_message"}]
    else:
        targets=[{"recipient":"(staged)","action":"reliable_notify.staged"}]
        staged=True
    not_before=next_allowed_timestamp(
        now,priority,settings.get("quiet_hours",{}),timezone)
    archive_days=retention_for_message(data,settings.get("archive_retention",{}))
    return {"mode":"dry_run","priority":priority,"recipients":targets,
            "staged":staged,
            "not_before":not_before,"scheduled":not_before>now,
            "archive_days":archive_days,"would_enqueue":len(targets),
            "would_send":False,"timestamp":datetime.fromtimestamp(now).isoformat()}
