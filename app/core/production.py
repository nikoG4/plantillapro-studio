from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from .models import TextField
from .renderer import render_text_template


def variable_fields(fields: Iterable[TextField]) -> list[TextField]:
    return [field for field in fields if field.is_variable()]


def source_columns(rows: Iterable[dict[str, str]]) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def build_production_rows(fields: Iterable[TextField], rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Resolve each variable text field from either a data column or a number sequence."""
    fields = variable_fields(fields)
    data_count = len(rows)
    number_count = max((max(1, field.number_count) for field in fields if field.production_source == "numbering"), default=0)
    count = max(data_count, number_count, 1)

    result: list[dict[str, str]] = [deepcopy(rows[index]) if index < data_count else {} for index in range(count)]
    for index, row in enumerate(result):
        row.setdefault("numero", str(index + 1))
        for field in fields:
            key = field.variable_key()
            if field.production_source == "numbering":
                value = field.number_start + index * field.number_step
                number = str(value).zfill(max(0, field.number_digits)) if field.number_digits else str(value)
                row[key] = f"{field.number_prefix}{number}{field.number_suffix}"
            else:
                source = field.source_column or key
                row[key] = str(row.get(source, ""))
    return result


def production_errors(fields: Iterable[TextField], rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    columns = set(source_columns(rows))
    for field in variable_fields(fields):
        if field.production_source == "column":
            source = field.source_column or field.variable_key()
            if not rows:
                errors.append(f"'{field.name}' necesita una lista de datos")
            elif source not in columns:
                errors.append(f"'{field.name}' apunta a la columna '{source}', que no existe")
        elif field.production_source == "numbering" and field.number_count <= 0:
            errors.append(f"'{field.name}' necesita una cantidad de numeración mayor a cero")
    return errors


def suggested_filename_pattern(fields: Iterable[TextField], mode: str, field_id: str = "", custom: str = "") -> str:
    variables = variable_fields(fields)
    selected = next((field for field in variables if field.id == field_id), variables[0] if variables else None)
    key = selected.variable_key() if selected else "numero"
    if mode == "field":
        return "{{" + key + "}}"
    if mode == "number_field":
        return "{{numero}}_{{" + key + "}}"
    if mode == "custom":
        return custom.strip() or "{{numero}}"
    return "{{numero}}"


def filename_preview(pattern: str, rows: list[dict[str, str]]) -> str:
    row = rows[0] if rows else {"numero": "1"}
    return render_text_template(pattern, row, 1) or "archivo"
