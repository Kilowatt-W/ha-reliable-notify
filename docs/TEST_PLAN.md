# Validation and acceptance test plan for HA OS

GitHub Actions perform Python syntax, unit tests, frontend JS syntax, hassfest and HACS validation. They **cannot** confirm your Telegram account, SMTP server, Android/iOS devices or HA OS mounts; run these tests before relying on v2 for real alarms.

| Test | Steps | Expected |
|---|---|---|
| DB migration | Back up v1.1, upgrade to v2 beta, restart HA Core | Queue, media, archive and dead letters preserved |
| Staging | Send without recipient or with test mode stage | Visible in staging, no provider sends |
| Simulator | Preview same message from panel and HA action | No queue changes, no transport calls |
| Telegram callback | Send critical Telegram alert, click Confirm | Acknowledgement timestamp set, later escalation blocked |
| Companion callback | Send to phone, click Confirm/Snooze/Escalate | Correct action processed once; no repeated escalation |
| Crash boundary | Interrupt HA Core during first escalation then restart | A stage is inserted no more than once in SQLite |
| Quiet hours | Info at 23:00; critical at 23:01 | Info scheduled to morning, critical sent immediately |
| Rate limit | Burst >10 info messages/60 seconds | Attempts delayed per endpoint, no cross-recipient blockage |
| Digest | Send 5 identical-key messages in 5 minutes | Exactly one summarized pending message |
| Database backup | Trigger admin backup while WAL active | Snapshot opens, PRAGMA quick_check returns ok |
| SMTP attachment | Queue local PDF, remove source, reconnect network | Snapshotted content still sent |
| Storage guard | Simulate low-space path on a test HA VM | New jobs refused; old pending preserved |
| Native ntfy | Valid HTTPS route and token; provider outage | Delivery or retry + classified failure |
| Native Gotify | Valid HTTPS token; provider outage | Delivery or retry + classified failure |
| Webhook | Configured route and HTTPS receiver | Receives JSON; non-2xx fails with retry |
| HA reload | Reload integration with panel open | No duplicate service/WS paths; active session recovers |
| Deep links | Tap Companion push, open message ID in panel | Full archived text shown to admin |
| Role separation | Sign in as non-admin | Routing editor, archive details and panel denied |
| Long-term | Run daily for 7 days with bursts and queued media | No unbounded growth beyond intentional protected records |

**Status:** These are acceptance tests for the operator to execute. Passing GitHub CI does not mean these were completed on real devices. Record actual results in a release checklist or GitHub issue before a production critical-alarm deployment.
