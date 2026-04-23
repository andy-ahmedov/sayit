from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Callable

from pdf_tts_ru.audio import concat_audio, convert_audio, write_silence_wav
from pdf_tts_ru.document_extract import extract_document_pages
from pdf_tts_ru.models import ProgressEvent, ProgressStage, SynthesisRequest
from pdf_tts_ru.normalize import normalize_text_for_speech
from pdf_tts_ru.output_plan import build_prose_output_path, build_table_output_path
from pdf_tts_ru.pdf_extract import SegmentKind
from pdf_tts_ru.tts.base import TtsEngine
from pdf_tts_ru.tts.factory import create_tts_engine


class PdfTtsPipeline:
    """Orchestrates extraction, normalization, TTS, and audio export."""

    def __init__(
        self,
        engine: TtsEngine | None = None,
        progress_callback: Callable[[ProgressEvent], None] | None = None,
    ) -> None:
        self._engine = engine
        self._progress_callback = progress_callback

    def run(self, request: SynthesisRequest) -> list[Path]:
        """Run the synthesis pipeline."""

        request.output_dir.mkdir(parents=True, exist_ok=True)
        self._emit(
            ProgressStage.EXTRACTING,
            f"Extracting text from {request.input_path.name}",
        )
        extracted_pages = extract_document_pages(
            request.input_path,
            request.pages,
            table_strategy=request.table_strategy.value,
        )
        engine = self._engine or create_tts_engine(request)
        prose_outputs: list[Path] = []
        table_outputs: list[Path] = []
        announce_page_numbers = _should_announce_page_numbers(request)

        with tempfile.TemporaryDirectory(
            prefix="pdf_tts_ru_", dir=request.output_dir
        ) as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            prose_wavs_for_merge: list[tuple[int, Path]] = []

            for page in extracted_pages:
                prose_text = _join_prose_segments(page.segments)
                if prose_text:
                    self._emit(
                        ProgressStage.SYNTHESIZING,
                        f"Synthesizing page {page.page_number}",
                        page_number=page.page_number,
                    )
                    rendered_text = _prepare_text(
                        prose_text,
                        page.page_number,
                        announce_page_numbers=announce_page_numbers,
                    )
                    prose_wav = temp_dir / f"page_{page.page_number:04d}_prose.wav"
                    engine.synthesize_to_wav(rendered_text, prose_wav)

                    if request.split_mode.value == "per-page":
                        final_output = build_prose_output_path(
                            input_path=request.input_path,
                            output_dir=request.output_dir,
                            pages=[page.page_number],
                            split_mode=request.split_mode,
                            output_format=request.output_format,
                        )
                        self._emit(
                            ProgressStage.EXPORTING,
                            f"Exporting page {page.page_number} to {final_output.name}",
                            page_number=page.page_number,
                            output_path=final_output,
                        )
                        _finalize_audio(
                            prose_wav,
                            final_output,
                            ffmpeg_bin=request.ffmpeg_bin,
                        )
                        prose_outputs.append(final_output)
                    else:
                        prose_wavs_for_merge.append((page.page_number, prose_wav))

                table_index = 0
                for segment in page.segments:
                    if segment.kind != SegmentKind.TABLE:
                        continue

                    table_index += 1
                    self._emit(
                        ProgressStage.SYNTHESIZING,
                        f"Synthesizing table {table_index} on page {page.page_number}",
                        page_number=page.page_number,
                        table_index=table_index,
                    )
                    rendered_text = _prepare_text(
                        segment.text,
                        page.page_number,
                        announce_page_numbers=announce_page_numbers,
                    )
                    table_wav = temp_dir / (
                        f"page_{page.page_number:04d}_table_{table_index:02d}.wav"
                    )
                    engine.synthesize_to_wav(rendered_text, table_wav)
                    final_output = build_table_output_path(
                        input_path=request.input_path,
                        output_dir=request.output_dir,
                        page_number=page.page_number,
                        table_index=table_index,
                        output_format=request.output_format,
                    )
                    self._emit(
                        ProgressStage.EXPORTING,
                        f"Exporting table {table_index} on page {page.page_number}",
                        page_number=page.page_number,
                        table_index=table_index,
                        output_path=final_output,
                    )
                    _finalize_audio(table_wav, final_output, ffmpeg_bin=request.ffmpeg_bin)
                    table_outputs.append(final_output)

            if request.split_mode.value != "per-page" and prose_wavs_for_merge:
                merge_inputs = _with_silence_between_pages(
                    prose_wavs_for_merge,
                    temp_dir=temp_dir,
                    pause_between_pages_ms=request.pause_between_pages_ms,
                )
                merged_wav = temp_dir / "merged_prose.wav"
                concat_audio(merge_inputs, merged_wav, ffmpeg_bin=request.ffmpeg_bin)
                final_output = build_prose_output_path(
                    input_path=request.input_path,
                    output_dir=request.output_dir,
                    pages=request.pages,
                    split_mode=request.split_mode,
                    output_format=request.output_format,
                )
                self._emit(
                    ProgressStage.EXPORTING,
                    f"Exporting merged audio to {final_output.name}",
                    output_path=final_output,
                )
                _finalize_audio(merged_wav, final_output, ffmpeg_bin=request.ffmpeg_bin)
                prose_outputs.append(final_output)

        outputs = prose_outputs + table_outputs
        if not outputs:
            raise ValueError("no speechable text found in selected pages")

        self._emit(
            ProgressStage.DONE,
            f"Created {len(outputs)} audio file(s)",
        )
        return outputs

    def _emit(
        self,
        stage: ProgressStage,
        message: str,
        *,
        page_number: int | None = None,
        table_index: int | None = None,
        output_path: Path | None = None,
    ) -> None:
        if self._progress_callback is None:
            return
        self._progress_callback(
            ProgressEvent(
                stage=stage,
                message=message,
                page_number=page_number,
                table_index=table_index,
                output_path=output_path,
            )
        )


def _join_prose_segments(segments) -> str:
    prose_parts = [segment.text.strip() for segment in segments if segment.kind == SegmentKind.PROSE]
    prose_parts = [part for part in prose_parts if part]
    return normalize_text_for_speech("\n\n".join(prose_parts))


def _prepare_text(text: str, page_number: int, *, announce_page_numbers: bool) -> str:
    normalized_text = normalize_text_for_speech(text)
    if not announce_page_numbers:
        return normalized_text
    return f"Страница {page_number}.\n\n{normalized_text}"


def _should_announce_page_numbers(request: SynthesisRequest) -> bool:
    if not request.announce_page_numbers:
        return False
    return request.input_path.suffix.lower() not in {".md", ".txt"}


def _with_silence_between_pages(
    prose_wavs: list[tuple[int, Path]],
    *,
    temp_dir: Path,
    pause_between_pages_ms: int,
) -> list[Path]:
    if pause_between_pages_ms <= 0 or len(prose_wavs) < 2:
        return [wav for _, wav in prose_wavs]

    inputs: list[Path] = []
    for index, (_page_number, wav_path) in enumerate(prose_wavs):
        inputs.append(wav_path)
        if index == len(prose_wavs) - 1:
            continue
        silence_wav = temp_dir / f"pause_{index + 1:04d}.wav"
        write_silence_wav(wav_path, silence_wav, pause_between_pages_ms)
        inputs.append(silence_wav)

    return inputs


def _finalize_audio(temp_wav: Path, output_file: Path, *, ffmpeg_bin: str) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    if output_file.suffix.lower() == ".wav":
        shutil.move(str(temp_wav), str(output_file))
        return

    convert_audio(temp_wav, output_file, ffmpeg_bin=ffmpeg_bin)
