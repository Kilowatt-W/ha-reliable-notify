# Reliable Notify

**Reliable notifications for Home Assistant.** A local SQLite-backed queue with retries, sender adapters, recipient and person routing, escalation, searchable archive, and a full admin panel.

![Version](https://img.shields.io/badge/version-2.5.0-blue)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-41BDF5)

> **Important:** GitHub CI does not prove that a phone displayed or received a push. Reliable Notify uses *at-least-once* delivery to the transport, so providers can receive duplicates after ambiguous timeouts. Test your actual installation and devices before using critical alarm chains.

## Installation

Install from the public repository **Kilowatt-W/ha-reliable-notify** as a custom Integration repository in HACS/Home Assistant Marketplace. Choose the latest **published release**, restart Home Assistant Core, then add **Reliable Notify** under Settings → Devices & services. Development changes are validated on a branch before an official tagged release is published.

The optional default notify entity can remain empty; unaddressed messages are stored in the **Staging** inbox instead of being delivered.

## What's included in v2.5

| Area | Capabilities |
|---|---|
| Reliable delivery | SQLite queue, separate workers, retries, rate limits, dead letters, TTL and idempotent escalation insertion |
| Messaging | Telegram (text, image, keyboards), Companion App, HA notify entities, SMTP with snapshotted local attachments |
| Native transport | HTTPS ntfy, Gotify and outbound webhooks; credentials stay in route settings, not queue payloads |
| Routing | Named recipients, groups, people, priority-based and optional Home Assistant zone-based channel choices |
| Escalations | Signed Telegram/Companion **acknowledge**, **snooze 15 min**, **escalate** buttons; no untrusted unsigned callbacks |
| Smart | Quiet hours, digest grouping, deduplication and per-destination attempt limits |
| Data lifecycle | Configurable archive retention by type, delete-after-send, 2000-entry/32MiB cap on completed message bodies |
| Health | Queue age, transport failure counts, media/DB use, integrity check and passive WAL checkpoint |
| Backup | Online SQLite-consistent backups with integrity verification and configurable retention |
| Administration | Full HA sidebar panel **Reliable Notify** with staging, archives, people/routes, incident wizard, simulator, statistics and settings |
| Testing | Explicit test-mode staging, side-effect-free simulation, transport-specific sanitized logging, CI regression suite |

## Quick start

Set up your recipients under the sidebar **Reliable Notify → Empfänger & Personen**, or create `/config/reliable_notify_routes.yaml`:

```yaml
recipients:
  phone:
    action: notify.mobile_app_my_phone
  telegram:
    action: telegram_bot.send_message
    data:
      chat_id: 123456789
persons:
  me:
    entity: person.me
    channels:
      mobile: phone
      telegram: telegram
    preferred:
      info: mobile
      warning: telegram
      critical: [mobile, telegram]
groups:
  family: [me]
```

Send from an automation:

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [me]
    priority: warning
    message_type: windows
    title: "Fensterwarnung"
    message: "Schlafzimmerfenster seit 90 Minuten offen."
    archive_days: 2
    dedup_key: bedroom_window
```

**Dry run without queueing or sending** (supports response):

```yaml
- action: reliable_notify.simulate
  data:
    recipients: [me]
    priority: warning
    message: "Test der Zustellregel"
  response_variable: preview
```

For real test-mode staging, configure `test_mode: stage` in integration options. Nothing marked as staged is picked up by workers, including escalation workers.

## Native ntfy example

```yaml
recipients:
  mobile_ntfy:
    action: reliable_notify.ntfy
    data:
      base_url: https://ntfy.example.org
      topic: security
      token: YOUR_TOKEN
```

**Never commit tokens to a public repository.** Route credentials live in local HA configuration. The SQLite jobs store an endpoint digest, not tokens. If you change an endpoint, queued jobs for that old endpoint require manual review. Direct HTTPS is required by default; set `allow_private: true` on a route if your intentional on-premise endpoint uses a private IP.

## Administration and docs

- **Sidebar:** `/reliable-notify` (administrators only).
- **Lovelace:** `type: custom:reliable-notify-card`; register the resource `/reliable_notify/reliable-notify-card.js` as a JavaScript module.
- **Archive deep links:** Set integration `archive_url` to `/reliable-notify` or a Lovelace view with the card. Non-admin users cannot read the full archive.
- [Configuration and routing](docs/CONFIGURATION.md)
- [Transport channels and HTTP security](docs/TRANSPORTS.md)
- [Operations, backups and recovery](docs/OPERATIONS.md)
- [Service and WebSocket API](docs/API_V2.md)
- [Integration and device test plan](docs/TEST_PLAN.md)
- [Upgrade from older versions](docs/MIGRATION.md)
- [Security notes](SECURITY.md)
- [Change history](CHANGELOG.md)

Source licensed under [MIT](LICENSE). Issues and contributions are welcome.

## v2.5: Native Notify and migration advisor

All configured, validly named recipients, people and groups are now also available as **modern Home Assistant notify entities**. For a route named `telegram_wolfgang`, use `notify.send_message` with `target.entity_id: notify.reliable_telegram_wolfgang` (check actual entity ID in Home Assistant). For classic automations, the optional `notify.reliable_telegram_wolfgang` service is available with conventional `message` and `title` keys and optional nested Reliable Notify `data` settings.

Open the admin panel **Automation-Migration** tab for a safe, read-only audit of `automations.yaml` and `scripts.yaml`. Static, unambiguous actions receive conversion proposals; complex/templated actions are explicitly marked manual. No automation files are modified.

Version 2.5 also adds reusable notification templates via `reliable_notify.send_template`, up to one year of daily transport aggregates, and database indexes. See [Notify migration](docs/NOTIFY_MIGRATION.md) and [v2.5 release notes](RELEASE_NOTES_v2.5.0.md).
