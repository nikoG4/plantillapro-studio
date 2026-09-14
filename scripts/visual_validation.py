from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, ImageDraw, ImageStat
from PySide6.QtWidgets import QApplication

from app.core.document_renderer import render_document
from app.core.imposition import build_imposed_pages, render_imposed_page
from app.core.models import (
    ExportSettings, FieldStyle, FillMode, ImageElement, NumberingSettings,
    OrderMode, PageSize, ShapeElement, TextField,
)
from app.ui.advanced_main_window import AdvancedMainWindow


def _not_blank(path: Path) -> bool:
    with Image.open(path).convert("RGB") as image:
        stat = ImageStat.Stat(image)
        return sum(stat.var) > 20


def main() -> None:
    output = Path("artifacts")
    output.mkdir(exist_ok=True)
    base_path = output / "sample-ticket.png"
    overlay_path = output / "sample-photo.png"

    base = Image.new("RGB", (720, 360), "#f8fafc")
    draw = ImageDraw.Draw(base)
    draw.rounded_rectangle((8, 8, 712, 352), radius=20, outline="#111827", width=5)
    draw.text((40, 35), "PLANTILLAPRO VISUAL CI", fill="#111827")
    draw.line((40, 115, 680, 115), fill="#94a3b8", width=2)
    base.save(base_path)

    photo = Image.new("RGB", (300, 220), "#2563eb")
    photo_draw = ImageDraw.Draw(photo)
    photo_draw.rectangle((150, 0, 299, 219), fill="#f97316")
    photo_draw.ellipse((80, 50, 220, 190), fill="#f8fafc")
    photo.save(overlay_path)

    fields = [
        TextField(
            id="name", name="Nombre", template="{{nombre}}", x=260, y=120,
            width=390, height=90, z_index=20,
            style=FieldStyle(font_size=58, min_font_size=20, color="#0f172a", bold=True),
        )
    ]
    elements = [
        ShapeElement(id="accent", name="Acento", x=35, y=135, width=180, height=130,
                     fill_color="#dbeafe", stroke_color="#2563eb", stroke_width=4,
                     corner_radius=24, rotation=-4, z_index=2),
        ImageElement(id="photo", name="Foto", path=str(overlay_path), x=55, y=150,
                     width=140, height=100, fit_mode="cover", crop_left=0.12,
                     crop_right=0.08, rotation=5, z_index=5),
        ShapeElement(id="badge", name="Badge", shape_type="ellipse", x=560, y=245,
                     width=110, height=70, fill_color="#fef3c7", stroke_color="#d97706",
                     stroke_width=3, opacity=0.9, z_index=30),
    ]
    row = {"nombre": "Lucas Demo"}

    rendered_path = output / "advanced-document.png"
    render_document(base_path, fields, row, elements).convert("RGB").save(rendered_path)

    settings = ExportSettings(
        dpi=150, page_size=PageSize.A4_PORTRAIT, use_original_piece_size=False,
        piece_width_mm=85, piece_height_mm=42.5, margin_left_mm=8, margin_top_mm=8,
        margin_right_mm=8, margin_bottom_mm=8, gap_x_mm=3, gap_y_mm=3,
        fill_mode=FillMode.GRID, order_mode=OrderMode.CUT_STACK,
        numbering=NumberingSettings(enabled=True, start=1, count=24, digits=4),
    )
    layout, pages, _ = build_imposed_pages(base_path, [], settings)
    mapping = []
    for index, page_items in enumerate(pages[:2], start=1):
        render_imposed_page(base_path, fields, layout, page_items, elements).convert("RGB").save(output / f"imposition-page-{index}.png")
        mapping.append([item.get("numero") if item else None for item in page_items])

    app = QApplication.instance() or QApplication([])
    window = AdvancedMainWindow()
    window.resize(1500, 900)
    window.project.image_path = str(base_path)
    window.project.image_width = 720
    window.project.image_height = 360
    window.project.fields = fields
    window.project.elements = elements
    window.project.data = [row]
    window.canvas.load_image(str(base_path))
    window.canvas.set_document(fields, elements)
    window.data_table.set_rows([row])
    window.canvas.select_id("photo")
    window.show()
    app.processEvents()
    ui_path = output / "advanced-editor-ui.png"
    window.grab().save(str(ui_path))
    canvas_path = output / "advanced-editor-canvas.png"
    window.canvas.grab().save(str(canvas_path))
    window.close()
    app.processEvents()

    required = [rendered_path, ui_path, canvas_path, output / "imposition-page-1.png"]
    blank = [path.name for path in required if not path.exists() or path.stat().st_size < 1000 or not _not_blank(path)]
    if blank:
        raise RuntimeError(f"Visual artifacts missing or blank: {blank}")

    manifest = {
        "visual_validation": "passed",
        "artifacts": {path.name: path.stat().st_size for path in required},
        "layout": {"columns": layout.columns, "rows": layout.rows, "slots": layout.slots_per_page},
        "page_order": mapping,
        "features_shown": ["text", "image", "crop", "shape", "rotation", "layers", "selection_handles"],
    }
    (output / "visual-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "page-order.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
