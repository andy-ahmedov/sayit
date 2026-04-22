from __future__ import annotations

from pathlib import Path

from pdf_tts_ru.models import OutputFormat, SplitMode
from pdf_tts_ru.page_ranges import format_page_label


def build_prose_output_path(
    *,
    input_path: Path,
    output_dir: Path,
    pages: list[int],
    split_mode: SplitMode,
    output_format: OutputFormat,
) -> Path:
    """Build a deterministic output path for prose audio."""

    stem = _safe_stem(input_path)
    if split_mode == SplitMode.PER_PAGE:
        if len(pages) != 1:
            raise ValueError("per-page output requires exactly one page")
        name = f"{stem}_page_{pages[0]:04d}.{output_format.value}"
    elif split_mode == SplitMode.PER_RANGE:
        name = f"{stem}_{format_page_label(pages)}.{output_format.value}"
    else:
        name = f"{stem}_merged_{format_page_label(pages)}.{output_format.value}"

    return output_dir / name


def build_table_output_path(
    *,
    input_path: Path,
    output_dir: Path,
    page_number: int,
    table_index: int,
    output_format: OutputFormat,
) -> Path:
    """Build a deterministic output path for a separate table segment."""

    if page_number < 1:
        raise ValueError("page_number must be positive")
    if table_index < 1:
        raise ValueError("table_index must be positive")

    stem = _safe_stem(input_path)
    name = f"{stem}_page_{page_number:04d}_table_{table_index:02d}.{output_format.value}"
    return output_dir / name


def _safe_stem(path: Path) -> str:
    return path.stem.replace(" ", "_")
