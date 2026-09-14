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


class FillMode(str, Enum):
    GRID = "grid"
    VERTICAL_ONLY = "vertical_only"


class OrderMode(str, Enum):
    NORMAL = "normal"
    CUT_STACK = "cut_stack"


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
    opacity: float = 1.0
    locked: bool = False
    visible: bool = True
    z_index: int = 100


@dataclass
class ImageElement:
    id: str
    name: str = "imagen"
    path: str = ""
    x: int = 0
    y: int = 0
    width: int = 300
    height: int = 300
    rotation: float = 0.0
    opacity: float = 1.0
    locked: bool = False
    visible: bool = True
    z_index: int = 10
    fit_mode: str = "cover"  # cover | contain | stretch
    flip_horizontal: bool = False
    flip_vertical: bool = False
    kind: str = "image"


@dataclass
class ShapeElement:
    id: str
    name: str = "forma"
    shape_type: str = "rectangle"  # rectangle | ellipse
    x: int = 0
    y: int = 0
    width: int = 300
    height: int = 180
    rotation: float = 0.0
    opacity: float = 1.0
    locked: bool = False
    visible: bool = True
    z_index: int = 20
    fill_color: str = "#ffffff"
    stroke_color: str = "#111827"
    stroke_width: int = 2
    corner_radius: int = 0
    kind: str = "shape"


GraphicElement = ImageElement | ShapeElement
EditorElement = TextField | GraphicElement


@dataclass
class NumberingSettings:
    enabled: bool = False
    start: int = 1
    count: int = 100
    step: int = 1
    digits: int = 0
    field_name: str = "numero"
    prefix: str = ""
    suffix: str = ""
    override_existing: bool = False


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
    use_original_piece_size: bool = True
    piece_width_mm: float = 50.0
    piece_height_mm: float = 30.0
    margin_left_mm: float = 5.0
    margin_top_mm: float = 5.0
    margin_right_mm: float = 5.0
    margin_bottom_mm: float = 5.0
    gap_x_mm: float = 2.0
    gap_y_mm: float = 2.0
    fill_mode: FillMode = FillMode.GRID
    order_mode: OrderMode = OrderMode.NORMAL
    numbering: NumberingSettings = field(default_factory=NumberingSettings)


@dataclass
class TemplateProject:
    image_path: str = ""
    image_width: int = 0
    image_height: int = 0
    fields: list[TextField] = field(default_factory=list)
    elements: list[GraphicElement] = field(default_factory=list)
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


def _graphic_element_from_dict(raw: dict[str, Any]) -> GraphicElement:
    data = dict(raw or {})
    kind = str(data.get("kind", "shape")).lower()
    if kind == "image":
        allowed = set(ImageElement.__dataclass_fields__)
        return ImageElement(**{k: v for k, v in data.items() if k in allowed})
    allowed = set(ShapeElement.__dataclass_fields__)
    return ShapeElement(**{k: v for k, v in data.items() if k in allowed})


def project_from_dict(raw: dict[str, Any]) -> TemplateProject:
    export_raw = dict(raw.get("export", {}) or {})
    if "page_size" in export_raw:
        export_raw["page_size"] = PageSize(export_raw["page_size"])
    if "fill_mode" in export_raw:
        export_raw["fill_mode"] = FillMode(export_raw["fill_mode"])
    if "order_mode" in export_raw:
        export_raw["order_mode"] = OrderMode(export_raw["order_mode"])
    export_raw["numbering"] = NumberingSettings(**dict(export_raw.get("numbering", {}) or {}))

    fields: list[TextField] = []
    for item in raw.get("fields", []) or []:
        style_raw = dict(item.get("style", {}) or {})
        if style_raw.get("uppercase") and "text_case" not in style_raw:
            style_raw["text_case"] = "upper"
        style = FieldStyle(**style_raw)
        data = {k: v for k, v in item.items() if k != "style"}
        allowed = set(TextField.__dataclass_fields__) - {"style"}
        fields.append(TextField(**{k: v for k, v in data.items() if k in allowed}, style=style))

    elements = [_graphic_element_from_dict(item) for item in (raw.get("elements", []) or [])]
    return TemplateProject(
        image_path=raw.get("image_path", ""),
        image_width=int(raw.get("image_width", 0) or 0),
        image_height=int(raw.get("image_height", 0) or 0),
        fields=fields,
        elements=elements,
        data=list(raw.get("data", []) or []),
        export=ExportSettings(**export_raw),
    )
