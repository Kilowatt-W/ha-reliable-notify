# Reliable Notify v3.0.0

## Release highlights

Reliable Notify v3 combines previously released durable notification queue, native Home Assistant `notify.*` endpoints and the administration panel with a new security-conscious external API, reusable notification profiles, controlled automation migration, expanded Telegram lifecycle and refreshed custom integration branding.

### Notification profiles (v2.8)
Define JSON profiles in **Reliable Notify → Profile & API**. Profiles provide shared defaults for recipients, priority, retention, TTL and digest. Explicit fields in a message override the profile.

```yaml
- action: reliable_notify.enqueue
  data:
    profile: temporary
    recipients: [telegram_wolfgang]
    message: "PVEC cycle finished."
```

Provided default profiles: `standard`, `important`, `critical`, `temporary`, `digest`. Custom profiles can be saved through the admin panel.

### External application API (v2.8)
An **opt-in**, authenticated `POST /api/reliable_notify/v1/messages` endpoint integrates external apps (such as openINFRA/openSYSLOG) through Home Assistant's standard long-lived access tokens. Restricted to Home Assistant administrators and a configured recipient allowlist; disabled by default; rate limit default 30 requests/minute/user; critical priority denied.

```bash
curl -X POST "https://YOUR-HOME-ASSISTANT/api/reliable_notify/v1/messages" \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"recipients":["telegram_wolfgang"],"priority":"warning","message":"openSYSLOG: repeated login failures"}'
```

HTTP 202 means the message was committed to the durable queue, **not** that it arrived at a device.

### Automation migration 2.0 (v2.6)
The **Automation-Migration** tab now scans `automations.yaml`, `scripts.yaml` and bounded direct `packages/*.yaml` / automation/script subdirectories. Suggested substitutions include an individual YAML diff and an unchanged-file SHA-256.

For straightforward *package* actions only, an administrator can explicitly approve **one change at a time**. The integration re-checks file SHA-256, rejects comments/anchors in the action, validates YAML, creates a restricted-permission backup under `/config/.storage/reliable_notify_migrations/`, and atomically replaces the file. You must reload package automations manually. UI-managed `automations.yaml` and `scripts.yaml` are deliberately **never automatically rewritten** to avoid HA editor conflicts. Complex dynamic destinations still require manual review.

### Telegram lifecycle (v2.7)
The integration tags Telegram send_message jobs with its queue ID and listens to `telegram_sent` events. Received Telegram chat/message IDs can be used with `reliable_notify.telegram_lifecycle` to edit or delete the most recent tracked message for an explicit configured Telegram recipient and `dedup_key`. This action calls the provider directly (it is **not** retry-queued). Events must have been captured first; historical messages without references cannot be edited retroactively.

### Dashboard and monitoring (v2.7 / v3)
Added a 30-day delivery bar chart and the profile/API controls. Existing long-term daily aggregates, queue/dead-letter counters, storage and transport diagnostics remain available.

### Integration branding and icon
A newly designed shield-bell-check brand icon is stored at `custom_components/reliable_notify/brand/icon.png`, `icon@2x.png`, `dark_icon.png`, `dark_icon@2x.png`, with matching light/dark logos. All PNGs are generated reproducibly from source SVGs by `tools/generate_brand.py`.

**Home Assistant 2026.3+** supports local integration branding. **The built-in Marketplace in Home Assistant 2026.11** also supports local custom integration images. Some older, standalone HACS versions can still show "Icon not available" even when the icon is correctly present and visible on HA's Integrations screen; see `docs/BRANDING.md`.

### Security, migration and compatibility
- Legacy `notify.reliable_<route>` services and modern `notify.send_message` entities remain supported.
- External API is disabled by default, bound to admin authentication and an explicit recipient allowlist. No new unauthenticated endpoint.
- Sender secrets do not appear in the queue via this new API; Home Assistant owns authentication and tokens.
- SQLite schema additions are backward-compatible (Telegram receipts only).
- Existing critical message delivery still relies on at-least-once transport semantics.
- Back up Home Assistant before upgrading, restart Core and test all configured transports.

### Limitations
Automated CI cannot run real Android/iOS, Telegram or SMTP tests against your installation. GitHub issue #3 remains open until a live HA OS acceptance run is completed. The integration's icon cannot force older standalone HACS frontends to read local brand assets.
