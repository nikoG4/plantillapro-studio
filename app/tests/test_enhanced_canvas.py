from __future__ import annotations

from pathlib import Path

from PIL import Image
from PySide6.QtWidgets import QApplication

from app.core.models import ImageElement, ShapeElement
from app.ui.enhanced_canvas_widget import EnhancedCanvasWidget


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_group_align_and_ungroup_commands() -> None:
    _app()
    canvas = EnhancedCanvasWidget()
    a = ShapeElement(id="a", x=10, y=20, width=50, height=40)
    b = ShapeElement(id="b", x=100, y=80, width=70, height=60)
    canvas.set_elements([a, b])
    canvas.selected_ids = {"a", "b"}
    canvas.selected_id = "a"

    canvas.group_selected()
    assert a.group_id
    assert a.group_id == b.group_id

    canvas.align_selected("left")
    assert a.x == b.x == 10

    canvas.ungroup_selected()
    assert a.group_id == ""
    assert b.group_id == ""


def test_image_crop_command_is_non_destructive(tmp_path: Path) -> None:
    _app()
    image_path = tmp_path / "photo.png"
    Image.new("RGB", (200, 100), "blue").save(image_path)
    canvas = EnhancedCanvasWidget()
    element = ImageElement(id="img", path=str(image_path))
    canvas.set_elements([element])
    canvas.select_id("img")
    canvas.crop_selected_image(0.1, 0.2, 0.15, 0.05)
    assert (element.crop_left, element.crop_top, element.crop_right, element.crop_bottom) == (0.1, 0.2, 0.15, 0.05)
    assert Image.open(image_path).size == (200, 100)


def test_rotation_handle_exists_for_selected_object() -> None:
    _app()
    canvas = EnhancedCanvasWidget()
    item = ShapeElement(id="shape", x=50, y=60, width=200, height=100)
    canvas.set_elements([item])
    canvas.select_id("shape")
    handles = canvas._handle_rects(item, 10)
    assert "rotate" in handles
    assert handles["rotate"].center().y() < item.y
