# Security policy

Reliable Notify is a third-party Home Assistant custom integration.

## Sensitive information

- Notification text, SMTP attachment references and Telegram route data may contain personal information. The SQLite database and HA backup storage must be protected.
- HMAC callback signing secret is stored in the HA configuration `.storage` directory and should not be committed to Git.
- Native ntfy/Gotify/webhook access tokens are kept in local route configuration; queue payloads only store endpoint fingerprints, not the token.
- Transport logs are deliberately limited to opaque message IDs, action types and error categories.
- Admin WebSocket endpoints check Home Assistant's administrator permission. The panel is admin-only.
- Test mode staging preserves full message bodies for manual review; do not stage passwords or other credentials.

## Native HTTPS security

Native destinations must use HTTPS and do not follow redirects. Local/privately-addressed literal IPs require explicit `allow_private: true`; this is **not** full DNS rebinding protection. Use only trusted endpoints. Use HA-level `rest_command` for complex authentication and network controls.

## Reporting vulnerabilities

Open a private GitHub security advisory for the repository, if supported, rather than publishing credentials, database contents or exploit details in an issue. Rotate any exposed tokens immediately.
