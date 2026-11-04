# Migration to Reliable Notify v2

## Preparation

- Ensure your existing release is functioning and back up Home Assistant.
- Use the admin `reliable_notify.backup` action or stop Core and copy the entire database and any WAL companions.
- Back up `/config/reliable_notify_routes.yaml`, integration options and the callback signing secret if upgrading from versions with signed action buttons.
- Test in a separate HA instance if you depend on security/critical alerts.

## From v0.8/v0.9/v1.0/v1.1

SQLite migrations are additive: new archive history duration values and acknowledgement action identifiers are added automatically. Existing messages stay queued and keep their previously captured retention policy.

The regular `reliable_notify.enqueue` service is retained. Existing recipient and group names remain valid. Test modes are opt-in (`off` by default). New native transports are opt-in. Quiet hours remain disabled unless configured.

Default Notify remains optional. If no recipient and no default exists, the notification is staged, never sent.

## HA Core restart and frontend refresh

Install the release, restart Home Assistant Core, clear browser cache if the admin panel appears stale, and open `/reliable-notify`.

## Rollback

Do **not** assume the older integration can read the newer SQLite schema. Stop HA Core and restore a pre-upgrade snapshot, including matching `reliable_notify_callback_secret`. Then reinstall the prior release and restart. Do not reuse a v2 database for an unsupported downgrade.

## Known limitations

- Scheduled escalations are transactionally inserted, but provider receipts are not guaranteed.
- Signed native callback buttons are intended for text Telegram and Companion actions; Telegram photo acknowledgements require alternate manual workflow.
- Rich ntfy/Gotify media uploads are not supported by the native transports (text only).
- In-flight critical incidents and dead letters can be intentionally retained beyond normal archive quotas.
