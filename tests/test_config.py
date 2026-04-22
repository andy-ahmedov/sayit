from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from pdf_tts_ru.config import load_synthesis_config, resolve_synthesis_request
from pdf_tts_ru.models import (
    OutputFormat,
    SileroLineBreakMode,
    SplitMode,
    TableStrategy,
    TtsEngineKind,
)


def test_load_synthesis_config_parses_supported_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                'voice_model = "voices/ru.onnx"',
                'engine = "silero"',
                'ffmpeg_bin = "ffmpeg-custom"',
                'output_format = "m4a"',
                'split_mode = "merged"',
                'table_strategy = "separate"',
                'silero_line_break_mode = "flat"',
                "announce_page_numbers = true",
                "pause_between_pages_ms = 400",
                "length_scale = 1.1",
                "noise_scale = 0.6",
                "noise_w_scale = 0.9",
                'output_dir = "build/audio"',
                'silero_model_id = "v5_4_ru"',
                'silero_speaker = "kseniya"',
                "silero_sample_rate = 24000",
                'silero_device = "cpu"',
                "silero_transliterate_latin = false",
                "silero_verbalize_numbers = false",
                "silero_spell_cyrillic_abbreviations = false",
                "silero_expand_short_units = false",
            ]
        ),
        encoding="utf-8",
    )

    config = load_synthesis_config(config_path)

    assert config.engine == TtsEngineKind.SILERO
    assert config.voice_model == Path("voices/ru.onnx")
    assert config.ffmpeg_bin == "ffmpeg-custom"
    assert config.output_format == OutputFormat.M4A
    assert config.split_mode == SplitMode.MERGED
    assert config.table_strategy == TableStrategy.SEPARATE
    assert config.silero_line_break_mode == SileroLineBreakMode.FLAT
    assert config.announce_page_numbers is True
    assert config.pause_between_pages_ms == 400
    assert config.length_scale == pytest.approx(1.1)
    assert config.noise_scale == pytest.approx(0.6)
    assert config.noise_w_scale == pytest.approx(0.9)
    assert config.output_dir == Path("build/audio")
    assert config.silero_model_id == "v5_4_ru"
    assert config.silero_speaker == "kseniya"
    assert config.silero_sample_rate == 24000
    assert config.silero_device == "cpu"
    assert config.silero_transliterate_latin is False
    assert config.silero_verbalize_numbers is False
    assert config.silero_spell_cyrillic_abbreviations is False
    assert config.silero_expand_short_units is False


def test_load_synthesis_config_rejects_unknown_keys(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text('unexpected = "value"\n', encoding="utf-8")

    with pytest.raises(ValueError, match="unknown config keys"):
        load_synthesis_config(config_path)


def test_load_synthesis_config_defaults_to_silero_when_engine_is_omitted(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text('output_dir = "audio"\n', encoding="utf-8")

    config = load_synthesis_config(config_path)

    assert config.engine == TtsEngineKind.SILERO
    assert config.output_dir == Path("audio")


def test_resolve_synthesis_request_prefers_cli_values() -> None:
    request = resolve_synthesis_request(
        input_path=Path("book.pdf"),
        pages=[1, 2],
        engine=TtsEngineKind.PIPER,
        voice_model=Path("cli.onnx"),
        split_mode=SplitMode.MERGED,
        output_format=OutputFormat.WAV,
        table_strategy=TableStrategy.SKIP,
        announce_page_numbers=False,
        pause_between_pages_ms=0,
        ffmpeg_bin="ffmpeg-cli",
        length_scale=1.2,
        noise_scale=0.3,
        noise_w_scale=0.4,
        config=load_synthesis_config_from_text(
            "\n".join(
                [
                    'engine = "silero"',
                    'voice_model = "config.onnx"',
                    'split_mode = "per-page"',
                    'output_format = "mp3"',
                    'table_strategy = "inline"',
                    'silero_line_break_mode = "flat"',
                    "announce_page_numbers = true",
                    "pause_between_pages_ms = 500",
                    'ffmpeg_bin = "ffmpeg-config"',
                    "length_scale = 0.8",
                    "noise_scale = 0.6",
                    "noise_w_scale = 0.9",
                    'silero_model_id = "v5_4_ru"',
                    'silero_speaker = "baya"',
                    "silero_sample_rate = 24000",
                    'silero_device = "cuda"',
                    "silero_transliterate_latin = false",
                    "silero_verbalize_numbers = false",
                    "silero_spell_cyrillic_abbreviations = false",
                    "silero_expand_short_units = false",
                ]
            )
        ),
    )

    assert request.engine == TtsEngineKind.PIPER
    assert request.voice_model == Path("cli.onnx")
    assert request.split_mode == SplitMode.MERGED
    assert request.output_format == OutputFormat.WAV
    assert request.table_strategy == TableStrategy.SKIP
    assert request.announce_page_numbers is False
    assert request.pause_between_pages_ms == 0
    assert request.ffmpeg_bin == "ffmpeg-cli"
    assert request.tts_settings.length_scale == pytest.approx(1.2)
    assert request.tts_settings.noise_scale == pytest.approx(0.3)
    assert request.tts_settings.noise_w_scale == pytest.approx(0.4)
    assert request.silero_settings.model_id == "v5_4_ru"
    assert request.silero_settings.speaker == "baya"
    assert request.silero_settings.sample_rate == 24000
    assert request.silero_settings.device == "cuda"
    assert request.silero_settings.line_break_mode == SileroLineBreakMode.FLAT
    assert request.silero_settings.transliterate_latin is False
    assert request.silero_settings.verbalize_numbers is False
    assert request.silero_settings.spell_cyrillic_abbreviations is False
    assert request.silero_settings.expand_short_units is False


def test_resolve_synthesis_request_defaults_to_silero() -> None:
    request = resolve_synthesis_request(input_path=Path("book.pdf"), pages=[1])

    assert request.engine == TtsEngineKind.SILERO
    assert request.voice_model is None


def test_resolve_synthesis_request_requires_voice_model_for_explicit_piper() -> None:
    with pytest.raises(ValueError, match="voice model is required for Piper"):
        resolve_synthesis_request(
            input_path=Path("book.pdf"),
            pages=[1],
            engine=TtsEngineKind.PIPER,
        )


def test_resolve_synthesis_request_supports_silero_without_voice_model() -> None:
    request = resolve_synthesis_request(
        input_path=Path("book.pdf"),
        pages=[1],
        engine=TtsEngineKind.SILERO,
        silero_model_id="v5_4_ru",
        silero_speaker="kseniya",
        silero_sample_rate=24000,
        silero_device="cpu",
        silero_line_break_mode=SileroLineBreakMode.PRESERVE,
        silero_transliterate_latin=False,
        silero_verbalize_numbers=False,
        silero_spell_cyrillic_abbreviations=False,
        silero_expand_short_units=False,
    )

    assert request.engine == TtsEngineKind.SILERO
    assert request.voice_model is None
    assert request.silero_settings.model_id == "v5_4_ru"
    assert request.silero_settings.speaker == "kseniya"
    assert request.silero_settings.sample_rate == 24000
    assert request.silero_settings.device == "cpu"
    assert request.silero_settings.line_break_mode == SileroLineBreakMode.PRESERVE
    assert request.silero_settings.transliterate_latin is False
    assert request.silero_settings.verbalize_numbers is False
    assert request.silero_settings.spell_cyrillic_abbreviations is False
    assert request.silero_settings.expand_short_units is False


def load_synthesis_config_from_text(text: str):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as handle:
        path = Path(handle.name)
        handle.write(text)

    try:
        return load_synthesis_config(path)
    finally:
        path.unlink(missing_ok=True)
