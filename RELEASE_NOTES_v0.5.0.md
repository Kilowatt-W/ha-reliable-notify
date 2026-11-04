# Reliable Notify 0.5.0

- Per-notification retry and delete (`retry_one`, `delete_one`), both active and dead-letter queues.
- Local delivery history: last 2,000 outcome entries, up to 30 days, no message body/transport payload.
- Dashboard YAML example: queue, dead letters, counters and recent outcomes.
- Separate SMTP action lane. Support `smtp.send_message`, including provider-native `html` and `attachments` fields in `data`, with `notify.*` entity target.
- 200 MiB total quota for local Telegram photo spool, rejecting additional photo enqueue when full.
- GitHub Actions CI + HACS repository-ready layout for in-HA update flow.

**Breaking changes:** None expected for existing 0.4.0 database schema. **Upgrade:** Back up DB/config, then install the release using HA marketplace/HACS once published, restart HA Core. Local ZIP users must update manually until a GitHub repository with a release has been configured.

**Limitations:** SQLite at-least-once delivery (duplicates possible), no end-device read receipts. SMTP attachments are native HA `media_source` references; camera snapshot resolution happens when the email is dispatched, not at queue time. Dashboard is a native Lovelace example rather than a bespoke editable frontend. No live HA integration smoke test has been performed.