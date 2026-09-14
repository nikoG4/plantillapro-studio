from __future__ import annotations

import copy
import uuid
from pathlib import Path

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QImage, QKeyEvent, QMouseEvent, QPainter, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import QWidget

from app.core.models import ImageElement, ShapeElement, TextField


class AdvancedCanvasWidget(QWidget):
    fieldSelected = Signal(object)
    fieldsChanged = Signal()
    selectionChanged = Signal(object)
    statusChanged = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(640, 420)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.image_path = ""
        self.image_size = (0, 0)
        self._pixmap: QPixmap | None = None
        self.fields: list[TextField] = []
        self.elements: list[ImageElement | ShapeElement] = []
        self.selected_ids: set[str] = set()
        self.selected_id: str | None = None
        self.scale = 1.0
        self.offset = QPointF(30, 30)
        self._mode = "idle"
        self._resize_handle = ""
        self._space_pressed = False
        self._start = QPointF()
        self._last = QPointF()
        self._start_rect: QRectF | None = None
        self._move_origins: dict[str, tuple[int, int]] = {}
        self._undo: list[tuple[list[TextField], list[ImageElement | ShapeElement]]] = []
        self._redo: list[tuple[list[TextField], list[ImageElement | ShapeElement]]] = []
        self._clipboard: list[object] = []
        self._image_cache: dict[str, QPixmap] = {}

    def load_image(self, path: str) -> None:
        image = Image.open(path)
        self.image_size = image.size
        self.image_path = path
        self._pixmap = QPixmap.fromImage(QImage(ImageQt(image.convert("RGBA"))))
        self.fit_to_view()
        self.update()

    def fit_to_view(self) -> None:
        if not self._pixmap:
            return
        w = max(1, self.width() - 60)
        h = max(1, self.height() - 60)
        self.scale = min(w / self._pixmap.width(), h / self._pixmap.height(), 1.0)
        self.offset = QPointF((self.width() - self._pixmap.width() * self.scale) / 2, 25)
        self.update()

    def set_fields(self, fields: list[TextField]) -> None:
        self.fields = fields
        self.selected_ids.clear()
        self.selected_id = None
        self.update()

    def set_elements(self, elements: list[ImageElement | ShapeElement]) -> None:
        self.elements = elements
        self.selected_ids.clear()
        self.selected_id = None
        self.update()

    def set_document(self, fields: list[TextField], elements: list[ImageElement | ShapeElement]) -> None:
        self.fields = fields
        self.elements = elements
        self.selected_ids.clear()
        self.selected_id = None
        self.update()

    def all_items(self) -> list[object]:
        items: list[object] = [*self.elements, *self.fields]
        return sorted(items, key=lambda item: (int(getattr(item, "z_index", 0)), self._source_index(item)))

    def selected_element(self):
        return self._find(self.selected_id) if self.selected_id else None

    def selected_field(self) -> TextField | None:
        item = self.selected_element()
        return item if isinstance(item, TextField) else None

    def select_id(self, element_id: str, additive: bool = False) -> None:
        item = self._find(element_id)
        if not item:
            return
        if additive:
            if element_id in self.selected_ids:
                self.selected_ids.remove(element_id)
            else:
                self.selected_ids.add(element_id)
        else:
            self.selected_ids = {element_id}
        self.selected_id = element_id if element_id in self.selected_ids else (next(iter(self.selected_ids), None))
        self._emit_selection()
        self.update()

    def add_field(self) -> TextField:
        self._checkpoint()
        field = TextField(id=str(uuid.uuid4()), name="nombre", template="{{nombre}}", x=40, y=40, width=420, height=120, z_index=self._next_z())
        self.fields.append(field)
        self._select_only(field.id)
        self.fieldsChanged.emit()
        return field

    def add_image(self, path: str) -> ImageElement:
        self._checkpoint()
        width, height = 300, 300
        try:
            with Image.open(path) as image:
                ratio = image.width / max(1, image.height)
                if ratio >= 1:
                    width, height = 320, max(80, round(320 / ratio))
                else:
                    height, width = 320, max(80, round(320 * ratio))
        except OSError:
            pass
        element = ImageElement(id=str(uuid.uuid4()), name=Path(path).stem or "imagen", path=path, x=50, y=50, width=width, height=height, z_index=self._next_z())
        self.elements.append(element)
        self._select_only(element.id)
        self.fieldsChanged.emit()
        return element

    def add_shape(self, shape_type: str = "rectangle") -> ShapeElement:
        self._checkpoint()
        name = "Elipse" if shape_type == "ellipse" else "Rectángulo"
        element = ShapeElement(id=str(uuid.uuid4()), name=name, shape_type=shape_type, x=60, y=60, width=300, height=180, z_index=self._next_z())
        self.elements.append(element)
        self._select_only(element.id)
        self.fieldsChanged.emit()
        return element

    def duplicate_selected(self) -> None:
        items = self._selected_items()
        if not items:
            return
        self._checkpoint()
        new_ids: set[str] = set()
        for item in items:
            clone = copy.deepcopy(item)
            clone.id = str(uuid.uuid4())
            clone.name = f"{clone.name} copia"
            clone.x += 20
            clone.y += 20
            clone.z_index = self._next_z()
            if isinstance(clone, TextField):
                self.fields.append(clone)
            else:
                self.elements.append(clone)
            new_ids.add(clone.id)
        self.selected_ids = new_ids
        self.selected_id = next(iter(new_ids), None)
        self._emit_selection()
        self.fieldsChanged.emit()
        self.update()

    def delete_selected(self) -> None:
        if not self.selected_ids:
            return
        self._checkpoint()
        self.fields = [item for item in self.fields if item.id not in self.selected_ids]
        self.elements = [item for item in self.elements if item.id not in self.selected_ids]
        self.selected_ids.clear()
        self.selected_id = None
        self._emit_selection()
        self.fieldsChanged.emit()
        self.update()

    def copy_selected(self) -> None:
        self._clipboard = [copy.deepcopy(item) for item in self._selected_items()]

    def paste(self) -> None:
        if not self._clipboard:
            return
        self._checkpoint()
        new_ids: set[str] = set()
        for source in self._clipboard:
            clone = copy.deepcopy(source)
            clone.id = str(uuid.uuid4())
            clone.x += 20
            clone.y += 20
            clone.z_index = self._next_z()
            if isinstance(clone, TextField):
                self.fields.append(clone)
            else:
                self.elements.append(clone)
            new_ids.add(clone.id)
        self.selected_ids = new_ids
        self.selected_id = next(iter(new_ids), None)
        self._emit_selection()
        self.fieldsChanged.emit()
        self.update()

    def undo(self) -> None:
        if not self._undo:
            return
        self._redo.append(self._snapshot())
        self._restore(self._undo.pop())

    def redo(self) -> None:
        if not self._redo:
            return
        self._undo.append(self._snapshot())
        self._restore(self._redo.pop())

    def bring_to_front(self) -> None:
        self._set_selected_z(self._next_z())

    def send_to_back(self) -> None:
        self._set_selected_z(self._min_z() - 1)

    def move_layer(self, delta: int) -> None:
        item = self.selected_element()
        if not item:
            return
        self._checkpoint()
        item.z_index += delta
        self.fieldsChanged.emit()
        self.update()

    def toggle_lock(self) -> None:
        item = self.selected_element()
        if item:
            self._checkpoint(); item.locked = not item.locked; self.fieldsChanged.emit(); self._emit_selection(); self.update()

    def toggle_visibility(self) -> None:
        item = self.selected_element()
        if item:
            self._checkpoint(); item.visible = not item.visible; self.fieldsChanged.emit(); self._emit_selection(); self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#eef1f5"))
        if not self._pixmap:
            painter.setPen(QColor("#6b7280")); painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Carga una imagen PNG/JPG para comenzar"); return
        painter.save(); painter.translate(self.offset); painter.scale(self.scale, self.scale)
        painter.drawPixmap(0, 0, self._pixmap)
        for item in self.all_items():
            if not getattr(item, "visible", True):
                continue
            self._paint_item(painter, item)
        for item in self._selected_items():
            self._paint_selection(painter, item)
        painter.restore()

    def _paint_item(self, painter: QPainter, item: object) -> None:
        rect = QRectF(item.x, item.y, item.width, item.height)
        painter.save()
        painter.setOpacity(max(0.0, min(1.0, float(getattr(item, "opacity", 1.0)))))
        rotation = item.style.rotation if isinstance(item, TextField) else getattr(item, "rotation", 0.0)
        if rotation:
            center = rect.center(); painter.translate(center); painter.rotate(-rotation); painter.translate(-center)
        if isinstance(item, ImageElement):
            pixmap = self._image_pixmap(item.path)
            if pixmap:
                painter.drawPixmap(rect.toRect(), pixmap)
        elif isinstance(item, ShapeElement):
            painter.setPen(QPen(QColor(item.stroke_color), max(0, item.stroke_width)))
            painter.setBrush(QColor(item.fill_color))
            if item.shape_type == "ellipse": painter.drawEllipse(rect)
            else: painter.drawRoundedRect(rect, item.corner_radius, item.corner_radius)
        else:
            font = QFont(item.style.font_family); font.setPixelSize(max(6, item.style.font_size)); font.setBold(item.style.bold); font.setItalic(item.style.italic)
            painter.setFont(font); painter.setPen(QColor(item.style.color))
            flags = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap
            painter.drawText(rect.adjusted(item.style.padding, item.style.padding, -item.style.padding, -item.style.padding), int(flags), item.template)
        painter.restore()

    def _paint_selection(self, painter: QPainter, item: object) -> None:
        rect = QRectF(item.x, item.y, item.width, item.height)
        painter.setPen(QPen(QColor("#e11d48"), max(1, int(2 / self.scale)), Qt.PenStyle.SolidLine))
        painter.setBrush(Qt.BrushStyle.NoBrush); painter.drawRect(rect)
        if item.id == self.selected_id and not getattr(item, "locked", False):
            painter.setBrush(QColor("#e11d48"))
            size = 8 / self.scale
            for handle in self._handle_rects(item).values():
                painter.drawRect(handle.adjusted(-size / 2, -size / 2, size / 2, size / 2))

    def wheelEvent(self, event: QWheelEvent) -> None:
        if not self._pixmap:
            return
        old = self.scale; factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale = max(0.05, min(8.0, self.scale * factor))
        cursor = QPointF(event.position()); image_pos = (cursor - self.offset) / old
        self.offset = cursor - image_pos * self.scale
        self.update(); self.statusChanged.emit(f"Zoom: {self.scale * 100:.0f}%")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setFocus()
        if event.button() == Qt.MouseButton.MiddleButton or (event.button() == Qt.MouseButton.LeftButton and self._space_pressed):
            self._mode = "pan"; self._last = QPointF(event.position()); return
        if event.button() != Qt.MouseButton.LeftButton or not self._pixmap:
            return
        pos = self._to_image(event.position())
        hit, handle = self._hit_and_handle(pos)
        if not hit:
            self.selected_ids.clear(); self.selected_id = None; self._emit_selection(); self.update(); return
        additive = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        if additive:
            self.select_id(hit.id, True)
            if hit.id not in self.selected_ids: return
        elif hit.id not in self.selected_ids:
            self._select_only(hit.id)
        if getattr(hit, "locked", False):
            return
        self._checkpoint()
        self._start = pos; self._start_rect = QRectF(hit.x, hit.y, hit.width, hit.height)
        self._move_origins = {item.id: (item.x, item.y) for item in self._selected_items()}
        self._resize_handle = handle if hit.id == self.selected_id else ""
        self._mode = "resize" if self._resize_handle else "move"

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._mode == "pan":
            delta = QPointF(event.position()) - self._last; self.offset += delta; self._last = QPointF(event.position()); self.update(); return
        if self._mode not in {"move", "resize"}:
            return
        pos = self._to_image(event.position())
        item = self.selected_element()
        if not item:
            return
        if self._mode == "move":
            delta = pos - self._start
            for selected in self._selected_items():
                if selected.locked: continue
                ox, oy = self._move_origins[selected.id]
                selected.x = int(ox + delta.x()); selected.y = int(oy + delta.y())
        else:
            self._resize_item(item, pos)
        self.fieldsChanged.emit(); self.fieldSelected.emit(item); self.statusChanged.emit(f"x={item.x}, y={item.y}, ancho={item.width}, alto={item.height}"); self.update()

    def mouseReleaseEvent(self, _event: QMouseEvent) -> None:
        if self._mode in {"move", "resize"}:
            self.fieldsChanged.emit()
        self._mode = "idle"; self._resize_handle = ""; self._start_rect = None; self._move_origins = {}

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space:
            self._space_pressed = True; event.accept(); return
        mods = event.modifiers()
        if mods & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Z: self.undo(); return
            if event.key() == Qt.Key.Key_Y: self.redo(); return
            if event.key() == Qt.Key.Key_D: self.duplicate_selected(); return
            if event.key() == Qt.Key.Key_C: self.copy_selected(); return
            if event.key() == Qt.Key.Key_V: self.paste(); return
        if event.key() in {Qt.Key.Key_Delete, Qt.Key.Key_Backspace}:
            self.delete_selected(); return
        if event.key() in {Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down} and self.selected_ids:
            step = 10 if mods & Qt.KeyboardModifier.ShiftModifier else 1
            dx = -step if event.key() == Qt.Key.Key_Left else step if event.key() == Qt.Key.Key_Right else 0
            dy = -step if event.key() == Qt.Key.Key_Up else step if event.key() == Qt.Key.Key_Down else 0
            self._checkpoint()
            for item in self._selected_items():
                if not item.locked: item.x += dx; item.y += dy
            self.fieldsChanged.emit(); self._emit_selection(); self.update(); return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space:
            self._space_pressed = False; event.accept(); return
        super().keyReleaseEvent(event)

    def _to_image(self, point: QPointF | QPoint) -> QPointF:
        pos = (QPointF(point) - self.offset) / self.scale
        return QPointF(max(0, min(self.image_size[0], pos.x())), max(0, min(self.image_size[1], pos.y())))

    def _hit_and_handle(self, pos: QPointF):
        selected = self.selected_element()
        if selected and not getattr(selected, "locked", False):
            for name, rect in self._handle_rects(selected, max(12, 18 / self.scale)).items():
                if rect.contains(pos): return selected, name
        for item in reversed(self.all_items()):
            if not getattr(item, "visible", True): continue
            tolerance = max(4, 8 / self.scale)
            if QRectF(item.x, item.y, item.width, item.height).adjusted(-tolerance, -tolerance, tolerance, tolerance).contains(pos):
                return item, ""
        return None, ""

    def _handle_rects(self, item: object, size: float = 0.1) -> dict[str, QRectF]:
        x, y, w, h = item.x, item.y, item.width, item.height
        pts = {"nw": (x, y), "n": (x+w/2, y), "ne": (x+w, y), "e": (x+w, y+h/2), "se": (x+w, y+h), "s": (x+w/2, y+h), "sw": (x, y+h), "w": (x, y+h/2)}
        return {name: QRectF(px-size/2, py-size/2, size, size) for name, (px, py) in pts.items()}

    def _resize_item(self, item: object, pos: QPointF) -> None:
        if not self._start_rect: return
        left, top, right, bottom = self._start_rect.left(), self._start_rect.top(), self._start_rect.right(), self._start_rect.bottom()
        h = self._resize_handle
        if "w" in h: left = min(pos.x(), right - 8)
        if "e" in h: right = max(pos.x(), left + 8)
        if "n" in h: top = min(pos.y(), bottom - 8)
        if "s" in h: bottom = max(pos.y(), top + 8)
        item.x, item.y, item.width, item.height = int(left), int(top), int(right-left), int(bottom-top)

    def _image_pixmap(self, path: str) -> QPixmap | None:
        if path in self._image_cache: return self._image_cache[path]
        if not Path(path).exists(): return None
        pixmap = QPixmap(path)
        if pixmap.isNull(): return None
        self._image_cache[path] = pixmap
        return pixmap

    def _find(self, element_id: str | None):
        if not element_id: return None
        return next((item for item in [*self.elements, *self.fields] if item.id == element_id), None)

    def _selected_items(self) -> list[object]:
        return [item for item in self.all_items() if item.id in self.selected_ids]

    def _select_only(self, element_id: str) -> None:
        self.selected_ids = {element_id}; self.selected_id = element_id; self._emit_selection(); self.update()

    def _emit_selection(self) -> None:
        item = self.selected_element(); self.fieldSelected.emit(item); self.selectionChanged.emit(item)

    def _snapshot(self):
        return copy.deepcopy(self.fields), copy.deepcopy(self.elements)

    def _checkpoint(self) -> None:
        self._undo.append(self._snapshot())
        if len(self._undo) > 80: self._undo.pop(0)
        self._redo.clear()

    def _restore(self, state) -> None:
        self.fields, self.elements = copy.deepcopy(state[0]), copy.deepcopy(state[1])
        self.selected_ids.clear(); self.selected_id = None; self._emit_selection(); self.fieldsChanged.emit(); self.update()

    def _source_index(self, item: object) -> int:
        source = self.fields if isinstance(item, TextField) else self.elements
        try: return source.index(item)
        except ValueError: return 0

    def _next_z(self) -> int:
        items = [*self.elements, *self.fields]
        return max((item.z_index for item in items), default=0) + 1

    def _min_z(self) -> int:
        items = [*self.elements, *self.fields]
        return min((item.z_index for item in items), default=0)

    def _set_selected_z(self, value: int) -> None:
        items = self._selected_items()
        if not items: return
        self._checkpoint()
        for offset, item in enumerate(items): item.z_index = value + offset
        self.fieldsChanged.emit(); self.update()
