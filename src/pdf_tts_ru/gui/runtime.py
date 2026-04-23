from __future__ import annotations

import sys
from pathlib import Path


def detect_bundle_root() -> Path:
    """Return the runtime directory that may contain bundled assets."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def resolve_bundled_ffmpeg_path(*, bundle_root: Path | None = None) -> str:
    """Return a bundled ffmpeg path when present, otherwise fall back to 'ffmpeg'."""

    root = bundle_root or detect_bundle_root()
    candidates = [root / "ffmpeg.exe", root / "ffmpeg"]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return "ffmpeg"
