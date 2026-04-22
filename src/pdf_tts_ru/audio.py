from __future__ import annotations

import shutil
import subprocess
import tempfile
import wave
from pathlib import Path


def convert_audio(input_wav: Path, output_file: Path, ffmpeg_bin: str = "ffmpeg") -> None:
    """Convert a WAV file to another audio format."""

    input_wav = input_wav.resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if output_file.suffix.lower() == ".wav":
        if input_wav == output_file.resolve():
            return
        shutil.copyfile(input_wav, output_file)
        return

    command = [ffmpeg_bin, "-y", "-i", str(input_wav)]
    suffix = output_file.suffix.lower()
    if suffix == ".mp3":
        command.extend(["-c:a", "libmp3lame"])
    elif suffix == ".m4a":
        command.extend(["-c:a", "aac"])
    else:
        raise ValueError(f"unsupported audio format: {output_file.suffix}")

    command.append(str(output_file))
    _run_ffmpeg(command)


def concat_audio(inputs: list[Path], output_file: Path, ffmpeg_bin: str = "ffmpeg") -> None:
    """Concatenate multiple audio files into one."""

    if not inputs:
        raise ValueError("concat_audio requires at least one input file")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    if len(inputs) == 1:
        shutil.copyfile(inputs[0], output_file)
        return

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".txt", delete=False
    ) as list_file:
        list_path = Path(list_file.name)
        for input_path in inputs:
            escaped = str(input_path.resolve()).replace("'", "'\\''")
            list_file.write(f"file '{escaped}'\n")

    try:
        command = [
            ffmpeg_bin,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-c",
            "copy",
            str(output_file),
        ]
        _run_ffmpeg(command)
    finally:
        list_path.unlink(missing_ok=True)


def write_silence_wav(reference_wav: Path, output_wav: Path, duration_ms: int) -> None:
    """Write a silent WAV using the format of an existing WAV file."""

    if duration_ms < 0:
        raise ValueError("duration_ms must be zero or positive")

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(reference_wav), "rb") as source:
        params = source.getparams()
        frame_count = round(params.framerate * (duration_ms / 1000))

    silence_frame = b"\x00" * params.sampwidth * params.nchannels
    with wave.open(str(output_wav), "wb") as target:
        target.setparams(params)
        target.writeframes(silence_frame * frame_count)


def _run_ffmpeg(command: list[str]) -> None:
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"ffmpeg executable not found: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        raise RuntimeError(f"ffmpeg failed: {stderr or exc}") from exc
