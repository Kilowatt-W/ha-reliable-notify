# Reliable Notify v3.1.0

The settings-area dropdown is replaced by a single form with eight expanded sections: General, Quiet hours/limits/digest, retries for each of the three priorities, Archive retention, Test mode/backups and Transport logging. Values use ordinary fields instead of JSON text.

The admin panel now provides typed fields for recipients, groups, persons and their zone rules, notification profiles, templates, transport logging and simulation. All three routing categories are visible together. Existing entries load their complete definition before editing, retaining transport parameters and custom nested settings. Optional fields and list entries can be added or removed individually. Numbers and switches retain their types; secret fields are masked.

Each editor offers an optional, read-only YAML preview. In the HA options dialog choose “Show YAML before saving” to inspect the pending values before confirming. In the panel expand the YAML disclosure to see current form values. The previews may include configured credentials; handle them accordingly.

Existing configurations are retained. Route editing remains admin-only; route inventories and diagnostics remain redacted. File-backed routing entries are overridden through HA options rather than rewriting YAML files. To edit recipients, groups or persons use the Reliable Notify sidebar panel.

Validation: Python unit tests, functional DOM tests covering editing/saving/validation/YAML round trips, JavaScript syntax checks, hassfest, HACS validation and Home Assistant Core imports. No database schema changes.

Update through HACS/Marketplace, restart HA Core and refresh the browser to load the new interface.
