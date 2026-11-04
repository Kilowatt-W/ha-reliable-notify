# Configuration and routing

## Installation

1. Add `Kilowatt-W/ha-reliable-notify` as a custom Integration repository in HACS/Marketplace.
2. Install the latest published release and restart HA Core.
3. Add Reliable Notify under Settings → Devices & services. **Default Notify is optional**.
4. Open the **Reliable Notify** sidebar panel (admin only).
5. Set up recipients. The panel lists Companion notify services and `person.*` entities detected by HA.
6. To migrate existing automations, replace direct notify actions with `reliable_notify.enqueue` and explicitly list recipient aliases.

## Recipient examples

The optional `/config/reliable_notify_routes.yaml` supports `recipients`, `groups` and `persons`. UI-managed definitions override names in the YAML file; do not store the same name in several categories.

```yaml
recipients:
  phone:
    action: notify.mobile_app_my_phone
  telegram:
    action: telegram_bot.send_message
    data:
      chat_id: 123456789
  mail:
    action: notify.send_message
    target_entity: notify.my_mail
groups:
  family: [me]
persons:
  me:
    entity: person.me
    channels:
      mobile: phone
      telegram: telegram
    preferred:
      info: mobile
      warning: telegram
      critical: [telegram, mobile]
    preferred_by_zone:
      home:
        info: mobile
      driving:
        warning: telegram
```

Home Assistant `person.*` state is consulted when a new message is queued; changes in zone later do **not** reroute already-queued deliveries. An unknown/unavailable person state falls back to normal per-priority preferences. Zone overrides apply only to the priorities defined under that zone.

## Archive

`message_type` selects a central policy. Defaults: info 1 day, warning 7 days, critical 30 days.

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [me]
    message: "Status changed"
    priority: info
    archive: delete_after_send
```

For a special message use `archive_days: 0..365`. A value of zero removes the **archived body after successful delivery**; it does not delete pending or dead-letter messages.

## Quiet hours and digest

In the integration options, all sections are expanded on the same page. Edit the **Quiet hours, limits and digest** fields there, or use the admin panel.

```yaml
enabled: true
start: "22:00"
end: "07:00"
allow_priorities: [critical]
```

`strategy: digest` needs `dedup_key`, is available only for text notifications without attachments, and groups waiting occurrences into a single message. Default digest window: 300 seconds. Noncritical attempts are rate-limited by recipient/action (default 10 per minute); critical alerts bypass the limit.

## State-dependent alerts

The optional `only_if` field prevents obsolete notifications from being delivered after an internet outage. Reliable Notify checks the state **immediately before dispatch**, not just when the message was enqueued.

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [phone]
    title: "Schlafzimmerfenster noch offen"
    message: "Das Fenster wurde zu lange offengelassen."
    dedup_key: bedroom_window
    only_if:
      entity_id: binary_sensor.kontakt_fenster_schlafzimmer_extended
      state: "on"
```

If the window is already closed when the worker processes the queued message, its status becomes `suppressed` and no push is emitted. This reduces misleading delayed warnings; it is not a transactional guarantee against a state change in the milliseconds between the check and provider dispatch.

## Test mode

From integration options or admin panel choose `test_mode: stage`. With an empty `test_recipients` list **all** newly queued messages are staged; otherwise only matching endpoint targets are staged. Staged messages never send and never escalate. They can be assigned a real recipient manually later.

For a nonpersistent read-only policy preview use the **Simulation** tab or `reliable_notify.simulate`. It does not insert into SQLite, send a message or consume transport rate limits.

## Signed acknowledgement

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [telegram]
    title: "WAN disconnected"
    message: "Check the WAN uplink"
    priority: critical
    dedup_key: wan_down
    acknowledgement:
      required: true
      escalation:
        - after: 300
          recipients: [phone]
        - after: 600
          recipients: [family]
```

For supported Telegram text/Companion routes the integration adds **Bestätigen / 15 Min. später / Eskalieren** buttons with short HMAC-signed action identifiers. HA receives `telegram_callback` and `mobile_app_notification_action` events; unknown/unsigned actions are ignored. The callback secret is generated and stored locally in `/config/.storage/reliable_notify_callback_secret` with restrictive file permissions.

You can also manually call `reliable_notify.acknowledge` with the incident's `dedup_key`.

## Logging

Use the **Test mode, diagnostic logging and backup** options screen. Loglevels: `off`, `error`, `warning`, `info`, `debug`, separately for `telegram`, `smtp`, `notify`, `companion`, `ntfy`, `gotify` and `webhook`. Logs include only message IDs, transport type and classified failure reason; they do not intentionally print message bodies or credentials.

## Notify entity exports (v2.5)

For each safely named route, Reliable Notify creates `notify.reliable_<route>` with the supported modern `notify.send_message` service. The legacy `notify.reliable_<route>` action is enabled by default for compatibility and can be disabled in integration **General settings → Legacy notify services**. Reload the integration after editing the YAML recipient inventory to synchronize exposed services and entities.

## Templates (v2.5)

In the admin panel **Vorlagen**, store named JSON template specifications containing a Jinja `message` and optional `title`, `recipients`, `priority` and archive policy. Then invoke `reliable_notify.send_template` with a template name and simple variables. Template editing is administrator-only. Rendered message bodies have a size limit.

For conversion from existing automations, see [Notify migration](NOTIFY_MIGRATION.md). The automatic scan is deliberately read-only.

## Settings interface (v3.1)

The HA options dialog displays General, Quiet hours, three retry priorities, Archive retention, Test/backup and Transport logging simultaneously, with no area dropdown. All values use form fields. Existing custom retention types remain visible as numeric fields. Routes, profiles, external API settings and templates are edited in the admin panel.

The panel displays recipients, groups and persons in separate open cards. Select an existing name to load its complete definition before editing; adding a new item does not alter existing ones. Parameters can be added as text, numbers, switches, lists or nested fields. Secret fields are masked. Saving a file-backed route creates a UI override; only UI-managed entries can be deleted.

YAML previews are optional and read-only. In the options dialog, enable **Show YAML before saving** and submit; confirm on the preview page to save. In the panel, expand **YAML preview** to inspect live form values. Previews can contain configured transport credentials, so do not share them. No JSON editing is needed.
