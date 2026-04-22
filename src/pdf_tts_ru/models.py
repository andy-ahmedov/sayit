from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class TtsEngineKind(StrEnum):
    PIPER = "piper"
    SILERO = "silero"


class SplitMode(StrEnum):
    PER_PAGE = "per-page"
    PER_RANGE = "per-range"
    MERGED = "merged"


class OutputFormat(StrEnum):
    WAV = "wav"
    MP3 = "mp3"
    M4A = "m4a"


class TableStrategy(StrEnum):
    SKIP = "skip"
    INLINE = "inline"
    SEPARATE = "separate"


class SileroLineBreakMode(StrEnum):
    PRESERVE = "preserve"
    SMART = "smart"
    FLAT = "flat"


@dataclass(slots=True)
class PiperSynthesisSettings:
    """Piper-specific synthesis tuning."""

    length_scale: float | None = None
    noise_scale: float | None = None
    noise_w_scale: float | None = None


@dataclass(slots=True)
class SileroSynthesisSettings:
    """Silero-specific synthesis settings."""

    model_id: str = "v5_5_ru"
    speaker: str = "xenia"
    sample_rate: int = 48000
    device: str = "cpu"
    line_break_mode: SileroLineBreakMode = SileroLineBreakMode.SMART
    transliterate_latin: bool = True
    verbalize_numbers: bool = True
    spell_cyrillic_abbreviations: bool = True
    expand_short_units: bool = True


@dataclass(slots=True)
class SynthesisRequest:
    """Fully resolved synthesis request ready for pipeline execution."""

    input_path: Path
    output_dir: Path
    pages: list[int]
    split_mode: SplitMode
    output_format: OutputFormat
    engine: TtsEngineKind = TtsEngineKind.PIPER
    voice_model: Path | None = None
    ffmpeg_bin: str = "ffmpeg"
    table_strategy: TableStrategy = TableStrategy.INLINE
    announce_page_numbers: bool = False
    pause_between_pages_ms: int = 0
    tts_settings: PiperSynthesisSettings = field(default_factory=PiperSynthesisSettings)
    silero_settings: SileroSynthesisSettings = field(default_factory=SileroSynthesisSettings)
