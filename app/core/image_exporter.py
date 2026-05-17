from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

from .filename_utils import sanitize_filename, unique_path
from .models import ExportSettings, TextField
from .renderer import render_template, render_text_template


def export_images(
    image_path: str | Path,
    fields: Iterable[TextField],
    rows: list[dict[str, str]],
    settings: ExportSettings,
    output_folder: str | Path,
    progress: Callable[[int, int], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> list[Path]:
    folder = Path(output_folder)
    folder.mkdir(parents=True, exist_ok=True)
    ext = ".jpg" if settings.image_format.upper() in {"JPG", "JPEG"} else ".png"
    written: list[Path] = []
    for index, row in enumerate(rows, start=1):
        if should_cancel and should_cancel():
            break
        item = dict(row)
        item.setdefault("numero", str(index))
        name = render_text_template(settings.filename_pattern, item, index)
        path = unique_path(folder / f"{sanitize_filename(name)}{ext}")
        image = render_template(image_path, fields, item)
        if ext == ".jpg":
            image.convert("RGB").save(path, quality=settings.jpeg_quality)
        else:
            image.save(path)
        written.append(path)
        if progress:
            progress(len(written), len(rows))
    return written

