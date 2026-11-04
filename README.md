# Reliable Notify — Home Assistant

**Current version: 1.1.0.** SQLite-backed, restart-safe multi-channel notifications with configurable retries, notification archiving, acknowledgements, escalating alarms, recipient groups, per-priority people, Companion App notification lifecycle and smart notification scheduling.

> **Community integration.** At-least-once delivery is not end-device receipt; provider failures can create duplicates. Test your real providers before depending on it for critical alerts.

## Installation and upgrades

Add `Kilowatt-W/ha-reliable-notify` as a custom **Integration** repository in HACS / Home Assistant Marketplace, install the latest **published GitHub release**, restart Home Assistant Core and configure the integration under Settings → Devices & services. Configured recipients, queue and archive survive upgrades. Back up `/config/.storage/reliable_notify.db` with HA stopped.

## Version 1.1 highlights

- **0.9:** Daily DB maintenance, WAL checkpoint, dead-letter retention, manual acknowledgement with durable escalation.
- **1.0:** `persons` priority routing, `reliable_notify.update` and `reliable_notify.dismiss` for Companion notifications, live Lovelace refresh.
- **1.1:** DST-aware Quiet Hours, per-endpoint rate limits and digest coalescing.

Read `RELEASE_NOTES_v0.9.0.md`, `RELEASE_NOTES_v1.0.0.md` and `RELEASE_NOTES_v1.1.0.md` for exact examples, limitations and migration notes.

---
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


---

## Reliable Notify v0.6.0 — dashboard and delivery controls

**Development status:** v0.6.0 includes 32 passing local unit tests, but has **not** been end-to-end tested with Home Assistant OS, Telegram or SMTP. Do not treat this version as a verified alarm delivery system.

### Interactive Lovelace dashboard

Version 0.6 includes an interactive card with **Queue**, **Dead letters**, **Retry** and **Delete** actions, delivery history, retry policies and remaining disk space. The dashboard can also edit retry policies and trigger bulk retries; it uses an **admin-only** Home Assistant WebSocket API and does not expose message bodies or transport credentials.

Add a JavaScript module resource in the Home Assistant dashboard resources settings:

`/reliable_notify/reliable-notify-card.js`

Then add the card to a dashboard:

```yaml
- type: custom:reliable-notify-card
  title: Reliable Notify
```

Or use the supplied `dashboard.example.yaml`. The card is bundled with the integration: no additional frontend repository is required. **Restart Home Assistant Core after upgrading the Python integration.**

### Central retry policies

In **Settings → Devices & services → Reliable Notify → Configure → Retry policies by priority**, edit the JSON policies for info, warning and critical messages. Defaults:

| Priority | Attempts | Initial delay | Maximum delay |
| --- | ---: | ---: | ---: |
| Info | 8 | 30 seconds | 30 minutes |
| Warning | 20 | 30 seconds | 60 minutes |
| Critical | Unlimited on transient errors (0) | 15 seconds | 60 minutes |

Temporary network faults, rate limits and HTTP 5xx provider errors are retried; common payload and authentication errors go directly to dead letters. A TTL still takes precedence over retries. Unknown failures are treated as retryable, to avoid silently losing messages.

### Durable local SMTP attachments

For SMTP recipients, attachments whose source is a local `/media` path (or a local Home Assistant media-source URL) are copied to the persistent media spool *when queued*. This prevents changing camera images or reports from changing the contents during offline recovery.

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [it_email]
    title: System report
    message: Attached report
    priority: warning
    data:
      attachments:
        - path: /media/reports/report.pdf
          filename: report.pdf
```

The configured SMTP integration must support attachments. Attachments from non-local or third-party media sources are **not** snapshotted. Individual files are capped at 20 MiB; photos and attachments share a 200 MiB spool quota. Files are accessible to Home Assistant in `/media/reliable_notify`; protect backups accordingly.

### Automatic disk capacity checks

Queue insertion refuses new messages if the queue filesystem has less than **100 MiB free**. Media snapshots require the same safety margin on the media filesystem. Existing queued messages are not deleted to reclaim space. If you need later automation actions to run even after a local disk failure, add `continue_on_error: true` to `reliable_notify.enqueue`.

### Home Assistant Marketplace / HACS

This repository retains `hacs.json` for compatibility with both legacy HACS and the new Home Assistant Marketplace. Add this repository as a **custom Integration repository** until accepted into a public catalog. A GitHub release tag provides the versioned update channel. A Home Assistant Core restart is required after updating Python code.


## v0.6.1 — optional default and staging inbox

**When no default notify entity has been set**, and an automation calls `reliable_notify.enqueue` without `recipients`, `target_entity` or `action`, the message is **persisted without delivery**. An administrator can read the full content in the **Staged (no recipient)** section of the Reliable Notify Lovelace card, select a configured individual recipient and click **Assign and send**, or delete it. Staged items survive Home Assistant restarts and are ignored by all delivery workers, including bulk retry. A message with a TTL may expire before manual assignment.

Explicit recipients and groups remain the recommended normal behavior. To configure without a default notify entity, leave the optional Default Notify field empty in the setup wizard or integration options. Existing configurations retain their previously selected default until it is cleared.

### Companion app notifications (Android and iOS)

Reliable Notify can also queue the existing Home Assistant Companion App notify action — no additional app or push gateway is required. Configure the phone as a named recipient:

```yaml
recipients:
  wolfgang_phone:
    action: notify.mobile_app_your_device_id
groups:
  personal:
    - wolfgang_phone
```

Then send a message with a **tap destination**, using the Companion App's documented native parameters:

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [wolfgang_phone]
    priority: warning
    title: "Fensterwarnung"
    message: "Das Schlafzimmerfenster ist seit 90 Minuten geöffnet."
    data:
      data:
        # iOS
        url: "/lovelace/windows"
        # Android
        clickAction: "/lovelace/windows"
        # Replaces previous notification with the same tag on the device
        tag: "bedroom_window"
```

**Double `data` is intentional:** the outer map contains Reliable Notify transport parameters, while the nested map is passed through to the Companion App action. **Replace the example Lovelace path** with a view that really exists. When a notification is tapped, this opens the requested Home Assistant page instead of the app's default start view. On Android, swipe down to expand long notifications. The phone's operating system ultimately controls how much text is shown on the lock screen, and no custom integration can override those display/privacy settings.

Archive retention for completed notification bodies is configurable since v0.7.0; see v0.8.0 retention policies. For a durable in-HA copy of critical notices, use an additional `notify.persistent_notification` action or send to an HA dashboard entity/view containing the full details. The staging inbox is for **unaddressed test messages only**, not an archive of delivered push notifications.

**Privacy:** staged message bodies are readable to Home Assistant administrators through the dashboard. Avoid storing passwords, access tokens, or other secrets in notification messages.


## v0.7.0: full notification archive and Companion tap-to-read

The archive preserves **full message bodies** after a notification has been sent or removed from the queue. Administrator-only archive search and message details are available in the built-in `custom:reliable-notify-card`. Completed entries are retained for **30 days or up to 2000 messages**; still-pending and dead-letter messages remain available.

To make an Android/iOS push notification open its full text:

1. Create a Lovelace dashboard view, for example `/lovelace/reliable-notify`, that contains the Reliable Notify card.
2. Under **Settings → Devices & services → Reliable Notify → Configure → General settings**, set **Archive URL** to that same view path.
3. Add a named recipient whose action is the Companion app service `notify.mobile_app_<device>`.
4. Send via `reliable_notify.enqueue` with `recipients: [your_mobile_recipient]`.

The integration then attaches `data.url` (iOS) and `data.clickAction` (Android) to the outgoing Companion message, including the archived message ID. If the automation already provided a click destination, it is **not overridden**. The message detail is administrator-only; the deep link is useful only when the person is an HA administrator.

```yaml
recipients:
  my_phone:
    action: notify.mobile_app_my_phone
```

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [my_phone]
    title: "Fensterüberwachung"
    message: "Fenster Schlafzimmer seit 90 Minuten geöffnet."
    priority: warning
```

See `RELEASE_NOTES_v0.7.0.md` for privacy, retention and testing limitations. The queue and archive are local SQLite data; protect the HA database and backups.


## v0.8.0: automatic archive retention by message type

Reliable Notify now lets you decide **per notification** whether its full text should remain archived after successful delivery. Keeping a message in the *delivery queue* is separate from archiving its body: a message is never discarded before successful delivery just because archival retention is zero.

**Send but do not archive afterwards:**

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [wolfgang_phone]
    priority: info
    message_type: pvec
    archive: delete_after_send
    title: PVEC
    message: "Pool pump switched on."
```

**Retain a window warning for two days:**

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [wolfgang_phone]
    priority: warning
    message_type: windows
    archive_days: 2
    title: Open window
    message: "Bedroom window has been open for 90 minutes."
```

**Default retention:** info 1 day, warning 7 days, critical 30 days. Change per-type retention in **Settings → Devices & services → Reliable Notify → Configure → Archive retention by message type**, or edit the same JSON object in the interactive Lovelace card. Add custom types such as `windows`, `pvec` or `security`.

Priority order: `archive: delete_after_send` > explicit `archive_days` > configured `message_type` > `priority`. A zero-day policy means **immediate archive deletion upon successful send**. Failed and dead-letter messages remain available for retry and diagnosis. New settings apply to notifications subsequently queued; the existing archive retains its original retention settings.

Automatic cleanup runs as part of the ongoing database operations and caps completed archive messages at 2000 records. As with all SQLite databases, freed pages are typically reused but may not immediately reduce the size of the database file. See `RELEASE_NOTES_v0.8.0.md` for examples and migration notes.
