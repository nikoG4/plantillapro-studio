from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image

from .graphic_renderer import render_graphics
from .models import GraphicElement, TextField
from .renderer import render_on_image


def render_document(
    image_path: str | Path,
    fields: Iterable[TextField],
    row: dict[str, str],
    elements: Iterable[GraphicElement] | None = None,
) -> Image.Image:
    """Render the base template, graphic layers, then variable text fields."""
    with Image.open(image_path) as source:
        base = source.convert("RGBA")
    base = render_graphics(base, elements or [])
    return render_on_image(base, fields, row)
