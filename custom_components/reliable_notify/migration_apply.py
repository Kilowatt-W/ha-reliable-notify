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

from .migration_advisor import analyze, load_automation_yaml, AutomationLoader

MAX_BYTES=4*1024*1024


class MigrationError(ValueError):
    """Refused or failed single change; ``code`` is translated in the panel."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _find_node(root,path):
    """Resolve the advisory's canonical dotted/list path in a YAML syntax tree."""
    import re
    parts=re.findall(r"\[[0-9]+\]|\.[A-Za-z0-9_-]+",path[4:])
    if path!="root" and not parts:
        raise MigrationError("invalid_path","invalid action path")
    node=root
    for part in parts:
        if part.startswith("["):
            if not isinstance(node,yaml.SequenceNode):
                raise MigrationError("invalid_path","expected YAML sequence")
            node=node.value[int(part[1:-1])]
        else:
            if not isinstance(node,yaml.MappingNode):
                raise MigrationError("invalid_path","expected YAML object")
            key=part[1:]
            found=[v for k,v in node.value if getattr(k,"value",None)==key]
            if len(found)!=1:
                raise MigrationError("invalid_path","ambiguous YAML mapping key")
            node=found[0]
    return node


def _patch(source,path,replacement):
    try:
        doc=yaml.compose(source,Loader=AutomationLoader)
    except yaml.YAMLError as err:
        raise MigrationError("yaml_syntax","YAML syntax error") from err
    target=_find_node(doc,path)
    if not isinstance(target,yaml.MappingNode):
        raise MigrationError("not_action","action path is not a mapping")
    start,end=target.start_mark.index,target.end_mark.index
    # A block mapping ends where the next token starts; keep the line break and
    # indentation before a following list item, otherwise the items would merge.
    raw=source[start:end]
    before=raw.rstrip()
    end=start+len(before)
    if "#" in before or "&" in before or "*" in before:
        raise MigrationError("manual_edit","comments or YAML anchors in action require manual editing")
    # Only action mappings with the existing exact action fields are rewriteable.
    indent=target.start_mark.column
    lines=before.splitlines()
    normalized="\n".join([lines[0]]+[
        line[indent:] if line.startswith(" "*indent) else line
        for line in lines[1:]
    ])
    try:
        old_obj=yaml.load(normalized,Loader=AutomationLoader)  # noqa: S506 - SafeLoader subclass
    except yaml.YAMLError as err:
        raise MigrationError("manual_edit","action cannot be rewritten automatically") from err
    if not isinstance(old_obj,dict) or not ("action" in old_obj or "service" in old_obj):
        raise MigrationError("not_action","not a standalone notify action")
    dumped=yaml.safe_dump(replacement,sort_keys=False,allow_unicode=True,width=1000)
    replacement_text="\n".join(
        (" "*indent+line if idx else line)
        for idx,line in enumerate(dumped.rstrip("\n").split("\n"))
    )
    candidate=source[:start]+replacement_text+source[end:]
    # Parse the result as YAML before any disk changes.
    try:
        yaml.compose(candidate,Loader=AutomationLoader)
    except yaml.YAMLError as err:
        raise MigrationError("manual_edit","result would not be valid YAML") from err
    return candidate


def _apply_sync(config_dir,filename,file_hash,node_path,routes,confirmation):
    if confirmation!="APPLY_SINGLE_CHANGE":
        raise MigrationError("approval_required","explicit approval required")
    root=Path(config_dir).resolve()
    path=(root/filename).resolve()
    if path.is_symlink() or not path.is_file() or path.suffix not in (".yaml",".yml"):
        raise MigrationError("not_eligible","file not eligible")
    # To avoid racing the HA automation editor, only package files may be edited.
    packages=root/"packages"
    if not path.is_relative_to(packages) or path.parent!=packages:
        raise MigrationError("packages_only","automatic changes limited to root packages/*.yaml")
    if path.stat().st_size>MAX_BYTES:
        raise MigrationError("too_large","file too large")
    old_bytes=path.read_bytes()
    if hashlib.sha256(old_bytes).hexdigest()!=file_hash:
        raise MigrationError("file_changed","file changed since scan; rescan required")
    text=old_bytes.decode("utf8")
    report=analyze(load_automation_yaml(path) or [],routes)
    matches=[x for x in report if x["status"]=="proposed" and x["path"]==node_path]
    if len(matches)!=1:
        raise MigrationError("not_unique","migration proposal is no longer unique")
    new=_patch(text,node_path,matches[0]["replacement"])
    if new==text:
        raise MigrationError("no_change","no change")
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
            mode=path.stat().st_mode & 0o777
            if hasattr(os,"fchmod"):
                os.fchmod(f.fileno(),mode)
            else:  # Windows (development only); HA itself runs on POSIX.
                os.chmod(temp,mode)
            f.write(new.encode("utf8"))
            f.flush();os.fsync(f.fileno())
        # Revalidate checksum immediately before atomic replacement.
        if hashlib.sha256(path.read_bytes()).hexdigest()!=file_hash:
            raise MigrationError("file_changed","file changed during migration; no overwrite")
        os.replace(temp,path)
        return {"changed":True,"file":filename,"backup":str(backup),
                "new_sha256":hashlib.sha256(new.encode("utf8")).hexdigest(),
                "requires_reload":True}
    finally:
        if os.path.exists(temp):os.unlink(temp)


async def apply_single_package_change(config_dir,filename,file_hash,node_path,routes,confirmation):
    return await asyncio.to_thread(_apply_sync,config_dir,filename,file_hash,node_path,routes,confirmation)
