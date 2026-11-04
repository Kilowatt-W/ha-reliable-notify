"""Local snapshot spool for Telegram photos; bounded file-size, atomically copied."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import tempfile
import uuid

MAX_BYTES = 20 * 1024 * 1024


def snapshot_file(source: str, directory: str, quota_bytes: int = 200 * 1024 * 1024) -> str:
    file = Path(source).resolve(strict=True)
    if not file.is_file() or file.stat().st_size > MAX_BYTES:
        raise ValueError('Telegram photo must be a local file smaller than 20 MiB')
    dest = Path(directory)
    dest.mkdir(parents=True, exist_ok=True)
    current = sum(p.stat().st_size for p in dest.iterdir() if p.is_file())
    if current + file.stat().st_size > quota_bytes:
        raise OverflowError("Reliable Notify media quota exceeded (200 MiB)")
    suffix = file.suffix.lower()
    if suffix not in ('.jpg', '.jpeg', '.png', '.webp'):
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
            (file.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp') and str(file) not in referenced)):
            file.unlink(missing_ok=True)