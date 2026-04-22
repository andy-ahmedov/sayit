from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import fitz

from pdf_tts_ru.table_render import fallback_headers, format_spoken_table, normalize_table_cell


fitz.no_recommend_layout()


class SegmentKind(StrEnum):
    PROSE = "prose"
    TABLE = "table"


@dataclass(slots=True)
class ExtractedSegment:
    page_number: int
    index: int
    kind: SegmentKind
    text: str


@dataclass(slots=True)
class ExtractedPage:
    page_number: int
    segments: list[ExtractedSegment]


@dataclass(slots=True)
class PageInspection:
    page_number: int
    char_count: int
    table_count: int


@dataclass(slots=True)
class DocumentInspection:
    page_count: int
    pages: list[PageInspection]


def inspect_pdf(path: Path) -> DocumentInspection:
    """Inspect a PDF and return basic metadata."""

    pages: list[PageInspection] = []
    with _open_pdf(path) as document:
        for page_index in range(document.page_count):
            page = document[page_index]
            text = page.get_text("text", sort=True).strip()
            tables = _find_tables(page)
            pages.append(
                PageInspection(
                    page_number=page_index + 1,
                    char_count=len(text),
                    table_count=len(tables),
                )
            )

        return DocumentInspection(page_count=document.page_count, pages=pages)


def extract_pages(
    path: Path,
    pages: list[int],
    *,
    table_strategy: str = "inline",
) -> list[ExtractedPage]:
    """Extract selected pages from a PDF."""

    from pdf_tts_ru.models import TableStrategy

    strategy = TableStrategy(table_strategy)
    extracted: list[ExtractedPage] = []

    with _open_pdf(path) as document:
        for page_number in pages:
            if page_number < 1 or page_number > document.page_count:
                raise ValueError(
                    f"page {page_number} is out of bounds for document with "
                    f"{document.page_count} pages"
                )

            page = document[page_number - 1]
            extracted.append(_extract_page(page, page_number, strategy))

    return extracted


def _extract_page(
    page: fitz.Page, page_number: int, table_strategy
) -> ExtractedPage:
    tables = _find_tables(page)
    table_bboxes = [fitz.Rect(table.bbox) for table in tables]

    prose_items: list[tuple[float, float, str]] = []
    table_items: list[tuple[float, float, int, str]] = []
    for block in page.get_text("blocks", sort=True):
        x0, y0, x1, y1, text, *_rest = block
        block_type = block[6]
        if block_type != 0:
            continue
        cleaned_text = _clean_block_text(text)
        if not cleaned_text:
            continue
        block_rect = fitz.Rect(x0, y0, x1, y1)
        if any(block_rect.intersects(table_bbox) for table_bbox in table_bboxes):
            continue
        prose_items.append((y0, x0, cleaned_text))

    for table_index, table in enumerate(tables, start=1):
        y0 = table.bbox[1]
        x0 = table.bbox[0]
        table_items.append((y0, x0, table_index, _format_table_text(table, table_index)))

    segments: list[ExtractedSegment] = []
    segment_index = 1

    if table_strategy.value == "inline":
        combined_items: list[tuple[float, float, str]] = [
            (y0, x0, text) for y0, x0, text in prose_items
        ]
        combined_items.extend((y0, x0, text) for y0, x0, _, text in table_items)
        combined_text = _join_text_items(combined_items)
        if combined_text:
            segments.append(
                ExtractedSegment(
                    page_number=page_number,
                    index=segment_index,
                    kind=SegmentKind.PROSE,
                    text=combined_text,
                )
            )
    else:
        prose_text = _join_text_items(prose_items)
        if prose_text:
            segments.append(
                ExtractedSegment(
                    page_number=page_number,
                    index=segment_index,
                    kind=SegmentKind.PROSE,
                    text=prose_text,
                )
            )
            segment_index += 1

        if table_strategy.value == "separate":
            for _, _, table_index, table_text in table_items:
                segments.append(
                    ExtractedSegment(
                        page_number=page_number,
                        index=segment_index,
                        kind=SegmentKind.TABLE,
                        text=table_text,
                    )
                )
                segment_index += 1

    return ExtractedPage(page_number=page_number, segments=segments)


def _open_pdf(path: Path) -> fitz.Document:
    try:
        return fitz.open(path)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"input PDF not found: {path}") from exc
    except (fitz.EmptyFileError, fitz.FileDataError) as exc:
        raise ValueError(f"failed to open PDF {path}: {exc}") from exc


def _find_tables(page: fitz.Page) -> list:
    try:
        return page.find_tables().tables
    except Exception:
        return []


def _clean_block_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def _join_text_items(items: list[tuple[float, float, str]]) -> str:
    if not items:
        return ""
    ordered_texts = [text for _, _, text in sorted(items, key=lambda item: (item[0], item[1]))]
    return "\n\n".join(ordered_texts).strip()


def _format_table_text(table, table_index: int) -> str:
    rows = table.extract()
    headers = _resolve_table_headers(table, rows)

    if table.header.external:
        data_rows = rows
    else:
        data_rows = rows[1:] if rows else []

    return format_spoken_table(table_index, headers=headers, data_rows=data_rows)


def _resolve_table_headers(table, rows: list[list[str | None]]) -> list[str]:
    raw_headers = getattr(table.header, "names", []) or []
    headers = [normalize_table_cell(value) for value in raw_headers]
    column_count = table.col_count

    resolved: list[str] = []
    for index in range(column_count):
        name = headers[index] if index < len(headers) else ""
        resolved.append(name or f"Колонка {index + 1}")

    if not resolved and rows:
        return fallback_headers(len(rows[0]))

    return resolved


def _normalize_cell(value: str | None) -> str:
    return normalize_table_cell(value)
