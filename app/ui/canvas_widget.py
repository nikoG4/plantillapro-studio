from __future__ import annotations

import uuid
from pathlib import Path

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QAction, QColor, QImage, QMouseEvent, QPainter, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import QMenu, QWidget

from app.core.models import FieldStyle, TextField


class CanvasWidget(QWidget):
    fieldSelected = Signal(object)
    fieldsChanged = Signal()
    statusChanged = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(640, 420)
        self.setMouseTracking(True)
        self.image_path = ""
        self.image_size = (0, 0)
        self._pixmap: QPixmap | None = None
        self.fields: list[TextField] = []
        self.selected_id: str | None = None
        self.scale = 1.0
        self.offset = QPointF(30, 30)
        self._mode = "idle"
        self._resize_handle = ""
        self._start = QPointF()
        self._last = QPointF()
        self._start_rect: QRectF | None = None

    def load_image(self, path: str) -> None:
        image = Image.open(path)
        self.image_size = image.size
        self.image_path = path
        qimage = QImage(ImageQt(image.convert("RGBA")))
        self._pixmap = QPixmap.fromImage(qimage)
        self.fit_to_view()
        self.update()

    def fit_to_view(self) -> None:
        if not self._pixmap:
            return
        w = max(1, self.width() - 60)
        h = max(1, self.height() - 60)
        self.scale = min(w / self._pixmap.width(), h / self._pixmap.height(), 1.0)
        self.offset = QPointF((self.width() - self._pixmap.width() * self.scale) / 2, 25)

    def set_fields(self, fields: list[TextField]) -> None:
        self.fields = fields
        self.selected_id = fields[0].id if fields else None
        self.update()

    def selected_field(self) -> TextField | None:
        return next((f for f in self.fields if f.id == self.selected_id), None)

    def add_field(self) -> TextField:
        field = TextField(id=str(uuid.uuid4()), name="nombre", template="{{nombre}}", x=40, y=40, width=420, height=120)
        self.fields.append(field)
        self.selected_id = field.id
        self.fieldSelected.emit(field)
        self.fieldsChanged.emit()
        self.update()
        return field

    def duplicate_selected(self) -> None:
        src = self.selected_field()
        if not src:
            return
        field = TextField(
            id=str(uuid.uuid4()),
            name=f"{src.name}_copia",
            template=src.template,
            x=src.x + 20,
            y=src.y + 20,
            width=src.width,
            height=src.height,
            style=FieldStyle(**vars(src.style)),
        )
        self.fields.append(field)
        self.selected_id = field.id
        self.fieldSelected.emit(field)
        self.fieldsChanged.emit()
        self.update()

    def delete_selected(self) -> None:
        if not self.selected_id:
            return
        self.fields = [f for f in self.fields if f.id != self.selected_id]
        self.selected_id = self.fields[0].id if self.fields else None
        self.fieldSelected.emit(self.selected_field())
        self.fieldsChanged.emit()
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#f3f4f6"))
        if not self._pixmap:
            painter.setPen(QColor("#6b7280"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Carga una imagen PNG/JPG para comenzar")
            return
        painter.save()
        painter.translate(self.offset)
        painter.scale(self.scale, self.scale)
        painter.drawPixmap(0, 0, self._pixmap)
        for field in self.fields:
            selected = field.id == self.selected_id
            pen = QPen(QColor("#ef4444" if selected else "#2563eb"), max(1, int(2 / self.scale)))
            pen.setStyle(Qt.PenStyle.SolidLine if selected else Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(QColor(37, 99, 235, 25) if selected else QColor(59, 130, 246, 15))
            painter.drawRect(QRectF(field.x, field.y, field.width, field.height))
            if selected:
                painter.setBrush(QColor("#ef4444"))
                handle = 8 / self.scale
                for rect in self._handle_rects(field).values():
                    painter.drawRect(rect.adjusted(-handle / 2, -handle / 2, handle / 2, handle / 2))
        painter.restore()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if not self._pixmap:
            return
        old_scale = self.scale
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale = max(0.05, min(8.0, self.scale * factor))
        cursor = QPointF(event.position())
        image_pos = (cursor - self.offset) / old_scale
        self.offset = cursor - image_pos * self.scale
        self.update()
        self.statusChanged.emit(f"Zoom: {self.scale * 100:.0f}%")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self._show_menu(event.pos())
            return
        if event.button() == Qt.MouseButton.MiddleButton or (event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.SpaceModifier):
            self._mode = "pan"
            self._last = QPointF(event.position())
            return
        if event.button() != Qt.MouseButton.LeftButton or not self._pixmap:
            return
        pos = self._to_image(event.position())
        hit = self._hit_field(pos)
        self._start = pos
        self._last = QPointF(event.position())
        if hit:
            self.selected_id = hit.id
            self.fieldSelected.emit(hit)
            self._start_rect = QRectF(hit.x, hit.y, hit.width, hit.height)
            self._resize_handle = self._handle_at(hit, pos)
            self._mode = "resize" if self._resize_handle else "move"
            self.setCursor(self._cursor_for_handle(self._resize_handle) if self._resize_handle else Qt.CursorShape.SizeAllCursor)
        else:
            field = TextField(id=str(uuid.uuid4()), x=int(pos.x()), y=int(pos.y()), width=1, height=1)
            self.fields.append(field)
            self.selected_id = field.id
            self.fieldSelected.emit(field)
            self._mode = "draw"
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._mode == "pan":
            delta = QPointF(event.position()) - self._last
            self.offset += delta
            self._last = QPointF(event.position())
            self.update()
            return
        field = self.selected_field()
        if field and self._mode == "idle":
            handle = self._handle_at(field, self._to_image(event.position()))
            self.setCursor(self._cursor_for_handle(handle) if handle else Qt.CursorShape.ArrowCursor)
        if not field or self._mode == "idle":
            return
        pos = self._to_image(event.position())
        if self._mode == "draw":
            field.x = int(min(self._start.x(), pos.x()))
            field.y = int(min(self._start.y(), pos.y()))
            field.width = int(abs(pos.x() - self._start.x()))
            field.height = int(abs(pos.y() - self._start.y()))
        elif self._mode == "move" and self._start_rect:
            delta = pos - self._start
            field.x = int(self._start_rect.x() + delta.x())
            field.y = int(self._start_rect.y() + delta.y())
        elif self._mode == "resize" and self._start_rect:
            self._resize_field(field, pos)
        self.statusChanged.emit(f"x={field.x}, y={field.y}, ancho={field.width}, alto={field.height}")
        self.fieldSelected.emit(field)
        self.fieldsChanged.emit()
        self.update()

    def mouseReleaseEvent(self, _event: QMouseEvent) -> None:
        if self._mode in {"draw", "move", "resize"}:
            self.fieldsChanged.emit()
        self._mode = "idle"
        self._resize_handle = ""
        self._start_rect = None

    def _to_image(self, point: QPointF | QPoint) -> QPointF:
        pos = (QPointF(point) - self.offset) / self.scale
        return QPointF(max(0, min(self.image_size[0], pos.x())), max(0, min(self.image_size[1], pos.y())))

    def _hit_field(self, pos: QPointF) -> TextField | None:
        for field in reversed(self.fields):
            if QRectF(field.x, field.y, field.width, field.height).contains(pos):
                return field
        return None

    def _near_resize_handle(self, field: TextField, pos: QPointF) -> bool:
        return bool(self._handle_at(field, pos))

    def _handle_at(self, field: TextField, pos: QPointF) -> str:
        size = 10 / self.scale
        for name, rect in self._handle_rects(field, size).items():
            if rect.contains(pos):
                return name
        return ""

    def _handle_rects(self, field: TextField, size: float | None = None) -> dict[str, QRectF]:
        size = size or 0.1
        x, y, w, h = field.x, field.y, field.width, field.height
        points = {
            "nw": (x, y),
            "n": (x + w / 2, y),
            "ne": (x + w, y),
            "e": (x + w, y + h / 2),
            "se": (x + w, y + h),
            "s": (x + w / 2, y + h),
            "sw": (x, y + h),
            "w": (x, y + h / 2),
        }
        return {name: QRectF(px - size / 2, py - size / 2, size, size) for name, (px, py) in points.items()}

    def _cursor_for_handle(self, handle: str):
        if handle in {"nw", "se"}:
            return Qt.CursorShape.SizeFDiagCursor
        if handle in {"ne", "sw"}:
            return Qt.CursorShape.SizeBDiagCursor
        if handle in {"n", "s"}:
            return Qt.CursorShape.SizeVerCursor
        if handle in {"e", "w"}:
            return Qt.CursorShape.SizeHorCursor
        return Qt.CursorShape.ArrowCursor

    def _resize_field(self, field: TextField, pos: QPointF) -> None:
        if not self._start_rect:
            return
        left = self._start_rect.left()
        top = self._start_rect.top()
        right = self._start_rect.right()
        bottom = self._start_rect.bottom()
        handle = self._resize_handle
        if "w" in handle:
            left = min(pos.x(), right - 8)
        if "e" in handle:
            right = max(pos.x(), left + 8)
        if "n" in handle:
            top = min(pos.y(), bottom - 8)
        if "s" in handle:
            bottom = max(pos.y(), top + 8)
        field.x = int(left)
        field.y = int(top)
        field.width = int(right - left)
        field.height = int(bottom - top)

    def _show_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        add = QAction("Agregar campo", self)
        dup = QAction("Duplicar campo", self)
        delete = QAction("Borrar campo", self)
        fit = QAction("Ajustar a ventana", self)
        add.triggered.connect(self.add_field)
        dup.triggered.connect(self.duplicate_selected)
        delete.triggered.connect(self.delete_selected)
        fit.triggered.connect(lambda: (self.fit_to_view(), self.update()))
        menu.addActions([add, dup, delete, fit])
        menu.exec(self.mapToGlobal(pos))
