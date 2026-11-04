# Reliable Notify v2.0.0 — Reliable notification management for Home Assistant

**Version 2.0.0** extends the existing local SQLite-based notification system with the planned v1.2–v2.0 features and the additional test-mode, simulation and logging capabilities.

## Highlights

- **Reliability:** transactionally insert escalation messages and advance the durable escalation step in the same SQLite transaction, including cancellation of not-yet-leased escalation messages upon acknowledgement.
- **Actionable alerts:** HMAC-signed **Acknowledge**, **Snooze (15 min)** and **Escalate** actions for Telegram text and Companion notifications; Telegram callback confirmation; invalid or unrelated callbacks ignored.
- **Full administration panel:** administrator-only HA sidebar at `/reliable-notify`, with message queue/archive, dead letters, person/recipient/group editing, device discovery, escalation wizard, simulation, statistics and settings. Existing Lovelace card remains supported.
- **Smart recipient routing:** per-priority and optional `person.*`-zone-dependent channel selection. Priority/zone is resolved at enqueue time.
- **Notification lifecycle:** unchanged `update`/`dismiss` plus optional `only_if` state guard to suppress stale notifications (for example, closed windows after offline recovery).
- **Transports:** native HTTPS **ntfy**, **Gotify** and generic outbound **webhooks** (with explicit authorization, no redirects, endpoint fingerprint, no credentials in queue). Also supports HA `rest_command.*` gateway actions for other services; Telegram, Companion and SMTP remain.
- **Operational health:** per-transport volume and accepted/failed counts, delivery attempt latency, queue age, media/DB usage and health sensors, anonymized-by-content diagnostics.
- **Backups:** weekly online SQLite snapshot with integrity check, configured retention, admin-only `reliable_notify.backup` action.
- **Testing / diagnostics:** explicit staging mode per target, pure `reliable_notify.simulate` action, interactive simulation panel, per-transport sanitized log levels, real HA Core container import CI.
- **Documentation:** single updated README, configuration/API/operations/transport/migration guides, security policy and a detailed actual-HA-OS acceptance test plan.

## Upgrading

1. Create a full HA backup and preserve `/config/.storage/reliable_notify.db` plus associated `-wal`/`-shm` if HA is running; do not copy only the live database as a snapshot.
2. Install v2.0.0 through HACS/Home Assistant Marketplace or GitHub release, then restart Home Assistant Core.
3. Open the new admin sidebar **Reliable Notify**. Confirm recipients, queue/archive, media spool and the new diagnostic entities.
4. Test a staged notification and a manual real notification to each required transport.
5. Test critical acknowledgement and escalation with a separate nonproduction incident before relying on it for urgent alarms.

## Important limitations

- Provider acceptance is **not** evidence that a phone displayed a notification. Queue is at-least-once, and provider timeouts may produce duplicates.
- GitHub unit tests, HACS/hassfest and HA Core import checks do **not** constitute a complete live-device test. The Android/iOS/Telegram/SMTP acceptance checklist in `docs/TEST_PLAN.md` remains for the operator.
- Not all external transports have the same delivery, acknowledgment or notification-dismissal capabilities. Signal/Matrix use configured HA gateways, not native adapters in v2.
- Only administrators can view the full messages archive and manage routes and settings.
- Native HTTPS endpoints must be trusted administrators' destinations; hostname DNS resolution remains a trust boundary. Redirects are disabled.
- Protected critical dead letters, pending and unacknowledged incidents can exceed normal completed-archive limits intentionally; monitor storage.
- New database schema migrations are additive; downgrades are not automatically supported. Restore a matched preupgrade snapshot to revert.

## Links

- [Configuration](docs/CONFIGURATION.md)
- [Transports](docs/TRANSPORTS.md)
- [Operations and backups](docs/OPERATIONS.md)
- [API v2](docs/API_V2.md)
- [Migration](docs/MIGRATION.md)
- [Home Assistant OS acceptance test plan](docs/TEST_PLAN.md)
- [Security](SECURITY.md)
