from __future__ import annotations

from pathlib import Path

from pdf_tts_ru.normalize import strip_markdown_for_speech
from pdf_tts_ru.pdf_extract import (
    DocumentInspection,
    ExtractedPage,
    ExtractedSegment,
    PageInspection,
    SegmentKind,
)


def inspect_text_document(path: Path) -> DocumentInspection:
    """Inspect a plain-text or Markdown document."""

    text = _read_text_document(path)
    return DocumentInspection(
        page_count=1,
        pages=[
            PageInspection(
                page_number=1,
                char_count=len(text.strip()),
                table_count=0,
            )
        ],
    )


def extract_text_pages(path: Path, pages: list[int]) -> list[ExtractedPage]:
    """Extract a text or Markdown document as a single logical page."""

    _validate_single_page_selection(pages)
    text = _read_text_document(path)
    segments: list[ExtractedSegment] = []
    if text.strip():
        segments.append(
            ExtractedSegment(
                page_number=1,
                index=1,
                kind=SegmentKind.PROSE,
                text=text,
            )
        )
    return [ExtractedPage(page_number=1, segments=segments)]


def _read_text_document(path: Path) -> str:
    suffix = path.suffix.lower()
    raw_text = _read_text_file(path)
    if suffix == ".md":
        return strip_markdown_for_speech(raw_text)
    return raw_text


def _read_text_file(path: Path) -> str:
    try:
        data = path.read_bytes()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"input document not found: {path}") from exc

    for encoding in ("utf-8", "utf-8-sig", "cp1251"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError(
        "failed to decode text document "
        f"{path}: expected utf-8, utf-8-sig, or cp1251; convert the file and retry"
    )


def _validate_single_page_selection(pages: list[int]) -> None:
    for page_number in pages:
        if page_number != 1:
            raise ValueError("page 1 is the only available page for this document")
