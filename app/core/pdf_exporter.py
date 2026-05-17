from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Callable, Iterable

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .models import ExportSettings, PageSize, TextField
from .renderer import render_template

POINTS_PER_INCH = 72


def page_pixels(settings: ExportSettings, image_size: tuple[int, int]) -> tuple[int, int]:
    dpi = max(1, settings.dpi)
    sizes_in = {
        PageSize.A4_PORTRAIT: (8.2677, 11.6929),
        PageSize.A4_LANDSCAPE: (11.6929, 8.2677),
        PageSize.LETTER_PORTRAIT: (8.5, 11),
        PageSize.LETTER_LANDSCAPE: (11, 8.5),
    }
    if settings.page_size == PageSize.CUSTOM and settings.custom_width_px and settings.custom_height_px:
        return settings.custom_width_px, settings.custom_height_px
    if settings.page_size in sizes_in:
        w, h = sizes_in[settings.page_size]
        return int(w * dpi), int(h * dpi)
    return image_size


def export_pdf(
    image_path: str | Path,
    fields: Iterable[TextField],
    rows: list[dict[str, str]],
    settings: ExportSettings,
    output_path: str | Path,
    progress: Callable[[int, int], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> int:
    image = Image.open(image_path)
    target_px = page_pixels(settings, image.size)
    page_w = target_px[0] / settings.dpi * POINTS_PER_INCH
    page_h = target_px[1] / settings.dpi * POINTS_PER_INCH
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=(page_w, page_h))
    count = 0
    for index, row in enumerate(rows, start=1):
        if should_cancel and should_cancel():
            break
        item = dict(row)
        item.setdefault("numero", str(index))
        rendered = render_template(image_path, fields, item).convert("RGB")
        if rendered.size != target_px:
            rendered.thumbnail(target_px, Image.Resampling.LANCZOS)
            page = Image.new("RGB", target_px, "white")
            page.paste(rendered, ((target_px[0] - rendered.width) // 2, (target_px[1] - rendered.height) // 2))
            rendered = page
        buffer = BytesIO()
        rendered.save(buffer, format="PNG" if settings.max_quality_pdf else "JPEG", quality=settings.jpeg_quality)
        buffer.seek(0)
        pdf.drawImage(ImageReader(buffer), 0, 0, width=page_w, height=page_h, preserveAspectRatio=False)
        pdf.showPage()
        count += 1
        if progress:
            progress(count, len(rows))
    pdf.save()
    return count

