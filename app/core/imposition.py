from __future__ import annotations
from dataclasses import dataclass
from math import ceil
from pathlib import Path
from typing import Iterable
from PIL import Image
from .models import ExportSettings, FillMode, NumberingSettings, OrderMode, PageSize, TextField
from .renderer import render_template

@dataclass(frozen=True)
class Placement:
    x: int
    y: int
    width: int
    height: int
    position_index: int

@dataclass(frozen=True)
class LayoutInfo:
    page_width: int
    page_height: int
    piece_width: int
    piece_height: int
    columns: int
    rows: int
    slots_per_page: int
    placements: list[Placement]

def mm_to_px(value_mm: float, dpi: int) -> int:
    return max(0, round(float(value_mm) / 25.4 * max(1, dpi)))

def page_pixels(settings: ExportSettings, image_size: tuple[int, int]) -> tuple[int, int]:
    dpi = max(1, settings.dpi)
    sizes_in = {
        PageSize.A4_PORTRAIT: (8.2677, 11.6929),
        PageSize.A4_LANDSCAPE: (11.6929, 8.2677),
        PageSize.LETTER_PORTRAIT: (8.5, 11.0),
        PageSize.LETTER_LANDSCAPE: (11.0, 8.5),
    }
    if settings.page_size == PageSize.CUSTOM and settings.custom_width_px and settings.custom_height_px:
        return settings.custom_width_px, settings.custom_height_px
    if settings.page_size in sizes_in:
        width_in, height_in = sizes_in[settings.page_size]
        return round(width_in * dpi), round(height_in * dpi)
    return image_size

def piece_pixels(settings: ExportSettings, image_size: tuple[int, int]) -> tuple[int, int]:
    if settings.use_original_piece_size:
        return image_size
    return max(1, mm_to_px(settings.piece_width_mm, settings.dpi)), max(1, mm_to_px(settings.piece_height_mm, settings.dpi))

def compute_layout(settings: ExportSettings, image_size: tuple[int, int]) -> LayoutInfo:
    page_w, page_h = page_pixels(settings, image_size)
    piece_w, piece_h = piece_pixels(settings, image_size)
    if settings.page_size == PageSize.ORIGINAL and settings.use_original_piece_size:
        placement = Placement(0, 0, piece_w, piece_h, 0)
        return LayoutInfo(page_w, page_h, piece_w, piece_h, 1, 1, 1, [placement])
    left = mm_to_px(settings.margin_left_mm, settings.dpi)
    top = mm_to_px(settings.margin_top_mm, settings.dpi)
    right = mm_to_px(settings.margin_right_mm, settings.dpi)
    bottom = mm_to_px(settings.margin_bottom_mm, settings.dpi)
    gap_x = mm_to_px(settings.gap_x_mm, settings.dpi)
    gap_y = mm_to_px(settings.gap_y_mm, settings.dpi)
    usable_w = max(0, page_w - left - right)
    usable_h = max(0, page_h - top - bottom)
    columns = _fit_count(usable_w, piece_w, gap_x)
    rows = _fit_count(usable_h, piece_h, gap_y)
    if settings.fill_mode == FillMode.VERTICAL_ONLY:
        columns = 1 if columns else 0
    grid_w = columns * piece_w + max(0, columns - 1) * gap_x
    grid_h = rows * piece_h + max(0, rows - 1) * gap_y
    start_x = left + max(0, (usable_w - grid_w) // 2)
    start_y = top + max(0, (usable_h - grid_h) // 2)
    placements: list[Placement] = []
    for row in range(rows):
        for column in range(columns):
            index = row * columns + column
            placements.append(Placement(start_x + column * (piece_w + gap_x), start_y + row * (piece_h + gap_y), piece_w, piece_h, index))
    return LayoutInfo(page_w, page_h, piece_w, piece_h, columns, rows, len(placements), placements)

def apply_numbering(rows: list[dict[str, str]], settings: NumberingSettings) -> list[dict[str, str]]:
    if not settings.enabled:
        return [dict(row) for row in rows]
    count = settings.count if settings.count > 0 else len(rows)
    if count <= 0:
        return [dict(row) for row in rows]
    result = [dict(row) for row in rows[:count]]
    if len(result) < count:
        result.extend({} for _ in range(count - len(result)))
    for index, row in enumerate(result):
        value = settings.start + index * settings.step
        number = str(value).zfill(settings.digits) if settings.digits > 0 else str(value)
        number = f"{settings.prefix}{number}{settings.suffix}"
        if settings.override_existing or row.get(settings.field_name) in (None, ""):
            row[settings.field_name] = number
    return result

def prepare_rows(rows: list[dict[str, str]], settings: ExportSettings) -> list[dict[str, str]]:
    prepared = apply_numbering(rows, settings.numbering)
    if not settings.numbering.enabled:
        for index, row in enumerate(prepared, start=1):
            row.setdefault("numero", str(index))
    return prepared

def paginate_rows(rows: list[dict[str, str]], slots_per_page: int, order_mode: OrderMode) -> list[list[dict[str, str] | None]]:
    if slots_per_page <= 0:
        raise ValueError("La pieza no entra en la hoja con los márgenes y separaciones configurados.")
    if not rows:
        return []
    page_count = ceil(len(rows) / slots_per_page)
    pages: list[list[dict[str, str] | None]] = [[None for _ in range(slots_per_page)] for _ in range(page_count)]
    if order_mode == OrderMode.CUT_STACK:
        for slot_index in range(slots_per_page):
            for page_index in range(page_count):
                source_index = slot_index * page_count + page_index
                if source_index < len(rows):
                    pages[page_index][slot_index] = rows[source_index]
    else:
        for source_index, row in enumerate(rows):
            pages[source_index // slots_per_page][source_index % slots_per_page] = row
    return pages

def build_imposed_pages(image_path: str | Path, rows: list[dict[str, str]], settings: ExportSettings) -> tuple[LayoutInfo, list[list[dict[str, str] | None]], list[dict[str, str]]]:
    with Image.open(image_path) as image:
        layout = compute_layout(settings, image.size)
    prepared = prepare_rows(rows, settings)
    return layout, paginate_rows(prepared, layout.slots_per_page, settings.order_mode), prepared

def render_imposed_page(image_path: str | Path, fields: Iterable[TextField], layout: LayoutInfo, page_items: list[dict[str, str] | None]) -> Image.Image:
    page = Image.new("RGBA", (layout.page_width, layout.page_height), "white")
    for placement, item in zip(layout.placements, page_items):
        if item is None:
            continue
        rendered = render_template(image_path, fields, item)
        if rendered.size != (layout.piece_width, layout.piece_height):
            rendered = rendered.resize((layout.piece_width, layout.piece_height), Image.Resampling.LANCZOS)
        page.alpha_composite(rendered.convert("RGBA"), (placement.x, placement.y))
    return page

def _fit_count(available: int, item: int, gap: int) -> int:
    if item <= 0 or available < item:
        return 0
    return (available + gap) // (item + gap)
