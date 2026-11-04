"""Read-only filesystem inventory for automation migration proposals.

The scanner only reads HA's two well-known automation/script YAML paths.
It intentionally never writes or reloads automations and does not expand
arbitrary !include paths or edit UI-managed YAML files.
"""
from __future__ import annotations

import asyncio
import hashlib
import difflib
import json
from pathlib import Path

from homeassistant.util.yaml import load_yaml
import yaml

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
        for entry in proposals:
            if entry["status"]=="proposed":
                old={"action":entry["source"]}
                new=entry["replacement"]
                original=yaml.safe_dump(old,sort_keys=False,allow_unicode=True)
                updated=yaml.safe_dump(new,sort_keys=False,allow_unicode=True)
                entry["preview_diff"]="".join(difflib.unified_diff(
                    original.splitlines(True),updated.splitlines(True),
                    fromfile="before",tofile="suggested"))
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        return {"file":str(path),"sha256":digest,"proposals":proposals,
                "proposed":sum(x["status"]=="proposed" for x in proposals),
                "manual":sum(x["status"]=="manual" for x in proposals)}
    except Exception as err:
        # Avoid dumping YAML values/secret-bearing exception content into UI.
        return {"file":path.name,"error":type(err).__name__,"proposals":[]}


def _candidate_paths(root):
    """Only files within known HA automation/package locations, never symlinks."""
    names=("automations.yaml","scripts.yaml")
    candidates=[root/name for name in names]
    folders=("packages","automations","automation","scripts")
    for name in folders:
        folder=root/name
        if folder.is_symlink() or not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.yaml"))[:100]:
            candidates.append(path)
    return candidates[:200]


async def scan_automation_files(config_dir, routes):
    """Read-only package-aware analyzer, bounded to fixed user config locations."""
    root=Path(config_dir)
    reports=await asyncio.gather(*[
        asyncio.to_thread(_inspect_one,path,routes)
        for path in _candidate_paths(root)
    ])
    for result in reports:
        if result.get("sha256"):
            result["relative_file"]=str(Path(result["file"]).relative_to(root))
    return {
        "mode":"read_only",
        "writes_performed":0,
        "files":reports,
        "proposed":sum(x.get("proposed",0) for x in reports),
        "manual":sum(x.get("manual",0) for x in reports),
        "note":"Review each suggestion; apply through HA Automation Editor. No files changed.",
    }
