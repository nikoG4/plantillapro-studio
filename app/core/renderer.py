from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageColor, ImageDraw, ImageFont

from .models import FieldStyle, TextField

VARIABLE_RE = re.compile(r"{{\s*([a-zA-Z0-9_ -]+)\s*}}")


def render_template(image_path: str | Path, fields: Iterable[TextField], row: dict[str, str]) -> Image.Image:
    base = Image.open(image_path).convert("RGBA")
    return render_on_image(base, fields, row)


def render_on_image(base: Image.Image, fields: Iterable[TextField], row: dict[str, str]) -> Image.Image:
    image = base.convert("RGBA").copy()
    for field in fields:
        _draw_field(image, field, row)
    return image


def render_text_template(template: str, row: dict[str, str], numero: int | None = None) -> str:
    data = {str(k): "" if v is None else str(v) for k, v in row.items()}
    if numero is not None:
        data.setdefault("numero", str(numero))

    def replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        return data.get(key, "")

    return VARIABLE_RE.sub(replace, template)


def template_variables(template: str) -> set[str]:
    return {match.group(1).strip() for match in VARIABLE_RE.finditer(template)}


def missing_variables(fields: Iterable[TextField], columns: Iterable[str]) -> set[str]:
    available = set(columns) | {"numero"}
    required: set[str] = set()
    for field in fields:
        required |= template_variables(field.template)
    return required - available


def _draw_field(image: Image.Image, field: TextField, row: dict[str, str]) -> None:
    style = field.style
    text = render_text_template(field.template, row, _safe_num(row))
    if style.text_case == "upper" or style.uppercase:
        text = text.upper()
    elif style.text_case == "lower":
        text = text.lower()
    elif style.text_case == "title":
        text = text.title()
    box = (int(field.x), int(field.y), int(field.x + field.width), int(field.y + field.height))
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font_size = max(style.min_font_size, int(style.font_size))
    font = load_font(style, font_size)
    lines = _layout_text(text, font, field.width - 2 * style.padding, style)
    if style.auto_fit:
        while font_size > style.min_font_size:
            lines = _layout_text(text, font, field.width - 2 * style.padding, style)
            total_height = _text_block_height(lines, font, style)
            max_width = max((_text_size(font, line)[0] for line in lines), default=0)
            if total_height <= field.height - 2 * style.padding and max_width <= field.width - 2 * style.padding:
                break
            font_size -= 1
            font = load_font(style, font_size)
    _draw_lines(draw, box, lines, font, style)
    if style.print_border:
        draw.rectangle(box, outline=style.border_color, width=2)
    if style.rotation:
        crop = layer.crop(box)
        rotated = crop.rotate(style.rotation, expand=True, resample=Image.Resampling.BICUBIC)
        layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        px = field.x + (field.width - rotated.width) // 2
        py = field.y + (field.height - rotated.height) // 2
        layer.alpha_composite(rotated, (int(px), int(py)))
    image.alpha_composite(layer)


def load_font(style: FieldStyle, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if style.font_path:
        candidates.append(style.font_path)
    windir = Path.home().anchor + "Windows/Fonts"
    family = style.font_family.lower().replace(" ", "")
    family_map = {
        "arial": "arialbd.ttf" if style.bold else "arial.ttf",
        "calibri": "calibrib.ttf" if style.bold else "calibri.ttf",
        "segoeui": "segoeuib.ttf" if style.bold else "segoeui.ttf",
        "timesnewroman": "timesbd.ttf" if style.bold else "times.ttf",
        "couriernew": "courbd.ttf" if style.bold else "cour.ttf",
        "verdana": "verdanab.ttf" if style.bold else "verdana.ttf",
        "tahoma": "tahomabd.ttf" if style.bold else "tahoma.ttf",
        "georgia": "georgiab.ttf" if style.bold else "georgia.ttf",
        "trebuchetms": "trebucbd.ttf" if style.bold else "trebuc.ttf",
        "comic sans ms": "comicbd.ttf" if style.bold else "comic.ttf",
        "comicsansms": "comicbd.ttf" if style.bold else "comic.ttf",
    }
    names = [family_map.get(family, ""), "arialbd.ttf" if style.bold else "arial.ttf", "calibri.ttf", "segoeui.ttf"]
    candidates.extend(str(Path(windir) / name) for name in names)
    for path in candidates:
        try:
            if path and Path(path).exists():
                return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _layout_text(text: str, font: ImageFont.ImageFont, max_width: int, style: FieldStyle) -> list[str]:
    if style.single_line:
        return [text.replace("\n", " ")]
    lines: list[str] = []
    for raw_line in text.splitlines() or [""]:
        if not style.word_wrap:
            lines.append(raw_line)
            continue
        words = raw_line.split(" ")
        current = ""
        for word in words:
            trial = word if not current else f"{current} {word}"
            if _text_size(font, trial)[0] <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def _draw_lines(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], lines: list[str], font: ImageFont.ImageFont, style: FieldStyle) -> None:
    x1, y1, x2, y2 = box
    inner_w = max(1, x2 - x1 - 2 * style.padding)
    total_h = _text_block_height(lines, font, style)
    if style.v_align == "top":
        y = y1 + style.padding
    elif style.v_align == "bottom":
        y = y2 - style.padding - total_h
    else:
        y = y1 + ((y2 - y1) - total_h) / 2
    color = ImageColor.getrgb(style.color) + (255,)
    line_step = max(1, int(_text_size(font, "Ag")[1] * style.line_spacing))
    for line in lines:
        width, _ = _text_size(font, line)
        if style.h_align == "left":
            x = x1 + style.padding
        elif style.h_align == "right":
            x = x1 + style.padding + inner_w - width
        else:
            x = x1 + style.padding + (inner_w - width) / 2
        draw.text((int(x), int(y)), line, fill=color, font=font)
        y += line_step


def _text_size(font: ImageFont.ImageFont, text: str) -> tuple[int, int]:
    bbox = font.getbbox(text or " ")
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _text_block_height(lines: list[str], font: ImageFont.ImageFont, style: FieldStyle) -> int:
    if not lines:
        return 0
    line_h = max(1, int(_text_size(font, "Ag")[1] * style.line_spacing))
    return line_h * len(lines)


def _safe_num(row: dict[str, str]) -> int | None:
    value = row.get("numero")
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None
