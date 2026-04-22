from __future__ import annotations

import re


_WHITESPACE_RE = re.compile(r"[ \t]+")
_MULTILINE_RE = re.compile(r"\n{3,}")
_FENCED_CODE_RE = re.compile(r"(^|\n)(```|~~~).*?(\n\2[^\n]*|$)", re.DOTALL)
_MARKDOWN_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]+\)")
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MARKDOWN_STYLE_RE = re.compile(r"(\*\*|__|\*|_|~~)")
_INLINE_CODE_RE = re.compile(r"`([^`]*)`")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s*")
_BLOCKQUOTE_RE = re.compile(r"^\s{0,3}>\s?")
_LIST_MARKER_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+")


def normalize_text_for_speech(text: str) -> str:
    """Apply a conservative cleanup suitable for v1 speech synthesis.

    This function is intentionally simple in the scaffold. The implementation may
    become smarter later, but it should remain predictable and well-tested.
    """
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    text = "\n".join(lines)
    text = _WHITESPACE_RE.sub(" ", text)
    text = _MULTILINE_RE.sub("\n\n", text)
    return text.strip()


def strip_markdown_for_speech(text: str) -> str:
    """Remove common Markdown markup while keeping readable prose."""

    text = _FENCED_CODE_RE.sub("\n", text)
    text = _MARKDOWN_IMAGE_RE.sub(lambda match: match.group(1).strip(), text)
    text = _MARKDOWN_LINK_RE.sub(lambda match: match.group(1), text)
    text = _INLINE_CODE_RE.sub(lambda match: match.group(1), text)
    text = _MARKDOWN_STYLE_RE.sub("", text)

    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = _HEADING_RE.sub("", raw_line)
        line = _BLOCKQUOTE_RE.sub("", line)
        line = _LIST_MARKER_RE.sub("", line)
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)
