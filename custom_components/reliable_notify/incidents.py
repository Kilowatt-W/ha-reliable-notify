"""Alarm window: filtering and public views of open incidents (no HA imports)."""
from __future__ import annotations

PRIORITY_RANK = {"info": 0, "warning": 1, "critical": 2}
# Actions every signed-in user may take unless restricted in the options.
RESIDENT_ACTIONS = frozenset(("ack", "snooze"))


def visible_incidents(records, areas=None, message_types=None, min_priority="info",
                      include_acknowledged=False):
    """Open incidents for a view, highest priority first, newest first within a priority."""
    minimum = PRIORITY_RANK.get(min_priority, 0)
    result = []
    for record in records:
        if record["state"] == "closed":
            continue
        if record["state"] == "acknowledged" and not include_acknowledged:
            continue
        if areas and record.get("area") not in areas:
            continue
        if message_types and record.get("message_type") not in message_types:
            continue
        if PRIORITY_RANK.get(record.get("priority"), 0) < minimum:
            continue
        result.append(record)
    result.sort(key=lambda r: (-PRIORITY_RANK.get(r.get("priority"), 0), -(r.get("opened_at") or 0)))
    return result


def public_incident(record, is_admin=False):
    """What the alarm card shows. Residents see the display text, not internal details."""
    view = {key: record.get(key) for key in (
        "dedup_key", "title", "priority", "area", "message_type", "state", "opened_at",
        "resolved_at", "acknowledged_at", "acknowledged_by", "snoozed_until",
        "escalation_step", "escalation_steps")}
    view["text"] = record.get("display_text") or record.get("message") or ""
    if is_admin:
        view["message"] = record.get("message")
    return view


def may_act(action, is_admin, admin_only=False):
    """Residents may acknowledge and snooze; everything else needs an administrator."""
    if is_admin:
        return True
    return not admin_only and action in RESIDENT_ACTIONS


def summary(records):
    """State and attributes for the open-incidents sensor."""
    open_records = [r for r in records if r["state"] != "closed"]
    critical = [r for r in open_records if r.get("priority") == "critical" and r["state"] in ("active", "resolved")]
    return {
        "count": len(open_records),
        "critical_unacknowledged": len(critical),
        "incidents": [{key: r.get(key) for key in (
            "dedup_key", "title", "priority", "state", "opened_at", "resolved_at", "area")}
            for r in visible_incidents(open_records, include_acknowledged=True)[:20]],
    }
