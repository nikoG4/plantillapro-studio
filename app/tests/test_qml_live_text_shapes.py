from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QSG_RHI_BACKEND", "software")

from PIL import Image
from PySide6.QtWidgets import QApplication

from app.core.graphic_renderer import render_graphics
from app.core.models import ShapeElement
from app.qml.modern_bridge import ModernStudioBridge
from app.qml.qml_app import _load_qml_source, qml_entrypoint


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_static_text_preview_updates_canvas_model_immediately() -> None:
    _app()
    bridge = ModernStudioBridge()
    bridge.newA4()
    bridge.addStaticText()

    bridge.previewSelectedText("Cambio mientras escribo")

    assert bridge.elements[-1]["text"] == "Cambio mientras escribo"
    assert bridge.project.fields[-1].template == "Cambio mientras escribo"


def test_modern_bridge_adds_shape_palette_types() -> None:
    _app()
    bridge = ModernStudioBridge()
    bridge.newA4()

    expected = [
        "rectangle",
        "rounded_rectangle",
        "ellipse",
        "circle",
        "triangle",
        "diamond",
        "line",
    ]
    for shape_type in expected:
        bridge.addShape(shape_type)

    assert [item.shape_type for item in bridge.project.elements] == expected
    assert bridge.project.elements[-1].name == "Línea"

    circle = next(item for item in bridge.project.elements if item.shape_type == "circle")
    bridge.resizeItem(circle.id, 510, 320)
    assert circle.width == circle.height == 510


def test_extended_shapes_render_to_export_surface() -> None:
    base = Image.new("RGBA", (420, 300), "white")
    shapes = [
        ShapeElement(id="triangle", shape_type="triangle", x=10, y=10, width=100, height=100, fill_color="#f59e0b"),
        ShapeElement(id="diamond", shape_type="diamond", x=130, y=10, width=100, height=100, fill_color="#a855f7"),
        ShapeElement(id="circle", shape_type="circle", x=250, y=10, width=100, height=100, fill_color="#22c55e"),
        ShapeElement(id="line", shape_type="line", x=20, y=170, width=340, height=40, stroke_color="#111827", stroke_width=10),
    ]

    rendered = render_graphics(base, shapes)

    assert rendered.getpixel((60, 70))[:3] != (255, 255, 255)
    assert rendered.getpixel((180, 60))[:3] != (255, 255, 255)
    assert rendered.getpixel((300, 60))[:3] != (255, 255, 255)
    assert rendered.getpixel((200, 190))[:3] != (255, 255, 255)


def test_polished_qml_routes_text_and_shapes_through_modern_components() -> None:
    source = _load_qml_source(qml_entrypoint()).decode("utf-8")

    assert "studio.previewSelectedText(text)" in source
    assert "ShapeToolButton" in source
    assert "ShapePreview" in source
    assert 'tip: "Rectángulo"; onClicked: studio.addRectangle()' not in source
