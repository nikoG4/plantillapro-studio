from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from PIL import Image, ImageColor

from .models import TemplateProject


def document_base_path(project: TemplateProject) -> str:
    """Return the real background image or a cached generated blank canvas PNG."""
    image_path = Path(project.image_path) if project.image_path else None
    if image_path and image_path.exists():
        return str(image_path)

    width, height = project.document_size()
    color = project.document.background_color or "#ffffff"
    transparent = bool(project.document.transparent)
    signature = f"{width}x{height}|{color}|{transparent}".encode("utf-8")
    digest = hashlib.sha1(signature).hexdigest()[:16]
    target = Path(tempfile.gettempdir()) / f"plantillapro-canvas-{digest}.png"
    if target.exists():
        return str(target)

    rgb = ImageColor.getrgb(color)
    rgba = (*rgb, 0 if transparent else 255)
    Image.new("RGBA", (width, height), rgba).save(target)
    return str(target)
