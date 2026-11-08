# Automation migration in v3

The integration's **Automation-Migration** tab scans the standard `automations.yaml` and `scripts.yaml` plus known package directories, all read-only during scanning. Results contain proposals, unresolved targets, a before/after YAML preview and SHA-256 of each source file.

## Confirming a change

For direct `packages/*.yaml` files only, the admin panel presents a button to approve a single straightforward replacement. The implementation:

1. Requires explicit per-action confirmation.
2. Re-reads the file, verifies SHA-256 against the scan, reanalyzes the selected action.
3. Rejects action blocks containing comments or YAML anchors/aliases, `!secret`/`!include` values, or more complex transport data. Refusals return a stable code (for example `file_changed`, `manual_edit`, `not_unique`) that the panel shows in German or English.
4. Parses the patched YAML before writing anything.
5. Creates a restricted-permission backup in `.storage/reliable_notify_migrations/`.
6. Uses an atomic file replacement and returns the backup and new SHA-256.
7. Does **not** reload automation or restart Home Assistant automatically.

UI-managed `automations.yaml` and `scripts.yaml`, dynamically computed destinations, complex packages/includes and actions with comments remain **manual suggestions only**. This is intentional to avoid overwriting HA editor state or changing behavior silently.

Back up HA before migration. Review each suggestion, compare actual Telegram/Companion target behavior, test a manually selected automation and only then proceed with bulk review.
