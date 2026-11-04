# Reliable Notify v0.6.1

## Changes

- Default Notify is optional in setup and options.
- If no recipient, explicit action, or configured default destination exists, notifications are persisted **without sending** in a staging inbox.
- The administrator-only Lovelace card displays staged message bodies, offers an explicit recipient selector and **Assign and send** / **Delete**.
- Staged messages survive HA restarts and are never picked up by background workers or generic bulk retry.
- Existing users with a configured Default Notify retain their previous behavior until clearing that setting.
- Companion App notification services (`notify.mobile_app_*`) are supported through named recipients; platform-specific `data.url` (iOS) and `data.clickAction` (Android) can be passed through to open a specific dashboard.
- Declared HTTP/WebSocket component dependencies to address hassfest validation.
- Added staging persistence regression tests.

## Limitations

- This is a development release. Live testing with Home Assistant OS and both phone platforms is required.
- Long notification text display is controlled by Android/iOS, not Reliable Notify.
- Delivered Companion push bodies are not archived automatically: staging is intentionally only for unaddressed messages.
- Staged messages require an administrator to assign an individual recipient. Staged messages cannot be automatically dispatched by bulk retry.
