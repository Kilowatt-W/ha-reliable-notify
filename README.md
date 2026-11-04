# Reliable Notify for Home Assistant

**Persistent, retryable notifications for Home Assistant — built for unreliable internet connections.**

Reliable Notify stores notifications in a local SQLite queue **before** attempting delivery. When Telegram, email or another Home Assistant notification service is temporarily unavailable, it retries without making the calling automation wait for the remote provider. It supports Telegram photos and inline keyboards, named recipients, nested groups, and configurable message lifetimes.

> **Development release (v0.5.0).** This is an independent community integration, not part of Home Assistant Core. End-to-end operation with Home Assistant OS and actual providers has not yet been verified. Test before relying on it for safety-critical alerts.

## Features

| Capability | Details |
| --- | --- |
| Durable queue | SQLite-backed, survives Home Assistant restarts |
| Automatic retries | Exponential backoff; critical messages retry indefinitely on transient failures unless a TTL expires |
| Telegram | Text, local photo snapshots and inline keyboards |
| Other services | Home Assistant notify entities/services, SMTP HTML mail with provider-supported attachments |
| Recipients and groups | Manage endpoints and nested groups through configuration UI or YAML |
| Message lifecycle | Priority, expiration (TTL), deduplication keys, replace and cancel |
| Delivery isolation | Separate Telegram and general notify/mail workers |
| Operations | Dead-letter queue, targeted retry/delete, history, diagnostic sensors and dashboard example |

A delivery acknowledged by a provider is **not** proof that a person received or read a message. Rare duplicates are possible after connection loss: the semantics are *at least once*.

## How it works

```text
Automation / Script
        |
        v
reliable_notify.enqueue
        |
        v
SQLite persistent queue
        |
        +----> Telegram worker ----> Telegram
        |
        +----> Notify/mail workers -> SMTP / mobile / HA notify
        |
        +----> Retry, expiry, dead letters and diagnostics
```

<!-- ha-marketplace:exclude-start -->
## Installation with Home Assistant Marketplace / HACS

- **Home Assistant 2026.11 and later:** use **Settings → Marketplace** (the built-in successor to HACS).
- **Earlier Home Assistant versions:** use **HACS**, if installed.
- Until the integration is accepted into the public catalog, add this repository as a **custom repository** of type **Integration**:
  `https://github.com/Kilowatt-W/ha-reliable-notify`
- Download/install the integration, restart Home Assistant Core, then add **Reliable Notify** under **Settings → Devices & services**.
- An actual GitHub release is needed for a stable tagged-version update workflow. Installing from the default branch may be available as a development option. Repositories visible in Marketplace/HACS are not automatically approved catalog entries.

After a Python code update, **restart Home Assistant Core**; reloading an integration alone does not reliably reload its Python modules.

For manual installation, copy `custom_components/reliable_notify` to `/config/custom_components/reliable_notify` and restart. Back up configuration and SQLite before upgrading.
<!-- ha-marketplace:exclude-end -->

## Configure recipients and groups

Use **Settings → Devices & services → Reliable Notify → Configure** to maintain simple endpoints and groups, or place a YAML file at `/config/reliable_notify_routes.yaml` and run `reliable_notify.reload_routes`.

Example (replace placeholder IDs and entities):

```yaml
recipients:
  wolfgang_telegram:
    action: telegram_bot.send_message
    data:
      chat_id: 123456789
  family_email:
    action: notify.send_message
    target_entity: notify.family_mail
groups:
  family:
    - wolfgang_telegram
    - family_email
```

Routes are resolved when a message is enqueued. Each physical recipient gets its own queue record. UI-defined routes override YAML entries with the same name.

## Examples

### Send a queued Telegram message with inline buttons

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [wolfgang_telegram]
    priority: warning
    message: "<b>Bedroom window</b> has been open for 90 minutes"
    dedup_key: bedroom_window
    strategy: replace
    ttl: 3600
    data:
      inline_keyboard:
        - "Status:/window_status, OK:/window_ack"
```

Button presses require a **separate Telegram callback automation** in Home Assistant.

### Persist a camera photo until Telegram is available

```yaml
- action: camera.snapshot
  target:
    entity_id: camera.front_door
  data:
    filename: /media/front_door.jpg

- action: reliable_notify.enqueue
  data:
    recipients: [wolfgang_telegram]
    priority: critical
    media: photo
    message: "Motion at the front door"
    data:
      file: /media/front_door.jpg
      inline_keyboard:
        - "Open camera:/front_door, Dismiss:/dismiss"
```

Reliable Notify copies local photos into `/media/reliable_notify/` so an overwritten source image does not change a queued message. Telegram needs read access to the spool directory. Merge the following path into your **existing** Home Assistant configuration (do not duplicate `homeassistant:`):

```yaml
homeassistant:
  allowlist_external_dirs:
    - /media/reliable_notify
```

Local photos are size-limited and the snapshot spool has a total quota. Remote image URLs are **not** cached.

### Fan out to a group

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [family]
    title: "Home Assistant"
    message: "A critical event occurred"
    priority: critical
```

### Cancel an outdated warning

```yaml
- action: reliable_notify.cancel
  data:
    dedup_key: bedroom_window
```

Only waiting records can be cancelled. In-flight and delivered messages cannot be recalled.

## Actions and monitoring

- `reliable_notify.enqueue`: enqueue a text/photo notification with recipients, priority, TTL and deduplication options.
- `reliable_notify.cancel`: cancel pending messages by deduplication key.
- `reliable_notify.retry_one`, `reliable_notify.delete_one`: manage individual queued or dead-letter records.
- `reliable_notify.retry_all`, `reliable_notify.retry_dead`, `reliable_notify.clear_queue`, `reliable_notify.reload_routes`.
- Diagnostic entities include queue size, dead letters, delivery history, success/failure counters and a retry button.
- `dashboard.example.yaml` offers a native Lovelace monitoring example.

For SMTP, use an existing `smtp.send_message` provider and refer to `reliable_notify_routes.example.yaml`. Attachments stored in media sources are resolved by the SMTP provider **at send time**, not copied to durable storage.

## Operational limitations

- **At-least-once delivery:** provider acceptance is not recipient confirmation, and some duplicates can occur after timeouts.
- SQLite or disk errors may still cause `enqueue` to fail. Use `continue_on_error: true` in an automation if no notification failure should interrupt later actions.
- Critical retries can continue indefinitely for temporary errors; explicit TTLs take precedence. Noncritical messages become dead letters after repeated failures.
- Filesystem and queue quotas prevent unbounded normal growth but do not replace free-space monitoring.
- No automatic processing of Telegram inline-keyboard callback events.
- The current configuration UI is a route editor, **not** a full interactive queue dashboard.
- This v0.5.0 integration **requires real-world testing** of Telegram, photo delivery, email, offline recovery and upgrades.

## Development and validation

```sh
python -m unittest discover -s tests -v
python -m compileall -q custom_components/reliable_notify
```

GitHub Actions includes Python tests and HACS validation. See `RELEASE_NOTES_v0.5.0.md` for changes.

## Support

Open an issue in this repository for reproducible bugs and feature requests:
https://github.com/Kilowatt-W/ha-reliable-notify/issues

**Compatibility note:** HACS is being replaced by the built-in **Home Assistant Marketplace** starting with Home Assistant **2026.11**. The metadata file retains its historical name `hacs.json` because **both HACS and Marketplace use it**.
