from __future__ import annotations

from pathlib import Path

from PIL import Image
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.ui.canvas_widget import CanvasWidget


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _point(widget: CanvasWidget, x: int, y: int) -> QPoint:
    return QPoint(int(widget.offset.x() + x * widget.scale), int(widget.offset.y() + y * widget.scale))


def test_canvas_mouse_moves_and_resizes_field(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = _app()
    image_path = tmp_path / "base.png"
    Image.new("RGB", (800, 500), "white").save(image_path)
    widget = CanvasWidget()
    widget.resize(900, 650)
    widget.show()
    widget.load_image(str(image_path))
    field = widget.add_field()
    field.x, field.y, field.width, field.height = 100, 100, 200, 80
    widget.update()
    app.processEvents()

    QTest.mousePress(widget, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, _point(widget, 150, 130))
    QTest.mouseMove(widget, _point(widget, 250, 200), delay=20)
    QTest.mouseRelease(widget, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, _point(widget, 250, 200))
    assert (field.x, field.y) == (200, 170)

    QTest.mousePress(widget, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, _point(widget, 400, 250))
    QTest.mouseMove(widget, _point(widget, 460, 300), delay=20)
    QTest.mouseRelease(widget, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, _point(widget, 460, 300))
    assert field.width >= 250
    assert field.height >= 120
