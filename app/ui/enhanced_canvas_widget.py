from __future__ import annotations

import math
import uuid

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPixmap

from app.core.editor_ops import Bounds, align_items, distribute_items, snap_delta
from app.core.models import ImageElement, TextField
from app.ui.advanced_canvas_widget import AdvancedCanvasWidget


class EnhancedCanvasWidget(AdvancedCanvasWidget):
    """Advanced canvas with guides, snapping, grouping and direct rotation."""

    def __init__(self) -> None:
        super().__init__()
        self._guides: list[tuple[str, float]] = []
        self._rotation_start_angle = 0.0
        self._rotation_start_value = 0.0

    def select_id(self, element_id: str, additive: bool = False) -> None:
        item = self._find(element_id)
        if not item:
            return
        group_id = getattr(item, "group_id", "")
        group_ids = {candidate.id for candidate in self.all_items() if group_id and getattr(candidate, "group_id", "") == group_id}
        targets = group_ids or {element_id}
        if additive:
            if targets.issubset(self.selected_ids):
                self.selected_ids -= targets
            else:
                self.selected_ids |= targets
        else:
            self.selected_ids = set(targets)
        self.selected_id = element_id if element_id in self.selected_ids else next(iter(self.selected_ids), None)
        self._emit_selection()
        self.update()

    def _select_only(self, element_id: str) -> None:
        item = self._find(element_id)
        group_id = getattr(item, "group_id", "") if item else ""
        if group_id:
            self.selected_ids = {candidate.id for candidate in self.all_items() if getattr(candidate, "group_id", "") == group_id}
        else:
            self.selected_ids = {element_id}
        self.selected_id = element_id
        self._emit_selection()
        self.update()

    def group_selected(self) -> None:
        items = self._selected_items()
        if len(items) < 2:
            return
        self._checkpoint()
        group_id = str(uuid.uuid4())
        for item in items:
            item.group_id = group_id
        self.fieldsChanged.emit()
        self.update()

    def ungroup_selected(self) -> None:
        items = self._selected_items()
        if not items:
            return
        self._checkpoint()
        for item in items:
            item.group_id = ""
        self.fieldsChanged.emit()
        self.update()

    def align_selected(self, mode: str) -> None:
        items = [item for item in self._selected_items() if not item.locked]
        if len(items) < 2:
            return
        self._checkpoint()
        align_items(items, mode)
        self.fieldsChanged.emit()
        self.update()

    def distribute_selected(self, axis: str) -> None:
        items = [item for item in self._selected_items() if not item.locked]
        if len(items) < 3:
            return
        self._checkpoint()
        distribute_items(items, axis)
        self.fieldsChanged.emit()
        self.update()

    def crop_selected_image(self, left: float, top: float, right: float, bottom: float) -> None:
        item = self.selected_element()
        if not isinstance(item, ImageElement):
            return
        self._checkpoint()
        item.crop_left = max(0.0, min(0.95, left))
        item.crop_top = max(0.0, min(0.95, top))
        item.crop_right = max(0.0, min(0.95, right))
        item.crop_bottom = max(0.0, min(0.95, bottom))
        self.fieldsChanged.emit()
        self.update()

    def reset_crop(self) -> None:
        self.crop_selected_image(0.0, 0.0, 0.0, 0.0)

    def _handle_rects(self, item: object, size: float = 0.1) -> dict[str, QRectF]:
        handles = super()._handle_rects(item, size)
        rotate_offset = 32 / max(self.scale, 0.05)
        rotate_size = max(size, 16 / max(self.scale, 0.05))
        cx = item.x + item.width / 2
        cy = item.y - rotate_offset
        handles["rotate"] = QRectF(cx - rotate_size / 2, cy - rotate_size / 2, rotate_size, rotate_size)
        return handles

    def _paint_selection(self, painter: QPainter, item: object) -> None:
        super()._paint_selection(painter, item)
        if item.id != self.selected_id or getattr(item, "locked", False):
            return
        cx = item.x + item.width / 2
        top = item.y
        rotate_y = item.y - 32 / max(self.scale, 0.05)
        painter.setPen(QPen(QColor("#e11d48"), max(1, int(2 / self.scale))))
        painter.drawLine(QPointF(cx, top), QPointF(cx, rotate_y))
        painter.setBrush(QColor("#ffffff"))
        radius = 6 / max(self.scale, 0.05)
        painter.drawEllipse(QPointF(cx, rotate_y), radius, radius)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if not self._guides or not self._pixmap:
            return
        painter = QPainter(self)
        painter.save()
        painter.translate(self.offset)
        painter.scale(self.scale, self.scale)
        painter.setPen(QPen(QColor("#06b6d4"), max(1, int(1 / self.scale)), Qt.PenStyle.DashLine))
        width, height = self.image_size
        for orientation, value in self._guides:
            if orientation == "v":
                painter.drawLine(QPointF(value, 0), QPointF(value, height))
            else:
                painter.drawLine(QPointF(0, value), QPointF(width, value))
        painter.restore()

    def _paint_item(self, painter: QPainter, item: object) -> None:
        if not isinstance(item, ImageElement):
            super()._paint_item(painter, item)
            return
        pixmap = self._image_pixmap(item.path)
        if not pixmap:
            return
        left = max(0.0, min(0.95, item.crop_left))
        top = max(0.0, min(0.95, item.crop_top))
        right = max(0.0, min(0.95, item.crop_right))
        bottom = max(0.0, min(0.95, item.crop_bottom))
        sx = round(pixmap.width() * left)
        sy = round(pixmap.height() * top)
        sw = max(1, round(pixmap.width() * (1 - left - right)))
        sh = max(1, round(pixmap.height() * (1 - top - bottom)))
        cropped = pixmap.copy(sx, sy, sw, sh)
        rect = QRectF(item.x, item.y, item.width, item.height)
        painter.save()
        painter.setOpacity(max(0.0, min(1.0, item.opacity)))
        if item.rotation:
            center = rect.center()
            painter.translate(center)
            painter.rotate(-item.rotation)
            painter.translate(-center)
        painter.drawPixmap(rect.toRect(), cropped)
        painter.restore()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        if self._mode == "resize" and self._resize_handle == "rotate":
            item = self.selected_element()
            if item:
                center = QPointF(item.x + item.width / 2, item.y + item.height / 2)
                self._rotation_start_angle = math.atan2(self._start.y() - center.y(), self._start.x() - center.x())
                self._rotation_start_value = item.style.rotation if isinstance(item, TextField) else item.rotation
                self._mode = "rotate"

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._mode == "rotate":
            item = self.selected_element()
            if not item:
                return
            pos = self._to_image(event.position())
            center = QPointF(item.x + item.width / 2, item.y + item.height / 2)
            angle = math.atan2(pos.y() - center.y(), pos.x() - center.x())
            value = self._rotation_start_value + math.degrees(angle - self._rotation_start_angle)
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                value = round(value / 15) * 15
            if isinstance(item, TextField):
                item.style.rotation = value
            else:
                item.rotation = value
            self.statusChanged.emit(f"Rotación: {value:.1f}°")
            self.fieldsChanged.emit()
            self.update()
            return

        if self._mode == "move":
            pos = self._to_image(event.position())
            selected = [item for item in self._selected_items() if not item.locked]
            if not selected:
                return
            min_x = min(self._move_origins[item.id][0] for item in selected)
            min_y = min(self._move_origins[item.id][1] for item in selected)
            max_x = max(self._move_origins[item.id][0] + item.width for item in selected)
            max_y = max(self._move_origins[item.id][1] + item.height for item in selected)
            start_bounds = Bounds(min_x, min_y, max_x, max_y)
            dx = pos.x() - self._start.x()
            dy = pos.y() - self._start.y()
            other_items = [item for item in self.all_items() if item.id not in self.selected_ids and item.visible]
            dx, dy, self._guides = snap_delta(start_bounds, dx, dy, self.image_size, other_items, max(3, 7 / self.scale))
            for item in selected:
                ox, oy = self._move_origins[item.id]
                item.x = round(ox + dx)
                item.y = round(oy + dy)
            active = self.selected_element()
            if active:
                self.fieldSelected.emit(active)
                self.statusChanged.emit(f"x={active.x}, y={active.y}, ancho={active.width}, alto={active.height}")
            self.fieldsChanged.emit()
            self.update()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        was_rotate = self._mode == "rotate"
        if was_rotate:
            self.fieldsChanged.emit()
            self._mode = "idle"
            self._resize_handle = ""
            self._start_rect = None
            self._move_origins = {}
        else:
            super().mouseReleaseEvent(event)
        self._guides = []
        self.update()
