# Reliable Notify v0.8.0 — Message archive retention controls

## New features

- **Delete after delivery:** Set `archive: delete_after_send` on an enqueue call to remove the archive message body in the *same database transaction* that records successful delivery. The queue retains the content until the provider has accepted it. Failed/dead-letter messages remain available for troubleshooting and retry.
- **Retention by message type:** An optional `message_type` such as `windows`, `pvec`, or `security` selects a centrally configured number of days.
- **Per-message override:** Set `archive_days: 0..365` to override the type policy. `archive_days: 0` also deletes the archived body immediately after successful delivery.
- **Automatic cleanup:** Completed archive entries expire based on their last status update plus configured retention. An independent maximum of **2,000 completed records** prevents unlimited growth.
- **Backward-compatible migration:** Existing archive messages remain at the historical 30-day retention unless updated; existing queued and dead-letter records remain intact.
- **Companion links:** Automatic deep links are skipped for messages set to delete after delivery, because the content will not remain available to read.

## Default archive policies

| Type | Days |
| --- | ---: |
| `info` | 1 |
| `warning` | 7 |
| `critical` | 30 |

Configure more message types in **Settings → Devices & services → Reliable Notify → Configure → Archive retention by message type**, for example:

```json
{
  "info": 1,
  "warning": 7,
  "critical": 30,
  "windows": 2,
  "pvec": 3,
  "security": 60
}
```

### Transient status (do not archive after delivery)

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [wolfgang_phone]
    priority: info
    archive: delete_after_send
    message_type: pvec
    title: PVEC
    message: "Pool pump started."
```

### Keep a warning for two days

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [wolfgang_phone]
    priority: warning
    message_type: windows
    archive_days: 2
    title: Window warning
    message: "Bedroom window open."
```

### Priority resolution

1. `archive: delete_after_send` takes precedence over any number of days.
2. Explicit `archive_days` overrides configured rules.
3. An exact `message_type` match uses the configured rule.
4. Otherwise the message's priority (`info`, `warning`, `critical`) selects the default.

## Notes

The retention policy is **captured when the message is enqueued**, so changes in the settings apply to new messages, not existing archive rows. In-flight, staged and dead-letter messages are not purged merely because their archive retention expired; their delivery or manual investigation would otherwise break. Existing TTL values are separate from archive retention. GitHub Actions validate syntax, tests, HACS and hassfest before a tagged release. Home Assistant Core restart required after update.

**SQLite caveat:** Deleting records marks database pages for reuse but does not necessarily shrink the file on disk. For unusually large databases, plan SQLite maintenance/backup with Home Assistant stopped; do not vacuum a running WAL database from outside the integration.
