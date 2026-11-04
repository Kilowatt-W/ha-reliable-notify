# Reliable Notify v3 Profiles

Profiles are named defaults for common categories of messages. The caller's explicit fields always take precedence.

Use the form fields in **Reliable Notify → Profile & API**. Add named profiles and optional fields individually; existing guards and escalation settings remain editable. Expand **YAML preview** when you want to inspect the resulting configuration.

```yaml
standard:
  priority: info
important:
  priority: warning
critical:
  priority: critical
temporary:
  priority: info
  archive: delete_after_send
digest:
  priority: info
  strategy: digest
window_warning:
  priority: warning
  message_type: windows
  archive_days: 7
```

Use in HA:

```yaml
- action: reliable_notify.enqueue
  data:
    profile: window_warning
    recipients: [wolfgang_phone]
    dedup_key: window_bedroom
    message: "Schlafzimmerfenster noch offen"
```

Or call a configured profile from an external application (API permissions apply). Profiles can set priority, recipient aliases, message_type, archive, archive_days, ttl, strategy and state guards. The REST API specifically prevents profiles from bypassing the noncritical restriction.

Creating a custom profile dictionary replaces the default dictionary unless you include the default names. Optional `strategy: digest` still requires an explicit unique `dedup_key`.
