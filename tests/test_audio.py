from __future__ import annotations

import subprocess
import wave
from pathlib import Path

from pdf_tts_ru.audio import concat_audio, convert_audio, write_silence_wav


def test_convert_audio_builds_mp3_command(tmp_path: Path, monkeypatch) -> None:
    input_wav = write_test_wav(tmp_path / "input.wav")
    output_file = tmp_path / "out.mp3"
    captured: dict[str, list[str]] = {}

    def fake_run(command, check, capture_output, text):
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    convert_audio(input_wav, output_file, ffmpeg_bin="ffmpeg-custom")

    assert captured["command"] == [
        "ffmpeg-custom",
        "-y",
        "-i",
        str(input_wav.resolve()),
        "-c:a",
        "libmp3lame",
        str(output_file),
    ]


def test_convert_audio_builds_m4a_command(tmp_path: Path, monkeypatch) -> None:
    input_wav = write_test_wav(tmp_path / "input.wav")
    output_file = tmp_path / "out.m4a"
    captured: dict[str, list[str]] = {}

    def fake_run(command, check, capture_output, text):
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    convert_audio(input_wav, output_file)

    assert captured["command"][-3:] == ["-c:a", "aac", str(output_file)]


def test_concat_audio_builds_concat_demuxer_command(tmp_path: Path, monkeypatch) -> None:
    first = write_test_wav(tmp_path / "first.wav")
    second = write_test_wav(tmp_path / "second.wav")
    output_file = tmp_path / "merged.wav"
    captured: dict[str, str | list[str]] = {}

    def fake_run(command, check, capture_output, text):
        captured["command"] = command
        captured["list_file"] = Path(command[7]).read_text(encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)

    concat_audio([first, second], output_file, ffmpeg_bin="ffmpeg-custom")

    assert captured["command"][:8] == [
        "ffmpeg-custom",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        captured["command"][7],
    ]
    assert "first.wav" in captured["list_file"]
    assert "second.wav" in captured["list_file"]


def test_write_silence_wav_preserves_reference_format(tmp_path: Path) -> None:
    reference = write_test_wav(tmp_path / "reference.wav", duration_ms=100, sample_rate=16000)
    silence = tmp_path / "silence.wav"

    write_silence_wav(reference, silence, duration_ms=250)

    with wave.open(str(silence), "rb") as wav_file:
        assert wav_file.getframerate() == 16000
        assert wav_file.getnchannels() == 1
        assert wav_file.getnframes() == 4000


def write_test_wav(
    path: Path, *, duration_ms: int = 50, sample_rate: int = 22050, channels: int = 1
) -> Path:
    frame_count = round(sample_rate * (duration_ms / 1000))
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * channels * frame_count)
    return path
