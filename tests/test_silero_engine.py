from __future__ import annotations

import types
import wave
from dataclasses import dataclass
from pathlib import Path

import pytest

from pdf_tts_ru.models import SileroLineBreakMode, SileroRate, SileroSynthesisSettings
from pdf_tts_ru.tts.silero_engine import SileroEngine
from pdf_tts_ru.tts.silero_text import (
    latin_word_to_russian,
    number_token_to_russian,
    prepare_text_for_silero,
    spell_cyrillic_abbreviation,
)


@dataclass
class FakeApplyCall:
    text: str | None
    ssml_text: str | None
    speaker: str
    sample_rate: int


class FakeModel:
    def __init__(self) -> None:
        self.to_calls: list[object] = []
        self.apply_calls: list[FakeApplyCall] = []

    def to(self, device: object) -> None:
        self.to_calls.append(device)

    def apply_tts(
        self,
        *,
        text: str | None = None,
        ssml_text: str | None = None,
        speaker: str,
        sample_rate: int,
    ):
        self.apply_calls.append(
            FakeApplyCall(
                text=text,
                ssml_text=ssml_text,
                speaker=speaker,
                sample_rate=sample_rate,
            )
        )
        return [0.0, 0.25, -0.25, 0.5]


def test_silero_engine_loads_once_and_writes_wav(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_model = FakeModel()
    load_calls: list[tuple[str, str]] = []

    def fake_import_module(name: str):
        if name == "torch":
            return types.SimpleNamespace(device=lambda value: f"device:{value}")
        if name == "silero":
            def silero_tts(*, language: str, speaker: str):
                load_calls.append((language, speaker))
                return fake_model, "example"

            return types.SimpleNamespace(silero_tts=silero_tts)
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("pdf_tts_ru.tts.silero_engine.importlib.import_module", fake_import_module)

    engine = SileroEngine(
        SileroSynthesisSettings(model_id="v5_5_ru", speaker="xenia", sample_rate=48000)
    )

    engine.synthesize_to_wav("hello", tmp_path / "first.wav")
    engine.synthesize_to_wav("world", tmp_path / "second.wav")

    assert load_calls == [("ru", "v5_5_ru")]
    assert fake_model.to_calls == ["device:cpu"]
    assert fake_model.apply_calls == [
        FakeApplyCall(text="хелло", ssml_text=None, speaker="xenia", sample_rate=48000),
        FakeApplyCall(text="ворлд", ssml_text=None, speaker="xenia", sample_rate=48000),
    ]
    with wave.open(str(tmp_path / "first.wav"), "rb") as wav_file:
        assert wav_file.getframerate() == 48000
        assert wav_file.getnchannels() == 1
        assert wav_file.getnframes() == 4


def test_silero_engine_preprocesses_latin_words_numbers_abbreviations_and_units(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_model = FakeModel()

    def fake_import_module(name: str):
        if name == "torch":
            return types.SimpleNamespace(device=lambda value: value)
        if name == "silero":
            return types.SimpleNamespace(silero_tts=lambda **_: (fake_model, "example"))
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("pdf_tts_ru.tts.silero_engine.importlib.import_module", fake_import_module)

    engine = SileroEngine()
    engine.synthesize_to_wav("VPG_5 PDF ВПГ 42 3.14 10% 5 нм", tmp_path / "prep.wav")

    prepared_text = fake_model.apply_calls[0].text
    assert prepared_text is not None
    assert "ви пи джи" in prepared_text
    assert "пи ди эф" in prepared_text
    assert "вэ пэ гэ" in prepared_text
    assert "сорок два" in prepared_text
    assert "три запятая один четыре" in prepared_text
    assert "десять процентов" in prepared_text
    assert "пять нанометров" in prepared_text
    assert fake_model.apply_calls[0].speaker == "xenia"
    assert fake_model.apply_calls[0].sample_rate == 48000


def test_silero_engine_can_disable_text_preprocessing_features(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_model = FakeModel()

    def fake_import_module(name: str):
        if name == "torch":
            return types.SimpleNamespace(device=lambda value: value)
        if name == "silero":
            return types.SimpleNamespace(silero_tts=lambda **_: (fake_model, "example"))
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("pdf_tts_ru.tts.silero_engine.importlib.import_module", fake_import_module)

    engine = SileroEngine(
        SileroSynthesisSettings(
            line_break_mode=SileroLineBreakMode.PRESERVE,
            transliterate_latin=False,
            verbalize_numbers=False,
            spell_cyrillic_abbreviations=False,
            expand_short_units=False,
        )
    )
    engine.synthesize_to_wav("ВПГ\nhello 42 нм", tmp_path / "raw.wav")

    assert fake_model.apply_calls[0].text == "ВПГ\nhello 42 нм"


def test_silero_engine_uses_ssml_when_rate_is_configured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_model = FakeModel()

    def fake_import_module(name: str):
        if name == "torch":
            return types.SimpleNamespace(device=lambda value: value)
        if name == "silero":
            return types.SimpleNamespace(silero_tts=lambda **_: (fake_model, "example"))
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("pdf_tts_ru.tts.silero_engine.importlib.import_module", fake_import_module)

    engine = SileroEngine(SileroSynthesisSettings(rate=SileroRate.SLOW))
    engine.synthesize_to_wav("A & B", tmp_path / "ssml.wav")

    call = fake_model.apply_calls[0]
    assert call.text is None
    assert call.ssml_text == '<speak><prosody rate="slow">эй &amp; би</prosody></speak>'


def test_silero_engine_requires_non_empty_text(tmp_path: Path) -> None:
    engine = SileroEngine()

    with pytest.raises(ValueError, match="empty text"):
        engine.synthesize_to_wav("   ", tmp_path / "out.wav")


def test_silero_engine_requires_torch_dependency(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_import_module(name: str):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("pdf_tts_ru.tts.silero_engine.importlib.import_module", fake_import_module)

    engine = SileroEngine()

    with pytest.raises(RuntimeError, match="requires the 'torch' package"):
        engine.synthesize_to_wav("hello", tmp_path / "out.wav")


def test_silero_engine_rejects_unsupported_sample_rate(tmp_path: Path) -> None:
    engine = SileroEngine(SileroSynthesisSettings(sample_rate=16000))

    with pytest.raises(ValueError, match="unsupported Silero sample rate"):
        engine.synthesize_to_wav("hello", tmp_path / "out.wav")


def test_silero_engine_surfaces_speaker_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_model = FakeModel()

    def fake_apply_tts(
        *,
        text: str | None = None,
        ssml_text: str | None = None,
        speaker: str,
        sample_rate: int,
    ):
        raise ValueError(f"unknown speaker: {speaker}")

    fake_model.apply_tts = fake_apply_tts  # type: ignore[method-assign]

    def fake_import_module(name: str):
        if name == "torch":
            return types.SimpleNamespace(device=lambda value: value)
        if name == "silero":
            return types.SimpleNamespace(silero_tts=lambda **_: (fake_model, "example"))
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("pdf_tts_ru.tts.silero_engine.importlib.import_module", fake_import_module)

    engine = SileroEngine(SileroSynthesisSettings(speaker="missing"))

    with pytest.raises(RuntimeError, match="failed to synthesize with Silero"):
        engine.synthesize_to_wav("hello", tmp_path / "out.wav")


def test_silero_engine_chunks_long_text(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_model = FakeModel()

    def fake_import_module(name: str):
        if name == "torch":
            return types.SimpleNamespace(device=lambda value: value)
        if name == "silero":
            return types.SimpleNamespace(silero_tts=lambda **_: (fake_model, "example"))
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("pdf_tts_ru.tts.silero_engine.importlib.import_module", fake_import_module)

    engine = SileroEngine()
    long_text = ("Первое предложение. " * 70).strip()

    engine.synthesize_to_wav(long_text, tmp_path / "long.wav")

    assert len(fake_model.apply_calls) >= 2
    with wave.open(str(tmp_path / "long.wav"), "rb") as wav_file:
        assert wav_file.getframerate() == 48000
        assert wav_file.getnframes() > 4 * len(fake_model.apply_calls)


def test_silero_sanitizes_unsupported_symbols() -> None:
    sanitized = prepare_text_for_silero("Тест (pH) < 7 / 10 ~ * ^ 2", SileroSynthesisSettings())

    assert "(" not in sanitized
    assert ")" not in sanitized
    assert "<" not in sanitized
    assert "/" not in sanitized
    assert "~" not in sanitized
    assert "^" not in sanitized
    assert "*" not in sanitized
    assert "меньше" in sanitized
    assert "примерно" in sanitized
    assert "в степени" in sanitized
    assert "семь" in sanitized
    assert "десять" in sanitized


def test_prepare_text_for_silero_smartly_flattens_technical_line_breaks() -> None:
    text = "Первая строка\nвторая строка\nТретья строка.\nчетвертая строка\n\nНовый абзац\n- пункт\n2) второй"

    prepared = prepare_text_for_silero(text, SileroSynthesisSettings())

    assert prepared == (
        "Первая строка вторая строка Третья строка.\n"
        "четвертая строка\n\nНовый абзац\n- пункт\nдва, второй"
    )


def test_prepare_text_for_silero_preserve_mode_keeps_line_breaks() -> None:
    text = "Первая строка\nвторая строка"

    prepared = prepare_text_for_silero(
        text,
        SileroSynthesisSettings(line_break_mode=SileroLineBreakMode.PRESERVE),
    )

    assert prepared == "Первая строка\nвторая строка"


def test_prepare_text_for_silero_flat_mode_flattens_even_after_punctuation() -> None:
    text = "Первая строка.\nвторая строка"

    prepared = prepare_text_for_silero(
        text,
        SileroSynthesisSettings(line_break_mode=SileroLineBreakMode.FLAT),
    )

    assert prepared == "Первая строка. вторая строка"


def test_prepare_text_for_silero_spells_cyrillic_abbreviations() -> None:
    prepared = prepare_text_for_silero("ВПГ ЦМВ ЦНС", SileroSynthesisSettings())

    assert "вэ пэ гэ" in prepared
    assert "цэ эм вэ" in prepared
    assert "цэ эн эс" in prepared


def test_prepare_text_for_silero_expands_short_units() -> None:
    prepared = prepare_text_for_silero("5 нм 12 мм 250 мг", SileroSynthesisSettings())

    assert "пять нанометров" in prepared
    assert "двенадцать миллиметров" in prepared
    assert "двести пятьдесят миллиграммов" in prepared


def test_prepare_text_for_silero_spells_standalone_short_units() -> None:
    prepared = prepare_text_for_silero("нм мм мг", SileroSynthesisSettings())

    assert prepared == "эн эм эм эм эм гэ"


def test_latin_word_to_russian_handles_words_and_acronyms() -> None:
    assert latin_word_to_russian("hello") == "хелло"
    assert latin_word_to_russian("PDF") == "пи ди эф"


def test_spell_cyrillic_abbreviation_handles_uppercase_tokens() -> None:
    assert spell_cyrillic_abbreviation("ВПГ") == "вэ пэ гэ"
    assert spell_cyrillic_abbreviation("ЦНС") == "цэ эн эс"


def test_number_token_to_russian_supports_integers_decimals_and_percentages() -> None:
    assert number_token_to_russian("42") == "сорок два"
    assert number_token_to_russian("3.14") == "три запятая один четыре"
    assert number_token_to_russian("10%") == "десять процентов"


def test_silero_engine_retries_when_model_reports_text_too_long(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_model = FakeModel()

    def fake_apply_tts(
        *,
        text: str | None = None,
        ssml_text: str | None = None,
        speaker: str,
        sample_rate: int,
    ):
        fake_model.apply_calls.append(
            FakeApplyCall(
                text=text,
                ssml_text=ssml_text,
                speaker=speaker,
                sample_rate=sample_rate,
            )
        )
        payload = ssml_text or text or ""
        if len(payload) > 120:
            raise Exception("Model couldn't generate your text, probably it's too long")
        return [0.0, 0.25, -0.25, 0.5]

    fake_model.apply_tts = fake_apply_tts  # type: ignore[method-assign]

    def fake_import_module(name: str):
        if name == "torch":
            return types.SimpleNamespace(device=lambda value: value)
        if name == "silero":
            return types.SimpleNamespace(silero_tts=lambda **_: (fake_model, "example"))
        raise ModuleNotFoundError(name)

    monkeypatch.setattr("pdf_tts_ru.tts.silero_engine.importlib.import_module", fake_import_module)

    engine = SileroEngine(SileroSynthesisSettings(rate=SileroRate.FAST))
    long_text = "\n".join(f"Строка {index}." for index in range(1, 30))

    engine.synthesize_to_wav(long_text, tmp_path / "retry.wav")

    assert len(fake_model.apply_calls) > 2
    assert all(call.ssml_text is not None for call in fake_model.apply_calls)
    with wave.open(str(tmp_path / "retry.wav"), "rb") as wav_file:
        assert wav_file.getframerate() == 48000
        assert wav_file.getnframes() > 4
