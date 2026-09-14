from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QDockWidget, QMessageBox

from app.core.imposition import compute_layout
from app.core.models import ImageElement, ShapeElement, TextField
from app.core.renderer import missing_variables
from app.ui.advanced_main_window import AdvancedMainWindow
from app.ui.graphic_properties_panel import GraphicPropertiesPanel


class ProMainWindow(AdvancedMainWindow):
    """Final editor window with contextual properties and static-design validation."""

    def __init__(self) -> None:
        super().__init__()
        self._install_graphic_properties()
        self._deduplicate_shortcuts()

    def _install_graphic_properties(self) -> None:
        self.graphic_properties = GraphicPropertiesPanel()
        self.graphic_properties.changed.connect(self._graphic_properties_changed)
        dock = QDockWidget("Propiedades gráficas", self)
        dock.setObjectName("graphicPropertiesDock")
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        dock.setWidget(self.graphic_properties)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        layers_dock = self.findChild(QDockWidget, "layersDock")
        if layers_dock is not None:
            self.splitDockWidget(layers_dock, dock, Qt.Orientation.Vertical)
        self.canvas.fieldSelected.connect(self._sync_graphic_properties_selection)
        self._sync_graphic_properties_selection(self.canvas.selected_element())

    def _sync_graphic_properties_selection(self, item) -> None:
        self.graphic_properties.set_element(item if isinstance(item, (ImageElement, ShapeElement)) else None)

    def _graphic_properties_changed(self) -> None:
        self.canvas.update()
        self.canvas.fieldsChanged.emit()
        self._refresh_layers()

    def _deduplicate_shortcuts(self) -> None:
        seen: set[str] = set()
        for action in self.findChildren(QAction):
            key = action.shortcut().toString()
            if not key:
                continue
            if key in seen:
                action.setShortcut(QKeySequence())
            else:
                seen.add(key)

    def _validate(self, require_output: bool) -> bool:
        self._sync_project()
        if not self.project.image_path or not Path(self.project.image_path).exists():
            QMessageBox.warning(self, "Falta imagen", "Carga una imagen base válida.")
            return False
        if not self.project.fields and not self.project.elements:
            QMessageBox.warning(self, "Diseño vacío", "Agrega al menos texto, una imagen o una forma.")
            return False

        rows = self._table_rows()
        if not rows and not (self.project.export.numbering.enabled and self.project.export.numbering.count > 0):
            QMessageBox.warning(self, "Faltan datos", "Carga datos, activa numeración o crea un diseño estático.")
            return False

        columns: set[str] = set()
        for row in rows:
            columns.update(row.keys())
        if self.project.export.numbering.enabled:
            columns.add(self.project.export.numbering.field_name)
        missing = missing_variables(self.project.fields, columns)
        if missing:
            QMessageBox.warning(self, "Variables no encontradas", "No existen estas columnas: " + ", ".join(sorted(missing)))
            return False

        try:
            layout = compute_layout(self.project.export, (self.project.image_width, self.project.image_height))
            if layout.slots_per_page <= 0:
                QMessageBox.warning(self, "La pieza no entra", "Reduce el tamaño de la pieza, los márgenes o las separaciones.")
                return False
        except Exception as exc:
            self._error("Configuración de hoja inválida", exc)
            return False
        return True
