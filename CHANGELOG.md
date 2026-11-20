# Changelog

## 3.8.0
- Alarm window phase 3: `incident.mirror` (`none`, `persistent_notification`, `repairs`) and the option *Mirror open incidents by default*. The notification bell shows an entry per unacknowledged incident; dismissing it acknowledges the incident. Repairs show an error (critical) or warning (warning) issue. Entries disappear when acknowledged or closed and are restored after an HA restart.
- Sensor *Open incidents <area>* for every incident area; new areas appear automatically.
- Visual editor for `custom:reliable-notify-alarm-card` (areas, message types, minimum priority, snooze buttons, acknowledged incidents, confirmation, compact layout), German/English.
- `persistent_notification` added to the manifest dependencies.

## 3.7.0
- Alarm window phase 2: `incident.source_entity` with `problem_state`/`problem_states` (default `on`) – Reliable Notify watches the cause itself. When the entity leaves the problem state for `resolve_after` seconds the incident is resolved; if the problem returns before anyone acknowledged, it becomes active again (`reactivated`). `unavailable`/`unknown` never resolve. Waiting periods are stored and all watched entities are re-subscribed and re-evaluated after an HA restart.
- `incident.auto_close_after`: close a resolved, unacknowledged incident after a period (not for `critical`).
- Incident history (created, acknowledged, snoozed, escalated, resolved, reactivated, reopened, closed) kept for 90 days and shown in the admin panel under *Escalations → History*.
- Alarm card shows the cause entity ("Cause: …") and opens it on tap.
- Fix: Telegram button presses, Companion app actions and Telegram message receipts are processed in the event loop again. Without `@callback`, HA ran these handlers in a worker thread where creating tasks is not allowed, so presses could be lost. The alarm card's live subscription had the same issue and is fixed.

## 3.6.0
- Alarm window (phase 1): acknowledged notifications with `incident` (`display_text`, `area`, `escalate_while_resolved`) become incidents that stay visible until acknowledged, also after the cause is gone. States active → resolved / acknowledged → closed.
- New services `reliable_notify.resolve` (optionally stopping reminders), `reliable_notify.snooze` (minutes) and `reliable_notify.reopen`. Snoozing and escalating no longer move the incident's opening time.
- Event `reliable_notify_incident` with `dedup_key`, `action`, `by`, `priority`, `title`, `message_type`, `area` and `state` for every change, whatever the source (Telegram, app, card, panel, service).
- Entities: sensor *Open incidents* (with the incident list) and binary sensor *Critical incident open*.
- New card `custom:reliable-notify-alarm-card` for all users (loaded automatically): one band per incident by priority, "since", "resolved at", acknowledge and snooze buttons, escalate for admins, live updates, hidden when nothing is open; German/English.
- Signed-in users may acknowledge and snooze incidents (option to restrict to administrators); escalating, resolving and reopening need an administrator.
- Open incidents are kept regardless of priority; closed ones are removed after 30 days. Existing acknowledgements are migrated without losing open ones.
- The admin panel shows "since", "resolved at" and snooze status and can mark incidents as resolved; help examples for the alarm window.

## 3.5.0
- Scheduled notifications: `send_at` (date/time) and `delay` (seconds) in `reliable_notify.enqueue`, up to 31 days ahead; quiet hours apply from the send time and `ttl` counts from it. The simulation shows the planned time per target.
- Quiet hours per recipient and per person (also when a person is reached through a group); the recipient's own setting wins, then the person's, then the global one. Editable in the admin panel via "Add field".
- ntfy: buttons (`actions`, view/http), click link, image (`attach`), icon, tags and file name. ntfy is now published as JSON, so UTF-8 titles and labels are safe. Gotify: click link and large image. Webhook: extra fields are sent as `data`. Links are validated when queueing.
- Companion app notifications are grouped by message type (Android `group`, iOS `thread-id`); option in General, values set by the call are kept.
- Optional daily failure report (counts and top causes per target, no message texts) to a chosen target at a chosen time, only when there were failures.
- Help texts and examples for scheduling, ntfy extras and per-target quiet hours.

## 3.4.0
- Keep a sanitised error text for every failure (URLs, tokens, e-mail addresses and long IDs masked) in dead letters, archive and history instead of only the exception class.
- New **Statistics → Failure analysis**: dead, expired and retrying notifications grouped by cause and target, with German/English advice; also part of the diagnostics export (`failures`).
- Messages past their `ttl` are recorded as `expired` in history and statistics instead of disappearing silently.
- Each dead letter fires `reliable_notify_dead_letter` and a repair issue is shown while dead letters exist.
- Retry rules give up after a time span: new `max_hours` (info 6 h, warning 24 h, critical never); `max_attempts` defaults to 0 (unlimited). Untouched pre-3.4 defaults (8/20 attempts, about 1 h for info) are migrated automatically.
- Waiting for HA to load a transport action (e.g. at start-up) no longer uses up attempts.
- HA validation errors are permanent `invalid_payload` failures instead of being retried for hours as `unknown`.
- A missing or unavailable notify entity is a retryable failure instead of a false "sent".
- Extra call data is filtered per transport; a single-target call with unsupported keys fails immediately with the key list instead of becoming a dead letter later.
- Optional `fallback` per recipient: a finally failed message is sent once to another recipient, group or person.
- Telegram routes may use `data.entity_id` again (it was wrongly rejected as an override).
- Help texts explain the failure analysis, time limit and fallback.

## 3.3.2
- Recognise Reliable Notify's own notify entities (entity registry platform, so also after renaming, plus the `notify.reliable_` prefix) and never use them as targets: hidden in the panel's target picker and action list, refused when saving a target or a default target, and rejected when queueing. Sending to them would queue the message again (endless loop).
- The automation check ignores actions that already deliver through Reliable Notify, including `notify.send_message` to its entities (previously listed for manual review).
- Help for **Targets & people** explains buttons, images and extra data per transport, with copyable examples for Companion app actions and images, Telegram inline keyboards and photos, and automations reacting to button presses.
- Document transport capabilities in `docs/TRANSPORTS.md`.

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
