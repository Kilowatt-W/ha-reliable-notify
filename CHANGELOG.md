# Changelog

## 2.5.0 — 2026-11-04
- Native notify entities per configured recipient/group/person and optional classic notify.reliable_* services.
- Read-only migration advisor with safe suggestions for automation/script notifications.
- User-configurable Jinja message templates with bounded variable mappings.
- Long-term daily aggregates (365 days) and query indexes for delivery reporting.
- Better route lifecycle and compatibility settings; tests and docs.


## 2.0.0 — 2026-11-04
- Admin-only HA sidebar panel with integrated queue, people/groups/routes editor, incident wizard, safe simulator, statistics and test-mode controls.
- Signed native Companion / Telegram ACK, snooze and escalate callbacks, compact enough for Telegram.
- Exactly-once SQLite escalation step advancement and queued message creation (not provider-side exactly-once receipt).
- Native HTTPS ntfy, Gotify and generic webhook POST with endpoint pinning and secret-free persisted payloads.
- Location/zone-aware person channel preferences; Companion device discovery.
- Transport health sensors, delivery-latency statistics and anonymized diagnostic summaries.
- Weekly online SQLite backup snapshots and admin backup action.
- Dedicated test-mode staging and per-transport log levels.
- API reference, security guide, migration steps and HA OS acceptance test matrix.

## 1.1.0
- Quiet hours, per-endpoint rate limiting, digest coalescing.

## 1.0.0
- Person routing, Companion tag-based update and dismissal, live Lovelace refresh.

## 0.9.0
- DB maintenance, dead letter retention, durable acknowledgement and escalation.

## 0.8.0
- Per-message archive retention and completed archive size cap.
