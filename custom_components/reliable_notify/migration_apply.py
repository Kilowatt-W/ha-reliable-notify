"""Opt-in, single-action YAML migration with checksum, backup, and atomic write.

Only standalone package files are writable. Home Assistant UI-managed
automations.yaml and scripts.yaml are always suggestion-only.
"""
from __future__ import annotations

import asyncio
import hashlib
import os
from pathlib import Path
import tempfile
import time

import yaml
from homeassistant.util.yaml import load_yaml

from .migration_advisor import analyze

MAX_BYTES=4*1024*1024


def _find_node(root,path):
    """Resolve the advisory's canonical dotted/list path in a YAML syntax tree."""
    import re
    parts=re.findall(r"\[[0-9]+\]|\.[A-Za-z0-9_-]+",path[4:])
    if path!="root" and not parts:
        raise ValueError("invalid action path")
    node=root
    for part in parts:
        if part.startswith("["):
            if not isinstance(node,yaml.SequenceNode):
                raise ValueError("expected YAML sequence")
            node=node.value[int(part[1:-1])]
        else:
            if not isinstance(node,yaml.MappingNode):
                raise ValueError("expected YAML object")
            key=part[1:]
            found=[v for k,v in node.value if getattr(k,"value",None)==key]
            if len(found)!=1:
                raise ValueError("ambiguous YAML mapping key")
            node=found[0]
    return node


def _patch(source,path,replacement):
    doc=yaml.compose(source)
    target=_find_node(doc,path)
    if not isinstance(target,yaml.MappingNode):
        raise ValueError("action path is not a mapping")
    start,end=target.start_mark.index,target.end_mark.index
    before=source[start:end]
    if "#" in before or "&" in before or "*" in before:
        raise ValueError("comments or YAML anchors in action require manual editing")
    # Only action mappings with the existing exact action fields are rewriteable.
    lines=before.splitlines()
    normalized="\n".join([lines[0]]+[
        line[indent:] if line.startswith(" "*indent) else line
        for line in lines[1:]
    ])
    old_obj=yaml.safe_load(normalized)
    if not isinstance(old_obj,dict) or not ("action" in old_obj or "service" in old_obj):
        raise ValueError("not a standalone notify action")
    indent=target.start_mark.column
    dumped=yaml.safe_dump(replacement,sort_keys=False,allow_unicode=True,width=1000)
    replacement_text="\n".join(
        (" "*indent+line if idx else line)
        for idx,line in enumerate(dumped.rstrip("\n").split("\n"))
    )
    candidate=source[:start]+replacement_text+source[end:]
    # Parse the result as YAML before any disk changes.
    yaml.compose(candidate)
    return candidate


def _apply_sync(config_dir,filename,file_hash,node_path,routes,confirmation):
    if confirmation!="APPLY_SINGLE_CHANGE":
        raise ValueError("explicit approval required")
    root=Path(config_dir).resolve()
    path=(root/filename).resolve()
    if path.is_symlink() or not path.is_file() or path.suffix not in (".yaml",".yml"):
        raise ValueError("file not eligible")
    # To avoid racing the HA automation editor, only package files may be edited.
    packages=root/"packages"
    if not path.is_relative_to(packages) or path.parent!=packages:
        raise ValueError("automatic changes limited to root packages/*.yaml")
    if path.stat().st_size>MAX_BYTES:
        raise ValueError("file too large")
    old_bytes=path.read_bytes()
    if hashlib.sha256(old_bytes).hexdigest()!=file_hash:
        raise ValueError("file changed since scan; rescan required")
    text=old_bytes.decode("utf8")
    report=analyze(load_yaml(path) or [],routes)
    matches=[x for x in report if x["status"]=="proposed" and x["path"]==node_path]
    if len(matches)!=1:
        raise ValueError("migration proposal is no longer unique")
    new=_patch(text,node_path,matches[0]["replacement"])
    if new==text:
        raise ValueError("no change")
    backup_dir=root/".storage"/"reliable_notify_migrations"
    backup_dir.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256(old_bytes).hexdigest()[:12]
    backup=backup_dir/(path.stem+"-"+digest+"-"+str(time.time_ns())+".yaml.bak")
    with backup.open("xb") as f:
        os.chmod(backup,0o600)
        f.write(old_bytes)
        f.flush();os.fsync(f.fileno())
    fd,temp=tempfile.mkstemp(prefix="."+path.name+".",dir=path.parent)
    try:
        with os.fdopen(fd,"wb") as f:
            os.fchmod(f.fileno(),path.stat().st_mode & 0o777)
            f.write(new.encode("utf8"))
            f.flush();os.fsync(f.fileno())
        # Revalidate checksum immediately before atomic replacement.
        if hashlib.sha256(path.read_bytes()).hexdigest()!=file_hash:
            raise ValueError("file changed during migration; no overwrite")
        os.replace(temp,path)
        return {"changed":True,"file":filename,"backup":str(backup),
                "new_sha256":hashlib.sha256(new.encode("utf8")).hexdigest(),
                "requires_reload":True}
    finally:
        if os.path.exists(temp):os.unlink(temp)


async def apply_single_package_change(config_dir,filename,file_hash,node_path,routes,confirmation):
    return await asyncio.to_thread(_apply_sync,config_dir,filename,file_hash,node_path,routes,confirmation)
