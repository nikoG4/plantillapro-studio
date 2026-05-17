from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QFontDatabase

from app.core.models import TextField


class FieldPropertiesPanel(QWidget):
    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.field: TextField | None = None
        self._syncing = False
        layout = QVBoxLayout(self)
        title = QLabel("Campo seleccionado")
        title.setStyleSheet("font-weight: 600;")
        layout.addWidget(title)
        box = QGroupBox()
        form = QFormLayout(box)
        self.name = QLineEdit()
        self.template = QTextEdit()
        self.template.setFixedHeight(68)
        self.x = QSpinBox(); self.x.setRange(0, 100000)
        self.y = QSpinBox(); self.y.setRange(0, 100000)
        self.w = QSpinBox(); self.w.setRange(1, 100000)
        self.h = QSpinBox(); self.h.setRange(1, 100000)
        self.font_size = QSpinBox(); self.font_size.setRange(1, 500)
        self.min_font = QSpinBox(); self.min_font.setRange(1, 300)
        self.color = QLineEdit("#000000")
        color_btn = QPushButton("Color")
        color_btn.clicked.connect(self._pick_color)
        color_row = QHBoxLayout(); color_row.addWidget(self.color); color_row.addWidget(color_btn)
        self.font_path = QLineEdit()
        font_btn = QPushButton("TTF")
        font_btn.clicked.connect(self._pick_font)
        font_row = QHBoxLayout(); font_row.addWidget(self.font_path); font_row.addWidget(font_btn)
        self.font_family = QComboBox()
        self.font_family.setEditable(True)
        families = QFontDatabase.families()
        self.font_family.addItems(families)
        self.h_align = QComboBox(); self.h_align.addItems(["left", "center", "right"])
        self.v_align = QComboBox(); self.v_align.addItems(["top", "center", "bottom"])
        self.text_case = QComboBox(); self.text_case.addItems(["normal", "upper", "lower", "title"])
        self.line_spacing = QDoubleSpinBox(); self.line_spacing.setRange(0.5, 4); self.line_spacing.setSingleStep(0.05)
        self.padding = QSpinBox(); self.padding.setRange(0, 500)
        self.words_per_line = QSpinBox(); self.words_per_line.setRange(0, 50)
        self.words_per_line.setSpecialValueText("Auto")
        self.rotation = QDoubleSpinBox(); self.rotation.setRange(-360, 360)
        self.bold = QCheckBox()
        self.italic = QCheckBox()
        self.uppercase = QCheckBox()
        self.auto_fit = QCheckBox()
        self.word_wrap = QCheckBox()
        self.single_line = QCheckBox()
        self.print_border = QCheckBox()
        form.addRow("Nombre", self.name)
        form.addRow("Texto", self.template)
        form.addRow("X", self.x); form.addRow("Y", self.y); form.addRow("Ancho", self.w); form.addRow("Alto", self.h)
        form.addRow("Fuente TTF", font_row)
        form.addRow("Fuente del sistema", self.font_family)
        form.addRow("Tamaño", self.font_size); form.addRow("Mínimo", self.min_font)
        form.addRow("Color", color_row)
        form.addRow("Negrita", self.bold); form.addRow("Cursiva", self.italic)
        form.addRow("Alineación H", self.h_align); form.addRow("Alineación V", self.v_align)
        form.addRow("Interlineado", self.line_spacing); form.addRow("Margen interno", self.padding)
        form.addRow("Palabras por línea", self.words_per_line)
        form.addRow("Transformar texto", self.text_case)
        form.addRow("Mayúsculas legacy", self.uppercase); form.addRow("Autoajustar", self.auto_fit)
        form.addRow("Salto automático", self.word_wrap); form.addRow("Una línea", self.single_line)
        form.addRow("Rotación", self.rotation); form.addRow("Imprimir borde", self.print_border)
        layout.addWidget(box)
        layout.addStretch()
        for widget in self.findChildren(QTextEdit):
            widget.textChanged.connect(self._apply)
        for widget in self.findChildren(QLineEdit):
            widget.textChanged.connect(self._apply)
        for widget in self.findChildren(QComboBox):
            widget.currentTextChanged.connect(self._apply)
        for widget in self.findChildren(QCheckBox):
            widget.toggled.connect(self._apply)
        for widget in [*self.findChildren(QSpinBox), *self.findChildren(QDoubleSpinBox)]:
            widget.valueChanged.connect(self._apply)

    def set_field(self, field: TextField | None) -> None:
        self.field = field
        self.setEnabled(field is not None)
        if not field:
            return
        self._syncing = True
        s = field.style
        self.name.setText(field.name); self.template.setPlainText(field.template)
        self.x.setValue(field.x); self.y.setValue(field.y); self.w.setValue(field.width); self.h.setValue(field.height)
        self.font_path.setText(s.font_path); self.font_family.setCurrentText(s.font_family)
        self.font_size.setValue(s.font_size); self.min_font.setValue(s.min_font_size)
        self.color.setText(s.color); self.bold.setChecked(s.bold); self.italic.setChecked(s.italic)
        self.h_align.setCurrentText(s.h_align); self.v_align.setCurrentText(s.v_align)
        self.line_spacing.setValue(s.line_spacing); self.padding.setValue(s.padding)
        self.words_per_line.setValue(s.words_per_line)
        self.text_case.setCurrentText(s.text_case); self.uppercase.setChecked(s.uppercase); self.auto_fit.setChecked(s.auto_fit)
        self.word_wrap.setChecked(s.word_wrap); self.single_line.setChecked(s.single_line)
        self.rotation.setValue(s.rotation); self.print_border.setChecked(s.print_border)
        self._syncing = False

    def _apply(self) -> None:
        if self._syncing or not self.field:
            return
        s = self.field.style
        self.field.name = self.name.text().strip() or "campo"
        self.field.template = self.template.toPlainText()
        self.field.x = self.x.value(); self.field.y = self.y.value(); self.field.width = self.w.value(); self.field.height = self.h.value()
        s.font_path = self.font_path.text().strip(); s.font_family = self.font_family.currentText().strip() or "Arial"
        s.font_size = self.font_size.value(); s.min_font_size = self.min_font.value()
        s.color = self.color.text().strip() or "#000000"; s.bold = self.bold.isChecked(); s.italic = self.italic.isChecked()
        s.h_align = self.h_align.currentText(); s.v_align = self.v_align.currentText()
        s.line_spacing = self.line_spacing.value(); s.padding = self.padding.value()
        s.words_per_line = self.words_per_line.value()
        s.text_case = self.text_case.currentText(); s.uppercase = self.uppercase.isChecked(); s.auto_fit = self.auto_fit.isChecked()
        s.word_wrap = self.word_wrap.isChecked(); s.single_line = self.single_line.isChecked()
        s.rotation = self.rotation.value(); s.print_border = self.print_border.isChecked()
        self.changed.emit()

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(QColor(self.color.text()), self)
        if color.isValid():
            self.color.setText(color.name())

    def _pick_font(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar fuente", "", "TrueType (*.ttf *.otf)")
        if path:
            self.font_path.setText(path)
