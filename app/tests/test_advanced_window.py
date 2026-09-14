from __future__ import annotations

from PySide6.QtWidgets import QApplication

from app.ui.advanced_main_window import AdvancedMainWindow
from app.ui.advanced_canvas_widget import AdvancedCanvasWidget


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_advanced_window_starts_with_multilayer_canvas() -> None:
    app = _app()
    window = AdvancedMainWindow()
    try:
        assert isinstance(window.canvas, AdvancedCanvasWidget)
        assert window.project.elements == []
        assert window.layers is not None
        window.canvas.add_shape("rectangle")
        app.processEvents()
        assert len(window.canvas.elements) == 1
        assert len(window.project.elements) == 1
    finally:
        window.close()
