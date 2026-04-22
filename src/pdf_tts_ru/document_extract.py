from __future__ import annotations

from pathlib import Path

from pdf_tts_ru.docx_extract import extract_docx_pages, inspect_docx
from pdf_tts_ru.pdf_extract import extract_pages as extract_pdf_pages
from pdf_tts_ru.pdf_extract import inspect_pdf
from pdf_tts_ru.text_extract import extract_text_pages, inspect_text_document


SUPPORTED_INPUT_SUFFIXES = (".pdf", ".docx", ".md", ".txt")


def inspect_document(path: Path):
    """Inspect a supported input document."""

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return inspect_pdf(path)
    if suffix == ".docx":
        return inspect_docx(path)
    if suffix in {".md", ".txt"}:
        return inspect_text_document(path)
    if suffix == ".doc":
        raise ValueError(_doc_conversion_message(path))
    raise ValueError(_unsupported_input_message(path))


def extract_document_pages(
    path: Path,
    pages: list[int],
    *,
    table_strategy: str = "inline",
):
    """Extract selected logical pages from a supported input document."""

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf_pages(path, pages, table_strategy=table_strategy)
    if suffix == ".docx":
        return extract_docx_pages(path, pages, table_strategy=table_strategy)
    if suffix in {".md", ".txt"}:
        return extract_text_pages(path, pages)
    if suffix == ".doc":
        raise ValueError(_doc_conversion_message(path))
    raise ValueError(_unsupported_input_message(path))


def _unsupported_input_message(path: Path) -> str:
    supported = ", ".join(SUPPORTED_INPUT_SUFFIXES) + ", .doc"
    return f"unsupported input format for {path}: expected one of {supported}"


def _doc_conversion_message(path: Path) -> str:
    output_docx = path.with_suffix(".docx").name
    return (
        f"direct .doc input is not supported for {path}. "
        f"Convert it to .docx first, for example: "
        f"'pandoc {path.name} -o {output_docx}' or "
        f"'libreoffice --headless --convert-to docx --outdir . {path.name}'"
    )
