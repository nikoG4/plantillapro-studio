from __future__ import annotations

from pathlib import Path

from PIL import Image
from PySide6.QtWidgets import QApplication

from app.core.models import ShapeElement
from app.ui.pro_main_window import ProMainWindow


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_static_shape_only_design_is_valid(tmp_path: Path) -> None:
    _app()
    base_path = tmp_path / "base.png"
    Image.new("RGB", (800, 500), "white").save(base_path)
    window = ProMainWindow()
    try:
        shape = ShapeElement(id="shape", x=40, y=40, width=200, height=120)
        window.project.image_path = str(base_path)
        window.project.image_width = 800
        window.project.image_height = 500
        window.canvas.load_image(str(base_path))
        window.canvas.set_document([], [shape])
        window.canvas.select_id("shape")
        window._sync_fields()
        assert window._table_rows() == [{}]
        assert window._validate(require_output=False) is True
        assert window.graphic_properties.element is shape

        window.graphic_properties.x.setValue(77)
        window.graphic_properties.opacity.setValue(0.65)
        window.graphic_properties.fill.setText("#ff0000")
        assert shape.x == 77
        assert shape.opacity == 0.65
        assert shape.fill_color == "#ff0000"
    finally:
        window.close()
