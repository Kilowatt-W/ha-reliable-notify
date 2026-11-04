# External Applications API v3 (openINFRA, openSYSLOG, openPROXY)

**Endpoint:** `POST /api/reliable_notify/v1/messages`.

The external API uses the **existing Home Assistant Bearer/Long-Lived Access Token authentication**, not independent credentials. By default it returns HTTP 403: disabled.

Configure under **Reliable Notify → Profile & API**. Enable the API, explicitly select allowed recipient aliases and set a maximum rate (1–60 requests/minute/authenticated HA admin). Empty allowlist means deny all, even when enabled.

```bash
curl -i -X POST 'https://YOUR-HA/api/reliable_notify/v1/messages' \
 -H 'Authorization: Bearer YOUR_HA_LONG_LIVED_TOKEN' \
 -H 'Content-Type: application/json' \
 --data '{"recipients":["telegram_wolfgang"],"priority":"warning","message_type":"it","message":"Disk space low","dedup_key":"infra_disk_warning"}'
```

**Response:**
```json
{"status":"queued","receipt":"durable_queue","version":"1"}
```

HTTP 202 means the message is safely stored, not that Telegram or a phone accepted or displayed it. Failed storage/validation will cause a non-2xx response.

Supported JSON keys: `message`, `title`, `recipients` (required), `priority` (info/warning only), `message_type`, `dedup_key`, `profile`, `archive`, `archive_days`, `ttl`. Other keys are rejected. The body limit is 16 KiB. No attachments or arbitrary target/action override are allowed. Profiles may not escalate the effective priority to critical through the API.

Security notes: use HTTPS at the reverse proxy, keep bearer tokens in secure secret storage, rotate compromised tokens, do not expose access tokens in logs. Only HA administrators with explicit allowlisted routes can send via this API. Route groups may fan out to several recipients; include them only if that is intentional. The endpoint has basic per-user rate limiting but is not a substitute for reverse-proxy network controls.
