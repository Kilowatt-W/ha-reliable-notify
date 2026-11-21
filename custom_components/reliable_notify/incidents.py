"""Alarm window: filtering and public views of open incidents (no HA imports)."""
from __future__ import annotations

PRIORITY_RANK = {"info": 0, "warning": 1, "critical": 2}
# Actions every signed-in user may take unless restricted in the options.
RESIDENT_ACTIONS = frozenset(("ack", "snooze"))


UNDECIDED_STATES = frozenset(("unavailable", "unknown"))


def source_decision(state, problem_states):
    """'problem', 'clear' or None (entity missing/unavailable: never resolve on that)."""
    if state is None or state in UNDECIDED_STATES:
        return None
    return "problem" if state in (problem_states or ["on"]) else "clear"


def plan_incident(record, state, timer_due=False):
    """Next step for a watched incident given the cause entity's current state.

    Returns 'reactivate', 'resolve', 'start_wait', 'reset_wait' or None.
    ``timer_due``: resolve_after has elapsed (resolve if the cause is still gone).
    """
    decision = source_decision(state, record.get("problem_states"))
    if decision == "problem":
        if record["state"] == "resolved":
            return "reactivate"
        return "reset_wait" if record.get("clear_since") else None
    if decision == "clear" and record["state"] in ("active", "acknowledged"):
        if timer_due or not record.get("resolve_after"):
            return "resolve"
        return None if record.get("clear_since") else "start_wait"
    return None


def mirror_plan(record, default_mode="none"):
    """Where an incident is mirrored: {'notification': 'show'|'hide', 'issue': 'error'|'warning'|'hide'}.

    Only unacknowledged incidents (active or resolved) are shown; info priority gets no repair issue.
    """
    mode = record.get("mirror") or default_mode or "none"
    open_unacked = record["state"] in ("active", "resolved")
    show_note = mode == "persistent_notification" and open_unacked
    severity = {"critical": "error", "warning": "warning"}.get(record.get("priority"))
    show_issue = mode == "repairs" and open_unacked and severity is not None
    return {"notification": "show" if show_note else "hide", "issue": severity if show_issue else "hide"}


def dismissed_incidents(update_type, notification_ids, own_removals=()):
    """Incident keys acknowledged because a user removed their bell entry (rn_<key>).

    Removals made by Reliable Notify itself (``own_removals``) are ignored. Dismissing
    one entry removes exactly one notification; ``persistent_notification.dismiss_all``
    removes all of them in a single update – that is a clean-up (for example by a
    start-up automation), not an acknowledgement (3.8.3, see ``bulk_removed_incidents``).
    """
    if str(update_type) != "removed" or len(notification_ids) != 1:
        return []
    return [key for key in _mirror_keys(notification_ids) if key not in own_removals]


def bulk_removed_incidents(update_type, notification_ids, own_removals=()):
    """Mirror entries removed together by dismiss_all; they are shown again (3.8.3)."""
    if str(update_type) != "removed" or len(notification_ids) < 2:
        return []
    return [key for key in _mirror_keys(notification_ids) if key not in own_removals]


def _mirror_keys(notification_ids):
    return [nid[3:] for nid in notification_ids if isinstance(nid, str) and nid.startswith("rn_") and len(nid) > 3]


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
        "escalation_step", "escalation_steps", "source_entity")}
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
