from __future__ import annotations

from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QScrollArea, QSpinBox, QVBoxLayout

from app.core.models import TextField
from app.core.renderer import render_template


class PreviewDialog(QDialog):
    def __init__(self, image_path: str, fields: list[TextField], rows: list[dict[str, str]], start_index: int = 0, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Visor e impresión")
        self.resize(900, 700)
        self.image_path = image_path
        self.fields = fields
        self.rows = rows
        self.index = max(0, min(start_index, len(rows) - 1))
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.prev_btn = QPushButton("Anterior")
        self.next_btn = QPushButton("Siguiente")
        self.row_spin = QSpinBox()
        self.row_spin.setRange(1, max(1, len(rows)))
        self.info = QLabel()
        self.print_current_btn = QPushButton("Imprimir página")
        self.print_all_btn = QPushButton("Imprimir todo")
        controls.addWidget(self.prev_btn)
        controls.addWidget(self.next_btn)
        controls.addWidget(QLabel("Fila"))
        controls.addWidget(self.row_spin)
        controls.addWidget(self.info, 1)
        controls.addWidget(self.print_current_btn)
        controls.addWidget(self.print_all_btn)
        layout.addLayout(controls)
        scroll = QScrollArea()
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setWidget(self.label)
        layout.addWidget(scroll)
        self.prev_btn.clicked.connect(lambda: self._set_index(self.index - 1))
        self.next_btn.clicked.connect(lambda: self._set_index(self.index + 1))
        self.row_spin.valueChanged.connect(lambda value: self._set_index(value - 1))
        self.print_current_btn.clicked.connect(lambda: self._print(False))
        self.print_all_btn.clicked.connect(lambda: self._print(True))
        self._refresh()

    def _set_index(self, index: int) -> None:
        index = max(0, min(index, len(self.rows) - 1))
        if index == self.index:
            return
        self.index = index
        self._refresh()

    def _row_with_number(self, index: int) -> dict[str, str]:
        row = dict(self.rows[index])
        row.setdefault("numero", str(index + 1))
        return row

    def _render_qimage(self, index: int) -> QImage:
        image = render_template(self.image_path, self.fields, self._row_with_number(index)).convert("RGBA")
        return QImage(ImageQt(image))

    def _refresh(self) -> None:
        qimage = self._render_qimage(self.index)
        self.label.setPixmap(QPixmap.fromImage(qimage))
        self.label.resize(qimage.size())
        self.row_spin.blockSignals(True)
        self.row_spin.setValue(self.index + 1)
        self.row_spin.blockSignals(False)
        current = self._row_with_number(self.index)
        preview = current.get("nombre") or next(iter(current.values()), "")
        self.info.setText(f"{self.index + 1} / {len(self.rows)}   {preview}")
        self.prev_btn.setEnabled(self.index > 0)
        self.next_btn.setEnabled(self.index < len(self.rows) - 1)

    def _print(self, all_pages: bool) -> None:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return
        indexes = range(len(self.rows)) if all_pages else [self.index]
        painter = QPainter(printer)
        try:
            for pos, row_index in enumerate(indexes):
                if pos:
                    printer.newPage()
                qimage = self._render_qimage(row_index)
                target = printer.pageRect(QPrinter.Unit.DevicePixel)
                scaled = qimage.scaled(target.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                x = target.x() + (target.width() - scaled.width()) // 2
                y = target.y() + (target.height() - scaled.height()) // 2
                painter.drawImage(x, y, scaled)
        except Exception as exc:
            QMessageBox.critical(self, "Error de impresión", str(exc))
        finally:
            painter.end()
