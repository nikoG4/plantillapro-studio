from __future__ import annotations
from io import BytesIO
from pathlib import Path
from typing import Callable, Iterable
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from .imposition import build_imposed_pages, render_imposed_page
from .models import ExportSettings, TextField
POINTS_PER_INCH = 72

def export_pdf(image_path: str | Path, fields: Iterable[TextField], rows: list[dict[str, str]], settings: ExportSettings, output_path: str | Path, progress: Callable[[int, int], None] | None = None, should_cancel: Callable[[], bool] | None = None) -> int:
    layout, pages, _ = build_imposed_pages(image_path, rows, settings)
    page_w = layout.page_width / settings.dpi * POINTS_PER_INCH
    page_h = layout.page_height / settings.dpi * POINTS_PER_INCH
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(output_path), pagesize=(page_w, page_h))
    count = 0
    for page_items in pages:
        if should_cancel and should_cancel():
            break
        rendered = render_imposed_page(image_path, fields, layout, page_items).convert("RGB")
        buffer = BytesIO()
        rendered.save(buffer, format="PNG" if settings.max_quality_pdf else "JPEG", quality=settings.jpeg_quality)
        buffer.seek(0)
        pdf.drawImage(ImageReader(buffer), 0, 0, width=page_w, height=page_h, preserveAspectRatio=False)
        pdf.showPage()
        count += 1
        if progress:
            progress(count, len(pages))
    pdf.save()
    return count
