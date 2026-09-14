from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.core.document_renderer import render_document
from app.core.models import ImageElement, ShapeElement, TemplateProject, project_from_dict, project_to_dict


def test_graphic_elements_round_trip() -> None:
    project = TemplateProject(elements=[
        ShapeElement(id="shape-1", name="Marco", fill_color="#ff0000", rotation=12.5, opacity=0.7),
        ImageElement(id="image-1", name="Foto", path="foto.png", fit_mode="contain", flip_horizontal=True),
    ])
    restored = project_from_dict(project_to_dict(project))
    assert len(restored.elements) == 2
    assert isinstance(restored.elements[0], ShapeElement)
    assert restored.elements[0].fill_color == "#ff0000"
    assert restored.elements[0].rotation == 12.5
    assert isinstance(restored.elements[1], ImageElement)
    assert restored.elements[1].fit_mode == "contain"
    assert restored.elements[1].flip_horizontal is True


def test_render_document_composites_shape_and_image(tmp_path: Path) -> None:
    base_path = tmp_path / "base.png"
    overlay_path = tmp_path / "overlay.png"
    Image.new("RGBA", (120, 100), "white").save(base_path)
    Image.new("RGBA", (20, 20), "#0000ff").save(overlay_path)

    elements = [
        ShapeElement(id="shape", x=10, y=10, width=50, height=40, fill_color="#ff0000", stroke_width=0, z_index=1),
        ImageElement(id="image", path=str(overlay_path), x=70, y=20, width=30, height=30, fit_mode="stretch", z_index=2),
    ]
    rendered = render_document(base_path, [], {}, elements)

    assert rendered.getpixel((20, 20))[:3] == (255, 0, 0)
    assert rendered.getpixel((80, 30))[:3] == (0, 0, 255)
    assert rendered.getpixel((110, 90))[:3] == (255, 255, 255)
