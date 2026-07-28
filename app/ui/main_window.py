from __future__ import annotations

from pathlib import Path
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QInputDialog, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QProgressDialog, QPushButton, QScrollArea,
    QSpinBox, QSplitter, QStatusBar, QToolBar, QVBoxLayout, QWidget,
)

from app.core.data_loader import load_data_file, rows_from_pasted_text
from app.core.image_exporter import export_images
from app.core.imposition import compute_layout, prepare_rows
from app.core.models import ExportSettings, FillMode, OrderMode, PageSize, TemplateProject
from app.core.pdf_exporter import export_pdf
from app.core.project_io import load_project, save_project
from app.core.renderer import missing_variables
from app.ui.canvas_widget import CanvasWidget
from app.ui.data_table import DataTableWidget
from app.ui.field_properties_panel import FieldPropertiesPanel
from app.ui.preview_dialog import PreviewDialog


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PlantillaPro Studio")
        icon_path = Path(__file__).resolve().parents[2] / "assets" / "plantillapro_logo.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1550, 920)
        self.project = TemplateProject()
        self.project_path: Path | None = None
        self._build_ui()
        self._connect()
        self._load_export_settings()

    def _build_ui(self) -> None:
        self.toolbar = QToolBar("Acciones")
        self.addToolBar(self.toolbar)
        actions = [
            ("Nuevo", self.new_project), ("Abrir proyecto", self.open_project),
            ("Guardar", self.save_project), ("Guardar como", self.save_project_as),
            ("Cargar imagen", self.load_image), ("Cargar datos", self.load_data),
            ("Pegar lista", self.paste_data), ("Agregar campo", self.add_field),
            ("Duplicar", lambda: self.canvas.duplicate_selected()),
            ("Borrar", lambda: self.canvas.delete_selected()),
            ("Generar", self.open_generated_viewer), ("Previsualizar hoja", self.preview),
            ("Generar PDF", self.generate_pdf), ("Exportar imágenes", self.generate_images),
        ]
        for text, slot in actions:
            action = QAction(text, self)
            action.triggered.connect(slot)
            self.toolbar.addAction(action)

        self.canvas = CanvasWidget()
        self.properties = FieldPropertiesPanel()
        self.data_table = DataTableWidget()
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        left_content = QWidget()
        left_layout = QVBoxLayout(left_content)
        self.image_info = QLabel("Imagen: no cargada")
        self.image_info.setWordWrap(True)
        left_layout.addWidget(self.image_info)

        page_group = QGroupBox("Hoja de impresión")
        page_form = QFormLayout(page_group)
        self.size_combo = QComboBox()
        for label, value in [
            ("Tamaño original", PageSize.ORIGINAL.value), ("A4 vertical", PageSize.A4_PORTRAIT.value),
            ("A4 horizontal", PageSize.A4_LANDSCAPE.value), ("Carta vertical", PageSize.LETTER_PORTRAIT.value),
            ("Carta horizontal", PageSize.LETTER_LANDSCAPE.value), ("Personalizado", PageSize.CUSTOM.value),
        ]:
            self.size_combo.addItem(label, value)
        self.dpi = QSpinBox(); self.dpi.setRange(72, 1200); self.dpi.setValue(300)
        self.custom_w = QSpinBox(); self.custom_w.setRange(1, 30000); self.custom_w.setValue(2480)
        self.custom_h = QSpinBox(); self.custom_h.setRange(1, 30000); self.custom_h.setValue(3508)
        page_form.addRow("Tamaño", self.size_combo)
        page_form.addRow("DPI", self.dpi)
        page_form.addRow("Ancho personalizado px", self.custom_w)
        page_form.addRow("Alto personalizado px", self.custom_h)
        left_layout.addWidget(page_group)

        piece_group = QGroupBox("Pieza y relleno")
        piece_form = QFormLayout(piece_group)
        self.use_original_piece = QCheckBox("Usar tamaño original de la imagen")
        self.piece_w_mm = self._mm_spin(50)
        self.piece_h_mm = self._mm_spin(30)
        self.margin_mm = self._mm_spin(5)
        self.gap_x_mm = self._mm_spin(2)
        self.gap_y_mm = self._mm_spin(2)
        self.fill_mode = QComboBox()
        self.fill_mode.addItem("Vertical y horizontal", FillMode.GRID.value)
        self.fill_mode.addItem("Solo vertical", FillMode.VERTICAL_ONLY.value)
        self.order_mode = QComboBox()
        self.order_mode.addItem("Normal, consecutivo por hoja", OrderMode.NORMAL.value)
        self.order_mode.addItem("Apilado para cortar", OrderMode.CUT_STACK.value)
        piece_form.addRow(self.use_original_piece)
        piece_form.addRow("Ancho de pieza mm", self.piece_w_mm)
        piece_form.addRow("Alto de pieza mm", self.piece_h_mm)
        piece_form.addRow("Margen de hoja mm", self.margin_mm)
        piece_form.addRow("Separación horizontal mm", self.gap_x_mm)
        piece_form.addRow("Separación vertical mm", self.gap_y_mm)
        piece_form.addRow("Relleno", self.fill_mode)
        piece_form.addRow("Orden", self.order_mode)
        left_layout.addWidget(piece_group)

        numbering_group = QGroupBox("Numeración automática")
        numbering_form = QFormLayout(numbering_group)
        self.numbering_enabled = QCheckBox("Generar numeración")
        self.number_start = QSpinBox(); self.number_start.setRange(-999999999, 999999999); self.number_start.setValue(1)
        self.number_count = QSpinBox(); self.number_count.setRange(1, 1000000); self.number_count.setValue(100)
        self.number_step = QSpinBox(); self.number_step.setRange(-999999, 999999); self.number_step.setValue(1)
        self.number_digits = QSpinBox(); self.number_digits.setRange(0, 20)
        self.number_prefix = QLineEdit()
        self.number_suffix = QLineEdit()
        self.override_number = QCheckBox("Reemplazar columna numero importada")
        numbering_form.addRow(self.numbering_enabled)
        numbering_form.addRow("Número inicial", self.number_start)
        numbering_form.addRow("Cantidad", self.number_count)
        numbering_form.addRow("Incremento", self.number_step)
        numbering_form.addRow("Cantidad de dígitos", self.number_digits)
        numbering_form.addRow("Prefijo", self.number_prefix)
        numbering_form.addRow("Sufijo", self.number_suffix)
        numbering_form.addRow(self.override_number)
        left_layout.addWidget(numbering_group)

        self.layout_info = QLabel("Carga una imagen para calcular cuántas piezas entran.")
        self.layout_info.setWordWrap(True)
        self.layout_info.setStyleSheet("font-weight: 600; padding: 6px;")
        left_layout.addWidget(self.layout_info)
        left_layout.addStretch()

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left_content)
        left_scroll.setMinimumWidth(310)

        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        table_buttons = QHBoxLayout()
        add_row = QPushButton("Agregar fila"); add_row.clicked.connect(self.data_table.add_empty_row)
        del_row = QPushButton("Eliminar filas"); del_row.clicked.connect(self.data_table.delete_selected_rows)
        table_buttons.addWidget(QLabel("Datos opcionales")); table_buttons.addStretch()
        table_buttons.addWidget(add_row); table_buttons.addWidget(del_row)
        bottom_layout.addLayout(table_buttons)
        bottom_layout.addWidget(self.data_table)

        center_split = QSplitter(Qt.Orientation.Vertical)
        center_split.addWidget(self.canvas); center_split.addWidget(bottom); center_split.setSizes([620, 240])
        main_split = QSplitter(Qt.Orientation.Horizontal)
        main_split.addWidget(left_scroll); main_split.addWidget(center_split); main_split.addWidget(self.properties)
        main_split.setSizes([330, 900, 320])
        self.setCentralWidget(main_split)
        self.setStatusBar(QStatusBar())

    @staticmethod
    def _mm_spin(value: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox(); spin.setRange(0, 2000); spin.setDecimals(2); spin.setSingleStep(0.5); spin.setValue(value)
        return spin

    def _connect(self) -> None:
        self.canvas.fieldSelected.connect(self.properties.set_field)
        self.canvas.fieldsChanged.connect(self._sync_fields)
        self.canvas.statusChanged.connect(self.statusBar().showMessage)
        self.properties.changed.connect(lambda: (self.canvas.update(), self._sync_fields()))
        controls = [
            self.size_combo, self.dpi, self.custom_w, self.custom_h, self.use_original_piece,
            self.piece_w_mm, self.piece_h_mm, self.margin_mm, self.gap_x_mm, self.gap_y_mm,
            self.fill_mode, self.order_mode, self.numbering_enabled, self.number_start,
            self.number_count, self.number_step, self.number_digits, self.number_prefix,
            self.number_suffix, self.override_number,
        ]
        for control in controls:
            signal = getattr(control, "currentIndexChanged", None) or getattr(control, "valueChanged", None) or getattr(control, "toggled", None) or getattr(control, "textChanged", None)
            signal.connect(self._on_export_changed)

    def _on_export_changed(self, *_args) -> None:
        self._sync_export_settings()
        self._update_control_states()
        self._update_layout_info()

    def new_project(self) -> None:
        self.project = TemplateProject(); self.project_path = None
        self.canvas.set_fields([]); self.data_table.set_rows([])
        self.image_info.setText("Imagen: no cargada")
        self._load_export_settings(); self.statusBar().showMessage("Proyecto nuevo")

    def load_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Cargar imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if not path: return
        try:
            with Image.open(path) as image:
                self.project.image_path = path
                self.project.image_width, self.project.image_height = image.size
                self.image_info.setText(f"Imagen: {Path(path).name}\n{image.width} × {image.height} px")
            self.canvas.load_image(path); self._update_layout_info(); self.statusBar().showMessage("Imagen cargada")
        except Exception as exc: self._error("No se pudo cargar la imagen", exc)

    def add_field(self) -> None:
        if not self.project.image_path:
            QMessageBox.warning(self, "Imagen requerida", "Carga una imagen antes de crear campos."); return
        self.canvas.add_field(); self._sync_fields()

    def load_data(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Cargar datos", "", "Datos (*.txt *.csv *.xlsx)")
        if not path: return
        try:
            rows = load_data_file(path); self.project.data = rows; self.data_table.set_rows(rows)
            self.statusBar().showMessage(f"Datos cargados: {len(rows)} filas")
        except Exception as exc: self._error("No se pudieron cargar los datos", exc)

    def paste_data(self) -> None:
        rows = rows_from_pasted_text(QGuiApplication.clipboard().text())
        if not rows:
            QMessageBox.warning(self, "Portapapeles vacío", "No se detectaron filas para pegar."); return
        self.project.data = rows; self.data_table.set_rows(rows)
        self.statusBar().showMessage(f"Datos pegados: {len(rows)} filas")

    def preview(self) -> None:
        self.open_generated_viewer()

    def open_generated_viewer(self) -> None:
        if not self._validate(require_output=False): return
        PreviewDialog(self.project.image_path, self.project.fields, self._table_rows(), self.project.export, 0, self).exec()

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
                should_cancel=progress.wasCanceled)
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
        self.project.export.output_folder = folder
        self.project.export.filename_pattern = pattern or "{{numero}}_{{nombre}}"
        self.project.export.image_format = fmt
        progress = QProgressDialog("Exportando imágenes...", "Cancelar", 0, 1, self)
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        try:
            files = export_images(self.project.image_path, self.project.fields, self._table_rows(), self.project.export, folder,
                progress=lambda done, total: (progress.setMaximum(total), progress.setValue(done), QApplication.processEvents()),
                should_cancel=progress.wasCanceled)
            QMessageBox.information(self, "Imágenes exportadas", f"Archivos generados: {len(files)}\nCarpeta: {folder}")
        except Exception as exc: self._error("No se pudieron exportar las imágenes", exc)
        finally: progress.close()

    def open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Abrir proyecto", "", "Proyecto JSON (*.json)")
        if not path: return
        try:
            self.project = load_project(path); self.project_path = Path(path)
            if self.project.image_path and Path(self.project.image_path).exists():
                self.canvas.load_image(self.project.image_path)
                self.image_info.setText(f"Imagen: {Path(self.project.image_path).name}\n{self.project.image_width} × {self.project.image_height} px")
            self.canvas.set_fields(self.project.fields); self.data_table.set_rows(self.project.data)
            self._load_export_settings(); self.statusBar().showMessage("Proyecto abierto")
        except Exception as exc: self._error("No se pudo abrir el proyecto", exc)

    def save_project(self) -> None:
        if not self.project_path: self.save_project_as(); return
        self._sync_project()
        try: save_project(self.project, self.project_path); self.statusBar().showMessage("Proyecto guardado")
        except Exception as exc: self._error("No se pudo guardar el proyecto", exc)

    def save_project_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Guardar proyecto", "proyecto_plantilla.json", "Proyecto JSON (*.json)")
        if not path: return
        self.project_path = Path(path); self.save_project()

    def _sync_fields(self) -> None:
        self.project.fields = self.canvas.fields

    def _sync_project(self) -> None:
        self._sync_fields(); self.project.data = self._table_rows(); self._sync_export_settings()

    def _sync_export_settings(self) -> None:
        e = self.project.export
        e.dpi = self.dpi.value(); e.page_size = PageSize(self.size_combo.currentData())
        e.custom_width_px = self.custom_w.value(); e.custom_height_px = self.custom_h.value()
        e.use_original_piece_size = self.use_original_piece.isChecked()
        e.piece_width_mm = self.piece_w_mm.value(); e.piece_height_mm = self.piece_h_mm.value()
        e.margin_left_mm = e.margin_top_mm = e.margin_right_mm = e.margin_bottom_mm = self.margin_mm.value()
        e.gap_x_mm = self.gap_x_mm.value(); e.gap_y_mm = self.gap_y_mm.value()
        e.fill_mode = FillMode(self.fill_mode.currentData()); e.order_mode = OrderMode(self.order_mode.currentData())
        n = e.numbering
        n.enabled = self.numbering_enabled.isChecked(); n.start = self.number_start.value()
        n.count = self.number_count.value(); n.step = self.number_step.value(); n.digits = self.number_digits.value()
        n.prefix = self.number_prefix.text(); n.suffix = self.number_suffix.text(); n.override_existing = self.override_number.isChecked()

    def _load_export_settings(self) -> None:
        e = self.project.export
        self.size_combo.setCurrentIndex(max(0, self.size_combo.findData(e.page_size.value)))
        self.dpi.setValue(e.dpi); self.custom_w.setValue(e.custom_width_px or 2480); self.custom_h.setValue(e.custom_height_px or 3508)
        self.use_original_piece.setChecked(e.use_original_piece_size)
        self.piece_w_mm.setValue(e.piece_width_mm); self.piece_h_mm.setValue(e.piece_height_mm)
        self.margin_mm.setValue(e.margin_left_mm); self.gap_x_mm.setValue(e.gap_x_mm); self.gap_y_mm.setValue(e.gap_y_mm)
        self.fill_mode.setCurrentIndex(max(0, self.fill_mode.findData(e.fill_mode.value)))
        self.order_mode.setCurrentIndex(max(0, self.order_mode.findData(e.order_mode.value)))
        n = e.numbering
        self.numbering_enabled.setChecked(n.enabled); self.number_start.setValue(n.start); self.number_count.setValue(n.count)
        self.number_step.setValue(n.step); self.number_digits.setValue(n.digits); self.number_prefix.setText(n.prefix)
        self.number_suffix.setText(n.suffix); self.override_number.setChecked(n.override_existing)
        self._update_control_states(); self._update_layout_info()

    def _update_control_states(self) -> None:
        custom_page = self.size_combo.currentData() == PageSize.CUSTOM.value
        self.custom_w.setEnabled(custom_page); self.custom_h.setEnabled(custom_page)
        custom_piece = not self.use_original_piece.isChecked()
        self.piece_w_mm.setEnabled(custom_piece); self.piece_h_mm.setEnabled(custom_piece)
        enabled = self.numbering_enabled.isChecked()
        for widget in [self.number_start, self.number_count, self.number_step, self.number_digits, self.number_prefix, self.number_suffix, self.override_number]:
            widget.setEnabled(enabled)

    def _update_layout_info(self) -> None:
        if not self.project.image_width or not self.project.image_height:
            self.layout_info.setText("Carga una imagen para calcular cuántas piezas entran."); return
        try:
            layout = compute_layout(self.project.export, (self.project.image_width, self.project.image_height))
            total = len(prepare_rows(self._table_rows(), self.project.export))
            pages = (total + layout.slots_per_page - 1) // layout.slots_per_page if layout.slots_per_page and total else 0
            self.layout_info.setText(
                f"Entran {layout.columns} columnas × {layout.rows} filas = {layout.slots_per_page} piezas por hoja.\n"
                f"Piezas a generar: {total}. Hojas necesarias: {pages}."
            )
        except Exception as exc:
            self.layout_info.setText(str(exc))

    def _table_rows(self) -> list[dict[str, str]]:
        return self.data_table.rows()

    def _validate(self, require_output: bool) -> bool:
        self._sync_project()
        if not self.project.image_path or not Path(self.project.image_path).exists():
            QMessageBox.warning(self, "Falta imagen", "Carga una imagen base válida."); return False
        if not self.project.fields:
            QMessageBox.warning(self, "Faltan campos", "Crea al menos un rectángulo de texto."); return False
        rows = self._table_rows()
        if not rows and not (self.project.export.numbering.enabled and self.project.export.numbering.count > 0):
            QMessageBox.warning(self, "Faltan datos", "Carga datos o activa la numeración automática con una cantidad mayor a cero."); return False
        columns: set[str] = set()
        for row in rows: columns.update(row.keys())
        if self.project.export.numbering.enabled: columns.add(self.project.export.numbering.field_name)
        missing = missing_variables(self.project.fields, columns)
        if missing:
            QMessageBox.warning(self, "Variables no encontradas", "No existen estas columnas: " + ", ".join(sorted(missing))); return False
        try:
            layout = compute_layout(self.project.export, (self.project.image_width, self.project.image_height))
            if layout.slots_per_page <= 0:
                QMessageBox.warning(self, "La pieza no entra", "Reduce el tamaño de la pieza, los márgenes o las separaciones."); return False
        except Exception as exc:
            self._error("Configuración de hoja inválida", exc); return False
        return True

    def _error(self, title: str, exc: Exception) -> None:
        QMessageBox.critical(self, title, str(exc))
