from __future__ import annotations

from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QFormLayout, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QMessageBox, QPushButton, QProgressDialog, QScrollArea,
    QSizePolicy, QStackedWidget, QTabWidget, QToolBar, QToolButton, QVBoxLayout,
    QWidget,
)

from app.core.document_base import document_base_path
from app.core.image_exporter import export_images
from app.core.models import DocumentSettings, ImageElement, ShapeElement, TemplateProject, TextField
from app.core.pdf_exporter import export_pdf
from app.ui.advanced_main_window import AdvancedPreviewDialog
from app.ui.document_properties_panel import DocumentPropertiesPanel
from app.ui.new_document_dialog import DocumentChoice, NewDocumentDialog
from app.ui.pro_main_window import ProMainWindow
from app.ui.studio_canvas_widget import StudioCanvasWidget


class StudioMainWindow(ProMainWindow):
    """Polished UX shell that separates designing from batch production."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PlantillaPro Studio")
        self.resize(1500, 900)
        self._legacy_root = self.takeCentralWidget()
        if self._legacy_root:
            self._legacy_root.hide()
        self.toolbar.hide()
        self._replace_canvas_with_studio_canvas()
        self._detach_legacy_docks()
        self.document_properties = DocumentPropertiesPanel(self._document_changed)
        self._build_top_toolbar()
        self._build_studio_pages()
        self._apply_studio_style()
        self.show_welcome()

    def _replace_canvas_with_studio_canvas(self) -> None:
        old = self.canvas
        canvas = StudioCanvasWidget()
        canvas.set_document(old.fields, old.elements)
        self.canvas = canvas
        self.canvas.fieldSelected.connect(self._on_editor_selection)
        self.canvas.fieldSelected.connect(self._sync_graphic_properties_selection)
        self.canvas.fieldsChanged.connect(self._sync_fields)
        self.canvas.statusChanged.connect(self.statusBar().showMessage)

    def _detach_legacy_docks(self) -> None:
        for dock in self.findChildren(QWidget):
            if hasattr(dock, "setFloating") and hasattr(dock, "widget"):
                try:
                    dock.hide()
                except Exception:
                    pass
        self.layers.setParent(None)
        self.graphic_properties.setParent(None)
        self.properties.setParent(None)
        self.data_table.setParent(None)

    def _build_top_toolbar(self) -> None:
        bar = QToolBar("Principal")
        bar.setObjectName("studioTopBar")
        bar.setMovable(False)
        bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, bar)
        self.studio_toolbar = bar

        title = QLabel("  PlantillaPro Studio   ")
        title.setStyleSheet("font-size: 17px; font-weight: 700;")
        bar.addWidget(title)

        self.design_mode_btn = QToolButton()
        self.design_mode_btn.setText("Diseño")
        self.design_mode_btn.setCheckable(True)
        self.design_mode_btn.clicked.connect(self.show_design)
        self.production_mode_btn = QToolButton()
        self.production_mode_btn.setText("Producción")
        self.production_mode_btn.setCheckable(True)
        self.production_mode_btn.clicked.connect(self.show_production)
        bar.addWidget(self.design_mode_btn)
        bar.addWidget(self.production_mode_btn)
        bar.addSeparator()

        for text, slot in [
            ("Nuevo", self.show_new_document_dialog),
            ("Abrir", self.open_project),
            ("Guardar", self.save_project),
            ("Exportar", self.show_production),
        ]:
            action = QAction(text, self)
            action.triggered.connect(slot)
            bar.addAction(action)

    def _build_studio_pages(self) -> None:
        self.pages = QStackedWidget()
        self.welcome_page = self._build_welcome_page()
        self.design_page = self._build_design_page()
        self.production_page = self._build_production_page()
        self.pages.addWidget(self.welcome_page)
        self.pages.addWidget(self.design_page)
        self.pages.addWidget(self.production_page)
        self.setCentralWidget(self.pages)

    def _build_welcome_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(80, 45, 80, 55)
        outer.addStretch()

        card = QFrame()
        card.setObjectName("welcomeCard")
        card.setMaximumWidth(980)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 30, 36, 30)
        card_layout.setSpacing(18)

        heading = QLabel("Empieza tu diseño")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setStyleSheet("font-size: 32px; font-weight: 800; color: #0f172a;")
        subtitle = QLabel("Crea desde un lienzo vacío, usa una imagen como fondo o continúa un proyecto.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 15px; color: #64748b;")
        card_layout.addWidget(heading)
        card_layout.addWidget(subtitle)

        primary = QHBoxLayout()
        primary.setSpacing(14)
        primary.addWidget(self._welcome_action("＋", "Crear lienzo en blanco", "Empieza sin imagen de fondo", self.show_new_document_dialog))
        primary.addWidget(self._welcome_action("▣", "Cargar imagen de fondo", "Usa una imagen como base", self.load_image))
        primary.addWidget(self._welcome_action("▢", "Abrir proyecto", "Continúa donde lo dejaste", self.open_project))
        card_layout.addLayout(primary)

        divider = QFrame(); divider.setFrameShape(QFrame.Shape.HLine)
        card_layout.addWidget(divider)
        preset_title = QLabel("Formatos rápidos")
        preset_title.setStyleSheet("font-weight: 700; color: #334155;")
        card_layout.addWidget(preset_title)
        presets = QHBoxLayout()
        for label, preset in [
            ("Ticket\n7 × 3 cm", "ticket"), ("Flyer\nA5", "a5"),
            ("Sticker\n5 × 5 cm", "sticker"), ("Tarjeta\n9 × 5 cm", "card"),
            ("Post cuadrado\n1080 px", "social-square"),
        ]:
            button = QPushButton(label)
            button.setMinimumHeight(78)
            button.clicked.connect(lambda _=False, p=preset: self.show_new_document_dialog(p))
            presets.addWidget(button)
        card_layout.addLayout(presets)

        row = QHBoxLayout(); row.addStretch(); row.addWidget(card); row.addStretch()
        outer.addLayout(row)
        outer.addStretch()
        return page

    def _welcome_action(self, icon: str, title: str, subtitle: str, slot) -> QPushButton:
        button = QPushButton(f"{icon}\n{title}\n{subtitle}")
        button.setMinimumHeight(135)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button.clicked.connect(slot)
        return button

    def _build_design_page(self) -> QWidget:
        page = QWidget()
        root = QHBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        rail = QFrame(); rail.setObjectName("toolRail"); rail.setFixedWidth(105)
        rail_layout = QVBoxLayout(rail); rail_layout.setContentsMargins(10, 16, 10, 16); rail_layout.setSpacing(10)
        for text, slot in [
            ("T\nTexto", self.add_field),
            ("▣\nImagen", self.add_graphic_image),
            ("○△\nForma", lambda: self.canvas.add_shape("rectangle")),
            ("▦\nPlantillas", lambda: self.statusBar().showMessage("Plantillas: próximamente")),
        ]:
            btn = QPushButton(text); btn.setMinimumHeight(70); btn.clicked.connect(slot); rail_layout.addWidget(btn)
        rail_layout.addStretch()
        bg = QPushButton("▧\nFondo"); bg.setMinimumHeight(62); bg.clicked.connect(self.load_image); rail_layout.addWidget(bg)
        root.addWidget(rail)

        center = QWidget(); center_layout = QVBoxLayout(center); center_layout.setContentsMargins(14, 12, 14, 12); center_layout.setSpacing(8)
        self.quick_actions = QFrame(); self.quick_actions.setObjectName("quickActions")
        quick = QHBoxLayout(self.quick_actions); quick.setContentsMargins(8, 5, 8, 5)
        self.quick_buttons: list[QPushButton] = []
        for text, slot in [
            ("Duplicar", self.canvas.duplicate_selected), ("Frente", self.canvas.bring_to_front),
            ("Atrás", self.canvas.send_to_back), ("Bloquear", self.canvas.toggle_lock),
            ("Eliminar", self.canvas.delete_selected),
        ]:
            btn = QPushButton(text); btn.clicked.connect(slot); quick.addWidget(btn); self.quick_buttons.append(btn)
        quick.addStretch()
        center_layout.addWidget(self.quick_actions)
        center_layout.addWidget(self.canvas, 1)
        zoom_row = QHBoxLayout(); zoom_row.addWidget(QLabel("Rueda: zoom · Espacio + arrastrar: mover lienzo")); zoom_row.addStretch()
        fit = QPushButton("Ajustar vista"); fit.clicked.connect(self.canvas.fit_to_view); zoom_row.addWidget(fit)
        center_layout.addLayout(zoom_row)
        root.addWidget(center, 1)

        right = QFrame(); right.setObjectName("inspectorPanel"); right.setFixedWidth(340)
        right_layout = QVBoxLayout(right); right_layout.setContentsMargins(10, 10, 10, 10)
        self.right_tabs = QTabWidget()
        self.inspector_stack = QStackedWidget()
        self.inspector_stack.addWidget(self.document_properties)
        self.inspector_stack.addWidget(self.properties)
        self.inspector_stack.addWidget(self.graphic_properties)
        self.right_tabs.addTab(self.inspector_stack, "Propiedades")
        self.right_tabs.addTab(self.layers, "Capas")
        right_layout.addWidget(self.right_tabs)
        root.addWidget(right)

        self.canvas.fieldSelected.connect(self._studio_selection_changed)
        self._studio_selection_changed(None)
        return page

    def _studio_selection_changed(self, item) -> None:
        if isinstance(item, TextField):
            self.inspector_stack.setCurrentWidget(self.properties)
        elif isinstance(item, (ImageElement, ShapeElement)):
            self.inspector_stack.setCurrentWidget(self.graphic_properties)
        else:
            self.document_properties.set_project(self.project)
            self.inspector_stack.setCurrentWidget(self.document_properties)
        selected = item is not None
        for button in getattr(self, "quick_buttons", []):
            button.setEnabled(selected)

    def _build_production_page(self) -> QWidget:
        page = QWidget(); root = QHBoxLayout(page); root.setContentsMargins(18, 16, 18, 16); root.setSpacing(14)
        main = QWidget(); main_layout = QVBoxLayout(main); main_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Producción"); title.setStyleSheet("font-size: 28px; font-weight: 800;")
        subtitle = QLabel("Genera archivos listos para imprimir a partir de tu diseño y tus datos."); subtitle.setStyleSheet("color: #64748b;")
        main_layout.addWidget(title); main_layout.addWidget(subtitle)

        steps = QLabel("① Datos     ② Numeración     ③ Imposición     ④ Exportación")
        steps.setStyleSheet("padding: 14px; background: white; border: 1px solid #e2e8f0; border-radius: 10px; font-weight: 700;")
        main_layout.addWidget(steps)

        data_group = QGroupBox("1. Datos")
        data_layout = QVBoxLayout(data_group)
        buttons = QHBoxLayout()
        import_btn = QPushButton("Importar CSV / Excel"); import_btn.clicked.connect(self.load_data)
        paste_btn = QPushButton("Pegar lista"); paste_btn.clicked.connect(self.paste_data)
        add_btn = QPushButton("Agregar fila"); add_btn.clicked.connect(self.data_table.add_empty_row)
        buttons.addWidget(import_btn); buttons.addWidget(paste_btn); buttons.addWidget(add_btn); buttons.addStretch()
        data_layout.addLayout(buttons); data_layout.addWidget(self.data_table)
        main_layout.addWidget(data_group, 1)
        root.addWidget(main, 1)

        sidebar_scroll = QScrollArea(); sidebar_scroll.setWidgetResizable(True); sidebar_scroll.setFixedWidth(390)
        sidebar = QWidget(); side = QVBoxLayout(sidebar); side.setContentsMargins(8, 8, 8, 8)
        summary = QGroupBox("Resumen de producción"); summary_layout = QVBoxLayout(summary)
        self.production_summary = QLabel("Configura los datos y la imposición para ver el resumen.")
        self.production_summary.setWordWrap(True); summary_layout.addWidget(self.production_summary)
        preview_btn = QPushButton("Vista previa de impresión"); preview_btn.clicked.connect(self.preview); summary_layout.addWidget(preview_btn)
        side.addWidget(summary)

        numbering = QGroupBox("2. Numeración"); nf = QFormLayout(numbering)
        nf.addRow(self.numbering_enabled); nf.addRow("Inicio", self.number_start); nf.addRow("Cantidad", self.number_count)
        nf.addRow("Incremento", self.number_step); nf.addRow("Dígitos", self.number_digits); nf.addRow("Prefijo", self.number_prefix); nf.addRow("Sufijo", self.number_suffix)
        side.addWidget(numbering)

        imposition = QGroupBox("3. Imposición"); imf = QFormLayout(imposition)
        imf.addRow("Hoja", self.size_combo); imf.addRow("DPI", self.dpi); imf.addRow(self.use_original_piece)
        imf.addRow("Ancho pieza mm", self.piece_w_mm); imf.addRow("Alto pieza mm", self.piece_h_mm)
        imf.addRow("Margen mm", self.margin_mm); imf.addRow("Separación H", self.gap_x_mm); imf.addRow("Separación V", self.gap_y_mm)
        imf.addRow("Relleno", self.fill_mode); imf.addRow("Orden", self.order_mode)
        side.addWidget(imposition)

        export = QGroupBox("4. Exportación"); ex = QVBoxLayout(export)
        pdf = QPushButton("Generar PDF"); pdf.clicked.connect(self.generate_pdf)
        images = QPushButton("Exportar PNG / JPG"); images.clicked.connect(self.generate_images)
        ex.addWidget(pdf); ex.addWidget(images)
        side.addWidget(export); side.addStretch()
        sidebar_scroll.setWidget(sidebar); root.addWidget(sidebar_scroll)
        return page

    def show_welcome(self) -> None:
        self.pages.setCurrentWidget(self.welcome_page)
        self.design_mode_btn.setChecked(False); self.production_mode_btn.setChecked(False)

    def show_design(self) -> None:
        if self.project.image_width <= 0 or self.project.image_height <= 0:
            self.show_welcome(); return
        self.pages.setCurrentWidget(self.design_page)
        self.design_mode_btn.setChecked(True); self.production_mode_btn.setChecked(False)
        self.document_properties.set_project(self.project)
        self.canvas.fit_to_view()

    def show_production(self) -> None:
        if self.project.image_width <= 0 or self.project.image_height <= 0:
            self.show_welcome(); return
        self._sync_project(); self._update_production_summary()
        self.pages.setCurrentWidget(self.production_page)
        self.design_mode_btn.setChecked(False); self.production_mode_btn.setChecked(True)

    def show_new_document_dialog(self, preset: str | None = None) -> None:
        dialog = NewDocumentDialog(self, preset)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.create_blank_document(dialog.choice())

    def create_blank_document(self, choice: DocumentChoice) -> None:
        self.project = TemplateProject(document=DocumentSettings(
            width=choice.width, height=choice.height, background_color=choice.background_color,
            transparent=choice.transparent, preset=choice.preset,
        ))
        self.project.image_width = choice.width
        self.project.image_height = choice.height
        self.project_path = None
        self.canvas.set_document([], [])
        self.canvas.set_blank_document(choice.width, choice.height, choice.background_color, choice.transparent)
        self.data_table.set_rows([])
        self.image_info.setText(f"Lienzo: {choice.width} × {choice.height} px")
        self._load_export_settings()
        self.document_properties.set_project(self.project)
        self.statusBar().showMessage("Lienzo en blanco creado")
        self.show_design()

    def new_project(self) -> None:
        self.project = TemplateProject()
        self.project_path = None
        self.canvas.set_document([], [])
        self.data_table.set_rows([])
        self.show_welcome()

    def load_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Cargar imagen de fondo", "", "Imágenes (*.png *.jpg *.jpeg *.webp *.bmp)")
        if not path:
            return
        try:
            with Image.open(path) as image:
                width, height = image.size
            if self.project.image_width <= 0 or self.project.image_height <= 0:
                self.project = TemplateProject()
            self.project.image_path = path
            self.project.image_width = width; self.project.image_height = height
            self.project.document.width = width; self.project.document.height = height
            self.project.document.transparent = False; self.project.document.preset = "background-image"
            self.canvas.load_image(path)
            self.canvas.set_document(self.project.fields, self.project.elements)
            self.image_info.setText(f"Fondo: {Path(path).name}\n{width} × {height} px")
            self._update_layout_info(); self.document_properties.set_project(self.project)
            self.statusBar().showMessage("Imagen de fondo cargada")
            self.show_design()
        except Exception as exc:
            self._error("No se pudo cargar la imagen", exc)

    def add_field(self) -> None:
        if self.project.image_width <= 0 or self.project.image_height <= 0:
            self.show_new_document_dialog(); return
        self.canvas.add_field(); self._sync_fields(); self.show_design()

    def add_graphic_image(self) -> None:
        if self.project.image_width <= 0 or self.project.image_height <= 0:
            self.show_new_document_dialog(); return
        super().add_graphic_image()
        self.show_design()

    def open_project(self) -> None:
        super().open_project()
        if self.project.image_width <= 0 or self.project.image_height <= 0:
            return
        if self.project.image_path and Path(self.project.image_path).exists():
            self.canvas.load_image(self.project.image_path)
        else:
            width, height = self.project.document_size()
            self.project.image_width = width; self.project.image_height = height
            self.canvas.set_blank_document(width, height, self.project.document.background_color, self.project.document.transparent)
        self.canvas.set_document(self.project.fields, self.project.elements)
        self.document_properties.set_project(self.project)
        self.show_design()

    def _document_changed(self) -> None:
        width, height = self.project.document_size()
        self.project.image_width = width; self.project.image_height = height
        if not self.project.image_path:
            self.canvas.set_blank_document(width, height, self.project.document.background_color, self.project.document.transparent)
            self.canvas.set_document(self.project.fields, self.project.elements)
        self._update_layout_info(); self.statusBar().showMessage("Lienzo actualizado")

    def open_generated_viewer(self) -> None:
        if not self._validate(require_output=False):
            return
        base = document_base_path(self.project)
        AdvancedPreviewDialog(base, self.project.fields, self.project.elements, self._table_rows(), self.project.export, 0, self).exec()

    def generate_pdf(self) -> None:
        if not self._validate(require_output=False):
            return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "plantillas_generadas.pdf", "PDF (*.pdf)")
        if not path:
            return
        progress = QProgressDialog("Generando PDF...", "Cancelar", 0, 1, self)
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        try:
            count = export_pdf(document_base_path(self.project), self.project.fields, self._table_rows(), self.project.export, path,
                progress=lambda done, total: (progress.setMaximum(total), progress.setValue(done), QApplication.processEvents()),
                should_cancel=progress.wasCanceled, elements=self.project.elements)
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
        self.project.export.output_folder = folder
        progress = QProgressDialog("Exportando imágenes...", "Cancelar", 0, 1, self)
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        try:
            files = export_images(document_base_path(self.project), self.project.fields, self._table_rows(), self.project.export, folder,
                progress=lambda done, total: (progress.setMaximum(total), progress.setValue(done), QApplication.processEvents()),
                should_cancel=progress.wasCanceled, elements=self.project.elements)
            QMessageBox.information(self, "Imágenes exportadas", f"Archivos generados: {len(files)}\nCarpeta: {folder}")
        except Exception as exc:
            self._error("No se pudieron exportar las imágenes", exc)
        finally:
            progress.close()

    def _update_production_summary(self) -> None:
        rows = self._table_rows()
        width, height = self.project.document_size()
        text = [f"Diseño: {width} × {height} px", f"Registros: {len(rows) if rows else 1}"]
        if self.layout_info.text():
            text.append(self.layout_info.text())
        self.production_summary.setText("\n\n".join(text))

    def _apply_studio_style(self) -> None:
        self.setStyleSheet(self.styleSheet() + """
            QMainWindow, QWidget { background: #f6f8fc; color: #0f172a; }
            QToolBar#studioTopBar { background: white; border-bottom: 1px solid #e2e8f0; spacing: 8px; padding: 7px; }
            QToolButton { padding: 8px 14px; border-radius: 9px; }
            QToolButton:checked { background: #dbeafe; color: #1d4ed8; font-weight: 700; }
            QFrame#welcomeCard, QFrame#inspectorPanel, QFrame#quickActions { background: white; border: 1px solid #e2e8f0; border-radius: 12px; }
            QFrame#toolRail { background: white; border-right: 1px solid #e2e8f0; }
            QPushButton { background: white; border: 1px solid #dbe3ef; border-radius: 9px; padding: 8px 10px; }
            QPushButton:hover { border-color: #60a5fa; background: #f8fbff; }
            QPushButton:pressed { background: #eff6ff; }
            QGroupBox { background: white; border: 1px solid #e2e8f0; border-radius: 10px; margin-top: 10px; padding-top: 12px; font-weight: 700; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
            QTabWidget::pane { border: none; background: white; }
        """)
