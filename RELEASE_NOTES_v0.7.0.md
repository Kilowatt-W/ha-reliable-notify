# Reliable Notify v0.7.0 — searchable notification archive

## New

- **Persistent message archive** stores complete message text and title across successful delivery, restarts, and queue removal. It does not store transport payloads, API tokens or attachment bytes in the archive table.
- **Admin-only archive search and detail** via WebSocket. The interactive Lovelace card includes an archive panel with search and full-text message display.
- **Direct links from Companion App notifications**: set an Archive dashboard URL under integration Configure → General settings (for example `/lovelace/reliable-notify`), create a view containing the Reliable Notify card at that path, and configure an endpoint with action `notify.mobile_app_<phone_id>`. Reliable Notify adds `url` (iOS) and `clickAction` (Android), pointing to the archived message after it has been assigned a durable ID. Caller-provided click targets are preserved.
- **Retention**: archive keeps up to 2000 completed records / 30 days, while pending and dead-letter records remain accessible. Staged test messages continue to work.
- **Status tracking**: queued, retrying, sent, dead, staged, manually cancelled/deleted, or cleared.

## Companion example

In the configuration of Reliable Notify choose `archive_url` = `/lovelace/reliable-notify` and place a card there:

```yaml
type: custom:reliable-notify-card
title: Reliable Notify
```

Define a phone route and send:

```yaml
recipients:
  phone:
    action: notify.mobile_app_your_phone
```

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [phone]
    title: "Fensteralarm"
    message: "Das Fenster ist seit 90 Minuten geöffnet."
    priority: warning
```

A tap on the mobile notification opens the configured dashboard view, where the card retrieves the specific message text. The archive is restricted to Home Assistant administrators, so non-admin mobile accounts cannot access this detail view.

## Important

- **Use the correct dashboard path**, including a Lovelace view with the card. Otherwise the app cannot display the archived message.
- Phone OS settings still determine the amount of text visible in the push preview.
- A Home Assistant send-service success does not mean the phone received or displayed the notification. SQLite delivery is at-least-once; duplicates are possible after lost acknowledgements.
- Archive message bodies can contain personal details. They are readable to HA administrators; database backups should be protected.
- Local unit tests and CI do not replace live validation on HA OS + Android/iOS.
- Home Assistant Core restart required after updating custom integration code.


Release workflow: publication is gated on Python tests, HACS checks and hassfest. Test under Home Assistant before relying on this for alarms.
