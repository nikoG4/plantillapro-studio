from __future__ import annotations

import copy
import uuid
from pathlib import Path
from typing import Any

from PIL import Image
from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtWidgets import QFileDialog

from app.core.data_loader import load_data_file
from app.core.document_base import document_base_path
from app.core.image_exporter import export_images
from app.core.models import (
    DocumentSettings,
    ImageElement,
    ShapeElement,
    TemplateProject,
    TextField,
)
from app.core.pdf_exporter import export_pdf
from app.core.production import build_production_rows, production_errors, source_columns, variable_fields
from app.core.project_io import load_project, save_project


class StudioBridge(QObject):
    projectChanged = Signal()
    selectionChanged = Signal()
    modeChanged = Signal()
    toast = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.project = TemplateProject()
        self._selected_id = ""
        self._mode = "welcome"
        self._current_path = ""

    # ---- high level state -------------------------------------------------
    @Property(str, notify=modeChanged)
    def mode(self) -> str:
        return self._mode

    @Property(str, notify=projectChanged)
    def projectName(self) -> str:
        return Path(self._current_path).stem if self._current_path else "Sin guardar"

    @Property(int, notify=projectChanged)
    def documentWidth(self) -> int:
        return self.project.document_size()[0]

    @Property(int, notify=projectChanged)
    def documentHeight(self) -> int:
        return self.project.document_size()[1]

    @Property(str, notify=projectChanged)
    def documentBackground(self) -> str:
        return self.project.document.background_color

    @Property(bool, notify=projectChanged)
    def documentTransparent(self) -> bool:
        return bool(self.project.document.transparent)

    @Property(str, notify=selectionChanged)
    def selectedId(self) -> str:
        return self._selected_id

    @Property("QVariantList", notify=projectChanged)
    def elements(self) -> list[dict[str, Any]]:
        items = sorted([*self.project.elements, *self.project.fields], key=lambda item: item.z_index)
        return [self._item_dict(item) for item in items if getattr(item, "visible", True)]

    @Property("QVariantMap", notify=selectionChanged)
    def selectedData(self) -> dict[str, Any]:
        item = self._find_item(self._selected_id)
        return self._item_dict(item) if item is not None else {}

    @Property("QVariantList", notify=projectChanged)
    def layers(self) -> list[dict[str, Any]]:
        items = sorted([*self.project.elements, *self.project.fields], key=lambda item: item.z_index, reverse=True)
        return [self._item_dict(item) for item in items]

    @Property("QVariantList", notify=projectChanged)
    def variableMappings(self) -> list[dict[str, Any]]:
        columns = source_columns(self.project.data)
        result: list[dict[str, Any]] = []
        for field in variable_fields(self.project.fields):
            result.append({
                "id": field.id,
                "name": field.name,
                "key": field.variable_key(),
                "source": field.production_source,
                "column": field.source_column or field.variable_key(),
                "columns": columns,
                "start": field.number_start,
                "step": field.number_step,
                "count": field.number_count,
                "digits": field.number_digits,
                "prefix": field.number_prefix,
                "suffix": field.number_suffix,
            })
        return result

    @Property("QVariantList", notify=projectChanged)
    def dataColumns(self) -> list[str]:
        return source_columns(self.project.data)

    @Property("QVariantList", notify=projectChanged)
    def dataPreview(self) -> list[str]:
        columns = source_columns(self.project.data)
        result: list[str] = []
        for row in self.project.data[:50]:
            values = [str(row.get(column, "")) for column in columns]
            result.append("  ·  ".join(values))
        return result

    @Property(int, notify=projectChanged)
    def dataRowCount(self) -> int:
        return len(self.project.data)

    @Property(int, notify=projectChanged)
    def productionCount(self) -> int:
        return len(build_production_rows(self.project.fields, self.project.data))

    @Property(str, notify=projectChanged)
    def productionSummary(self) -> str:
        variables = variable_fields(self.project.fields)
        return f"{self.productionCount} copias · {len(variables)} campos variables · {len(self.project.data)} filas de datos"

    # ---- navigation / project --------------------------------------------
    @Slot(str)
    def setMode(self, mode: str) -> None:
        if mode not in {"welcome", "design", "production"}:
            return
        if self._mode != mode:
            self._mode = mode
            self.modeChanged.emit()

    @Slot()
    def newA4(self) -> None:
        self.project = TemplateProject(document=DocumentSettings())
        self._current_path = ""
        self._selected_id = ""
        self._mode = "design"
        self.projectChanged.emit()
        self.selectionChanged.emit()
        self.modeChanged.emit()

    @Slot(int, int, str, bool)
    def newDocument(self, width: int, height: int, color: str = "#ffffff", transparent: bool = False) -> None:
        width = max(1, int(width))
        height = max(1, int(height))
        self.project = TemplateProject(document=DocumentSettings(
            width=width,
            height=height,
            background_color=color or "#ffffff",
            transparent=bool(transparent),
            preset="custom",
        ))
        self._current_path = ""
        self._selected_id = ""
        self._mode = "design"
        self.projectChanged.emit()
        self.selectionChanged.emit()
        self.modeChanged.emit()

    @Slot()
    def openProject(self) -> None:
        path, _ = QFileDialog.getOpenFileName(None, "Abrir proyecto", "", "PlantillaPro (*.json);;JSON (*.json)")
        if not path:
            return
        try:
            self.project = load_project(path)
            self._current_path = path
            self._selected_id = ""
            self._mode = "design"
            self.projectChanged.emit()
            self.selectionChanged.emit()
            self.modeChanged.emit()
            self.toast.emit("Proyecto abierto")
        except Exception as exc:
            self.toast.emit(f"No se pudo abrir: {exc}")

    @Slot()
    def saveProject(self) -> None:
        path = self._current_path
        if not path:
            path, _ = QFileDialog.getSaveFileName(None, "Guardar proyecto", "diseno.json", "PlantillaPro (*.json)")
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            save_project(self.project, path)
            self._current_path = path
            self.projectChanged.emit()
            self.toast.emit("Proyecto guardado")
        except Exception as exc:
            self.toast.emit(f"No se pudo guardar: {exc}")

    @Slot()
    def loadBackground(self) -> None:
        path, _ = QFileDialog.getOpenFileName(None, "Imagen de fondo", "", "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp)")
        if not path:
            return
        try:
            with Image.open(path) as image:
                width, height = image.size
            self.project.image_path = path
            self.project.image_width = width
            self.project.image_height = height
            self.project.document.width = width
            self.project.document.height = height
            self.project.document.preset = "image"
            self.projectChanged.emit()
            self.toast.emit("Fondo actualizado")
        except Exception as exc:
            self.toast.emit(f"No se pudo cargar la imagen: {exc}")

    @Slot(str)
    def setDocumentBackground(self, color: str) -> None:
        if color:
            self.project.document.background_color = color
            self.projectChanged.emit()

    @Slot(bool)
    def setDocumentTransparent(self, transparent: bool) -> None:
        self.project.document.transparent = bool(transparent)
        self.projectChanged.emit()

    # ---- design elements --------------------------------------------------
    def _next_z(self) -> int:
        all_items = [*self.project.fields, *self.project.elements]
        return max((item.z_index for item in all_items), default=0) + 1

    @Slot()
    def addStaticText(self) -> None:
        field = TextField(
            id=str(uuid.uuid4()),
            name="Texto fijo",
            template="Escribe aquí",
            x=160,
            y=180,
            width=720,
            height=180,
            z_index=self._next_z(),
            text_mode="static",
        )
        self.project.fields.append(field)
        self._select_and_emit(field.id)

    @Slot()
    def addVariableText(self) -> None:
        existing = {field.variable_key() for field in variable_fields(self.project.fields)}
        index = 1
        key = "campo"
        while key in existing:
            index += 1
            key = f"campo_{index}"
        field = TextField(
            id=str(uuid.uuid4()),
            name="Campo variable",
            template="{{" + key + "}}",
            x=180,
            y=420,
            width=720,
            height=180,
            z_index=self._next_z(),
            text_mode="variable",
            variable_name=key,
            source_column=key,
        )
        self.project.fields.append(field)
        self._select_and_emit(field.id)

    @Slot()
    def addRectangle(self) -> None:
        shape = ShapeElement(
            id=str(uuid.uuid4()),
            name="Rectángulo",
            x=240,
            y=600,
            width=620,
            height=300,
            corner_radius=24,
            fill_color="#eef2ff",
            stroke_color="#c7d2fe",
            z_index=self._next_z(),
        )
        self.project.elements.append(shape)
        self._select_and_emit(shape.id)

    @Slot()
    def addEllipse(self) -> None:
        shape = ShapeElement(
            id=str(uuid.uuid4()),
            name="Elipse",
            shape_type="ellipse",
            x=260,
            y=620,
            width=360,
            height=360,
            fill_color="#dbeafe",
            stroke_color="#93c5fd",
            z_index=self._next_z(),
        )
        self.project.elements.append(shape)
        self._select_and_emit(shape.id)

    @Slot()
    def addImage(self) -> None:
        path, _ = QFileDialog.getOpenFileName(None, "Agregar imagen", "", "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp)")
        if not path:
            return
        try:
            with Image.open(path) as image:
                source_w, source_h = image.size
            max_w = max(240, int(self.documentWidth * 0.45))
            ratio = source_h / max(1, source_w)
            width = min(source_w, max_w)
            height = max(80, int(width * ratio))
            item = ImageElement(
                id=str(uuid.uuid4()),
                name=Path(path).stem,
                path=path,
                x=max(20, (self.documentWidth - width) // 2),
                y=max(20, (self.documentHeight - height) // 2),
                width=width,
                height=height,
                z_index=self._next_z(),
            )
            self.project.elements.append(item)
            self._select_and_emit(item.id)
        except Exception as exc:
            self.toast.emit(f"No se pudo agregar la imagen: {exc}")

    @Slot(str)
    def selectItem(self, item_id: str) -> None:
        if self._find_item(item_id) is None:
            return
        self._selected_id = item_id
        self.selectionChanged.emit()

    @Slot()
    def clearSelection(self) -> None:
        if self._selected_id:
            self._selected_id = ""
            self.selectionChanged.emit()

    @Slot(str, float, float)
    def moveItem(self, item_id: str, x: float, y: float) -> None:
        item = self._find_item(item_id)
        if item is None or item.locked:
            return
        item.x = int(max(-item.width + 20, min(self.documentWidth - 20, x)))
        item.y = int(max(-item.height + 20, min(self.documentHeight - 20, y)))
        self.projectChanged.emit()
        if item_id == self._selected_id:
            self.selectionChanged.emit()

    @Slot(str, float, float)
    def resizeItem(self, item_id: str, width: float, height: float) -> None:
        item = self._find_item(item_id)
        if item is None or item.locked:
            return
        item.width = max(20, int(width))
        item.height = max(20, int(height))
        self.projectChanged.emit()
        if item_id == self._selected_id:
            self.selectionChanged.emit()

    @Slot()
    def deleteSelected(self) -> None:
        if not self._selected_id:
            return
        self.project.fields = [item for item in self.project.fields if item.id != self._selected_id]
        self.project.elements = [item for item in self.project.elements if item.id != self._selected_id]
        self._selected_id = ""
        self.projectChanged.emit()
        self.selectionChanged.emit()

    @Slot()
    def duplicateSelected(self) -> None:
        item = self._find_item(self._selected_id)
        if item is None:
            return
        duplicate = copy.deepcopy(item)
        duplicate.id = str(uuid.uuid4())
        duplicate.name = f"{item.name} copia"
        duplicate.x += 36
        duplicate.y += 36
        duplicate.z_index = self._next_z()
        duplicate.group_id = ""
        if isinstance(duplicate, TextField):
            if duplicate.is_variable():
                duplicate.variable_name = f"{duplicate.variable_key()}_copia"
                duplicate.source_column = duplicate.variable_name
                duplicate.sync_variable_template()
            self.project.fields.append(duplicate)
        else:
            self.project.elements.append(duplicate)
        self._select_and_emit(duplicate.id)

    @Slot()
    def bringSelectedToFront(self) -> None:
        item = self._find_item(self._selected_id)
        if item is None:
            return
        item.z_index = self._next_z()
        self.projectChanged.emit()
        self.selectionChanged.emit()

    @Slot()
    def sendSelectedToBack(self) -> None:
        item = self._find_item(self._selected_id)
        if item is None:
            return
        minimum = min((entry.z_index for entry in [*self.project.fields, *self.project.elements]), default=0)
        item.z_index = minimum - 1
        self.projectChanged.emit()
        self.selectionChanged.emit()

    @Slot()
    def toggleSelectedLock(self) -> None:
        item = self._find_item(self._selected_id)
        if item is None:
            return
        item.locked = not item.locked
        self.projectChanged.emit()
        self.selectionChanged.emit()

    @Slot(str)
    def setSelectedName(self, name: str) -> None:
        item = self._find_item(self._selected_id)
        if item is None:
            return
        item.name = name.strip() or item.name
        if isinstance(item, TextField) and item.is_variable():
            item.variable_name = self._safe_key(item.name)
            item.sync_variable_template()
        self.projectChanged.emit()
        self.selectionChanged.emit()

    @Slot(str)
    def setSelectedText(self, text: str) -> None:
        item = self._find_item(self._selected_id)
        if isinstance(item, TextField) and not item.is_variable():
            item.template = text
            self.projectChanged.emit()
            self.selectionChanged.emit()

    @Slot(int)
    def setSelectedFontSize(self, size: int) -> None:
        item = self._find_item(self._selected_id)
        if isinstance(item, TextField):
            item.style.font_size = max(1, int(size))
            self.projectChanged.emit()
            self.selectionChanged.emit()

    @Slot(str)
    def setSelectedColor(self, color: str) -> None:
        item = self._find_item(self._selected_id)
        if item is None or not color:
            return
        if isinstance(item, TextField):
            item.style.color = color
        elif isinstance(item, ShapeElement):
            item.fill_color = color
        self.projectChanged.emit()
        self.selectionChanged.emit()

    @Slot(float)
    def setSelectedOpacity(self, opacity: float) -> None:
        item = self._find_item(self._selected_id)
        if item is None:
            return
        item.opacity = max(0.0, min(1.0, float(opacity)))
        self.projectChanged.emit()
        self.selectionChanged.emit()

    @Slot(float)
    def setSelectedRotation(self, rotation: float) -> None:
        item = self._find_item(self._selected_id)
        if item is None:
            return
        if isinstance(item, TextField):
            item.style.rotation = float(rotation)
        else:
            item.rotation = float(rotation)
        self.projectChanged.emit()
        self.selectionChanged.emit()

    # ---- production -------------------------------------------------------
    @Slot()
    def importData(self) -> None:
        path, _ = QFileDialog.getOpenFileName(None, "Importar datos", "", "Datos (*.xlsx *.csv *.txt)")
        if not path:
            return
        try:
            self.project.data = load_data_file(path)
            columns = source_columns(self.project.data)
            for field in variable_fields(self.project.fields):
                if field.production_source == "column" and (not field.source_column or field.source_column not in columns):
                    field.source_column = columns[0] if columns else field.variable_key()
            self.projectChanged.emit()
            self.toast.emit(f"Datos importados: {len(self.project.data)} filas")
        except Exception as exc:
            self.toast.emit(f"No se pudieron importar los datos: {exc}")

    @Slot()
    def addEmptyDataRow(self) -> None:
        columns = source_columns(self.project.data) or ["nombre"]
        self.project.data.append({column: "" for column in columns})
        self.projectChanged.emit()

    @Slot(int)
    def deleteDataRow(self, index: int) -> None:
        if 0 <= index < len(self.project.data):
            del self.project.data[index]
            self.projectChanged.emit()

    @Slot(str, str)
    def setVariableSource(self, field_id: str, source: str) -> None:
        field = next((field for field in self.project.fields if field.id == field_id), None)
        if field is None or not field.is_variable() or source not in {"column", "numbering"}:
            return
        field.production_source = source
        if source == "column":
            columns = source_columns(self.project.data)
            if columns and field.source_column not in columns:
                field.source_column = columns[0]
        self.projectChanged.emit()

    @Slot(str, str)
    def setVariableColumn(self, field_id: str, column: str) -> None:
        field = next((field for field in self.project.fields if field.id == field_id), None)
        if field is None or not field.is_variable():
            return
        field.source_column = column
        field.production_source = "column"
        self.projectChanged.emit()

    @Slot(str, str, str)
    def setNumberSetting(self, field_id: str, key: str, value: str) -> None:
        field = next((field for field in self.project.fields if field.id == field_id), None)
        if field is None or not field.is_variable():
            return
        try:
            if key == "start":
                field.number_start = int(value)
            elif key == "step":
                field.number_step = int(value)
            elif key == "count":
                field.number_count = max(1, int(value))
            elif key == "digits":
                field.number_digits = max(0, int(value))
            elif key == "prefix":
                field.number_prefix = value
            elif key == "suffix":
                field.number_suffix = value
            else:
                return
        except ValueError:
            return
        field.production_source = "numbering"
        self.projectChanged.emit()

    # ---- export -----------------------------------------------------------
    @Slot()
    def exportPdf(self) -> None:
        rows = build_production_rows(self.project.fields, self.project.data)
        errors = production_errors(self.project.fields, self.project.data)
        if errors:
            self.toast.emit(" · ".join(errors))
            return
        path, _ = QFileDialog.getSaveFileName(None, "Exportar PDF", "salida.pdf", "PDF (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        try:
            count = export_pdf(
                document_base_path(self.project), self.project.fields, rows,
                self.project.export, path, elements=self.project.elements,
            )
            self.toast.emit(f"PDF generado: {count} hoja(s)")
        except Exception as exc:
            self.toast.emit(f"No se pudo exportar: {exc}")

    @Slot()
    def exportImages(self) -> None:
        rows = build_production_rows(self.project.fields, self.project.data)
        errors = production_errors(self.project.fields, self.project.data)
        if errors:
            self.toast.emit(" · ".join(errors))
            return
        folder = QFileDialog.getExistingDirectory(None, "Carpeta de exportación")
        if not folder:
            return
        try:
            written = export_images(
                document_base_path(self.project), self.project.fields, rows,
                self.project.export, folder, elements=self.project.elements,
            )
            self.toast.emit(f"Imágenes generadas: {len(written)}")
        except Exception as exc:
            self.toast.emit(f"No se pudo exportar: {exc}")

    # ---- helpers ----------------------------------------------------------
    def _select_and_emit(self, item_id: str) -> None:
        self._selected_id = item_id
        self._mode = "design"
        self.projectChanged.emit()
        self.selectionChanged.emit()
        self.modeChanged.emit()

    def _find_item(self, item_id: str):
        if not item_id:
            return None
        for item in [*self.project.fields, *self.project.elements]:
            if item.id == item_id:
                return item
        return None

    @staticmethod
    def _safe_key(value: str) -> str:
        result = "".join(character.lower() if character.isalnum() else "_" for character in value.strip())
        result = "_".join(part for part in result.split("_") if part)
        return result or "campo"

    def _item_dict(self, item) -> dict[str, Any]:
        if item is None:
            return {}
        if isinstance(item, TextField):
            rotation = item.style.rotation
            kind = "variable" if item.is_variable() else "text"
            display_text = item.name if item.is_variable() else item.template
            return {
                "id": item.id, "kind": kind, "name": item.name, "text": display_text,
                "template": item.template, "x": item.x, "y": item.y,
                "width": item.width, "height": item.height, "rotation": rotation,
                "opacity": item.opacity, "locked": item.locked, "visible": item.visible,
                "z": item.z_index, "color": item.style.color, "fontSize": item.style.font_size,
                "bold": item.style.bold, "variable": item.is_variable(),
            }
        if isinstance(item, ImageElement):
            source = QUrl.fromLocalFile(str(Path(item.path).resolve())).toString() if item.path else ""
            return {
                "id": item.id, "kind": "image", "name": item.name, "text": item.name,
                "source": source, "x": item.x, "y": item.y, "width": item.width,
                "height": item.height, "rotation": item.rotation, "opacity": item.opacity,
                "locked": item.locked, "visible": item.visible, "z": item.z_index,
                "fitMode": item.fit_mode,
            }
        return {
            "id": item.id, "kind": "shape", "name": item.name, "text": item.name,
            "shapeType": item.shape_type, "x": item.x, "y": item.y,
            "width": item.width, "height": item.height, "rotation": item.rotation,
            "opacity": item.opacity, "locked": item.locked, "visible": item.visible,
            "z": item.z_index, "fillColor": item.fill_color, "strokeColor": item.stroke_color,
            "strokeWidth": item.stroke_width, "cornerRadius": item.corner_radius,
        }
