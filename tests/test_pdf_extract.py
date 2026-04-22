from __future__ import annotations

from pathlib import Path

import fitz

from pdf_tts_ru.models import TableStrategy
from pdf_tts_ru.pdf_extract import SegmentKind, extract_pages, inspect_pdf


def test_inspect_pdf_reports_page_and_table_counts(tmp_path: Path) -> None:
    pdf_path = create_sample_pdf(tmp_path / "sample.pdf")

    inspection = inspect_pdf(pdf_path)

    assert inspection.page_count == 2
    assert [page.table_count for page in inspection.pages] == [0, 1]
    assert inspection.pages[0].char_count > 0


def test_extract_pages_skip_omits_table_text(tmp_path: Path) -> None:
    pdf_path = create_sample_pdf(tmp_path / "sample.pdf")

    extracted_pages = extract_pages(pdf_path, [2], table_strategy=TableStrategy.SKIP.value)

    assert len(extracted_pages) == 1
    assert [segment.kind for segment in extracted_pages[0].segments] == [SegmentKind.PROSE]
    assert "Intro before table." in extracted_pages[0].segments[0].text
    assert "Таблица 1." not in extracted_pages[0].segments[0].text
    assert "Alice" not in extracted_pages[0].segments[0].text


def test_extract_pages_inline_embeds_spoken_table(tmp_path: Path) -> None:
    pdf_path = create_sample_pdf(tmp_path / "sample.pdf")

    extracted_pages = extract_pages(pdf_path, [2], table_strategy=TableStrategy.INLINE.value)

    text = extracted_pages[0].segments[0].text
    assert [segment.kind for segment in extracted_pages[0].segments] == [SegmentKind.PROSE]
    assert "Intro before table." in text
    assert "Таблица 1." in text
    assert "Колонки: Name; Score." in text
    assert "Строка 1. Name: Alice; Score: 5." in text


def test_extract_pages_separate_splits_table_segment(tmp_path: Path) -> None:
    pdf_path = create_sample_pdf(tmp_path / "sample.pdf")

    extracted_pages = extract_pages(pdf_path, [2], table_strategy=TableStrategy.SEPARATE.value)

    assert [segment.kind for segment in extracted_pages[0].segments] == [
        SegmentKind.PROSE,
        SegmentKind.TABLE,
    ]
    assert "Intro before table." in extracted_pages[0].segments[0].text
    assert "Таблица 1." in extracted_pages[0].segments[1].text


def create_sample_pdf(path: Path) -> Path:
    document = fitz.open()

    page = document.new_page(width=400, height=400)
    page.insert_text((72, 72), "First page without tables.")

    page = document.new_page(width=400, height=400)
    page.insert_text((72, 50), "Intro before table.")
    draw_table(page, origin_x=72, origin_y=90)
    page.insert_text((72, 240), "Outro after table.")

    document.save(path)
    document.close()
    return path


def draw_table(page: fitz.Page, *, origin_x: float, origin_y: float) -> None:
    shape = page.new_shape()
    for y in (origin_y, origin_y + 40, origin_y + 80):
        shape.draw_line((origin_x, y), (origin_x + 200, y))
    for x in (origin_x, origin_x + 100, origin_x + 200):
        shape.draw_line((x, origin_y), (x, origin_y + 80))
    shape.finish(width=1)
    shape.commit()

    page.insert_text((origin_x + 12, origin_y + 25), "Name")
    page.insert_text((origin_x + 112, origin_y + 25), "Score")
    page.insert_text((origin_x + 12, origin_y + 65), "Alice")
    page.insert_text((origin_x + 112, origin_y + 65), "5")
