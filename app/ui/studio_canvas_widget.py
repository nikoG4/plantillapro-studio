from __future__ import annotations

import uuid

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap

from app.core.models import TextField
from app.ui.enhanced_canvas_widget import EnhancedCanvasWidget


class StudioCanvasWidget(EnhancedCanvasWidget):
    """Editor canvas that can exist independently from a background image."""

    def __init__(self) -> None:
        super().__init__()
        self.document_background_color = "#ffffff"
        self.document_transparent = False

    def set_blank_document(self, width: int, height: int, color: str = "#ffffff", transparent: bool = False) -> None:
        width = max(1, int(width))
        height = max(1, int(height))
        self.image_path = ""
        self.image_size = (width, height)
        self.document_background_color = color or "#ffffff"
        self.document_transparent = bool(transparent)
        self._pixmap = self._make_document_pixmap(width, height)
        self.fit_to_view()
        self.update()

    def load_image(self, path: str) -> None:
        self.document_transparent = False
        super().load_image(path)

    def add_field(self) -> TextField:
        self._checkpoint()
        field = TextField(
            id=str(uuid.uuid4()), name="Texto fijo", template="Escribe aquí",
            x=40, y=40, width=420, height=120, z_index=self._next_z(),
            text_mode="static",
        )
        self.fields.append(field)
        self._select_only(field.id)
        self.fieldsChanged.emit()
        return field

    def add_variable_field(self) -> TextField:
        self._checkpoint()
        existing = {field.variable_key() for field in self.fields if field.is_variable()}
        base = "campo"
        key = base
        counter = 2
        while key in existing:
            key = f"{base}_{counter}"
            counter += 1
        field = TextField(
            id=str(uuid.uuid4()), name="Campo variable", template="{{" + key + "}}",
            x=60, y=80, width=420, height=120, z_index=self._next_z(),
            text_mode="variable", variable_name=key, source_column=key,
        )
        self.fields.append(field)
        self._select_only(field.id)
        self.fieldsChanged.emit()
        return field

    def set_background_style(self, color: str, transparent: bool) -> None:
        self.document_background_color = color or "#ffffff"
        self.document_transparent = bool(transparent)
        if not self.image_path and self.image_size[0] > 0 and self.image_size[1] > 0:
            self._pixmap = self._make_document_pixmap(*self.image_size)
            self.update()

    def _make_document_pixmap(self, width: int, height: int) -> QPixmap:
        pixmap = QPixmap(width, height)
        if not self.document_transparent:
            pixmap.fill(QColor(self.document_background_color))
            return pixmap

        pixmap.fill(QColor("#ffffff"))
        painter = QPainter(pixmap)
        cell = max(8, min(24, round(min(width, height) / 40)))
        light = QColor("#ffffff")
        dark = QColor("#e5e7eb")
        for y in range(0, height, cell):
            for x in range(0, width, cell):
                painter.fillRect(QRect(x, y, cell, cell), light if ((x // cell + y // cell) % 2 == 0) else dark)
        painter.end()
        return pixmap
