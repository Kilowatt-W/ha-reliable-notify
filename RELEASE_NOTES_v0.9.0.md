# Reliable Notify v0.9.0 — maintenance and acknowledgements

**Changes**
- Background SQLite maintenance with `PRAGMA quick_check(1)`, passive WAL checkpoint and database size diagnostics.
- Noncritical dead letters are deleted after a configurable 1–365 days (default 30); **critical dead letters are never automatically removed**.
- Acknowledged incidents are pruned after 30 days, while still-unacknowledged critical incidents remain.
- New database-size and maintenance-health sensors in Home Assistant.
- Durable acknowledgement records, manual `reliable_notify.acknowledge` service and administrator-only dashboard controls.
- Optional escalation schedule (up to five steps, delayed by seconds after initial enqueue) persists through HA restarts. Each step is enqueued to named recipients/groups. Escalations use retryable `enqueue` and can duplicate after crash boundaries (at-least-once); confirm an incident to stop later stages.

## Example

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [wolfgang_telegram]
    dedup_key: firewall_outage
    priority: critical
    title: "Firewall offline"
    message: "WAN firewall is unreachable"
    acknowledgement:
      required: true
      escalation:
        - after: 300
          recipients: [wolfgang_phone]
        - after: 600
          recipients: [it_team]
```

Confirm manually (including from a separate Telegram/Companion callback automation):

```yaml
- action: reliable_notify.acknowledge
  data:
    dedup_key: firewall_outage
    by: wolfgang
```

The integration **does not automatically equate a push delivery with user acknowledgement**; callback automations are required for phone/Telegram buttons. No dedicated browser panel yet; the bundled Lovelace card includes acknowledgements. Messages may still be delivered multiple times after an upstream timeout.

**Safety:** test against actual providers before depending on escalations. Backup the SQLite database only while HA is stopped; schema migration is automatic.