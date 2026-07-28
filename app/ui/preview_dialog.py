from __future__ import annotations

from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QHBoxLayout, QInputDialog, QLabel,
    QMessageBox, QProgressDialog, QPushButton, QScrollArea, QSpinBox, QVBoxLayout,
)

from app.core.image_exporter import export_images
from app.core.imposition import build_imposed_pages, render_imposed_page
from app.core.models import ExportSettings, TextField
from app.core.pdf_exporter import export_pdf


class PreviewDialog(QDialog):
    def __init__(self, image_path: str, fields: list[TextField], rows: list[dict[str, str]], settings: ExportSettings, start_index: int = 0, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Generador y visor de hojas")
        self.resize(1100, 820)
        self.image_path = image_path
        self.fields = fields
        self.rows = rows
        self.settings = settings
        self.layout_info, self.pages, self.prepared_rows = build_imposed_pages(image_path, rows, settings)
        self.index = max(0, min(start_index, max(0, len(self.pages) - 1)))

        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.prev_btn = QPushButton("Anterior")
        self.next_btn = QPushButton("Siguiente")
        self.page_spin = QSpinBox()
        self.page_spin.setRange(1, max(1, len(self.pages)))
        self.info = QLabel()
        self.print_current_btn = QPushButton("Imprimir hoja")
        self.print_all_btn = QPushButton("Imprimir todo")
        self.save_pdf_btn = QPushButton("Guardar PDF")
        self.save_images_btn = QPushButton("Imágenes individuales")
        controls.addWidget(self.prev_btn)
        controls.addWidget(self.next_btn)
        controls.addWidget(QLabel("Hoja"))
        controls.addWidget(self.page_spin)
        controls.addWidget(self.info, 1)
        controls.addWidget(self.print_current_btn)
        controls.addWidget(self.print_all_btn)
        controls.addWidget(self.save_pdf_btn)
        controls.addWidget(self.save_images_btn)
        layout.addLayout(controls)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setWidget(self.label)
        layout.addWidget(scroll)

        self.prev_btn.clicked.connect(lambda: self._set_index(self.index - 1))
        self.next_btn.clicked.connect(lambda: self._set_index(self.index + 1))
        self.page_spin.valueChanged.connect(lambda value: self._set_index(value - 1))
        self.print_current_btn.clicked.connect(lambda: self._print(False))
        self.print_all_btn.clicked.connect(lambda: self._print(True))
        self.save_pdf_btn.clicked.connect(self._save_pdf)
        self.save_images_btn.clicked.connect(self._save_images)
        self._refresh()

    def _set_index(self, index: int) -> None:
        index = max(0, min(index, len(self.pages) - 1))
        if index != self.index:
            self.index = index
            self._refresh()

    def _render_qimage(self, index: int) -> QImage:
        image = render_imposed_page(self.image_path, self.fields, self.layout_info, self.pages[index]).convert("RGBA")
        return QImage(ImageQt(image))

    def _refresh(self) -> None:
        qimage = self._render_qimage(self.index)
        available = self.size() - self.info.sizeHint()
        pixmap = QPixmap.fromImage(qimage).scaled(
            max(400, available.width() - 80), max(400, available.height() - 170),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation,
        )
        self.label.setPixmap(pixmap)
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(self.index + 1)
        self.page_spin.blockSignals(False)
        field_name = self.settings.numbering.field_name or "numero"
        values = [str(item.get(field_name, "")) for item in self.pages[self.index] if item]
        range_text = f" | {values[0]} … {values[-1]}" if values else ""
        self.info.setText(
            f"{self.index + 1} / {len(self.pages)} | "
            f"{self.layout_info.columns} × {self.layout_info.rows} = {self.layout_info.slots_per_page} por hoja{range_text}"
        )
        self.prev_btn.setEnabled(self.index > 0)
        self.next_btn.setEnabled(self.index < len(self.pages) - 1)

    def _print(self, all_pages: bool) -> None:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return
        indexes = range(len(self.pages)) if all_pages else [self.index]
        painter = QPainter(printer)
        try:
            for pos, page_index in enumerate(indexes):
                if pos:
                    printer.newPage()
                qimage = self._render_qimage(page_index)
                target = printer.pageRect(QPrinter.Unit.DevicePixel)
                scaled = qimage.scaled(target.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                x = target.x() + (target.width() - scaled.width()) // 2
                y = target.y() + (target.height() - scaled.height()) // 2
                painter.drawImage(x, y, scaled)
        except Exception as exc:
            QMessageBox.critical(self, "Error de impresión", str(exc))
        finally:
            painter.end()

    def _save_pdf(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "plantillas_generadas.pdf", "PDF (*.pdf)")
        if not path:
            return
        progress = QProgressDialog("Generando PDF...", "Cancelar", 0, max(1, len(self.pages)), self)
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        try:
            count = export_pdf(self.image_path, self.fields, self.rows, self.settings, path,
                progress=lambda done, total: (progress.setMaximum(total), progress.setValue(done), QApplication.processEvents()),
                should_cancel=progress.wasCanceled)
            QMessageBox.information(self, "PDF generado", f"Páginas generadas: {count}\nArchivo: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Error al generar PDF", str(exc))
        finally:
            progress.close()

    def _save_images(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Carpeta de salida")
        if not folder:
            return
        pattern, ok = QInputDialog.getText(self, "Patrón de archivo", "Patrón", text=self.settings.filename_pattern)
        if not ok:
            return
        fmt, ok = QInputDialog.getItem(self, "Formato", "Formato", ["PNG", "JPG"], 0, False)
        if not ok:
            return
        self.settings.filename_pattern = pattern or "{{numero}}_{{nombre}}"
        self.settings.image_format = fmt
        progress = QProgressDialog("Exportando imágenes...", "Cancelar", 0, max(1, len(self.prepared_rows)), self)
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        try:
            files = export_images(self.image_path, self.fields, self.rows, self.settings, folder,
                progress=lambda done, total: (progress.setMaximum(total), progress.setValue(done), QApplication.processEvents()),
                should_cancel=progress.wasCanceled)
            QMessageBox.information(self, "Imágenes exportadas", f"Archivos generados: {len(files)}\nCarpeta: {folder}")
        except Exception as exc:
            QMessageBox.critical(self, "Error al exportar imágenes", str(exc))
        finally:
            progress.close()
