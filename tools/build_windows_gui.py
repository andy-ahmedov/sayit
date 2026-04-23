#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the sayit Windows desktop bundle")
    parser.add_argument(
        "--name",
        default="sayit-desktop",
        help="Name of the generated Windows application bundle",
    )
    parser.add_argument(
        "--ffmpeg-bin",
        type=Path,
        help="Optional path to ffmpeg.exe to bundle into the app root",
    )
    parser.add_argument(
        "--icon",
        type=Path,
        help="Optional .ico path for the Windows executable",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        from PyInstaller.__main__ import run as pyinstaller_run
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "PyInstaller is required to build the desktop bundle. "
            "Install it with 'python -m pip install -e .[desktop]'."
        ) from exc

    command = [
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onedir",
        "--name",
        args.name,
        "--paths",
        "src",
        "src/pdf_tts_ru/gui/main.py",
    ]

    if args.ffmpeg_bin is not None:
        command.extend(["--add-binary", f"{args.ffmpeg_bin}{os.pathsep}."])

    if args.icon is not None:
        command.extend(["--icon", str(args.icon)])

    pyinstaller_run(command)


if __name__ == "__main__":
    main()
