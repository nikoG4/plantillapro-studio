from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class PageSize(str, Enum):
    ORIGINAL = "original"
    A4_PORTRAIT = "a4_portrait"
    A4_LANDSCAPE = "a4_landscape"
    LETTER_PORTRAIT = "letter_portrait"
    LETTER_LANDSCAPE = "letter_landscape"
    CUSTOM = "custom"


@dataclass
class FieldStyle:
    font_path: str = ""
    font_family: str = "Arial"
    font_size: int = 72
    min_font_size: int = 12
    color: str = "#000000"
    bold: bool = False
    italic: bool = False
    h_align: str = "center"
    v_align: str = "center"
    line_spacing: float = 1.15
    uppercase: bool = False
    text_case: str = "normal"
    auto_fit: bool = True
    word_wrap: bool = True
    single_line: bool = False
    words_per_line: int = 0
    padding: int = 8
    rotation: float = 0.0
    print_border: bool = False
    border_color: str = "#3b82f6"


@dataclass
class TextField:
    id: str
    name: str = "nombre"
    template: str = "{{nombre}}"
    x: int = 0
    y: int = 0
    width: int = 400
    height: int = 120
    style: FieldStyle = field(default_factory=FieldStyle)


@dataclass
class ExportSettings:
    dpi: int = 300
    page_size: PageSize = PageSize.ORIGINAL
    custom_width_px: int = 0
    custom_height_px: int = 0
    output_pdf: str = ""
    output_folder: str = ""
    image_format: str = "PNG"
    filename_pattern: str = "{{numero}}_{{nombre}}"
    jpeg_quality: int = 95
    max_quality_pdf: bool = True


@dataclass
class TemplateProject:
    image_path: str = ""
    image_width: int = 0
    image_height: int = 0
    fields: list[TextField] = field(default_factory=list)
    data: list[dict[str, str]] = field(default_factory=list)
    export: ExportSettings = field(default_factory=ExportSettings)


def _enum_to_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: _enum_to_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_enum_to_value(v) for v in value]
    return value


def project_to_dict(project: TemplateProject) -> dict[str, Any]:
    return _enum_to_value(asdict(project))


def project_from_dict(raw: dict[str, Any]) -> TemplateProject:
    export_raw = raw.get("export", {}) or {}
    if "page_size" in export_raw:
        export_raw["page_size"] = PageSize(export_raw["page_size"])
    fields: list[TextField] = []
    for item in raw.get("fields", []) or []:
        style_raw = item.get("style", {}) or {}
        if style_raw.get("uppercase") and "text_case" not in style_raw:
            style_raw["text_case"] = "upper"
        style = FieldStyle(**style_raw)
        data = {k: v for k, v in item.items() if k != "style"}
        fields.append(TextField(**data, style=style))
    return TemplateProject(
        image_path=raw.get("image_path", ""),
        image_width=int(raw.get("image_width", 0) or 0),
        image_height=int(raw.get("image_height", 0) or 0),
        fields=fields,
        data=list(raw.get("data", []) or []),
        export=ExportSettings(**export_raw),
    )
