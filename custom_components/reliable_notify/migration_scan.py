"""Read-only filesystem inventory for automation migration proposals.

The scanner only reads HA's two well-known automation/script YAML paths.
It intentionally never writes or reloads automations and does not expand
arbitrary !include paths or edit UI-managed YAML files.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from homeassistant.util.yaml import load_yaml

from .migration_advisor import analyze

MAX_BYTES = 4 * 1024 * 1024


def _inspect_one(path, routes):
    if path.is_symlink():
        return {"file":path.name,"error":"symlinks not scanned","proposals":[]}
    if not path.is_file():
        return {"file":path.name,"error":"file not present","proposals":[]}
    if path.stat().st_size>MAX_BYTES:
        return {"file":path.name,"error":"file exceeds 4 MiB limit","proposals":[]}
    try:
        parsed=load_yaml(path)
        proposals=analyze(parsed or [],routes)
        return {"file":path.name,"proposals":proposals,
                "proposed":sum(x["status"]=="proposed" for x in proposals),
                "manual":sum(x["status"]=="manual" for x in proposals)}
    except Exception as err:
        # Avoid dumping YAML values/secret-bearing exception content into UI.
        return {"file":path.name,"error":type(err).__name__,"proposals":[]}


async def scan_automation_files(config_dir, routes):
    """Never edits, reloads, disables or saves user automations."""
    root=Path(config_dir)
    reports=await asyncio.gather(*[
        asyncio.to_thread(_inspect_one,root/name,routes)
        for name in ("automations.yaml","scripts.yaml")
    ])
    return {
        "mode":"read_only",
        "writes_performed":0,
        "files":reports,
        "proposed":sum(x.get("proposed",0) for x in reports),
        "manual":sum(x.get("manual",0) for x in reports),
        "note":"Review each suggestion in Automation Editor. Nothing was modified.",
    }
