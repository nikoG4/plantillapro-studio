from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFormLayout, QFrame, QGroupBox, QHBoxLayout, QLabel,
    QListWidgetItem, QMessageBox, QProgressDialog, QPushButton, QScrollArea, QSplitter,
    QTabWidget, QToolBar, QToolButton, QVBoxLayout, QWidget,
)

from app.core.document_base import document_base_path
from app.core.image_exporter import export_images
from app.core.imposition import compute_layout
from app.core.models import ImageElement, ShapeElement, TextField
from app.core.pdf_exporter import export_pdf
from app.core.production import build_production_rows, production_errors, variable_fields
from app.ui.advanced_main_window import AdvancedPreviewDialog
from app.ui.icons import studio_icon
from app.ui.production_mapping_panel import ProductionMappingPanel
from app.ui.studio_main_window import StudioMainWindow


class RefinedStudioMainWindow(StudioMainWindow):
    """Studio UX with icon actions and explicit variable-to-data production mapping."""

    def _icon_button(self, icon: str, tooltip: str, slot, size: int = 38) -> QToolButton:
        button = QToolButton()
        button.setIcon(studio_icon(icon, 24))
        button.setIconSize(QSize(24, 24))
        button.setToolTip(tooltip)
        button.setStatusTip(tooltip)
        button.setAccessibleName(tooltip)
        button.setFixedSize(size, size)
        button.clicked.connect(slot)
        return button

    def _build_top_toolbar(self) -> None:
        bar = QToolBar("Principal")
        bar.setObjectName("studioTopBar")
        bar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, bar)
        self.studio_toolbar = bar

        title = QLabel("  PlantillaPro Studio   ")
        title.setStyleSheet("font-size:17px; font-weight:700;")
        bar.addWidget(title)

        self.design_mode_btn = QToolButton()
        self.design_mode_btn.setText("Diseño")
        self.design_mode_btn.setCheckable(True)
        self.design_mode_btn.setToolTip("Editar el diseño visual")
        self.design_mode_btn.clicked.connect(self.show_design)
        self.production_mode_btn = QToolButton()
        self.production_mode_btn.setText("Producción")
        self.production_mode_btn.setCheckable(True)
        self.production_mode_btn.setToolTip("Asignar datos, numeración y exportar")
        self.production_mode_btn.clicked.connect(self.show_production)
        bar.addWidget(self.design_mode_btn); bar.addWidget(self.production_mode_btn); bar.addSeparator()

        for icon, tip, slot in [
            ("new", "Nuevo diseño", self.show_new_document_dialog),
            ("open", "Abrir proyecto", self.open_project),
            ("save", "Guardar proyecto", self.save_project),
            ("export", "Ir a Producción / Exportar", self.show_production),
        ]:
            action = QAction(studio_icon(icon, 22), tip, self)
            action.setToolTip(tip); action.setStatusTip(tip)
            action.triggered.connect(slot)
            bar.addAction(action)

    def _build_design_page(self) -> QWidget:
        page = QWidget()
        root = QHBoxLayout(page); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        rail = QFrame(); rail.setObjectName("toolRail"); rail.setFixedWidth(72)
        rail_layout = QVBoxLayout(rail); rail_layout.setContentsMargins(10, 16, 10, 16); rail_layout.setSpacing(9)
        rail_actions = [
            ("text", "Agregar texto fijo", self.add_field),
            ("templates", "Agregar campo variable para Producción", self.add_variable_field),
            ("image", "Agregar imagen", self.add_graphic_image),
            ("shape", "Agregar forma", lambda: self.canvas.add_shape("rectangle")),
            ("templates", "Plantillas (próximamente)", lambda: self.statusBar().showMessage("Plantillas: próximamente")),
        ]
        for icon, tip, slot in rail_actions:
            button = self._icon_button(icon, tip, slot, 50)
            rail_layout.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)
        rail_layout.addStretch()
        rail_layout.addWidget(self._icon_button("background", "Cargar o reemplazar fondo", self.load_image, 50), 0, Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(rail)

        center = QWidget(); center_layout = QVBoxLayout(center); center_layout.setContentsMargins(14, 12, 14, 12); center_layout.setSpacing(8)
        self.quick_actions = QFrame(); self.quick_actions.setObjectName("quickActions")
        quick = QHBoxLayout(self.quick_actions); quick.setContentsMargins(8, 5, 8, 5); quick.setSpacing(5)
        self.quick_buttons: list[QToolButton] = []
        for icon, tip, slot in [
            ("duplicate", "Duplicar selección (Ctrl+D)", self.canvas.duplicate_selected),
            ("front", "Traer al frente", self.canvas.bring_to_front),
            ("back", "Enviar al fondo", self.canvas.send_to_back),
            ("lock", "Bloquear / desbloquear", self.canvas.toggle_lock),
            ("delete", "Eliminar selección (Supr)", self.canvas.delete_selected),
        ]:
            btn = self._icon_button(icon, tip, slot, 34); quick.addWidget(btn); self.quick_buttons.append(btn)
        quick.addStretch()
        center_layout.addWidget(self.quick_actions)
        center_layout.addWidget(self.canvas, 1)
        zoom_row = QHBoxLayout(); zoom_row.addWidget(QLabel("Rueda: zoom · Espacio + arrastrar: mover lienzo")); zoom_row.addStretch()
        zoom_row.addWidget(self._icon_button("fit", "Ajustar lienzo a la ventana", self.canvas.fit_to_view, 34))
        center_layout.addLayout(zoom_row)
        root.addWidget(center, 1)

        right = QFrame(); right.setObjectName("inspectorPanel"); right.setFixedWidth(340)
        right_layout = QVBoxLayout(right); right_layout.setContentsMargins(10, 10, 10, 10)
        self.right_tabs = QTabWidget(); self.inspector_stack = self._make_inspector_stack()
        self.right_tabs.addTab(self.inspector_stack, "Propiedades"); self.right_tabs.addTab(self.layers, "Capas")
        right_layout.addWidget(self.right_tabs); root.addWidget(right)

        self.canvas.fieldSelected.connect(self._studio_selection_changed)
        self._studio_selection_changed(None)
        return page

    def _make_inspector_stack(self):
        from PySide6.QtWidgets import QStackedWidget
        stack = QStackedWidget()
        stack.addWidget(self.document_properties); stack.addWidget(self.text_properties)
        stack.addWidget(self.graphic_properties); stack.addWidget(self.properties)
        return stack

    def add_variable_field(self) -> None:
        if self.project.image_width <= 0 or self.project.image_height <= 0:
            self.show_new_document_dialog(); return
        self.canvas.add_variable_field(); self._sync_fields(); self.show_design()

    def _refresh_layers(self) -> None:
        if not hasattr(self, "layers"):
            return
        selected = self.canvas.selected_id if hasattr(self, "canvas") else None
        self.layers.blockSignals(True); self.layers.clear()
        for item in reversed(self.canvas.all_items()):
            if isinstance(item, TextField):
                kind = "VAR" if item.is_variable() else "TXT"
            elif isinstance(item, ImageElement):
                kind = "IMG"
            else:
                kind = "FORMA"
            state = "oculto" if not item.visible else ""
            lock = "bloqueado" if item.locked else ""
            suffix = " · ".join(part for part in (state, lock) if part)
            row = QListWidgetItem(f"[{kind}] {item.name}" + (f" · {suffix}" if suffix else ""))
            row.setData(Qt.ItemDataRole.UserRole, item.id); self.layers.addItem(row)
            if item.id == selected:
                self.layers.setCurrentItem(row)
        self.layers.blockSignals(False)

    def _build_production_page(self) -> QWidget:
        page = QWidget(); root = QHBoxLayout(page); root.setContentsMargins(18, 16, 18, 16); root.setSpacing(14)
        main = QWidget(); main_layout = QVBoxLayout(main); main_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Producción"); title.setStyleSheet("font-size:28px; font-weight:800;")
        subtitle = QLabel("Define qué cambia en cada copia: asigna listas o numeración a tus campos variables y luego exporta.")
        subtitle.setWordWrap(True); subtitle.setStyleSheet("color:#64748b;")
        main_layout.addWidget(title); main_layout.addWidget(subtitle)
        steps = QLabel("1  Campos variables    →    2  Datos    →    3  Imposición    →    4  Exportación")
        steps.setStyleSheet("padding:14px; background:white; border:1px solid #e2e8f0; border-radius:10px; font-weight:700;")
        main_layout.addWidget(steps)

        vertical = QSplitter(Qt.Orientation.Vertical)
        mapping_group = QGroupBox("1. ¿Qué valor recibe cada campo variable?")
        mapping_layout = QVBoxLayout(mapping_group)
        mapping_scroll = QScrollArea(); mapping_scroll.setWidgetResizable(True)
        self.mapping_panel = ProductionMappingPanel(); self.mapping_panel.changed.connect(self._mapping_changed)
        mapping_scroll.setWidget(self.mapping_panel); mapping_layout.addWidget(mapping_scroll)
        vertical.addWidget(mapping_group)

        data_group = QGroupBox("2. Listas / datos")
        data_layout = QVBoxLayout(data_group)
        data_hint = QLabel("Importa una tabla con columnas o pega una lista. Luego asigna cada campo variable a la columna que corresponda arriba.")
        data_hint.setWordWrap(True); data_hint.setStyleSheet("color:#64748b;")
        data_layout.addWidget(data_hint)
        buttons = QHBoxLayout(); buttons.setSpacing(5)
        buttons.addWidget(self._icon_button("import", "Importar CSV / Excel", self.load_data))
        buttons.addWidget(self._icon_button("paste", "Pegar lista desde el portapapeles", self.paste_data))
        buttons.addWidget(self._icon_button("add", "Agregar fila", self._add_data_row))
        buttons.addWidget(self._icon_button("delete", "Eliminar filas seleccionadas (Supr)", self._delete_data_rows))
        buttons.addStretch(); data_layout.addLayout(buttons); data_layout.addWidget(self.data_table)
        self.data_table.itemChanged.connect(self._data_changed)
        vertical.addWidget(data_group); vertical.setSizes([440, 330])
        main_layout.addWidget(vertical, 1); root.addWidget(main, 1)

        sidebar_scroll = QScrollArea(); sidebar_scroll.setWidgetResizable(True); sidebar_scroll.setFixedWidth(390)
        sidebar = QWidget(); side = QVBoxLayout(sidebar); side.setContentsMargins(8, 8, 8, 8)
        summary = QGroupBox("Resumen"); summary_layout = QVBoxLayout(summary)
        self.production_summary = QLabel("Configura los campos variables para ver el resumen.")
        self.production_summary.setWordWrap(True); summary_layout.addWidget(self.production_summary)
        preview_btn = QPushButton(studio_icon("preview", 20), "Vista previa de impresión")
        preview_btn.clicked.connect(self.preview); summary_layout.addWidget(preview_btn); side.addWidget(summary)

        self.use_original_piece.setText("Usar tamaño del diseño")
        imposition = QGroupBox("3. Imposición"); imf = QFormLayout(imposition)
        imf.addRow("Hoja", self.size_combo); imf.addRow("DPI", self.dpi); imf.addRow(self.use_original_piece)
        imf.addRow("Ancho pieza mm", self.piece_w_mm); imf.addRow("Alto pieza mm", self.piece_h_mm)
        imf.addRow("Margen mm", self.margin_mm); imf.addRow("Separación H", self.gap_x_mm); imf.addRow("Separación V", self.gap_y_mm)
        imf.addRow("Relleno", self.fill_mode); imf.addRow("Orden", self.order_mode); side.addWidget(imposition)

        export = QGroupBox("4. Exportación"); ex = QVBoxLayout(export)
        pdf = QPushButton(studio_icon("pdf", 20), "Generar PDF"); pdf.clicked.connect(self.generate_pdf)
        images = QPushButton(studio_icon("image", 20), "Exportar PNG / JPG"); images.clicked.connect(self.generate_images)
        ex.addWidget(pdf); ex.addWidget(images); side.addWidget(export); side.addStretch()
        sidebar_scroll.setWidget(sidebar); root.addWidget(sidebar_scroll)
        return page

    def _add_data_row(self) -> None:
        self.data_table.add_empty_row(); self._data_changed()

    def _delete_data_rows(self) -> None:
        removed = self.data_table.delete_selected_rows()
        self.statusBar().showMessage(f"Filas eliminadas: {removed}" if removed else "Selecciona una fila para eliminar")
        self._data_changed()

    def _data_changed(self, *_args) -> None:
        if not hasattr(self, "mapping_panel"):
            return
        self.project.data = self.data_table.rows()
        self.mapping_panel.set_context(self.project.fields, self.project.data, self.project.export)
        self._update_production_summary(); self._update_layout_info()

    def load_data(self) -> None:
        super().load_data(); self._data_changed()

    def paste_data(self) -> None:
        super().paste_data(); self._data_changed()

    def _mapping_changed(self) -> None:
        self._sync_fields(); self._update_production_summary(); self._update_layout_info()

    def _raw_rows(self) -> list[dict[str, str]]:
        return self.data_table.rows()

    def _production_rows(self) -> list[dict[str, str]]:
        return build_production_rows(self.project.fields, self._raw_rows())

    def _sync_project(self) -> None:
        self._sync_fields(); self.project.data = self._raw_rows(); self._sync_export_settings()
        self.project.export.numbering.enabled = False

    def show_production(self) -> None:
        if self.project.image_width <= 0 or self.project.image_height <= 0:
            self.show_welcome(); return
        self._sync_project()
        self.mapping_panel.set_context(self.project.fields, self.project.data, self.project.export)
        self._update_production_summary(); self._update_layout_info()
        self.pages.setCurrentWidget(self.production_page)
        self.design_mode_btn.setChecked(False); self.production_mode_btn.setChecked(True)

    def _update_production_summary(self) -> None:
        rows = self._production_rows(); variables = variable_fields(self.project.fields)
        width, height = self.project.document_size()
        lines = [f"Diseño: {width} × {height} px", f"Copias a generar: {len(rows)}", f"Campos variables: {len(variables)}"]
        for field in variables:
            source = f"numeración ({field.number_start}…)" if field.production_source == "numbering" else f"columna '{field.source_column or field.variable_key()}'"
            lines.append(f"• {field.name} ← {source}")
        if self.layout_info.text(): lines.append(self.layout_info.text())
        self.production_summary.setText("\n".join(lines))

    def _update_layout_info(self) -> None:
        if not self.project.image_width or not self.project.image_height:
            self.layout_info.setText("Crea un lienzo para calcular la imposición."); return
        try:
            layout = compute_layout(self.project.export, self.project.document_size())
            total = len(self._production_rows())
            pages = (total + layout.slots_per_page - 1) // layout.slots_per_page if layout.slots_per_page and total else 0
            self.layout_info.setText(f"{layout.slots_per_page} por hoja · {total} copias · {pages} hoja(s)")
        except Exception as exc:
            self.layout_info.setText(str(exc))

    def _validate(self, require_output: bool) -> bool:
        self._sync_project(); width, height = self.project.document_size()
        if width <= 0 or height <= 0:
            QMessageBox.warning(self, "Falta lienzo", "Crea un lienzo o carga una imagen de fondo."); return False
        if self.project.image_path and not Path(self.project.image_path).exists():
            QMessageBox.warning(self, "Fondo no encontrado", "La imagen de fondo del proyecto ya no existe."); return False
        if not self.project.fields and not self.project.elements:
            QMessageBox.warning(self, "Diseño vacío", "Agrega al menos texto, una imagen o una forma."); return False
        errors = production_errors(self.project.fields, self._raw_rows())
        if errors:
            QMessageBox.warning(self, "Falta configurar Producción", "Corrige estas asignaciones:\n\n" + "\n".join("• " + e for e in errors)); return False
        try:
            layout = compute_layout(self.project.export, (width, height))
            if layout.slots_per_page <= 0:
                QMessageBox.warning(self, "La pieza no entra", "Reduce el tamaño de la pieza, los márgenes o las separaciones."); return False
        except Exception as exc:
            self._error("Configuración de hoja inválida", exc); return False
        return True

    def open_generated_viewer(self) -> None:
        if not self._validate(require_output=False): return
        base = document_base_path(self.project)
        AdvancedPreviewDialog(base, self.project.fields, self.project.elements, self._production_rows(), self.project.export, 0, self).exec()

    def generate_pdf(self) -> None:
        if not self._validate(require_output=False): return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "plantillas_generadas.pdf", "PDF (*.pdf)")
        if not path: return
        progress = QProgressDialog("Generando PDF...", "Cancelar", 0, 1, self); progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        try:
            count = export_pdf(document_base_path(self.project), self.project.fields, self._production_rows(), self.project.export, path,
                progress=lambda done, total: (progress.setMaximum(total), progress.setValue(done), QApplication.processEvents()),
                should_cancel=progress.wasCanceled, elements=self.project.elements)
            QMessageBox.information(self, "PDF generado", f"Páginas generadas: {count}\nArchivo: {path}")
        except Exception as exc: self._error("No se pudo generar el PDF", exc)
        finally: progress.close()

    def generate_images(self) -> None:
        if not self._validate(require_output=False): return
        folder = QFileDialog.getExistingDirectory(self, "Carpeta de salida")
        if not folder: return
        self.project.export.output_folder = folder
        progress = QProgressDialog("Exportando imágenes...", "Cancelar", 0, 1, self); progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        try:
            files = export_images(document_base_path(self.project), self.project.fields, self._production_rows(), self.project.export, folder,
                progress=lambda done, total: (progress.setMaximum(total), progress.setValue(done), QApplication.processEvents()),
                should_cancel=progress.wasCanceled, elements=self.project.elements)
            QMessageBox.information(self, "Imágenes exportadas", f"Archivos generados: {len(files)}\nCarpeta: {folder}")
        except Exception as exc: self._error("No se pudieron exportar las imágenes", exc)
        finally: progress.close()
