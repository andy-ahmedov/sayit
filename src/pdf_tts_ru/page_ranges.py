from __future__ import annotations


def parse_page_spec(spec: str, page_count: int) -> list[int]:
    """Parse a 1-based page specification into a sorted unique list of page numbers.

    Supported formats:
    - all
    - 1
    - 1,3,5
    - 1-5
    - 1,3-5,8
    """
    if page_count < 1:
        raise ValueError("page_count must be positive")

    spec = spec.strip().lower()
    if not spec:
        raise ValueError("page spec is empty")

    if spec == "all":
        return list(range(1, page_count + 1))

    pages: set[int] = set()
    parts = [part.strip() for part in spec.split(",") if part.strip()]
    if not parts:
        raise ValueError("page spec is invalid")

    for part in parts:
        if "-" in part:
            chunks = [c.strip() for c in part.split("-")]
            if len(chunks) != 2 or not chunks[0] or not chunks[1]:
                raise ValueError(f"invalid page range: {part}")
            try:
                start = int(chunks[0])
                end = int(chunks[1])
            except ValueError as exc:
                raise ValueError(f"invalid page range: {part}") from exc
            if start > end:
                raise ValueError(f"page range start is greater than end: {part}")
            if start < 1 or end > page_count:
                raise ValueError(f"page range out of bounds: {part}")
            for page in range(start, end + 1):
                pages.add(page)
        else:
            try:
                page = int(part)
            except ValueError as exc:
                raise ValueError(f"invalid page number: {part}") from exc
            if page < 1 or page > page_count:
                raise ValueError(f"page out of bounds: {page}")
            pages.add(page)

    return sorted(pages)


def coalesce_page_ranges(pages: list[int]) -> list[tuple[int, int]]:
    """Coalesce sorted page numbers into inclusive ranges."""

    if not pages:
        raise ValueError("pages must not be empty")

    ordered = sorted(set(pages))
    if ordered[0] < 1:
        raise ValueError("page numbers must be positive")

    ranges: list[tuple[int, int]] = []
    start = ordered[0]
    end = ordered[0]

    for page in ordered[1:]:
        if page == end + 1:
            end = page
            continue
        ranges.append((start, end))
        start = end = page

    ranges.append((start, end))
    return ranges


def format_page_label(pages: list[int]) -> str:
    """Format page numbers into a deterministic label suitable for filenames."""

    parts: list[str] = []
    for start, end in coalesce_page_ranges(pages):
        if start == end:
            parts.append(f"page_{start:04d}")
        else:
            parts.append(f"pages_{start:04d}-{end:04d}")

    return "_".join(parts)
