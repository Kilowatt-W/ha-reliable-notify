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

## Troubleshooting checklist

1. Check disk free bytes and maintenance integrity.
2. Inspect Queue and Dead Letters in the admin panel.
3. Use the Simulator to test priority, routing and quiet-hours decisions without sending.
4. Enable debug for only the failing transport. Logs deliberately omit message bodies and tokens.
5. Stage a test notification, then assign it to a real recipient once the route is verified.
6. Verify your actual device and service names; notify transports change with HA releases.
7. Use the backup and restore procedure above before major upgrades.

## v3 compatibility and branding

The integration brand images are shipped locally under `custom_components/reliable_notify/brand/`. If the new icon does not appear in HA integrations, restart HA Core and hard-refresh the browser. For legacy HACS that still displays its CDN placeholder even though HA shows the icon, use Home Assistant 2026.11 Marketplace where supported (see [branding](BRANDING.md)).

The external app API is disabled by default. Exposed routes are explicit, admin-authorized, and rate-limited; keep your HA Bearer token out of scripts you commit to source control. Protect automatic backups and migration backups under `.storage`.
