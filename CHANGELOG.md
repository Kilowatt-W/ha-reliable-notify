# Changelog

## 3.1.1
- Keep the default notify entity optional in setup and options; omit invalid empty entity suggestions and normalize cleared selections.
- Clarify target creation with a Ziele & Personen tab, explicit create buttons, setup hints and a direct entry from settings.

## 3.1.0
- Replace the settings-area dropdown with eight expanded settings sections.
- Replace admin-panel JSON editors with typed, nested form fields for routes, profiles, templates and simulation.
- Add optional read-only YAML previews and preserve existing options and transport parameters.
- Add admin-only single-route loading for editing; inventories and diagnostics remain redacted.
- Add functional DOM tests and options-save regression coverage.

## 3.0.0 — 2026-11-04
- New locally shipped and versioned shield-bell-check brand icons/logos, SVG sources and PNG generation workflow.
- Optional Home Assistant authenticated external API for applications, with administrator-only token access, rate limits and recipient allowlist.
- Named notification profiles and administrative editor; defaults can be explicitly overridden.
- Extended migration scanner to packages and known YAML folders, individual diff preview and opt-in single-package-action changes with preimage SHA-256, backup and atomic replacement; HA UI files never automatically rewritten.
- Telegram sent-message IDs tracked via telegram_sent; explicit edit/delete by configured chat and dedup key.
- 30-day delivery chart, regression tests, enhanced security/operational documentation.


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
