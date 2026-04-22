import pytest

from pdf_tts_ru.page_ranges import parse_page_spec


def test_parse_all() -> None:
    assert parse_page_spec("all", 3) == [1, 2, 3]


def test_parse_single_pages() -> None:
    assert parse_page_spec("1,3,2", 5) == [1, 2, 3]


def test_parse_range() -> None:
    assert parse_page_spec("2-4", 10) == [2, 3, 4]


def test_parse_mixed() -> None:
    assert parse_page_spec("1,3-5,8", 10) == [1, 3, 4, 5, 8]


def test_parse_rejects_invalid_page_range() -> None:
    with pytest.raises(ValueError, match="invalid page range"):
        parse_page_spec("1-a", 10)


def test_parse_rejects_invalid_page_number() -> None:
    with pytest.raises(ValueError, match="invalid page number"):
        parse_page_spec("x", 10)


def test_parse_rejects_reverse_range() -> None:
    with pytest.raises(ValueError, match="greater than end"):
        parse_page_spec("5-2", 10)


def test_parse_rejects_out_of_bounds_range() -> None:
    with pytest.raises(ValueError, match="out of bounds"):
        parse_page_spec("1-11", 10)
