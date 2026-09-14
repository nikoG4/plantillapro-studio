from __future__ import annotations

from pathlib import Path

from PIL import Image
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.core.models import ShapeElement
from app.ui.enhanced_canvas_widget import EnhancedCanvasWidget


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _point(widget: EnhancedCanvasWidget, x: float, y: float) -> QPoint:
    return QPoint(round(widget.offset.x() + x * widget.scale), round(widget.offset.y() + y * widget.scale))


def test_drag_snaps_to_canvas_center_then_rotate_and_undo(tmp_path: Path) -> None:
    app = _app()
    image_path = tmp_path / "base.png"
    Image.new("RGB", (600, 400), "white").save(image_path)

    widget = EnhancedCanvasWidget()
    widget.resize(820, 600)
    widget.show()
    widget.load_image(str(image_path))
    shape = ShapeElement(id="shape", x=50, y=80, width=100, height=80)
    widget.set_elements([shape])
    widget.select_id("shape")
    app.processEvents()

    # Drag the object's center close to the canvas horizontal center (x=300).
    QTest.mousePress(widget, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, _point(widget, 100, 120))
    QTest.mouseMove(widget, _point(widget, 299, 120), delay=20)
    QTest.mouseRelease(widget, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, _point(widget, 299, 120))
    assert shape.x + shape.width / 2 == 300

    # Use the rotation handle above the selected object and rotate about 90 degrees.
    rotate_x = shape.x + shape.width / 2
    rotate_y = shape.y - 32 / widget.scale
    center_y = shape.y + shape.height / 2
    QTest.mousePress(widget, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, _point(widget, rotate_x, rotate_y))
    QTest.mouseMove(widget, _point(widget, rotate_x + 80, center_y), delay=20)
    QTest.mouseRelease(widget, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, _point(widget, rotate_x + 80, center_y))
    assert 80 <= abs(shape.rotation) <= 100

    QTest.keyClick(widget, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    restored = widget.elements[0]
    assert abs(restored.rotation) < 0.01
    widget.close()
