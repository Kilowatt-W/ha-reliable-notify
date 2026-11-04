# Reliable Notify v1.0.0 — people, Companion lifecycle and dashboard improvements

This release builds on the published v0.9.0 maintenance and acknowledgement features.

- `persons:` mapping in YAML or config UI: each named person references existing recipients as channels, with **different preferred channels by priority**. Groups may include people. The `entity: person.*` property is stored as metadata, not used to automatically infer location or device availability.
- `reliable_notify.update` updates pending messages by `dedup_key` using replacement semantics. If a notification has already been delivered, an update creates a new message.
- `reliable_notify.dismiss` cancels still-waiting messages and reliably queues a Companion App `clear_notification` command for explicit recipients, using a stable, hashed notification `tag`. Telegram deletion is **not yet supported**.
- Companion App pushes with `dedup_key` automatically receive the stable tag unless the caller provides one.
- Lovelace card refreshes on `reliable_notify_updated` events (60-second polling fallback), displays configured person names and adapts its layout to small screens.
- Existing recipient/group routes remain supported without modification.

## Persons example

```yaml
recipients:
  mobile:
    action: notify.mobile_app_your_phone
  telegram:
    action: telegram_bot.send_message
    data:
      chat_id: 123456789
persons:
  me:
    entity: person.me
    channels:
      mobile: mobile
      telegram: telegram
    preferred:
      info: mobile
      warning: telegram
      critical: [telegram, mobile]
groups:
  family: [me]
```

## Lifecycle example

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [me]
    dedup_key: bedroom_window
    message: Window open
    priority: warning
```

Later:

```yaml
- action: reliable_notify.dismiss
  data:
    recipients: [me]
    dedup_key: bedroom_window
```

The platform ultimately controls clearing already delivered notifications. On iOS, a recently active Companion App may be necessary. A `clear_notification` command is not a guaranteed read confirmation.

**Warning:** Test on actual Home Assistant OS and Companion App platforms before production dependence. Core restart required after upgrade.
