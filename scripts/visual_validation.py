from __future__ import annotations
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw
from app.core.imposition import build_imposed_pages, render_imposed_page
from app.core.models import ExportSettings, FieldStyle, FillMode, NumberingSettings, OrderMode, PageSize, TextField


def main() -> None:
    output = Path("artifacts")
    output.mkdir(exist_ok=True)
    base_path = output / "sample-ticket.png"
    base = Image.new("RGB", (720, 360), "white")
    draw = ImageDraw.Draw(base)
    draw.rounded_rectangle((8, 8, 712, 352), radius=20, outline="black", width=5)
    draw.text((40, 35), "TALONARIO DE PRUEBA", fill="black")
    draw.line((40, 115, 680, 115), fill="black", width=2)
    draw.text((40, 145), "Numero:", fill="black")
    base.save(base_path)
    fields = [TextField(id="numero", name="numero", template="{{numero}}", x=260, y=125, width=390, height=120, style=FieldStyle(font_size=100, min_font_size=24, auto_fit=True))]
    settings = ExportSettings(
        dpi=150, page_size=PageSize.A4_PORTRAIT, use_original_piece_size=False,
        piece_width_mm=85, piece_height_mm=42.5, margin_left_mm=8, margin_top_mm=8,
        margin_right_mm=8, margin_bottom_mm=8, gap_x_mm=3, gap_y_mm=3,
        fill_mode=FillMode.GRID, order_mode=OrderMode.CUT_STACK,
        numbering=NumberingSettings(enabled=True, start=1, count=24, digits=4),
    )
    layout, pages, _ = build_imposed_pages(base_path, [], settings)
    mapping = []
    for index, page_items in enumerate(pages[:3], start=1):
        render_imposed_page(base_path, fields, layout, page_items).convert("RGB").save(output / f"imposition-page-{index}.png")
        mapping.append([item.get("numero") if item else None for item in page_items])
    (output / "page-order.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    print(f"Generated {len(pages)} pages, {layout.columns}x{layout.rows} pieces per page")

if __name__ == "__main__":
    main()
