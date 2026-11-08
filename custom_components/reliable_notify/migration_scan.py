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

import yaml

from .migration_advisor import analyze, load_automation_yaml

MAX_BYTES = 4 * 1024 * 1024


# Stable error codes (translated in the panel); English text kept for JSON exports.
ERRORS = {
    "symlink": "symlinks not scanned",
    "too_large": "file exceeds 4 MiB limit",
    "yaml_syntax": "YAML syntax error",
    "encoding": "file is not UTF-8 text",
    "not_automation_yaml": "file does not contain automations, scripts or packages",
    "read_failed": "file could not be read",
}


def _failure(path, code, **extra):
    return {"file": path.name, "error_code": code, "error": ERRORS[code], "proposals": [], **extra}


def _inspect_one(path, routes, own_entities=frozenset()):
    if path.is_symlink():
        return _failure(path, "symlink")
    if not path.is_file():
        # A missing default file (e.g. no scripts.yaml) is normal, not an error.
        return {"file": path.name, "skipped": "not_present", "proposals": []}
    if path.stat().st_size>MAX_BYTES:
        return _failure(path, "too_large")
    try:
        # Own safe loader: plain values, !secret/!include never resolved.
        parsed=load_automation_yaml(path)
    except yaml.YAMLError as err:
        mark=getattr(err, "problem_mark", None) or getattr(err, "context_mark", None)
        return _failure(path, "yaml_syntax", **({"line": mark.line+1} if mark else {}))
    except UnicodeDecodeError:
        return _failure(path, "encoding")
    except OSError:
        return _failure(path, "read_failed")
    if parsed is None:
        parsed=[]
    if not isinstance(parsed,(dict,list)):
        return _failure(path, "not_automation_yaml")
    try:
        proposals=analyze(parsed,routes,own_entities=own_entities)
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
    except Exception as err:
        # Avoid dumping YAML values/secret-bearing exception content into UI.
        return _failure(path, "read_failed", detail=type(err).__name__)
    return {"file":str(path),"sha256":digest,"proposals":proposals,
            "proposed":sum(x["status"]=="proposed" for x in proposals),
            "manual":sum(x["status"]=="manual" for x in proposals)}


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


async def scan_automation_files(config_dir, routes, own_entities=frozenset()):
    """Read-only package-aware analyzer, bounded to fixed user config locations."""
    root=Path(config_dir)
    reports=await asyncio.gather(*[
        asyncio.to_thread(_inspect_one,path,routes,frozenset(own_entities))
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
