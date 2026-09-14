from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageColor, ImageDraw, ImageOps

from .models import GraphicElement, ImageElement, ShapeElement


def render_graphics(image: Image.Image, elements: Iterable[GraphicElement]) -> Image.Image:
    """Composite visible graphic elements on a copy of *image* in z-order."""
    result = image.convert("RGBA").copy()
    ordered = sorted(enumerate(elements), key=lambda item: (item[1].z_index, item[0]))
    for _index, element in ordered:
        if not element.visible:
            continue
        if isinstance(element, ImageElement):
            _draw_image(result, element)
        elif isinstance(element, ShapeElement):
            _draw_shape(result, element)
    return result


def _draw_image(target: Image.Image, element: ImageElement) -> None:
    path = Path(element.path)
    if not path.exists() or element.width <= 0 or element.height <= 0:
        return
    with Image.open(path) as source:
        source = source.convert("RGBA")
        if element.flip_horizontal:
            source = ImageOps.mirror(source)
        if element.flip_vertical:
            source = ImageOps.flip(source)
        local = _fit_image(source, (element.width, element.height), element.fit_mode)
    _apply_opacity(local, element.opacity)
    _composite(target, local, element.x, element.y, element.width, element.height, element.rotation)


def _draw_shape(target: Image.Image, element: ShapeElement) -> None:
    if element.width <= 0 or element.height <= 0:
        return
    local = Image.new("RGBA", (element.width, element.height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(local)
    fill = ImageColor.getrgb(element.fill_color) + (255,)
    stroke = ImageColor.getrgb(element.stroke_color) + (255,)
    stroke_width = max(0, int(element.stroke_width))
    box = (0, 0, max(0, element.width - 1), max(0, element.height - 1))
    if element.shape_type == "ellipse":
        draw.ellipse(box, fill=fill, outline=stroke if stroke_width else None, width=stroke_width)
    else:
        radius = max(0, min(int(element.corner_radius), element.width // 2, element.height // 2))
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=stroke if stroke_width else None, width=stroke_width)
    _apply_opacity(local, element.opacity)
    _composite(target, local, element.x, element.y, element.width, element.height, element.rotation)


def _fit_image(source: Image.Image, size: tuple[int, int], mode: str) -> Image.Image:
    width, height = max(1, size[0]), max(1, size[1])
    if mode == "stretch":
        return source.resize((width, height), Image.Resampling.LANCZOS)
    if mode == "contain":
        contained = ImageOps.contain(source, (width, height), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        canvas.alpha_composite(contained, ((width - contained.width) // 2, (height - contained.height) // 2))
        return canvas
    return ImageOps.fit(source, (width, height), Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def _composite(target: Image.Image, local: Image.Image, x: int, y: int, width: int, height: int, rotation: float) -> None:
    content = local
    px, py = int(x), int(y)
    if rotation:
        content = local.rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC)
        px = int(x + (width - content.width) / 2)
        py = int(y + (height - content.height) / 2)
    target.alpha_composite(content, (px, py))


def _apply_opacity(layer: Image.Image, opacity: float) -> None:
    opacity = max(0.0, min(1.0, float(opacity)))
    if opacity >= 0.999:
        return
    alpha = layer.getchannel("A").point(lambda value: int(value * opacity))
    layer.putalpha(alpha)
