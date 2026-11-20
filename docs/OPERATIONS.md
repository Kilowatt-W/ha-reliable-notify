# Operations, backup and recovery

## Data locations

- `/config/.storage/reliable_notify.db`: SQLite messages, retries, dead letters, archive, acknowledgements and rate windows.
- `/config/.storage/reliable_notify_callback_secret`: HMAC action-token signing secret. **Protect this and preserve it through upgrades**; regenerating invalidates buttons still on phones.
- `/config/.storage/reliable_notify_backups/`: online SQLite backup snapshots (weekly by default, last 3).
- `/media/reliable_notify/`: snapshotted Telegram photos and local SMTP attachments.

## Database maintenance

The dedicated maintenance task performs retention for completed archive messages and noncritical dead letters, `PRAGMA quick_check(1)`, a passive WAL checkpoint and diagnostics.

The completed message-body archive is bounded by 2000 records and 32 MiB, but **in-flight, staged, dead-letter and unacknowledged critical incidents are intentionally preserved** and may still grow. Queue limits and the 100 MiB free-space guard protect the system from unbounded normal writes; configure monitoring for abnormal growth.

SQLite pages freed by DELETE are normally reused; the file may not shrink until maintenance such as VACUUM. Do not manually VACUUM a live HA database from outside the integration.

## Online backups

`reliable_notify.backup` is an administrator-only HA action returning filename, byte count and integrity result; the weekly task uses the same SQLite online-backup API to include WAL changes. The backup file is written to a temporary path and atomically renamed after `PRAGMA quick_check(1)` succeeds. The last N snapshots are kept.

**Do not restore while HA Core is running.** To restore:
1. Create a full Home Assistant backup and stop HA Core.
2. Copy the chosen snapshot to a safe temporary location.
3. Verify it with `sqlite3 snapshot.sqlite3 'PRAGMA quick_check;'` (must print `ok`).
4. Back up the old `reliable_notify.db` and its `-wal`/`-shm` siblings.
5. Replace the database with the verified snapshot and remove only the old WAL/SHM companions belonging to the replaced database.
6. Ensure filesystem ownership/permissions are correct; start Home Assistant and verify Queue/Dead Letters/Archive.

Do not overwrite a live SQLite file or attempt to restore just the .db file while a writer has WAL frames in progress.

## Health sensors

Look for Reliable Notify diagnostic entities:
- Health: `healthy`, `degraded`, `critical`, `unknown`.
- Transport Health: aggregated transport acceptance/failure signals; not phone delivery.
- Database Size, Maintenance Health, Storage Free, Media Size, Oldest Queued.
- Queue Size, Dead Letter Count, Delivery History, Sent, Failures.

Example HA automation:
```yaml
- alias: Reliable Notify health warning
  triggers:
    - trigger: state
      entity_id: sensor.reliable_notify_health
      to: critical
  actions:
    - action: persistent_notification.create
      data:
        title: Reliable Notify storage warning
        message: Reliable Notify health is critical. Check disk and dead letters.
```

Entity IDs depend on the HA entity registry; verify yours in Developer Tools.

## Incident callbacks and security

Action IDs are HMAC signed and verified before the integration changes incident state. Third-party apps cannot acknowledge a message by guessing its dedup_key. Telegram callback feedback is attempted but provider API acceptance is not end-device acknowledgement.

## Retries, give-up and failure analysis (3.4.0)

- A failed delivery is retried with exponential backoff. A message gives up when the error is permanent, when **max attempts** is reached (0 = unlimited, the default since 3.4.0) or when it has been failing for **max hours** (defaults: info 6 h, warning 24 h, critical 0 = never). Untouched pre-3.4 defaults (8/20 attempts) are migrated automatically.
- Waiting for HA to load the transport action (e.g. during start-up) is retried every 60 s and does **not** use up attempts; max hours still applies.
- Delivering to a missing or `unavailable` notify entity is a retryable `target_unavailable` failure instead of a false "sent" (HA would skip the entity silently).
- HA validation errors (`Invalid`, `ServiceValidationError`) are permanent `invalid_payload` failures, so a call that can never succeed is not retried for hours.
- Failures store a sanitised error text: URLs, tokens, e-mail addresses and numbers with six or more digits (chat/phone IDs) are masked.
- Messages past their `ttl` are recorded as `expired` in history and statistics.
- **Statistics → Failure analysis** groups dead, expired and retrying messages by cause and target and gives advice per cause; the diagnostics export contains the same `failures` list.
- Each dead letter fires the event `reliable_notify_dead_letter` (`id`, `recipient`, `target`, `action`, `priority`, `category`; no message text) and maintains a repair issue while dead letters exist.
- A recipient may define `fallback: <recipient, group or person>`. When a message to it finally fails, a copy is queued once to the fallback (a fallback copy never falls back again).

## Alarm window (3.6.0)

An acknowledged notification with an `incident` mapping becomes an incident that stays visible until it is acknowledged, even when the cause is already gone:

- States: `active` → `resolved` (cause gone, `reliable_notify.resolve`) → `closed` once acknowledged; acknowledging while the cause persists gives `acknowledged` ("still present") until it is resolved. Plain acknowledgements without `incident` close on acknowledgement as before.
- `incident` fields: `display_text` (shown on dashboards), `area` (filter, a-z/0-9/_), `escalate_while_resolved` (default true: reminders continue after `resolve` until acknowledged). `incident` requires `dedup_key` and implies `acknowledgement: {required: true}`.
- Services: `reliable_notify.resolve` (`stop_escalation`), `reliable_notify.snooze` (`minutes`, only reminders pause, "since" is kept), `reliable_notify.reopen`; `reliable_notify.acknowledge` unchanged.
- Event `reliable_notify_incident` on every change: `dedup_key`, `action` (created, acknowledged, snoozed, escalated, resolved, reopened), `by`, `priority`, `title`, `message_type`, `area`, `state` – no matter whether the change came from Telegram, the app, the card, the panel or a service.
- Entities: sensor *Open incidents* (count, attribute `incidents`) and binary sensor *Critical incident open*.
- Card `custom:reliable-notify-alarm-card` (loaded automatically for all users): options `areas`, `message_types`, `min_priority`, `show_acknowledged`, `snooze_minutes` (up to three), `confirm_acknowledge`, `compact`. Live updates via WebSocket subscription; without open incidents the card hides itself. Every signed-in user may acknowledge and snooze (option *Only administrators may acknowledge or snooze incidents*); escalating, resolving and reopening need an administrator.
- Open incidents are kept regardless of priority; closed ones are removed after 30 days.

## Troubleshooting checklist

1. Check disk free bytes and maintenance integrity.
2. Inspect Queue and Dead Letters in the admin panel and open **Statistics → Failure analysis** for the cause per target.
3. Use the Simulator to test priority, routing and quiet-hours decisions without sending.
4. Enable debug for only the failing transport. Logs deliberately omit message bodies and tokens.
5. Stage a test notification, then assign it to a real recipient once the route is verified.
6. Verify your actual device and service names; notify transports change with HA releases.
7. Use the backup and restore procedure above before major upgrades.

## v3 compatibility and branding

The integration brand images are shipped locally under `custom_components/reliable_notify/brand/`. If the new icon does not appear in HA integrations, restart HA Core and hard-refresh the browser. For legacy HACS that still displays its CDN placeholder even though HA shows the icon, use Home Assistant 2026.11 Marketplace where supported (see [branding](BRANDING.md)).

The external app API is disabled by default. Exposed routes are explicit, admin-authorized, and rate-limited; keep your HA Bearer token out of scripts you commit to source control. Protect automatic backups and migration backups under `.storage`.
