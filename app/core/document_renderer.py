from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image

from .graphic_renderer import render_graphics
from .models import GraphicElement, TextField
from .renderer import _draw_field


def render_document(
    image_path: str | Path,
    fields: Iterable[TextField],
    row: dict[str, str],
    elements: Iterable[GraphicElement] | None = None,
) -> Image.Image:
    """Render text and graphic objects together in their shared z-order."""
    with Image.open(image_path) as source:
        image = source.convert("RGBA")

    ordered: list[tuple[int, int, object]] = []
    graphics = list(elements or [])
    text_fields = list(fields)
    for index, element in enumerate(graphics):
        ordered.append((element.z_index, index, element))
    offset = len(graphics)
    for index, field in enumerate(text_fields):
        ordered.append((field.z_index, offset + index, field))

    for _z, _index, item in sorted(ordered, key=lambda entry: (entry[0], entry[1])):
        if not getattr(item, "visible", True):
            continue
        if isinstance(item, TextField):
            layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
            _draw_field(layer, item, row)
            opacity = max(0.0, min(1.0, float(item.opacity)))
            if opacity < 0.999:
                alpha = layer.getchannel("A").point(lambda value: int(value * opacity))
                layer.putalpha(alpha)
            image.alpha_composite(layer)
        else:
            image = render_graphics(image, [item])
    return image
