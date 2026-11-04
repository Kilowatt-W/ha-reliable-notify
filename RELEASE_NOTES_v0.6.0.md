# Reliable Notify v0.6.0 (development)

- Interactive authenticated Lovelace queue dashboard with retry/delete, dead letters, history and disk usage.
- Central retry policies by priority, provider-aware transient/permanent/rate-limit classification.
- Immutable `/media` snapshots for local SMTP attachments with proper SQLite reference tracking.
- Disk-free prechecks to avoid queuing messages on a nearly full filesystem.
- SQLite migration adds `media_paths_json` to active and dead-letter tables; existing data retained.
- New unit tests for retry policy validation, error classifications and attachment references.

## Install / upgrade

Back up `/config/.storage/reliable_notify.db` and the YAML routes before updating. Restart HA Core after installation. Register `/reliable_notify/reliable-notify-card.js` as a JavaScript module resource in the dashboard and use `dashboard.example.yaml`. Configure policies through integration options. See README for media limitations and the SQLite at-least-once delivery contract.

**Status:** Developer release; tested locally against standalone unit tests only. Live HA and SMTP/Telegram tests are still outstanding.