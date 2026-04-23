from __future__ import annotations

from pathlib import Path
from typing import Callable

from pdf_tts_ru.config import (
    SynthesisConfig,
    load_synthesis_config,
    resolve_synthesis_request,
    save_synthesis_config,
)
from pdf_tts_ru.document_extract import inspect_document
from pdf_tts_ru.gui.models import DesktopFormState, DesktopInspectionSummary
from pdf_tts_ru.gui.runtime import resolve_bundled_ffmpeg_path
from pdf_tts_ru.models import ProgressEvent, ProgressStage
from pdf_tts_ru.page_ranges import parse_page_spec
from pdf_tts_ru.pipeline import PdfTtsPipeline


PipelineFactory = Callable[[Callable[[ProgressEvent], None] | None], PdfTtsPipeline]


class DesktopAppService:
    """Bridge the GUI and the existing document-to-audio pipeline."""

    def __init__(
        self,
        *,
        pipeline_factory: PipelineFactory | None = None,
    ) -> None:
        self._pipeline_factory = pipeline_factory or self._build_pipeline

    def make_default_form(self, *, input_path: Path | None = None) -> DesktopFormState:
        """Create a default form state using runtime-aware defaults."""

        config = SynthesisConfig(ffmpeg_bin=resolve_bundled_ffmpeg_path())
        return self.form_from_config(config, input_path=input_path)

    def form_from_config(
        self,
        config: SynthesisConfig,
        *,
        input_path: Path | None = None,
        pages_spec: str = "all",
    ) -> DesktopFormState:
        """Convert a config dataclass into desktop form state."""

        return DesktopFormState(
            input_path=input_path,
            pages_spec=pages_spec,
            output_dir=config.output_dir,
            engine=config.engine,
            voice_model=config.voice_model,
            ffmpeg_bin=config.ffmpeg_bin,
            output_format=config.output_format,
            split_mode=config.split_mode,
            table_strategy=config.table_strategy,
            announce_page_numbers=config.announce_page_numbers,
            pause_between_pages_ms=config.pause_between_pages_ms,
            length_scale=config.length_scale,
            noise_scale=config.noise_scale,
            noise_w_scale=config.noise_w_scale,
            silero_model_id=config.silero_model_id,
            silero_speaker=config.silero_speaker,
            silero_sample_rate=config.silero_sample_rate,
            silero_rate=config.silero_rate,
            silero_device=config.silero_device,
            silero_line_break_mode=config.silero_line_break_mode,
            silero_transliterate_latin=config.silero_transliterate_latin,
            silero_verbalize_numbers=config.silero_verbalize_numbers,
            silero_spell_cyrillic_abbreviations=config.silero_spell_cyrillic_abbreviations,
            silero_expand_short_units=config.silero_expand_short_units,
        )

    def load_form_from_config(
        self,
        path: Path,
        *,
        input_path: Path | None = None,
        pages_spec: str = "all",
    ) -> DesktopFormState:
        """Load a TOML config file into desktop form state."""

        config = load_synthesis_config(path)
        return self.form_from_config(config, input_path=input_path, pages_spec=pages_spec)

    def save_form_to_config(self, form: DesktopFormState, path: Path) -> None:
        """Persist the current form state as a TOML config file."""

        save_synthesis_config(path, self.config_from_form(form))

    def config_from_form(self, form: DesktopFormState) -> SynthesisConfig:
        """Convert desktop form state into a config dataclass."""

        return SynthesisConfig(
            engine=form.engine,
            voice_model=form.voice_model,
            ffmpeg_bin=form.ffmpeg_bin,
            output_format=form.output_format,
            split_mode=form.split_mode,
            table_strategy=form.table_strategy,
            announce_page_numbers=form.announce_page_numbers,
            pause_between_pages_ms=form.pause_between_pages_ms,
            length_scale=form.length_scale,
            noise_scale=form.noise_scale,
            noise_w_scale=form.noise_w_scale,
            output_dir=form.output_dir,
            silero_model_id=form.silero_model_id,
            silero_speaker=form.silero_speaker,
            silero_sample_rate=form.silero_sample_rate,
            silero_rate=form.silero_rate,
            silero_device=form.silero_device,
            silero_line_break_mode=form.silero_line_break_mode,
            silero_transliterate_latin=form.silero_transliterate_latin,
            silero_verbalize_numbers=form.silero_verbalize_numbers,
            silero_spell_cyrillic_abbreviations=form.silero_spell_cyrillic_abbreviations,
            silero_expand_short_units=form.silero_expand_short_units,
        )

    def inspect_input(self, input_path: Path) -> DesktopInspectionSummary:
        """Inspect the selected document and return a GUI-friendly summary."""

        inspection = inspect_document(input_path)
        lines = [
            f"Файл: {input_path}",
            f"Страниц: {inspection.page_count}",
        ]
        for page in inspection.pages:
            lines.append(
                f"Страница {page.page_number}: символов={page.char_count}, таблиц={page.table_count}"
            )
        return DesktopInspectionSummary(
            input_path=input_path,
            page_count=inspection.page_count,
            lines=lines,
        )

    def build_request(self, form: DesktopFormState):
        """Resolve GUI form state into a synthesis request."""

        input_path = _require_input_path(form)
        inspection = inspect_document(input_path)
        pages = parse_page_spec(_normalize_page_spec(form.pages_spec), inspection.page_count)
        return resolve_synthesis_request(
            input_path=input_path,
            pages=pages,
            output_dir=form.output_dir,
            engine=form.engine,
            voice_model=form.voice_model,
            ffmpeg_bin=form.ffmpeg_bin,
            output_format=form.output_format,
            split_mode=form.split_mode,
            table_strategy=form.table_strategy,
            announce_page_numbers=form.announce_page_numbers,
            pause_between_pages_ms=form.pause_between_pages_ms,
            length_scale=form.length_scale,
            noise_scale=form.noise_scale,
            noise_w_scale=form.noise_w_scale,
            silero_model_id=form.silero_model_id,
            silero_speaker=form.silero_speaker,
            silero_sample_rate=form.silero_sample_rate,
            silero_rate=form.silero_rate,
            silero_device=form.silero_device,
            silero_line_break_mode=form.silero_line_break_mode,
            silero_transliterate_latin=form.silero_transliterate_latin,
            silero_verbalize_numbers=form.silero_verbalize_numbers,
            silero_spell_cyrillic_abbreviations=form.silero_spell_cyrillic_abbreviations,
            silero_expand_short_units=form.silero_expand_short_units,
        )

    def run_synthesis(
        self,
        form: DesktopFormState,
        *,
        progress_callback: Callable[[ProgressEvent], None] | None = None,
    ) -> list[Path]:
        """Run a synthesis request from GUI state."""

        input_path = _require_input_path(form)
        self._emit(
            progress_callback,
            ProgressStage.INSPECTING,
            f"Inspecting {input_path.name}",
        )
        inspection = inspect_document(input_path)
        page_spec = _normalize_page_spec(form.pages_spec)
        pages = parse_page_spec(page_spec, inspection.page_count)
        request = resolve_synthesis_request(
            input_path=input_path,
            pages=pages,
            output_dir=form.output_dir,
            engine=form.engine,
            voice_model=form.voice_model,
            ffmpeg_bin=form.ffmpeg_bin,
            output_format=form.output_format,
            split_mode=form.split_mode,
            table_strategy=form.table_strategy,
            announce_page_numbers=form.announce_page_numbers,
            pause_between_pages_ms=form.pause_between_pages_ms,
            length_scale=form.length_scale,
            noise_scale=form.noise_scale,
            noise_w_scale=form.noise_w_scale,
            silero_model_id=form.silero_model_id,
            silero_speaker=form.silero_speaker,
            silero_sample_rate=form.silero_sample_rate,
            silero_rate=form.silero_rate,
            silero_device=form.silero_device,
            silero_line_break_mode=form.silero_line_break_mode,
            silero_transliterate_latin=form.silero_transliterate_latin,
            silero_verbalize_numbers=form.silero_verbalize_numbers,
            silero_spell_cyrillic_abbreviations=form.silero_spell_cyrillic_abbreviations,
            silero_expand_short_units=form.silero_expand_short_units,
        )
        pipeline = self._pipeline_factory(progress_callback)
        return pipeline.run(request)

    def _build_pipeline(
        self,
        progress_callback: Callable[[ProgressEvent], None] | None = None,
    ) -> PdfTtsPipeline:
        return PdfTtsPipeline(progress_callback=progress_callback)

    def _emit(
        self,
        callback: Callable[[ProgressEvent], None] | None,
        stage: ProgressStage,
        message: str,
    ) -> None:
        if callback is None:
            return
        callback(ProgressEvent(stage=stage, message=message))


def _require_input_path(form: DesktopFormState) -> Path:
    if form.input_path is None:
        raise ValueError("input file is required")
    return form.input_path


def _normalize_page_spec(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        return "all"
    return normalized
