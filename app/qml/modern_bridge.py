from __future__ import annotations

import uuid
from pathlib import Path

from PySide6.QtCore import Property, QUrl, Signal, Slot

from app.core.models import ShapeElement, TextField

from .studio_bridge import StudioBridge


class ModernStudioBridge(StudioBridge):
    """QML-specific view properties layered over the stable StudioBridge model API."""

    backgroundChanged = Signal()

    _SHAPE_PRESETS = {
        "rectangle": {
            "name": "Rectángulo",
            "width": 620,
            "height": 300,
            "corner_radius": 0,
            "fill_color": "#eef2ff",
            "stroke_color": "#c7d2fe",
            "stroke_width": 2,
        },
        "rounded_rectangle": {
            "name": "Rectángulo redondeado",
            "width": 620,
            "height": 300,
            "corner_radius": 48,
            "fill_color": "#eef2ff",
            "stroke_color": "#c7d2fe",
            "stroke_width": 2,
        },
        "ellipse": {
            "name": "Elipse",
            "width": 520,
            "height": 340,
            "corner_radius": 0,
            "fill_color": "#dbeafe",
            "stroke_color": "#93c5fd",
            "stroke_width": 2,
        },
        "circle": {
            "name": "Círculo",
            "width": 360,
            "height": 360,
            "corner_radius": 0,
            "fill_color": "#dcfce7",
            "stroke_color": "#86efac",
            "stroke_width": 2,
        },
        "triangle": {
            "name": "Triángulo",
            "width": 480,
            "height": 420,
            "corner_radius": 0,
            "fill_color": "#fef3c7",
            "stroke_color": "#fbbf24",
            "stroke_width": 3,
        },
        "diamond": {
            "name": "Rombo",
            "width": 420,
            "height": 420,
            "corner_radius": 0,
            "fill_color": "#f3e8ff",
            "stroke_color": "#c084fc",
            "stroke_width": 3,
        },
        "line": {
            "name": "Línea",
            "width": 620,
            "height": 80,
            "corner_radius": 0,
            "fill_color": "#ffffff",
            "stroke_color": "#475569",
            "stroke_width": 8,
        },
    }

    def __init__(self) -> None:
        super().__init__()
        # PySide6 can crash when a subclass Property uses an inherited Signal descriptor
        # directly as its notify signal. Mirror project changes through a local signal.
        self.projectChanged.connect(self.backgroundChanged.emit)

    def _background_source(self) -> str:
        path = (self.project.image_path or "").strip()
        if not path:
            return ""
        candidate = Path(path)
        if not candidate.exists():
            return ""
        return QUrl.fromLocalFile(str(candidate.resolve())).toString()

    backgroundSource = Property(str, _background_source, notify=backgroundChanged)

    @Slot(str)
    def previewSelectedText(self, text: str) -> None:
        """Update static text while typing without rebuilding the whole inspector."""
        item = self._find_item(self._selected_id)
        if isinstance(item, TextField) and not item.is_variable() and item.template != text:
            item.template = text
            # The canvas listens to projectChanged. Avoid selectionChanged here so the
            # TextArea keeps focus/cursor position during continuous typing.
            self.projectChanged.emit()

    @Slot(str)
    def addShape(self, shape_type: str) -> None:
        preset = self._SHAPE_PRESETS.get(shape_type)
        if preset is None:
            return
        width = int(preset["width"])
        height = int(preset["height"])
        shape = ShapeElement(
            id=str(uuid.uuid4()),
            name=str(preset["name"]),
            shape_type=shape_type,
            x=max(20, (self.documentWidth - width) // 2),
            y=max(20, (self.documentHeight - height) // 2),
            width=width,
            height=height,
            corner_radius=int(preset["corner_radius"]),
            fill_color=str(preset["fill_color"]),
            stroke_color=str(preset["stroke_color"]),
            stroke_width=int(preset["stroke_width"]),
            z_index=self._next_z(),
        )
        self.project.elements.append(shape)
        self._select_and_emit(shape.id)

    @Slot(str, float, float)
    def resizeItem(self, item_id: str, width: float, height: float) -> None:
        item = self._find_item(item_id)
        if isinstance(item, ShapeElement) and item.shape_type == "circle":
            size = max(20.0, max(width, height))
            super().resizeItem(item_id, size, size)
            return
        super().resizeItem(item_id, width, height)
