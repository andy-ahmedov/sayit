from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pdf_tts_ru.models import (
    OutputFormat,
    SileroLineBreakMode,
    SileroRate,
    SplitMode,
    TableStrategy,
    TtsEngineKind,
)


@dataclass(slots=True)
class DesktopFormState:
    """Structured GUI state for a synthesis run."""

    input_path: Path | None = None
    pages_spec: str = "all"
    output_dir: Path = Path("output")
    engine: TtsEngineKind = TtsEngineKind.SILERO
    voice_model: Path | None = None
    ffmpeg_bin: str = "ffmpeg"
    output_format: OutputFormat = OutputFormat.MP3
    split_mode: SplitMode = SplitMode.PER_PAGE
    table_strategy: TableStrategy = TableStrategy.INLINE
    announce_page_numbers: bool = False
    pause_between_pages_ms: int = 0
    length_scale: float | None = None
    noise_scale: float | None = None
    noise_w_scale: float | None = None
    silero_model_id: str = "v5_5_ru"
    silero_speaker: str = "xenia"
    silero_sample_rate: int = 48000
    silero_rate: SileroRate | None = None
    silero_device: str = "cpu"
    silero_line_break_mode: SileroLineBreakMode = SileroLineBreakMode.SMART
    silero_transliterate_latin: bool = True
    silero_verbalize_numbers: bool = True
    silero_spell_cyrillic_abbreviations: bool = True
    silero_expand_short_units: bool = True


@dataclass(slots=True)
class DesktopInspectionSummary:
    """A GUI-friendly document inspection summary."""

    input_path: Path
    page_count: int
    lines: list[str]

    def render_text(self) -> str:
        """Render the summary as multiline plain text."""

        return "\n".join(self.lines)
