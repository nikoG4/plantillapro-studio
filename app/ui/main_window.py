from __future__ import annotations

from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.core.data_loader import load_data_file, rows_from_pasted_text
from app.core.image_exporter import export_images
from app.core.models import ExportSettings, PageSize, TemplateProject
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
        self.resize(1450, 900)
        self.project = TemplateProject()
        self.project_path: Path | None = None
        self._build_ui()
        self._connect()

    def _build_ui(self) -> None:
        self.toolbar = QToolBar("Acciones")
        self.addToolBar(self.toolbar)
        actions = [
            ("Nuevo", self.new_project),
            ("Abrir proyecto", self.open_project),
            ("Guardar", self.save_project),
            ("Guardar como", self.save_project_as),
            ("Cargar imagen", self.load_image),
            ("Cargar datos", self.load_data),
            ("Pegar lista", self.paste_data),
            ("Agregar campo", self.add_field),
            ("Duplicar", lambda: self.canvas.duplicate_selected()),
            ("Borrar", lambda: self.canvas.delete_selected()),
            ("Generar", self.open_generated_viewer),
            ("Previsualizar fila", self.preview),
            ("Generar PDF", self.generate_pdf),
            ("Exportar imágenes", self.generate_images),
        ]
        for text, slot in actions:
            action = QAction(text, self)
            action.triggered.connect(slot)
            self.toolbar.addAction(action)

        self.canvas = CanvasWidget()
        self.properties = FieldPropertiesPanel()
        self.data_table = DataTableWidget()
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        self.image_info = QLabel("Imagen: no cargada")
        self.size_combo = QComboBox()
        for label, value in [
            ("Tamaño original", PageSize.ORIGINAL.value),
            ("A4 vertical", PageSize.A4_PORTRAIT.value),
            ("A4 horizontal", PageSize.A4_LANDSCAPE.value),
            ("Carta vertical", PageSize.LETTER_PORTRAIT.value),
            ("Carta horizontal", PageSize.LETTER_LANDSCAPE.value),
            ("Personalizado", PageSize.CUSTOM.value),
        ]:
            self.size_combo.addItem(label, value)
        self.dpi = QSpinBox(); self.dpi.setRange(72, 1200); self.dpi.setValue(300)
        self.custom_w = QSpinBox(); self.custom_w.setRange(1, 30000); self.custom_w.setValue(2480)
        self.custom_h = QSpinBox(); self.custom_h.setRange(1, 30000); self.custom_h.setValue(3508)
        left_layout.addWidget(self.image_info)
        left_layout.addWidget(QLabel("Tamaño de salida"))
        left_layout.addWidget(self.size_combo)
        left_layout.addWidget(QLabel("DPI"))
        left_layout.addWidget(self.dpi)
        left_layout.addWidget(QLabel("Ancho personalizado px"))
        left_layout.addWidget(self.custom_w)
        left_layout.addWidget(QLabel("Alto personalizado px"))
        left_layout.addWidget(self.custom_h)
        left_layout.addStretch()

        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        table_buttons = QHBoxLayout()
        add_row = QPushButton("Agregar fila"); add_row.clicked.connect(self.data_table.add_empty_row)
        del_row = QPushButton("Eliminar filas"); del_row.clicked.connect(self.data_table.delete_selected_rows)
        table_buttons.addWidget(QLabel("Datos"))
        table_buttons.addStretch()
        table_buttons.addWidget(add_row); table_buttons.addWidget(del_row)
        bottom_layout.addLayout(table_buttons)
        bottom_layout.addWidget(self.data_table)

        center_split = QSplitter(Qt.Orientation.Vertical)
        center_split.addWidget(self.canvas)
        center_split.addWidget(bottom)
        center_split.setSizes([620, 240])

        main_split = QSplitter(Qt.Orientation.Horizontal)
        main_split.addWidget(left)
        main_split.addWidget(center_split)
        main_split.addWidget(self.properties)
        main_split.setSizes([220, 900, 320])
        self.setCentralWidget(main_split)
        self.setStatusBar(QStatusBar())

    def _connect(self) -> None:
        self.canvas.fieldSelected.connect(self.properties.set_field)
        self.canvas.fieldsChanged.connect(self._sync_fields)
        self.canvas.statusChanged.connect(self.statusBar().showMessage)
        self.properties.changed.connect(lambda: (self.canvas.update(), self._sync_fields()))
        self.size_combo.currentIndexChanged.connect(self._sync_export_settings)
        self.dpi.valueChanged.connect(self._sync_export_settings)
        self.custom_w.valueChanged.connect(self._sync_export_settings)
        self.custom_h.valueChanged.connect(self._sync_export_settings)

    def new_project(self) -> None:
        self.project = TemplateProject()
        self.project_path = None
        self.canvas.set_fields([])
        self.data_table.set_rows([])
        self.image_info.setText("Imagen: no cargada")
        self.statusBar().showMessage("Proyecto nuevo")

    def load_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Cargar imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if not path:
            return
        try:
            image = Image.open(path)
            self.project.image_path = path
            self.project.image_width, self.project.image_height = image.size
            self.canvas.load_image(path)
            self.image_info.setText(f"Imagen: {Path(path).name}\n{image.width} x {image.height} px")
            self.statusBar().showMessage("Imagen cargada")
        except Exception as exc:
            self._error("No se pudo cargar la imagen", exc)

    def add_field(self) -> None:
        if not self.project.image_path:
            QMessageBox.warning(self, "Imagen requerida", "Carga una imagen antes de crear campos.")
            return
        self.canvas.add_field()
        self._sync_fields()

    def load_data(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Cargar datos", "", "Datos (*.txt *.csv *.xlsx)")
        if not path:
            return
        try:
            rows = load_data_file(path)
            self.project.data = rows
            self.data_table.set_rows(rows)
            self.statusBar().showMessage(f"Datos cargados: {len(rows)} filas")
        except Exception as exc:
            self._error("No se pudieron cargar los datos", exc)

    def paste_data(self) -> None:
        rows = rows_from_pasted_text(QGuiApplication.clipboard().text())
        if not rows:
            QMessageBox.warning(self, "Portapapeles vacío", "No se detectaron filas para pegar.")
            return
        self.project.data = rows
        self.data_table.set_rows(rows)
        self.statusBar().showMessage(f"Datos pegados: {len(rows)} filas")

    def preview(self) -> None:
        if not self._validate(require_output=False):
            return
        rows = self._table_rows()
        index, ok = QInputDialog.getInt(self, "Fila a previsualizar", "Número de fila", 1, 1, len(rows))
        if not ok:
            return
        self._sync_export_settings()
        PreviewDialog(self.project.image_path, self.project.fields, rows, self.project.export, index - 1, self).exec()

    def open_generated_viewer(self) -> None:
        if not self._validate(require_output=False):
            return
        self._sync_export_settings()
        PreviewDialog(self.project.image_path, self.project.fields, self._table_rows(), self.project.export, 0, self).exec()

    def generate_pdf(self) -> None:
        if not self._validate(require_output=False):
            return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "plantillas_generadas.pdf", "PDF (*.pdf)")
        if not path:
            return
        self._sync_export_settings()
        self.project.export.output_pdf = path
        rows = self._table_rows()
        progress = QProgressDialog("Generando PDF...", "Cancelar", 0, len(rows), self)
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        try:
            count = export_pdf(
                self.project.image_path,
                self.project.fields,
                rows,
                self.project.export,
                path,
                progress=lambda done, total: (progress.setValue(done), QApplication.processEvents()),
                should_cancel=progress.wasCanceled,
            )
            QMessageBox.information(self, "PDF generado", f"Páginas generadas: {count}\nArchivo: {path}")
        except Exception as exc:
            self._error("No se pudo generar el PDF", exc)
        finally:
            progress.close()

    def generate_images(self) -> None:
        if not self._validate(require_output=False):
            return
        folder = QFileDialog.getExistingDirectory(self, "Carpeta de salida")
        if not folder:
            return
        pattern, ok = QInputDialog.getText(self, "Patrón de archivo", "Patrón", text=self.project.export.filename_pattern)
        if not ok:
            return
        fmt, ok = QInputDialog.getItem(self, "Formato", "Formato", ["PNG", "JPG"], 0, False)
        if not ok:
            return
        self._sync_export_settings()
        self.project.export.output_folder = folder
        self.project.export.filename_pattern = pattern or "{{numero}}_{{nombre}}"
        self.project.export.image_format = fmt
        rows = self._table_rows()
        progress = QProgressDialog("Exportando imágenes...", "Cancelar", 0, len(rows), self)
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        try:
            files = export_images(
                self.project.image_path,
                self.project.fields,
                rows,
                self.project.export,
                folder,
                progress=lambda done, total: (progress.setValue(done), QApplication.processEvents()),
                should_cancel=progress.wasCanceled,
            )
            QMessageBox.information(self, "Imágenes exportadas", f"Archivos generados: {len(files)}\nCarpeta: {folder}")
        except Exception as exc:
            self._error("No se pudieron exportar las imágenes", exc)
        finally:
            progress.close()

    def open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Abrir proyecto", "", "Proyecto JSON (*.json)")
        if not path:
            return
        try:
            self.project = load_project(path)
            self.project_path = Path(path)
            if self.project.image_path and Path(self.project.image_path).exists():
                self.canvas.load_image(self.project.image_path)
                self.image_info.setText(f"Imagen: {Path(self.project.image_path).name}\n{self.project.image_width} x {self.project.image_height} px")
            self.canvas.set_fields(self.project.fields)
            self.data_table.set_rows(self.project.data)
            self._load_export_settings()
            self.statusBar().showMessage("Proyecto abierto")
        except Exception as exc:
            self._error("No se pudo abrir el proyecto", exc)

    def save_project(self) -> None:
        if not self.project_path:
            self.save_project_as()
            return
        self._sync_project()
        try:
            save_project(self.project, self.project_path)
            self.statusBar().showMessage("Proyecto guardado")
        except Exception as exc:
            self._error("No se pudo guardar el proyecto", exc)

    def save_project_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Guardar proyecto", "proyecto_plantilla.json", "Proyecto JSON (*.json)")
        if not path:
            return
        self.project_path = Path(path)
        self.save_project()

    def _sync_fields(self) -> None:
        self.project.fields = self.canvas.fields

    def _sync_project(self) -> None:
        self._sync_fields()
        self.project.data = self._table_rows()
        self._sync_export_settings()

    def _sync_export_settings(self) -> None:
        self.project.export.dpi = self.dpi.value()
        self.project.export.page_size = PageSize(self.size_combo.currentData())
        self.project.export.custom_width_px = self.custom_w.value()
        self.project.export.custom_height_px = self.custom_h.value()

    def _load_export_settings(self) -> None:
        e = self.project.export
        idx = self.size_combo.findData(e.page_size.value)
        self.size_combo.setCurrentIndex(max(0, idx))
        self.dpi.setValue(e.dpi)
        self.custom_w.setValue(e.custom_width_px or 2480)
        self.custom_h.setValue(e.custom_height_px or 3508)

    def _table_rows(self) -> list[dict[str, str]]:
        return self.data_table.rows()

    def _validate(self, require_output: bool) -> bool:
        self._sync_project()
        if not self.project.image_path or not Path(self.project.image_path).exists():
            QMessageBox.warning(self, "Falta imagen", "Carga una imagen base válida.")
            return False
        if not self.project.fields:
            QMessageBox.warning(self, "Faltan campos", "Crea al menos un rectángulo de texto.")
            return False
        rows = self._table_rows()
        if not rows:
            QMessageBox.warning(self, "Faltan datos", "Carga o pega al menos una fila de datos.")
            return False
        columns = set(rows[0].keys())
        missing = missing_variables(self.project.fields, columns)
        if missing:
            QMessageBox.warning(self, "Variables no encontradas", "No existen estas columnas: " + ", ".join(sorted(missing)))
            return False
        return True

    def _error(self, title: str, exc: Exception) -> None:
        QMessageBox.critical(self, title, str(exc))
