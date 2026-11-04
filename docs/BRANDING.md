# Reliable Notify – Home Assistant and HACS branding

## Source files

The integration ships proper Home Assistant brand images inside the integration itself:

```text
custom_components/reliable_notify/brand/
  icon.svg
  icon.png               # 256x256
  icon@2x.png            # 512x512
  dark_icon.png
  dark_icon@2x.png
  logo.svg
  logo.png               # 512x160
  logo@2x.png            # 1024x320
  dark_logo.png
  dark_logo@2x.png
```

The visual motif is a navy shield (reliability/security), a bell (notifications), layered turquoise signal arcs (transport redundancy) and a lime check (confirmed handling). The background outside the shield is fully transparent.

## Build

Run `python tools/generate_brand.py` after installing CairoSVG. The repository CI automatically generates and checks the PNGs when the source SVGs change on the development branch. Keep the generated PNGs committed so HACS/Marketplace can install them.

## Why HA or HACS can still say "Icon not available"

Starting with Home Assistant Core 2026.3, local `brand/` assets in custom integrations are officially supported. This icon is resolved from the installed integration itself. Restart HA Core and refresh the browser (Ctrl+Shift+R).

**Legacy standalone HACS** versions have been known to look up icons on the *old public brand CDN* even when local `brand/icon.png` exists, making them show a placeholder. This cannot be solved from a custom integration repository alone. Home Assistant's built-in **Marketplace introduced in 2026.11** resolves these local brand assets.

Verify the files exist in your installed `/config/custom_components/reliable_notify/brand/`, then see Settings → Devices & Services → Reliable Notify. If the icon works there but not in old HACS, upgrade Home Assistant and use the current Marketplace where available.

Avoid copying logos into the discontinued `home-assistant/brands/custom_integrations` workflow. That repository no longer accepts new custom-integration logos as of the 2026.3 migration.

Developer documentation: https://contributors.home-assistant.io/core/integrations/brands/
