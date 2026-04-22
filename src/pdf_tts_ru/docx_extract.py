from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from docx import Document as DocxDocument
from docx.document import Document as DocxDocumentType
from docx.oxml.ns import qn
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table
from docx.text.paragraph import Paragraph

from pdf_tts_ru.models import TableStrategy
from pdf_tts_ru.pdf_extract import (
    DocumentInspection,
    ExtractedPage,
    ExtractedSegment,
    PageInspection,
    SegmentKind,
)
from pdf_tts_ru.table_render import fallback_headers, format_spoken_table, normalize_table_cell


@dataclass(slots=True)
class _DocxPageState:
    page_number: int
    items: list[tuple[SegmentKind, str]]


def inspect_docx(path: Path) -> DocumentInspection:
    """Inspect a DOCX document using logical pages split by manual page breaks."""

    page_states = _collect_docx_pages(path)
    pages = [
        PageInspection(
            page_number=page.page_number,
            char_count=sum(len(text) for kind, text in page.items if kind == SegmentKind.PROSE),
            table_count=sum(1 for kind, _ in page.items if kind == SegmentKind.TABLE),
        )
        for page in page_states
    ]
    return DocumentInspection(page_count=len(pages), pages=pages)


def extract_docx_pages(
    path: Path,
    pages: list[int],
    *,
    table_strategy: str = "inline",
) -> list[ExtractedPage]:
    """Extract selected logical pages from a DOCX document."""

    strategy = TableStrategy(table_strategy)
    page_states = _collect_docx_pages(path)
    extracted: list[ExtractedPage] = []

    for page_number in pages:
        if page_number < 1 or page_number > len(page_states):
            raise ValueError(
                f"page {page_number} is out of bounds for document with {len(page_states)} pages"
            )
        extracted.append(_render_page(page_states[page_number - 1], strategy))

    return extracted


def _collect_docx_pages(path: Path) -> list[_DocxPageState]:
    document = _open_docx(path)
    pages = [_DocxPageState(page_number=1, items=[])]

    for block in _iter_block_items(document):
        current_page = pages[-1]
        if isinstance(block, Paragraph):
            chunks = _split_paragraph_on_page_breaks(block)
            for index, chunk in enumerate(chunks):
                cleaned = _clean_docx_text(chunk)
                if cleaned:
                    current_page.items.append((SegmentKind.PROSE, cleaned))
                if index != len(chunks) - 1:
                    next_page = _DocxPageState(page_number=len(pages) + 1, items=[])
                    pages.append(next_page)
                    current_page = next_page
        elif isinstance(block, Table):
            table_index = sum(1 for kind, _ in current_page.items if kind == SegmentKind.TABLE) + 1
            table_text = _format_docx_table(block, table_index)
            if table_text:
                current_page.items.append((SegmentKind.TABLE, table_text))

    return pages


def _render_page(page: _DocxPageState, strategy: TableStrategy) -> ExtractedPage:
    segment_index = 1
    segments: list[ExtractedSegment] = []

    if strategy == TableStrategy.INLINE:
        combined_text = "\n\n".join(text for _kind, text in page.items if text).strip()
        if combined_text:
            segments.append(
                ExtractedSegment(
                    page_number=page.page_number,
                    index=segment_index,
                    kind=SegmentKind.PROSE,
                    text=combined_text,
                )
            )
        return ExtractedPage(page_number=page.page_number, segments=segments)

    prose_text = "\n\n".join(text for kind, text in page.items if kind == SegmentKind.PROSE).strip()
    if prose_text:
        segments.append(
            ExtractedSegment(
                page_number=page.page_number,
                index=segment_index,
                kind=SegmentKind.PROSE,
                text=prose_text,
            )
        )
        segment_index += 1

    if strategy == TableStrategy.SEPARATE:
        for kind, text in page.items:
            if kind != SegmentKind.TABLE:
                continue
            segments.append(
                ExtractedSegment(
                    page_number=page.page_number,
                    index=segment_index,
                    kind=SegmentKind.TABLE,
                    text=text,
                )
            )
            segment_index += 1

    return ExtractedPage(page_number=page.page_number, segments=segments)


def _open_docx(path: Path) -> DocxDocumentType:
    try:
        return DocxDocument(path)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"input document not found: {path}") from exc
    except PackageNotFoundError as exc:
        raise ValueError(f"failed to open DOCX {path}: {exc}") from exc


def _iter_block_items(document: DocxDocumentType):
    body = document.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def _split_paragraph_on_page_breaks(paragraph: Paragraph) -> list[str]:
    if not paragraph.runs:
        return [paragraph.text]

    chunks: list[str] = []
    current_parts: list[str] = []

    for run in paragraph.runs:
        for child in run._element.iterchildren():
            tag = child.tag.rsplit("}", 1)[-1]
            if tag == "t":
                current_parts.append(child.text or "")
                continue
            if tag == "tab":
                current_parts.append("\t")
                continue
            if tag in {"br", "cr"}:
                break_type = child.get(qn("w:type"))
                if break_type == "page":
                    chunks.append("".join(current_parts))
                    current_parts = []
                else:
                    current_parts.append("\n")

    chunks.append("".join(current_parts))
    return chunks


def _format_docx_table(table: Table, table_index: int) -> str:
    rows = [[normalize_table_cell(cell.text) for cell in row.cells] for row in table.rows]
    rows = [row for row in rows if any(cell for cell in row)]
    if not rows:
        return ""

    column_count = max(len(row) for row in rows)
    if len(rows) > 1 and any(rows[0]):
        headers = _normalize_headers(rows[0], column_count)
        data_rows = rows[1:]
    else:
        headers = fallback_headers(column_count)
        data_rows = rows

    return format_spoken_table(table_index, headers=headers, data_rows=data_rows)


def _normalize_headers(row: list[str], column_count: int) -> list[str]:
    headers: list[str] = []
    for index in range(column_count):
        value = row[index] if index < len(row) else ""
        headers.append(value or f"Колонка {index + 1}")
    return headers


def _clean_docx_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines).strip()
