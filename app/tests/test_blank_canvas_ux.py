from __future__ import annotations

from pathlib import Path

from PIL import Image
from PySide6.QtWidgets import QApplication

from app.core.document_base import document_base_path
from app.core.models import DocumentSettings, ShapeElement, TemplateProject, project_from_dict, project_to_dict
from app.ui.new_document_dialog import DocumentChoice
from app.ui.studio_main_window import StudioMainWindow


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_blank_document_round_trip_and_materialization() -> None:
    project = TemplateProject(document=DocumentSettings(
        width=640, height=360, background_color="#123456", transparent=False, preset="custom"
    ))
    project.image_width = 640
    project.image_height = 360
    restored = project_from_dict(project_to_dict(project))
    assert restored.image_path == ""
    assert restored.document.width == 640
    assert restored.document.height == 360
    assert restored.document.background_color == "#123456"

    path = Path(document_base_path(restored))
    assert path.exists()
    with Image.open(path).convert("RGBA") as image:
        assert image.size == (640, 360)
        assert image.getpixel((10, 10)) == (18, 52, 86, 255)


def test_transparent_document_materializes_alpha() -> None:
    project = TemplateProject(document=DocumentSettings(width=320, height=200, transparent=True))
    path = Path(document_base_path(project))
    with Image.open(path).convert("RGBA") as image:
        assert image.getpixel((20, 20))[3] == 0


def test_studio_window_can_design_without_background_image() -> None:
    app = _app()
    window = StudioMainWindow()
    try:
        window.create_blank_document(DocumentChoice(800, 500, "#ffffff", False, "custom"))
        assert window.project.image_path == ""
        assert window.canvas.image_size == (800, 500)
        assert window.pages.currentWidget() is window.design_page

        window.canvas.add_shape("rectangle")
        app.processEvents()
        window._sync_fields()
        assert len(window.project.elements) == 1
        assert window._validate(require_output=False) is True

        window.show_production()
        assert window.pages.currentWidget() is window.production_page
        window.show_design()
        assert window.pages.currentWidget() is window.design_page
    finally:
        window.close()
