# Reliable Notify v2 public API

The integration uses Home Assistant actions and admin-only WebSocket commands. All payloads are JSON-serializable and remain subject to Home Assistant's access controls.

## Actions

| Action | Purpose |
|---|---|
| `reliable_notify.enqueue` | Persist + route to explicit recipients; returns after SQLite commit, not delivery |
| `reliable_notify.simulate` | Return a read-only routing/delay/retention preview; no DB writes or sends; use `response_variable` |
| `reliable_notify.update` | Replace pending notifications sharing a dedup_key |
| `reliable_notify.dismiss` | Cancel pending notifications and queue Companion clear_notification commands |
| `reliable_notify.acknowledge` | Manually confirm an incident key and stop future escalation steps |
| `reliable_notify.retry_all` | Retry waiting queued messages |
| `reliable_notify.retry_dead` | Restore failed messages (may duplicate provider sends) |
| `reliable_notify.retry_one` | Retry one queued/dead message |
| `reliable_notify.delete_one` | Delete a queued/dead message |
| `reliable_notify.clear_queue` | Delete waiting messages |
| `reliable_notify.cancel` | Cancel waiting messages by dedup_key |
| `reliable_notify.reload_routes` | Reload and validate YAML/GUI routes |
| `reliable_notify.backup` | Admin-only SQLite online snapshot with verified integrity; returns metadata |

### Enqueue payload

Required: `message`. Other fields: `title`, `recipients`, `priority` (info/warning/critical), `message_type`, `archive` (keep/delete_after_send), `archive_days` (0–365), `dedup_key`, `strategy` (always/replace/digest), `ttl` (seconds), `acknowledgement`, `data`, `media`, `test_mode`.

Do not pass both `recipients` and a direct `action`/`target_entity`. If neither a recipient nor default destination is configured, messages go to Staging. `test_mode: stage` forces local staging without any sending.

Example with delayed escalation:
```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [phone]
    title: "Security incident"
    message: "Check the perimeter"
    priority: critical
    dedup_key: security_incident_42
    acknowledgement:
      required: true
      escalation:
        - after: 300
          recipients: [telegram]
```

## Admin WebSocket

- `reliable_notify/dashboard`, `/archive`, `/archive_detail`
- `reliable_notify/set_archive_retention`, `/set_retry_policies`, `/set_smart_settings`
- `reliable_notify/acknowledge`, `/incident_action`, `/send_staged`
- `reliable_notify/simulate`, `/admin_inventory`, `/set_route`, `/settings_v2`
- `reliable_notify/statistics`

Admin commands use Home Assistant websocket authentication and enforce `connection.user.is_admin`. Diagnostic exports omit message bodies, passwords and API tokens.

## Stability and compatibility

A successful transport service call means **transport acceptance only**, not that a device displayed the push. End-to-end delivery confirmation remains provider-dependent. Retry and lease semantics are intentionally at-least-once.

Scheduled incident escalations are enqueued and their next stage advanced inside the same SQLite transaction; this closes the common crash-after-enqueue/before-advance duplicate window. Provider-side acknowledgements can still be ambiguous after a network failure.

The v2 API is additive relative to the 1.1 service names. Config options and SQLite schema are upgraded automatically.
