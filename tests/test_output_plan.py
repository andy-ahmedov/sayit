from pathlib import Path

import pytest

from pdf_tts_ru.models import OutputFormat, SplitMode
from pdf_tts_ru.output_plan import build_prose_output_path, build_table_output_path


def test_build_prose_output_path_for_per_page() -> None:
    result = build_prose_output_path(
        input_path=Path("My Book.pdf"),
        output_dir=Path("out"),
        pages=[7],
        split_mode=SplitMode.PER_PAGE,
        output_format=OutputFormat.MP3,
    )

    assert result == Path("out/My_Book_page_0007.mp3")


def test_build_prose_output_path_for_range() -> None:
    result = build_prose_output_path(
        input_path=Path("book.pdf"),
        output_dir=Path("out"),
        pages=[1, 3, 4, 5],
        split_mode=SplitMode.PER_RANGE,
        output_format=OutputFormat.M4A,
    )

    assert result == Path("out/book_page_0001_pages_0003-0005.m4a")


def test_build_prose_output_path_for_merged() -> None:
    result = build_prose_output_path(
        input_path=Path("book.pdf"),
        output_dir=Path("out"),
        pages=[2, 3],
        split_mode=SplitMode.MERGED,
        output_format=OutputFormat.WAV,
    )

    assert result == Path("out/book_merged_pages_0002-0003.wav")


def test_build_table_output_path() -> None:
    result = build_table_output_path(
        input_path=Path("book.pdf"),
        output_dir=Path("out"),
        page_number=2,
        table_index=3,
        output_format=OutputFormat.MP3,
    )

    assert result == Path("out/book_page_0002_table_03.mp3")


def test_build_prose_output_path_rejects_multi_page_per_page() -> None:
    with pytest.raises(ValueError, match="exactly one page"):
        build_prose_output_path(
            input_path=Path("book.pdf"),
            output_dir=Path("out"),
            pages=[1, 2],
            split_mode=SplitMode.PER_PAGE,
            output_format=OutputFormat.WAV,
        )
