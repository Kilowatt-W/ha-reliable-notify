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

Classic service aliases are optional and registered only when the requested service name is not already in use. They accept a nested `data` object; Reliable Notify configuration keys (`priority`, `message_type`, `archive`, `archive_days`, `dedup_key`, `ttl`, `strategy`, `acknowledgement`, `only_if`, `test_mode`) are extracted and the remaining transport fields are forwarded as transport parameters. The modern notify entity deliberately only accepts `message`/`title`, matching HA's public NotifyEntity API.

If two aliases target the same Telegram chat ID, the migration tool will mark the match **ambiguous**. Route definitions with invalid names are not exported as notify entities. A single message may be enqueued to multiple notify entities; HA does not provide exactly-once delivery across entities.

## Automation migration advisor

The admin sidebar contains **Automation-Migration**. Press **Benachrichtigungen analysieren / Analyse notifications** to inspect HA's `automations.yaml`, `scripts.yaml` and YAML files in `packages/`, `automations/` and `scripts/`. This is **read-only** and does not alter or reload your automations. Files are parsed with a safe loader: `!secret`, `!include`, `!input` and similar tags are never resolved, so secrets never reach the panel; actions using such values are listed for manual review. Missing default files are shown as skipped, not as errors; YAML syntax errors are reported with their line number. A bounded scanner traverses nested `choose`, `if`, `parallel` and `repeat` sequences.

It suggests a classic `notify.reliable_<alias>` action only when a static destination matches exactly one configured recipient and the original action uses only `message` and optionally `title` (plus its static destination). Extra Telegram buttons, multiple targets, template expressions, complex services, and unknown destinations require manual review.

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
