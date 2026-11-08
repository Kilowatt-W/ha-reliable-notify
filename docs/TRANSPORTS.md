# Supported transports and security

## Existing HA services

- `telegram_bot.send_message` and `telegram_bot.send_photo` with explicit `chat_id`/entity target.
- `notify.send_message` with `target_entity: notify.your_entity`.
- `notify.mobile_app_<device>` for Companion apps, including signed acknowledgement buttons and deep links.
- `smtp.send_message` through existing HA services where configured.
- `rest_command.<name>` for a Home Assistant configured HTTP command. The credentials and destination are managed by HA; this is a safe generic escape hatch.

Reliable Notify's own notify entities (`notify.reliable_<name>`, also after renaming their entity ID) are never accepted as a target or default target: delivering to them would queue the message again. The panel hides them from target pickers, saving such a target is refused, and the automation check ignores actions that already use them.

## Buttons, images and extra data

Extra data in `reliable_notify.enqueue` (`data:`) is passed to the transport of every resolved target. The panel help under **Ziele & Personen / Targets & people** contains copyable examples.

| Transport | Buttons | Images |
| --- | --- | --- |
| Companion app (`notify.mobile_app_*`) | `data: {data: {actions: [...]}}`; react with the `mobile_app_notification_action` event | `data: {data: {image: /media/local/...}}` (loaded when displayed) |
| Telegram (`telegram_bot.send_message`) | `data: {inline_keyboard: ["Text:/command, ..."]}`; react with the `telegram_callback` event | `media: photo` with `data: {file: /media/...}` (copied when queued) or `data: {url: https://...}` |
| `notify.send_message`, ntfy, Gotify, webhook | – | – (title and text only) |

The entity `notify.reliable_<name>` transmits title and text only; use `reliable_notify.enqueue` for buttons and images. For groups with mixed transports send one call per transport, because the extra data applies to every target.

**Telegram and Companion are provider actions, not proof the phone displayed a push.** All transports use retry and dead-letter policies. Unsupported or invalid actions are rejected while enqueueing.

## Native ntfy HTTPS

```yaml
recipients:
  ntfy:
    action: reliable_notify.ntfy
    data:
      base_url: https://ntfy.example.org
      topic: important
      token: PRIVATE_BEARER_TOKEN
```

Reliable Notify sends a UTF-8 POST with `Title`, `Priority` and optional `Authorization: Bearer`. Topic allows letters, digits, dash and underscore.

## Native Gotify HTTPS

```yaml
recipients:
  gotify:
    action: reliable_notify.gotify
    data:
      base_url: https://gotify.example.org
      token: PRIVATE_APP_TOKEN
```

The integration calls `POST /message` with the Gotify application token in the `X-Gotify-Key` header and a JSON body containing title, message and priority.

## Native generic outbound webhook

```yaml
recipients:
  status_webhook:
    action: reliable_notify.webhook
    data:
      base_url: https://hooks.example.org/notify
      token: OPTIONAL_SHARED_TOKEN
```

It sends `POST` with JSON `title`, `message` and `priority` and optional `Authorization: Bearer`.

## Endpoint safety

- Native adapters require HTTPS; redirects are disabled.
- Hostnames with credentials and nonpublic literal IP addresses are rejected unless explicitly configured with `allow_private: true`.
- Credentials and endpoint URL are **not persisted in the delivery queue**; the SQLite payload stores an endpoint fingerprint.
- Delivery checks the fingerprint again to avoid silently sending old queued messages to a newly configured destination.
- Store credentials only in local HA configuration protected by backups, never in public GitHub files.
- HA's `rest_command` is also available for advanced integrations (Teams, Matrix gateways, Signal gateways, etc.).
- A configured hostname can resolve differently over time. These native adapters trust the administrator's URL; they are not a sandbox against DNS rebinding or a compromised endpoint.

## What is not native

Signal and Matrix do not have built-in native adapters here. Configure an HA notify integration or explicit `rest_command` gateway. A direct Matrix/Signal API is not claimed.
