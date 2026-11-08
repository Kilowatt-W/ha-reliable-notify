# Changelog

## 3.3.1
- Fix the automation check on real Home Assistant installations: files are parsed with a safe, read-only loader that returns plain values. Previously HA's YAML node types made every file with a suggestion fail, and `!secret` values made whole files fail.
- `!secret`, `!include`, `!input` and similar tags are never resolved; affected actions are listed for manual review and secrets never reach the panel.
- Missing default files (e.g. no `scripts.yaml`) are shown as skipped instead of errors; YAML syntax errors show the line number.
- Fix applying a single package change when the action is not the last one in its list (the following list item was merged into the replacement and the change was refused).
- Reasons, file errors and refusals of the automation check use stable codes and are shown in German or English; route display names are shown in suggestions.
- Add in-panel help for every section (German/English) with steps, automation examples and links to the documentation; a header button shows or hides help and remembers the choice per browser.

## 3.3.0
- Add optional display names (Klarnamen) for targets, groups and people: free text up to 100 characters, edited in the admin panel or under `labels` in `reliable_notify_routes.yaml`. The internal name is suggested from the display name when creating an entry and stays the routing key.
- Show display names in the target list, in group/person/profile/escalation pickers, in the card's staged-message assignment, in real test notifications and as the friendly name of route notify entities. Entity IDs stay `notify.reliable_<internal name>`.
- Localize the remaining backend texts: Companion/Telegram action buttons and Telegram callback answers follow the HA system language (German for `de`, otherwise English).
- Translate select values in HA forms and actions (priority, media, archive, strategy, test mode, Telegram operation, log level) and in the panel/card (including message status), keeping stored values unchanged.
- Show admin-panel backend errors in German or English based on their error codes, keeping technical details.
- Make the Python test suite pass on Windows (test-only SQLite handles, `os.fchmod` fallback).

## 3.2.1
- Add semantic icons and section colours to all nine navigation entries, plus an explicit active-page marker and keyboard focus styling.
- Add icons to panel headings, form groups, YAML previews and every action, preserving German/English labels and user-defined values.
- Present queue metrics as five coloured tiles; add icons and semantic priority badges to the standalone card.
- Share the theme-aware palette and icon helpers between panel and card; retain readable text in light/dark HA themes and responsive navigation.

## 3.2.0
- Add admin-only real test notifications per saved recipient, group and person, with bounded live status polling, respecting quiet hours and test mode.
- Add theme-aware action colours, icons and accessible test statuses.
- Fix service translation metadata required by hassfest.
- Add a direct target-management link and clear sidebar instructions in setup and integration options (German and English).
- Localize the admin panel, Lovelace card, service descriptions/fields and diagnostic sensor names in German and English; use HA language, English fallback.
- Browse existing notify.* and person.* entities by friendly name and ID; suggest existing notification actions including classic notify.mobile_app_* services.
- Explain invalid internal route names with allowed characters, length and a valid example before submitting.
- Fix target-management navigation from an already rendered settings panel and preserve technical keys, aliases, secrets and message content during localization.

## 3.1.1
- Keep the default notify entity optional in setup and options; omit invalid empty entity suggestions and normalize cleared selections.
- Clarify target creation with a Ziele & Personen tab, explicit create buttons, setup hints and a direct entry from settings.

## 3.1.0
- Replace the settings-area dropdown with eight expanded settings sections.
- Replace admin-panel JSON editors with typed, nested form fields for routes, profiles, templates and simulation.
- Add optional read-only YAML previews and preserve existing options and transport parameters.
- Add admin-only single-route loading for editing; inventories and diagnostics remain redacted.
- Add functional DOM tests and options-save regression coverage.

## 3.0.0 — 2026-11-04
- New locally shipped and versioned shield-bell-check brand icons/logos, SVG sources and PNG generation workflow.
- Optional Home Assistant authenticated external API for applications, with administrator-only token access, rate limits and recipient allowlist.
- Named notification profiles and administrative editor; defaults can be explicitly overridden.
- Extended migration scanner to packages and known YAML folders, individual diff preview and opt-in single-package-action changes with preimage SHA-256, backup and atomic replacement; HA UI files never automatically rewritten.
- Telegram sent-message IDs tracked via telegram_sent; explicit edit/delete by configured chat and dedup key.
- 30-day delivery chart, regression tests, enhanced security/operational documentation.


## 2.5.0 — 2026-11-04
- Native notify entities per configured recipient/group/person and optional classic notify.reliable_* services.
- Read-only migration advisor with safe suggestions for automation/script notifications.
- User-configurable Jinja message templates with bounded variable mappings.
- Long-term daily aggregates (365 days) and query indexes for delivery reporting.
- Better route lifecycle and compatibility settings; tests and docs.


## 2.0.0 — 2026-11-04
- Admin-only HA sidebar panel with integrated queue, people/groups/routes editor, incident wizard, safe simulator, statistics and test-mode controls.
- Signed native Companion / Telegram ACK, snooze and escalate callbacks, compact enough for Telegram.
- Exactly-once SQLite escalation step advancement and queued message creation (not provider-side exactly-once receipt).
- Native HTTPS ntfy, Gotify and generic webhook POST with endpoint pinning and secret-free persisted payloads.
- Location/zone-aware person channel preferences; Companion device discovery.
- Transport health sensors, delivery-latency statistics and anonymized diagnostic summaries.
- Weekly online SQLite backup snapshots and admin backup action.
- Dedicated test-mode staging and per-transport log levels.
- API reference, security guide, migration steps and HA OS acceptance test matrix.

## 1.1.0
- Quiet hours, per-endpoint rate limiting, digest coalescing.

## 1.0.0
- Person routing, Companion tag-based update and dismissal, live Lovelace refresh.

## 0.9.0
- DB maintenance, dead letter retention, durable acknowledgement and escalation.

## 0.8.0
- Per-message archive retention and completed archive size cap.
