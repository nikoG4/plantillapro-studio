from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QApplication, QColorDialog, QDockWidget, QFileDialog, QInputDialog,
    QListWidget, QListWidgetItem, QMessageBox, QProgressDialog, QSplitter,
)

from app.core.image_exporter import export_images
from app.core.models import ImageElement, ShapeElement, TextField
from app.core.pdf_exporter import export_pdf
from app.ui.advanced_canvas_widget import AdvancedCanvasWidget
from app.ui.main_window import MainWindow
from app.ui.preview_dialog import PreviewDialog


class AdvancedMainWindow(MainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PlantillaPro Studio — Editor avanzado")
        self._install_advanced_canvas()
        self._install_layers()
        self._install_editor_actions()
        self.canvas.set_document(self.project.fields, self.project.elements)
        self._refresh_layers()

    def _install_advanced_canvas(self) -> None:
        old_canvas = self.canvas
        parent = old_canvas.parentWidget()
        canvas = AdvancedCanvasWidget()
        if isinstance(parent, QSplitter):
            index = parent.indexOf(old_canvas)
            parent.replaceWidget(index, canvas)
            old_canvas.deleteLater()
        self.canvas = canvas
        self.canvas.fieldSelected.connect(self._on_editor_selection)
        self.canvas.fieldsChanged.connect(self._sync_fields)
        self.canvas.statusChanged.connect(self.statusBar().showMessage)
        if self.project.image_path and Path(self.project.image_path).exists():
            self.canvas.load_image(self.project.image_path)

    def _install_layers(self) -> None:
        self.layers = QListWidget()
        self.layers.setAlternatingRowColors(True)
        self.layers.currentItemChanged.connect(self._layer_selected)
        dock = QDockWidget("Capas", self)
        dock.setObjectName("layersDock")
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        dock.setWidget(self.layers)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _install_editor_actions(self) -> None:
        self.toolbar.addSeparator()
        actions = [
            ("Imagen +", self.add_graphic_image),
            ("Rectángulo +", lambda: self.canvas.add_shape("rectangle")),
            ("Elipse +", lambda: self.canvas.add_shape("ellipse")),
            ("Deshacer", self.canvas.undo),
            ("Rehacer", self.canvas.redo),
            ("Frente", self.canvas.bring_to_front),
            ("Fondo", self.canvas.send_to_back),
            ("Bloquear", self.canvas.toggle_lock),
            ("Visible", self.canvas.toggle_visibility),
            ("Rotar", self.rotate_selected),
            ("Opacidad", self.change_opacity),
            ("Color", self.change_shape_color),
            ("Ajuste imagen", self.change_image_fit),
            ("Ajustar vista", self.canvas.fit_to_view),
        ]
        for text, slot in actions:
            action = QAction(text, self)
            action.triggered.connect(slot)
            self.toolbar.addAction(action)

    def _on_editor_selection(self, item) -> None:
        self.properties.set_field(item if isinstance(item, TextField) else None)
        self._refresh_layers()

    def _layer_selected(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        element_id = current.data(Qt.ItemDataRole.UserRole)
        if element_id:
            self.canvas.select_id(str(element_id))

    def _refresh_layers(self) -> None:
        if not hasattr(self, "layers"):
            return
        selected = self.canvas.selected_id if hasattr(self, "canvas") else None
        self.layers.blockSignals(True)
        self.layers.clear()
        for item in reversed(self.canvas.all_items()):
            kind = "T" if isinstance(item, TextField) else "I" if isinstance(item, ImageElement) else "F"
            eye = "👁" if item.visible else "—"
            lock = "🔒" if item.locked else ""
            row = QListWidgetItem(f"{eye} {lock} [{kind}] {item.name}")
            row.setData(Qt.ItemDataRole.UserRole, item.id)
            self.layers.addItem(row)
            if item.id == selected:
                self.layers.setCurrentItem(row)
        self.layers.blockSignals(False)

    def add_graphic_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Agregar imagen", "", "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp)")
        if path:
            self.canvas.add_image(path)
            self._sync_fields()

    def rotate_selected(self) -> None:
        item = self.canvas.selected_element()
        if not item:
            return
        current = item.style.rotation if isinstance(item, TextField) else item.rotation
        value, ok = QInputDialog.getDouble(self, "Rotación", "Grados", current, -360, 360, 1)
        if not ok:
            return
        self.canvas._checkpoint()
        if isinstance(item, TextField):
            item.style.rotation = value
        else:
            item.rotation = value
        self.canvas.fieldsChanged.emit(); self.canvas.update(); self._refresh_layers()

    def change_opacity(self) -> None:
        item = self.canvas.selected_element()
        if not item:
            return
        value, ok = QInputDialog.getDouble(self, "Opacidad", "0 = transparente, 1 = opaco", item.opacity, 0, 1, 2)
        if ok:
            self.canvas._checkpoint(); item.opacity = value; self.canvas.fieldsChanged.emit(); self.canvas.update()

    def change_shape_color(self) -> None:
        item = self.canvas.selected_element()
        if not isinstance(item, ShapeElement):
            return
        color = QColorDialog.getColor(QColor(item.fill_color), self, "Color de relleno")
        if color.isValid():
            self.canvas._checkpoint(); item.fill_color = color.name(); self.canvas.fieldsChanged.emit(); self.canvas.update()

    def change_image_fit(self) -> None:
        item = self.canvas.selected_element()
        if not isinstance(item, ImageElement):
            return
        modes = ["cover", "contain", "stretch"]
        value, ok = QInputDialog.getItem(self, "Ajuste de imagen", "Modo", modes, modes.index(item.fit_mode) if item.fit_mode in modes else 0, False)
        if ok:
            self.canvas._checkpoint(); item.fit_mode = value; self.canvas.fieldsChanged.emit(); self.canvas.update()

    def _sync_fields(self) -> None:
        self.project.fields = self.canvas.fields
        self.project.elements = self.canvas.elements
        self._refresh_layers()

    def new_project(self) -> None:
        super().new_project()
        if hasattr(self.canvas, "set_elements"):
            self.canvas.set_elements([])
        self._sync_fields()

    def open_project(self) -> None:
        super().open_project()
        if hasattr(self.canvas, "set_elements"):
            self.canvas.set_elements(self.project.elements)
        self._sync_fields()

    def open_generated_viewer(self) -> None:
        if not self._validate(require_output=False):
            return
        AdvancedPreviewDialog(self.project.image_path, self.project.fields, self.project.elements, self._table_rows(), self.project.export, 0, self).exec()

    def generate_pdf(self) -> None:
        if not self._validate(require_output=False): return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "plantillas_generadas.pdf", "PDF (*.pdf)")
        if not path: return
        self.project.export.output_pdf = path
        progress = QProgressDialog("Generando PDF...", "Cancelar", 0, 1, self)
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        try:
            count = export_pdf(self.project.image_path, self.project.fields, self._table_rows(), self.project.export, path,
                progress=lambda done, total: (progress.setMaximum(total), progress.setValue(done), QApplication.processEvents()),
                should_cancel=progress.wasCanceled, elements=self.project.elements)
            QMessageBox.information(self, "PDF generado", f"Páginas generadas: {count}\nArchivo: {path}")
        except Exception as exc: self._error("No se pudo generar el PDF", exc)
        finally: progress.close()

    def generate_images(self) -> None:
        if not self._validate(require_output=False): return
        folder = QFileDialog.getExistingDirectory(self, "Carpeta de salida")
        if not folder: return
        pattern, ok = QInputDialog.getText(self, "Patrón de archivo", "Patrón", text=self.project.export.filename_pattern)
        if not ok: return
        fmt, ok = QInputDialog.getItem(self, "Formato", "Formato", ["PNG", "JPG"], 0, False)
        if not ok: return
        self.project.export.output_folder = folder; self.project.export.filename_pattern = pattern or "{{numero}}_{{nombre}}"; self.project.export.image_format = fmt
        progress = QProgressDialog("Exportando imágenes...", "Cancelar", 0, 1, self)
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        try:
            files = export_images(self.project.image_path, self.project.fields, self._table_rows(), self.project.export, folder,
                progress=lambda done, total: (progress.setMaximum(total), progress.setValue(done), QApplication.processEvents()),
                should_cancel=progress.wasCanceled, elements=self.project.elements)
            QMessageBox.information(self, "Imágenes exportadas", f"Archivos generados: {len(files)}\nCarpeta: {folder}")
        except Exception as exc: self._error("No se pudieron exportar las imágenes", exc)
        finally: progress.close()


class AdvancedPreviewDialog(PreviewDialog):
    def __init__(self, image_path, fields, elements, rows, settings, start_index=0, parent=None):
        self.elements = elements
        super().__init__(image_path, fields, rows, settings, start_index, parent)

    def _render_qimage(self, index):
        from PIL.ImageQt import ImageQt
        from PySide6.QtGui import QImage
        from app.core.imposition import render_imposed_page
        image = render_imposed_page(self.image_path, self.fields, self.layout_info, self.pages[index], self.elements).convert("RGBA")
        return QImage(ImageQt(image))

    def _save_pdf(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "plantillas_generadas.pdf", "PDF (*.pdf)")
        if not path: return
        try:
            export_pdf(self.image_path, self.fields, self.rows, self.settings, path, elements=self.elements)
            QMessageBox.information(self, "PDF generado", f"Archivo: {path}")
        except Exception as exc: QMessageBox.critical(self, "Error al generar PDF", str(exc))

    def _save_images(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Carpeta de salida")
        if not folder: return
        try:
            files = export_images(self.image_path, self.fields, self.rows, self.settings, folder, elements=self.elements)
            QMessageBox.information(self, "Imágenes exportadas", f"Archivos generados: {len(files)}")
        except Exception as exc: QMessageBox.critical(self, "Error al exportar imágenes", str(exc))
