# Reliable Notify v1.1.0 — Smart Notifications

Builds on the v0.9 reliability changes and v1.0 person/lifecycle enhancements.

## Added

- **Quiet hours** in the Home Assistant timezone with daylight-saving-aware local clock calculations. Default disabled; when enabled defaults to 22:00–07:00, with critical alerts bypassing quiet hours.
- **Per-endpoint rate limiting** (default 10 send attempts/minute/target for info/warning). Multiple workers share one SQLite atomic rate window, so they cannot bypass the configured limit. Critical alerts bypass the limiter.
- **Digest coalescing** using `strategy: digest` and a required `dedup_key`. Repeated pending messages for the same target, action, priority and key are summarized into one notification. The digest waits 300 seconds by default, and does not keep postponing the first send indefinitely.
- **Smart settings UI** in integration Configure and administrator-only Lovelace dashboard, for quiet-hours JSON, max send attempts/minute and digest window.

## Quiet hours example

In integration Configure → Quiet hours, delivery limits and digests:

```json
{
  "enabled": true,
  "start": "22:00",
  "end": "07:00",
  "allow_priorities": ["critical"]
}
```

## Digest example

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [wolfgang_phone]
    dedup_key: pvec_cycle
    strategy: digest
    priority: info
    message_type: pvec
    archive: delete_after_send
    message: "PVEC: pump switched on."
```

Repeated messages within the 300-second window are replaced by a summary such as `3 events (latest): PVEC: pump switched off.`.

## Transport integration

Existing Telegram, SMTP and Companion App routing remain supported. ntfy and Gotify can be used through corresponding **existing Home Assistant notify services** when installed and explicitly configured. There is no direct unauthenticated HTTP/webhook sender in this release.

## Safety and operational behavior

- Quiet hours are calculated **when enqueuing**; modifying the policy later does not reschedule existing queued records. Deadline-based expiration still applies.
- Rate limiting applies to delivery **attempts**, not phone receipts. A provider may still enforce a stricter limit.
- Digest groups only notifications still waiting in the first digest window, and does not merge messages already in flight.
- Critical messages bypass both the quiet-hour pause and rate limiter, but they still respect storage, provider and retry controls.
- Browser UI, platform delivery, mobile clearing, and SQLite migration require live HA OS verification. Run a backup before upgrading; restart Home Assistant Core.

## Compatibility

Keeps HACS / Home Assistant Marketplace `hacs.json` support. Unit tests, Python compile, Node.js syntax, hassfest and HACS repository validation gate the GitHub release.
