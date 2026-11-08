# Reliable Notify v3.3.2

## Deutsch
- **Eigene Entitäten werden erkannt:** Notify-Entitäten von Reliable Notify (`notify.reliable_…`, auch nach dem Umbenennen der Entitäts-ID) werden nicht mehr als Ziel angeboten und beim Speichern eines Ziels, beim Standardziel und beim Einreihen abgelehnt. Eine solche Einstellung hätte jede Nachricht erneut eingereiht (Endlosschleife).
- **Automationsprüfung:** Aktionen, die bereits über Reliable Notify senden – auch `notify.send_message` an eine Reliable-Entität –, werden jetzt ignoriert statt zur manuellen Prüfung angezeigt.
- **Neue Beispiele in der Hilfe:** Unter *Ziele & Personen* zeigt die Hilfe, wie Buttons und Bilder gesendet werden – für Companion-App (actions, image) und Telegram (inline_keyboard, Fotos von Kamera oder URL) – und wie eine Automation auf einen Tastendruck reagiert. Alle Beispiele lassen sich kopieren.

## English
- **Own entities are recognised:** Reliable Notify's notify entities (`notify.reliable_…`, also after renaming the entity ID) are no longer offered as targets and are refused when saving a target, as default target and when queueing. Such a setting would have queued every message again (endless loop).
- **Automation check:** Actions that already send through Reliable Notify – including `notify.send_message` to a Reliable entity – are now ignored instead of being listed for manual review.
- **New help examples:** Under *Targets & people* the help shows how to send buttons and images – for the Companion app (actions, image) and Telegram (inline_keyboard, photos from a camera or URL) – and how an automation reacts to a button press. All examples can be copied.

Update through Marketplace, restart Home Assistant and reload the browser. / Über Marketplace aktualisieren, Home Assistant neu starten und die Browseransicht neu laden.
