from __future__ import annotations

import argparse
from pathlib import Path

from pdf_tts_ru.config import load_synthesis_config, resolve_synthesis_request
from pdf_tts_ru.document_extract import inspect_document
from pdf_tts_ru.models import (
    OutputFormat,
    SileroLineBreakMode,
    SplitMode,
    TableStrategy,
    TtsEngineKind,
)
from pdf_tts_ru.page_ranges import parse_page_spec
from pdf_tts_ru.pipeline import PdfTtsPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf-tts-ru",
        description="Local Russian document to audio",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a supported input document")
    inspect_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to input document (.pdf, .docx, .md, .txt)",
    )

    synth_parser = subparsers.add_parser("synth", help="Synthesize audio from a document")
    synth_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to input document (.pdf, .docx, .md, .txt)",
    )
    synth_parser.add_argument("--config", type=Path, help="Optional TOML config file")
    synth_parser.add_argument("--pages", required=True, help="Page spec: all | 1 | 1-5 | 1,3-5")
    synth_parser.add_argument("--engine", choices=[engine.value for engine in TtsEngineKind])
    synth_parser.add_argument("--split", choices=[mode.value for mode in SplitMode])
    synth_parser.add_argument(
        "--format",
        dest="output_format",
        choices=[fmt.value for fmt in OutputFormat],
    )
    synth_parser.add_argument("--output-dir", type=Path)
    synth_parser.add_argument(
        "--voice",
        default=None,
        type=Path,
        help="Path to Piper voice model (*.onnx); used only with --engine piper",
    )
    synth_parser.add_argument("--ffmpeg-bin")
    synth_parser.add_argument("--silero-model-id")
    synth_parser.add_argument("--silero-speaker")
    synth_parser.add_argument("--silero-sample-rate", type=int)
    synth_parser.add_argument("--silero-device")
    synth_parser.add_argument(
        "--silero-line-break-mode",
        choices=[mode.value for mode in SileroLineBreakMode],
        help="How Silero should treat single line breaks inside prose",
    )
    synth_parser.add_argument(
        "--silero-transliterate-latin",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Transliterate Latin words to Russian-like pronunciation for Silero",
    )
    synth_parser.add_argument(
        "--silero-verbalize-numbers",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Convert numeric tokens to Russian words for Silero",
    )
    synth_parser.add_argument(
        "--silero-spell-cyrillic-abbreviations",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Spell Cyrillic abbreviations letter by letter for Silero",
    )
    synth_parser.add_argument(
        "--silero-expand-short-units",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Expand short units like нм or мг into spoken Russian for Silero",
    )
    synth_parser.add_argument(
        "--table-strategy",
        choices=[strategy.value for strategy in TableStrategy],
    )
    synth_parser.add_argument(
        "--announce-page-numbers",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Speak 'Страница N' before each page or table segment",
    )
    synth_parser.add_argument("--pause-between-pages-ms", type=int)
    synth_parser.add_argument("--length-scale", type=float)
    synth_parser.add_argument("--noise-scale", type=float)
    synth_parser.add_argument("--noise-w-scale", type=float)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "inspect":
            inspection = inspect_document(args.input)
            print(render_inspection(args.input, inspection))
            return

        if args.command == "synth":
            inspection = inspect_document(args.input)
            config = load_synthesis_config(args.config) if args.config else None
            pages = parse_page_spec(args.pages, page_count=inspection.page_count)
            request = resolve_synthesis_request(
                input_path=args.input,
                pages=pages,
                output_dir=args.output_dir,
                engine=TtsEngineKind(args.engine) if args.engine else None,
                voice_model=args.voice,
                ffmpeg_bin=args.ffmpeg_bin,
                output_format=OutputFormat(args.output_format) if args.output_format else None,
                split_mode=SplitMode(args.split) if args.split else None,
                table_strategy=(
                    TableStrategy(args.table_strategy) if args.table_strategy else None
                ),
                announce_page_numbers=args.announce_page_numbers,
                pause_between_pages_ms=args.pause_between_pages_ms,
                length_scale=args.length_scale,
                noise_scale=args.noise_scale,
                noise_w_scale=args.noise_w_scale,
                silero_model_id=args.silero_model_id,
                silero_speaker=args.silero_speaker,
                silero_sample_rate=args.silero_sample_rate,
                silero_device=args.silero_device,
                silero_line_break_mode=(
                    SileroLineBreakMode(args.silero_line_break_mode)
                    if args.silero_line_break_mode
                    else None
                ),
                silero_transliterate_latin=args.silero_transliterate_latin,
                silero_verbalize_numbers=args.silero_verbalize_numbers,
                silero_spell_cyrillic_abbreviations=args.silero_spell_cyrillic_abbreviations,
                silero_expand_short_units=args.silero_expand_short_units,
                config=config,
            )
            outputs = PdfTtsPipeline().run(request)
            for output in outputs:
                print(output)
            return

        parser.error(f"unknown command: {args.command}")
    except Exception as exc:
        parser.exit(2, f"error: {exc}\n")


def render_inspection(input_path: Path, inspection) -> str:
    lines = [
        f"Input: {input_path}",
        f"Pages: {inspection.page_count}",
    ]
    for page in inspection.pages:
        lines.append(
            f"Page {page.page_number}: chars={page.char_count}, tables={page.table_count}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
