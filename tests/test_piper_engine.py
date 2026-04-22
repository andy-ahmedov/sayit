from __future__ import annotations

import wave
from pathlib import Path

import pytest

from pdf_tts_ru.models import PiperSynthesisSettings
from pdf_tts_ru.tts.piper_engine import PiperEngine


class FakeVoice:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object | None]] = []

    def synthesize_wav(self, text, wav_file, syn_config=None):
        self.calls.append((text, syn_config))
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(22050)
        wav_file.writeframes(b"\x00\x00" * 2205)


def test_piper_engine_loads_once_and_writes_wav(tmp_path: Path, monkeypatch) -> None:
    model_path = tmp_path / "voice.onnx"
    config_path = Path(f"{model_path}.json")
    model_path.write_bytes(b"model")
    config_path.write_text("{}", encoding="utf-8")
    fake_voice = FakeVoice()
    load_calls: list[tuple[Path, Path]] = []

    def fake_load(model_arg, config_path=None):
        load_calls.append((Path(model_arg), Path(config_path)))
        return fake_voice

    monkeypatch.setattr("pdf_tts_ru.tts.piper_engine.PiperVoice.load", fake_load)

    engine = PiperEngine(
        voice_model=model_path,
        tts_settings=PiperSynthesisSettings(length_scale=1.1, noise_scale=0.5),
    )

    engine.synthesize_to_wav("hello", tmp_path / "first.wav")
    engine.synthesize_to_wav("world", tmp_path / "second.wav")

    assert load_calls == [(model_path, config_path)]
    assert [text for text, _ in fake_voice.calls] == ["hello", "world"]
    with wave.open(str(tmp_path / "first.wav"), "rb") as wav_file:
        assert wav_file.getframerate() == 22050


def test_piper_engine_requires_existing_model(tmp_path: Path) -> None:
    engine = PiperEngine(voice_model=tmp_path / "missing.onnx")

    with pytest.raises(FileNotFoundError, match="voice model not found"):
        engine.synthesize_to_wav("hello", tmp_path / "out.wav")
