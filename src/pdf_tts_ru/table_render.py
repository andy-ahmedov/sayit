from __future__ import annotations


def format_spoken_table(
    table_index: int,
    *,
    headers: list[str],
    data_rows: list[list[str | None]],
) -> str:
    """Render a table into an explicit spoken Russian structure."""

    parts = [f"Таблица {table_index}."]
    if headers:
        parts.append("Колонки: " + "; ".join(headers) + ".")

    for row_index, row in enumerate(data_rows, start=1):
        cells: list[str] = []
        for col_index, value in enumerate(row):
            cell_text = normalize_table_cell(value)
            if not cell_text:
                continue
            header = headers[col_index] if col_index < len(headers) else f"Колонка {col_index + 1}"
            cells.append(f"{header}: {cell_text}")
        if cells:
            parts.append(f"Строка {row_index}. " + "; ".join(cells) + ".")

    return "\n".join(parts)


def normalize_table_cell(value: str | None) -> str:
    """Collapse table cell whitespace into a single line."""

    if value is None:
        return ""
    return " ".join(part for part in value.split())


def fallback_headers(column_count: int) -> list[str]:
    """Build generic spoken headers when a table has no explicit names."""

    return [f"Колонка {index + 1}" for index in range(column_count)]
