# Reliable Notify v2.5.0 — Native Home Assistant Notify & Migration Assistant

## 2.1 — Native notify integration (backward-compatible)

Every safely named configured Reliable Notify recipient, group or person now creates a modern **NotifyEntity** with a stable unique ID, and optionally a compatibility notify service.

Example with configured recipient `telegram_wolfgang`:

```yaml
- action: notify.send_message
  target:
    entity_id: notify.reliable_telegram_wolfgang
  data:
    title: "Fensterwarnung"
    message: "Schlafzimmerfenster seit 90 Minuten offen."
```

The optional legacy compatibility API preserves existing notify syntax:

```yaml
- action: notify.reliable_telegram_wolfgang
  data:
    title: "Fensterwarnung"
    message: "Schlafzimmerfenster seit 90 Minuten offen."
    data:
      priority: warning
      message_type: windows
      archive_days: 2
```

Both interfaces enqueue into Reliable Notify's existing SQLite queue. A successful action only confirms durable enqueue, not phone delivery. The legacy interface is opt-in by default and may be disabled with `legacy_notify_services: false` in options. **Modern notify entity IDs can be renamed in HA's Entity Registry; check your actual entity ID before changing automations.** Updating the route inventory and reloading the integration synchronizes exposed endpoints.

## 2.2 — Improved receiver management

The admin panel continues to discover Companion services, display people/groups, and now exposes the new modern notify entities. Routes can be added, updated and removed through existing options and panel. Only valid route aliases are exposed as notify entities. Orphaned Reliable Notify entities are cleaned up when the route is removed.

## 2.3 — Reusable notification templates and event rules

New `reliable_notify.send_template` action renders an administrator-configured Jinja message template and routes the result into the same queue.

```yaml
- action: reliable_notify.send_template
  data:
    template: fensterwarnung
    variables:
      room: Schlafzimmer
      minutes: 90
    recipients: [wolfgang_phone]
```

Configure/edit templates under **Reliable Notify → Vorlagen**, for example:

```json
{
  "fensterwarnung": {
    "title": "Fensterwarnung",
    "message": "Das Fenster {{ room }} ist seit {{ minutes }} Minuten geöffnet.",
    "priority": "warning",
    "message_type": "windows",
    "archive_days": 2
  }
}
```

The existing `only_if` state guard continues to prevent obsolete notifications from being delivered (e.g., a window already closed when an offline queue resumes).

## 2.4 — Long-term statistics

The SQLite data store now maintains daily transport-status summaries separately from the short-term history, for up to 366 days. The admin statistics API includes `daily_trends`, by day, action and status. Only metadata is included, not message bodies. Additional indexes accelerate history and deduplication lookups.

## 2.5 — Performance and stability

Added indexes for route/dedup lookup, transport history and dead-letter cleanup. Daily aggregates are independently pruned; archived bodies and pending/critical messages retain their existing independent limits and protection. Legacy and modern notify APIs share the same durable queue and retention implementation.

## Automation migration assistant — read-only by design

In the admin panel, choose **Automation-Migration → Benachrichtigungen analysieren**. It inspects `automations.yaml` and `scripts.yaml` without modifying, disabling or reloading automations. The scanner finds simple static Telegram, Companion and notify destinations that correspond **unambiguously** to configured Reliable Notify routes and proposes replacements such as `notify.reliable_telegram_wolfgang`. Templated, advanced, multiple-target and ambiguous cases are flagged for manual review. Recommendations can be downloaded as JSON.

No migration is silently applied. HA's UI-managed `automations.yaml` must not be directly rewritten by custom integrations. Apply approved proposals in the built-in Automation/Script Editor after making a backup. Package YAML files and Jinja-generated destinations require separate manual review.

## Safety & testing

- Native notify entities expose only `message` and `title`, as required by the HA platform. To specify Reliable-Notify-only options, use legacy compatibility `data:` or `reliable_notify.enqueue`.
- Default notify remains optional. The migration advisor cannot infer that a `notify.notify` broadcast means a specific recipient.
- Some legacy notify actions have different title formatting, recipients or additional platform data; ambiguous cases are intentionally not converted.
- On first upgrade, restart Home Assistant Core. Confirm entity IDs and perform a test message before making migration changes.
- Existing queue/archive data is migrated automatically. Take a full HA backup first.
- Official publication requires unit tests, JS syntax validation, HACS, hassfest and real HA Core import smoke to succeed. Live provider tests on the user's HA OS remain a separate acceptance step.
