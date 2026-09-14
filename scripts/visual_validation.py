from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, ImageDraw, ImageStat
from PySide6.QtWidgets import QApplication

from app.core.document_base import document_base_path
from app.core.document_renderer import render_document
from app.core.imposition import build_imposed_pages, render_imposed_page
from app.core.models import (
    DocumentSettings, ExportSettings, FieldStyle, FillMode, ImageElement,
    NumberingSettings, OrderMode, PageSize, ShapeElement, TemplateProject, TextField,
)
from app.ui.new_document_dialog import DocumentChoice
from app.ui.studio_main_window import StudioMainWindow


def _not_blank(path: Path) -> bool:
    with Image.open(path).convert("RGB") as image:
        stat = ImageStat.Stat(image)
        return sum(stat.var) > 20


def main() -> None:
    output = Path("artifacts")
    output.mkdir(exist_ok=True)
    overlay_path = output / "sample-photo.png"

    photo = Image.new("RGB", (360, 240), "#dbeafe")
    draw = ImageDraw.Draw(photo)
    draw.rectangle((0, 145, 359, 239), fill="#c08457")
    draw.ellipse((55, 55, 145, 145), fill="#ffffff")
    draw.rectangle((75, 95, 125, 190), fill="#ffffff")
    draw.rectangle((200, 100, 320, 135), fill="#f8fafc")
    draw.rectangle((215, 138, 320, 173), fill="#ffffff")
    photo.save(overlay_path)

    project = TemplateProject(document=DocumentSettings(
        width=720, height=960, background_color="#ffffff", transparent=False, preset="a5"
    ))
    project.image_width = 720
    project.image_height = 960
    fields = [
        TextField(
            id="headline", name="Título", template="Ideas que\nse imprimen", x=75, y=85,
            width=570, height=190, z_index=20,
            style=FieldStyle(font_size=76, min_font_size=28, color="#2563eb", bold=True),
        )
    ]
    elements = [
        ImageElement(id="photo", name="Foto", path=str(overlay_path), x=80, y=330,
                     width=560, height=300, fit_mode="cover", crop_left=0.08,
                     crop_right=0.08, rotation=0, z_index=5),
        ShapeElement(id="badge", name="Mensaje", x=150, y=700, width=420, height=105,
                     fill_color="#eef2ff", stroke_color="#c7d2fe", stroke_width=2,
                     corner_radius=52, z_index=8),
        ShapeElement(id="spark", name="Acento", shape_type="ellipse", x=175, y=730,
                     width=42, height=42, fill_color="#2563eb", stroke_width=0, z_index=9),
    ]
    project.fields = fields
    project.elements = elements
    project.data = [{"nombre": "Ana Torres", "numero": "001"}, {"nombre": "Luis Ramírez", "numero": "002"}]

    base_path = Path(document_base_path(project))
    rendered_path = output / "blank-canvas-document.png"
    render_document(base_path, fields, {}, elements).convert("RGB").save(rendered_path)

    settings = ExportSettings(
        dpi=150, page_size=PageSize.A4_PORTRAIT, use_original_piece_size=False,
        piece_width_mm=70, piece_height_mm=93, margin_left_mm=8, margin_top_mm=8,
        margin_right_mm=8, margin_bottom_mm=8, gap_x_mm=3, gap_y_mm=3,
        fill_mode=FillMode.GRID, order_mode=OrderMode.NORMAL,
        numbering=NumberingSettings(enabled=True, start=1, count=6, digits=3),
    )
    project.export = settings
    layout, pages, _ = build_imposed_pages(base_path, project.data, settings)
    imposed = output / "production-sheet.png"
    render_imposed_page(base_path, fields, layout, pages[0], elements).convert("RGB").save(imposed)

    app = QApplication.instance() or QApplication([])
    window = StudioMainWindow()
    window.resize(1600, 920)
    window.show()
    app.processEvents()

    welcome = output / "ux-welcome.png"
    window.grab().save(str(welcome))

    window.create_blank_document(DocumentChoice(720, 960, "#ffffff", False, "a5"))
    window.project.fields = fields
    window.project.elements = elements
    window.project.data = project.data
    window.project.export = settings
    window.canvas.set_document(fields, elements)
    window.data_table.set_rows(project.data)
    window._load_export_settings()
    window.canvas.select_id("headline")
    window.show_design()
    app.processEvents()
    design = output / "ux-design.png"
    window.grab().save(str(design))
    canvas = output / "ux-design-canvas.png"
    window.canvas.grab().save(str(canvas))

    window.show_production()
    app.processEvents()
    production = output / "ux-production.png"
    window.grab().save(str(production))
    window.close()
    app.processEvents()

    required = [welcome, design, canvas, production, rendered_path, imposed]
    blank = [path.name for path in required if not path.exists() or path.stat().st_size < 1000 or not _not_blank(path)]
    if blank:
        raise RuntimeError(f"Visual artifacts missing or blank: {blank}")

    manifest = {
        "visual_validation": "passed",
        "artifacts": {path.name: path.stat().st_size for path in required},
        "layout": {"columns": layout.columns, "rows": layout.rows, "slots": layout.slots_per_page},
        "features_shown": [
            "welcome_empty_state", "blank_canvas", "design_mode", "production_mode",
            "contextual_properties", "layers", "text", "image", "shape", "imposition",
        ],
    }
    (output / "visual-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
