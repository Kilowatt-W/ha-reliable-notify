# Reliable Notify v0.5.0 (Home Assistant custom integration)

**Status: development / test deployment.** Implements local-first, persistent *at-least-once* notification delivery. Not a guarantee that recipients receive or read a message, and duplicates are possible if an upstream provider accepts a message before HA times out. **No Supernotify dependency.**

## Changes introduced in v0.4.0 (retained in v0.5.0)

- Dedicated Telegram delivery lane (one worker) and independent notify/mail lane (two workers). Failure of one channel does not block another lane. Workers poll every <=10s; each request times out after 35s.
- **Critical** messages are retried indefinitely for transient failures (exponential backoff up to 1 hour), unless they expire due to a caller-provided TTL. Invalid saved payloads may enter dead letters immediately.
- Noncritical messages go to dead letters after 12 failed attempts; retry with `reliable_notify.retry_dead`.
- **Photo spool**: local files for Telegram `send_photo` are copied immediately into `/media/reliable_notify/`, persisted across HA restarts, and removed when no longer referenced. 20 MiB upper limit per source file, jpg/png/webp. Remote image URLs are referenced, not downloaded/snapshotted, so availability at retry time is not guaranteed. Copies count toward disk usage.
- **UI-managed recipients and groups** under Settings > Devices & services > Reliable Notify > Configure: add/update person/endpoint, add/update group, remove UI-defined route, general settings. UI entries override YAML entries with the same name. No complete Lovelace dashboard or visual live-queue editor yet.
- Queue & dead-letter sensors now publish up to 10 sanitized recent records (IDs, targets, actions, attempts, times and error strings; messages, Telegram chat ID payloads and mail contents are not displayed).
- SQLite schema automatically migrates v0.3 tables to include photo references. Existing v0.1/v0.2/v0.3 queue data is retained.

## Installation / update

1. Back up `/config/.storage/reliable_notify.db` and `/config/reliable_notify_routes.yaml`; **stop HA before copying a SQLite database**, because it runs in WAL mode.
2. Extract `custom_components/reliable_notify` into `/config/custom_components/reliable_notify` (overwrite previous version). Restart Home Assistant.
3. Add the integration under Settings > Devices & services if not already present; choose a default `notify.*` **entity**.
4. Configure named destinations using the integration's **Configure** UI or copy and edit `reliable_notify_routes.example.yaml` to `/config/reliable_notify_routes.yaml` and run `reliable_notify.reload_routes`.
5. When sending Telegram **local photos**, allowlist the spool path (required by Telegram bot). Add to `configuration.yaml` and restart HA:

```yaml
homeassistant:
  allowlist_external_dirs:
    - /media/reliable_notify
```

If `homeassistant:` or `allowlist_external_dirs` already exists, **merge** with that configuration; do not duplicate the key. Telegram must have permission to read the source snapshot too if it is used directly outside Reliable Notify.

### Existing mail / other notification providers

Reliable Notify uses `notify.send_message` with a real notify entity, or a concrete legacy `notify.<service>` action. Mail/SMTP configuration stays inside the existing HA integration; Reliable Notify does not implement its own SMTP credentials. Only HA `notify.*` actions and Telegram `send_message/send_photo` are allowed (not arbitrary service execution).

## Example: Telegram message with inline keyboard

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [wolfgang_telegram]
    priority: warning
    dedup_key: window_bedroom
    strategy: replace
    ttl: 3600
    message: "<b>Fenster Schlafzimmer</b> ist seit 90 Minuten offen"
    data:
      inline_keyboard:
        - "Status:/window_status, OK:/window_ack"
```

Buttons only **send** Telegram callback events. Callback handling still requires an HA Telegram event automation; no click callback action is automatically registered by Reliable Notify. See Home Assistant's Telegram bot examples.

## Example: Telegram photo with persistent spool

First create a snapshot, then queue it:

```yaml
- action: camera.snapshot
  target:
    entity_id: camera.eingang
  data:
    filename: /media/eingang.jpg
- action: reliable_notify.enqueue
  data:
    recipients: [wolfgang_telegram]
    media: photo
    message: "Bewegung am Eingang"
    priority: critical
    data:
      file: /media/eingang.jpg
      inline_keyboard:
        - "Kamera: /camera_eingang, Ignorieren:/ignore"
```

When enqueued, a separate immutable copy goes to `/media/reliable_notify`. The temporary `/media/eingang.jpg` may then be overwritten. Configure `allowlist_external_dirs` for `/media/reliable_notify` as above. The photo is not copied into an SQLite BLOB. Replacing a queued message does not force an already-in-flight send to stop.

## Example: send via group to Telegram + mail + mobile app

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [it_alarm]
    message: "PVEC Scheduler: Netzbezug über Limit"
    title: "IT Alarm"
    priority: critical
    strategy: replace
    dedup_key: pvec_net_overlimit
```

Each physical recipient gets a separate durable queue record. Groups may contain other groups; duplicates are merged within a single enqueue. Routing is evaluated *at enqueue time*, so changing recipients does not reroute queued jobs.

## Cancel outdated status warnings

```yaml
- action: reliable_notify.cancel
  data:
    dedup_key: window_bedroom
```

Pending nonleased messages are removed. Messages in-flight or already delivered cannot be cancelled. An automation should still use `continue_on_error: true` on enqueue if even local disk/SQLite failures must not interrupt the remaining automation.

## Service list and entities

- `reliable_notify.enqueue` – message, title, recipients (or `action` / `target_entity`), media `text|photo`, data, priority `info|warning|critical`, ttl (0=no expiration), dedup_key, strategy `always|replace`.
- `reliable_notify.cancel`, `reliable_notify.retry_all`, `reliable_notify.retry_dead`, `reliable_notify.clear_queue`, `reliable_notify.reload_routes`.
- Diagnostic sensors: Queue Size, Dead Letter Count, Sent, Failures. Retry button.

## Operational guarantees and limitations

- A successfully executed HA service indicates that the **upstream integration** accepted the call, not an end-device receipt/read acknowledgement.
- If HA is abruptly interrupted between successful upstream delivery and SQLite acknowledgement, the message may be delivered twice.
- The long-term local queue can fill disks. The integration enforces a 10,000-message limit, but photo storage is bounded only per image, **not by a total disk quota**. Monitor available free disk space.
- A Telegram photo's local filesystem path requires an allowlist; remote URLs might expire and are not cached.
- Notifications are processed at priority order *within each lane*; enqueue order among different workers is not guaranteed.
- A Telegram outage does not block other lane workers, but a nonresponsive mail service could temporarily occupy one of the two general workers.
- Dead-letter records remain until retried; media cleanup retains photos referenced by dead letters.
- UI only supports adding/updating basic route records and comma-separated group members. YAML supports advanced transport payloads and other notify actions. The options flow does **not** expose existing YAML routes for editing, and UI deletion does not delete YAML routes.
- **Not yet verified with a running Home Assistant OS instance.** Run a real Telegram send/photo/keyboard, mail send, offline recovery and upgrade smoke test before depending on this for security alerts.

## Local testing

```sh
python -m unittest discover -s tests -v
python -m compileall -q custom_components/reliable_notify
```

## Next improvements

- Dedicated frontend panel with editable queue, dead letters, per-route status and manual control.
- Mail-specific attachment support, additional channels and per-route time windows.
- Provider-aware error classification and queue total-size safeguards.
- HA runtime tests, test fixtures and GitHub CI/HACS validation for public release.

---

## v0.5.0 – Updates and new functions

### Updating inside Home Assistant (instead of copying a ZIP)

**Yes, via HACS / the Home Assistant Marketplace.** This project is prepared as a custom-repository-compatible GitHub repository, but this ZIP is **not yet published** to a GitHub repository. The `OWNER` placeholder in `manifest.json` must be replaced with the actual GitHub owner and the repository must be published before an update can be offered in HA.

1. Create a GitHub repository, for example `reliable-notify`, and commit the **contents of this ZIP's `reliable_notify/` directory to the repository root** (including `custom_components/reliable_notify`, `hacs.json`, README, tests).
2. Replace `OWNER` in `manifest.json` with the GitHub account name; update other repository links as needed.
3. Create an actual published GitHub **Release** tagged `v0.5.0`, with version `0.5.0` in `manifest.json` (release tag prefix `v` supported by HACS). GitHub CI runs tests and HACS validation.
4. In HACS choose **Custom repositories**, add your GitHub repository URL, category **Integration**, and download it. In HA versions with the built-in Marketplace, the flow may differ.
5. Future GitHub releases (e.g. `v0.5.1`) appear as update notifications in Home Assistant. Press **Install**, then **restart Home Assistant Core** to load changed Python code. You do NOT need to manually unzip files each time. Updating Python integration code by mere **Reload integration** generally does not reload Python modules.
6. If Reliable Notify was previously copied manually, back up config/SQLite first. Ensure HACS installs to the same `custom_components/reliable_notify` path. Verify HACS ownership/update tracking; otherwise HACS may treat it as a manual installation.

Never implement an unauthenticated self-downloader of arbitrary updates inside the integration. Let HA/HACS handle signed-in UI actions and versioned upstream releases.

### New actions

```yaml
# Retry a single waiting record
- action: reliable_notify.retry_one
  data:
    id: 15

# Restore dead-letter record ID 8 to the active queue
- action: reliable_notify.retry_one
  data:
    id: 8
    dead: true

# Delete dead-letter record ID 8
- action: reliable_notify.delete_one
  data:
    id: 8
    dead: true
```

`delete_one` and `retry_one` reject active leases so they cannot cancel a request already in-flight. Delivery outcomes are stored for at most 30 days/2000 entries in SQLite, without message bodies or transport credentials. A **Delivery History** sensor exposes recent outcomes.

### Dashboard

Import `dashboard.example.yaml` as a **separate dashboard's raw YAML configuration** or copy its `views` into your existing dashboard. This is native Lovelace; it needs no frontend dependencies. Entity names can differ from the examples, so check Developer Tools > States. Native markdown cards show up to 10 queued/dead and 15 history entries. Per-ID operations are available from Developer Tools > Actions; **there is no interactive row-button frontend in this version**.

### SMTP with HTML and attachments

SMTP 2026.8+ supports `smtp.send_message` (vs generic `notify.send_message` for normal email). Define a named recipient:

```yaml
recipients:
  it_email:
    action: smtp.send_message
    target_entity: notify.your_smtp_recipient
```

Use a native HA media-source attachment, for example:

```yaml
- action: reliable_notify.enqueue
  data:
    recipients: [it_email]
    title: "Alarm"
    message: "Eingang: Bewegung erkannt"
    data:
      html: "<h2>Eingang</h2><p>Bewegung erkannt.</p>"
      attachments:
        - media_source:
            media_content_id: "media-source://camera/camera.eingang"
            media_content_type: "image/jpeg"
          filename: eingang.jpg
```

This attachment is **resolved by the SMTP integration at send time**; it is **not a durable image snapshot**. If the camera or media entity disappears before delivery, the send may fail or the image may differ. Telegram local images still use the immutable spool and 200 MiB total quota. Generic `notify.send_message` does not support universal attachments.

### Safety

The queue is *at-least-once*. Always guard critical alarm actions with other channels if you need independent assurance. Confirm the SMTP/Telegram service accepts an action in HA before registering as a route. For maximum safety continue using `continue_on_error: true` on the enqueue action when an I/O failure in SQLite must not stop an automation.