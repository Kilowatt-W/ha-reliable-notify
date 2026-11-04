"""Local snapshot spool for Telegram photos; bounded file-size, atomically copied."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import tempfile
import uuid

MAX_BYTES = 20 * 1024 * 1024
MEDIA_ROOT = Path('/media')


def snapshot_file(source: str, directory: str, quota_bytes: int = 200 * 1024 * 1024, allowed_suffixes=('.jpg', '.jpeg', '.png', '.webp')) -> str:
    file = Path(source).resolve(strict=True)
    if not file.is_file() or file.stat().st_size > MAX_BYTES:
        raise ValueError('Telegram photo must be a local file smaller than 20 MiB')
    dest = Path(directory)
    dest.mkdir(parents=True, exist_ok=True)
    current = sum(p.stat().st_size for p in dest.iterdir() if p.is_file())
    if current + file.stat().st_size > quota_bytes:
        raise OverflowError("Reliable Notify media quota exceeded (200 MiB)")
    suffix = file.suffix.lower()
    if allowed_suffixes is not None and suffix not in allowed_suffixes:
        raise ValueError('Unsupported image format; use jpg, png or webp')
    # Avoid full memory buffering and avoid writing partial photos to final destination.
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=dest, prefix='.rn-', delete=False) as tmp:
            tmp_path = Path(tmp.name)
            with file.open('rb') as inp:
                shutil.copyfileobj(inp, tmp)
        final = dest / f'{uuid.uuid4().hex}{suffix}'
        os.replace(tmp_path, final)
        return str(final)
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


def cleanup_media(directory: str, referenced: set[str]):
    folder = Path(directory)
    if not folder.is_dir():
        return
    for file in folder.iterdir():
        if file.is_file() and (file.name.startswith('.rn-') or
            (not file.name.startswith('.') and str(file) not in referenced)):
            file.unlink(missing_ok=True)


def free_disk_bytes(directory: str) -> int:
    """Return free disk bytes on the storage filesystem."""
    folder = Path(directory)
    folder.mkdir(parents=True, exist_ok=True)
    return shutil.disk_usage(folder).free


def snapshot_attachments(payload: dict, spool: str, *, quota_bytes: int = 200 * 1024 * 1024,
                         min_free_bytes: int = 100 * 1024 * 1024) -> tuple[dict, list[str]]:
    """Snapshot local SMTP attachments to immutable HA media-source references.

    A local file may be given as {path: /media/...} or as the local
    media-source URL (media-source://media_source/local/...). Other providers'
    or remote references are passed through unchanged; they are NOT durable.
    """
    source_attachments = payload.get('attachments')
    if source_attachments is None:
        return payload, []
    if not isinstance(source_attachments, list):
        raise ValueError('attachments must be a list')
    snapshots = []
    result = dict(payload)
    converted = []
    try:
        for record in source_attachments:
            if not isinstance(record, dict):
                raise ValueError('attachment must be an object')
            item = dict(record)
            media = item.get('media_source')
            source = item.pop('path', None)
            if source is None and isinstance(media, dict):
                uri = media.get('media_content_id', '')
                prefix = 'media-source://media_source/local/'
                if uri.startswith(prefix):
                    rel = uri[len(prefix):]
                    base = MEDIA_ROOT.resolve()
                    candidate = (base / rel).resolve(strict=True)
                    if not candidate.is_relative_to(base):
                        raise ValueError('attachment path outside /media')
                    source = str(candidate)
            if source is not None:
                source_path = Path(source).resolve(strict=True)
                base = MEDIA_ROOT.resolve()
                if not source_path.is_relative_to(base):
                    raise ValueError('local attachment must be under /media')
                if not source_path.is_file() or source_path.stat().st_size > MAX_BYTES:
                    raise ValueError('attachment must be a file <=20MiB')
                if free_disk_bytes(spool) - source_path.stat().st_size < min_free_bytes:
                    raise OSError('insufficient free disk space for attachment spool')
                copy = snapshot_file(str(source_path), spool, quota_bytes=quota_bytes,
                                     allowed_suffixes=None)
                snapshots.append(copy)
                item['media_source'] = {
                    'media_content_id': 'media-source://media_source/local/reliable_notify/' + Path(copy).name,
                    'media_content_type': 'application/octet-stream',
                }
                item.setdefault('filename', source_path.name)
            converted.append(item)
        result['attachments'] = converted
        return result, snapshots
    except Exception:
        for name in snapshots:
            Path(name).unlink(missing_ok=True)
        raise