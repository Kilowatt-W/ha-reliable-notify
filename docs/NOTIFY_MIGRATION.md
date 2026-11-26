# Notify entities and automation migration

## New notify destinations

Reliable Notify exposes each valid named recipient, group or person as a modern Home Assistant notify entity. Entities are named `Reliable <alias>` with stable unique IDs; Home Assistant ordinarily gives them entity IDs `notify.reliable_<alias>`. The actual ID may differ when a user has renamed the entity or another entity already occupied that ID.

Use this preferred modern action:

```yaml
- action: notify.send_message
  target:
    entity_id: notify.reliable_telegram_wolfgang
  data:
    title: "IT"
    message: "Firewall nicht erreichbar"
```

Or preserve traditional syntax:

```yaml
- action: notify.reliable_telegram_wolfgang
  data:
    message: "Firewall nicht erreichbar"
    title: "IT"
```

Classic service aliases are optional and registered only when the requested service name is not already in use. They accept a nested `data` object; Reliable Notify configuration keys (`priority`, `message_type`, `archive`, `archive_days`, `dedup_key`, `ttl`, `strategy`, `acknowledgement`, `only_if`, `test_mode`) are extracted and the remaining fields are forwarded per transport: for classic notify targets (Companion app, e-mail, YAML groups) they become that service's own `data` (e.g. `tag`, `channel`, `actions`) and are merged with the target's default `data`; for Telegram they stay top-level (`parse_mode`, keyboards). Before 3.9.0 Companion fields given this way were dropped. The modern notify entity deliberately only accepts `message`/`title`, matching HA's public NotifyEntity API.

If two aliases target the same Telegram chat ID, the migration tool will mark the match **ambiguous**. Route definitions with invalid names are not exported as notify entities. A single message may be enqueued to multiple notify entities; HA does not provide exactly-once delivery across entities.

## Automation migration advisor

The admin sidebar contains **Automation-Migration**. Press **Benachrichtigungen analysieren / Analyse notifications** to inspect HA's `automations.yaml`, `scripts.yaml` and YAML files in `packages/`, `automations/` and `scripts/`. This is **read-only** and does not alter or reload your automations. Files are parsed with a safe loader: `!secret`, `!include`, `!input` and similar tags are never resolved, so secrets never reach the panel; actions using such values are listed for manual review. Missing default files are shown as skipped, not as errors; YAML syntax errors are reported with their line number. A bounded scanner traverses nested `choose`, `if`, `parallel` and `repeat` sequences.

It suggests a classic `notify.reliable_<alias>` action when a static destination matches exactly one configured recipient. Since 3.9.0 the empty `metadata: {}` the HA editor adds is kept, Companion `data` and Telegram fields are carried over (through `reliable_notify.enqueue` when a field is named like a Reliable Notify option such as `priority` or `ttl`), and `target: device_id` is resolved to the device's notify entity when it has exactly one. Actions whose response is used later (`response_variable`, e.g. a Telegram message ID), multiple or template targets, notify services that no longer exist and unknown destinations require manual review; for an unknown static destination the panel offers **Create a target for it** with a prefilled form. `notify.persistent_notification` (HA bell) is not listed. For entries of `automations.yaml`/`scripts.yaml` the panel links to HA's editor and offers the replacement as copyable YAML.

Example old action:

```yaml
- action: telegram_bot.send_message
  data:
    chat_id: 123456789
    message: "Fenster noch offen"
```

Suggested alternative:

```yaml
- action: notify.reliable_telegram_wolfgang
  data:
    message: "Fenster noch offen"
```

**Always verify title/message formatting, recipients, notification tags and platform-specific data**. The scan report contains JSON snippets for review or download. Apply accepted changes through Home Assistant's Automation Editor, not by modifying `automations.yaml` from a separate integration.

Each manual-review entry carries a stable `reason_code` (shown in German or English in the panel; the English `reason` stays in the JSON download). Unsupported sources include custom included directories and Jinja-computed targets. For those, use manual review or add them to a separate migration process. Scripts and automation packages may have differing include/file structures.

## Why no automatic file rewrites?

Home Assistant manages `automations.yaml` through the UI and documents that direct manual editing of UI-managed content can cause problems. More importantly, Reliable Notify cannot guarantee that a Telegram photo/keyboard action or dynamic target is behaviorally equivalent to a generic notify entity. The tool therefore only **suggests** changes until each action is reviewed and approved.
