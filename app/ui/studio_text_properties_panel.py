from __future__ import annotations

import re

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QFontDatabase
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QTextEdit, QVBoxLayout, QWidget,
)

from app.core.models import TextField


class StudioTextPropertiesPanel(QWidget):
    changed = Signal()
    advancedRequested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.field: TextField | None = None
        self._syncing = False
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)

        title = QLabel("Texto seleccionado")
        title.setStyleSheet("font-size: 17px; font-weight: 700;")
        root.addWidget(title)

        type_box = QGroupBox("Tipo de texto")
        type_form = QFormLayout(type_box)
        self.text_mode = QComboBox()
        self.text_mode.addItem("Texto fijo · siempre muestra lo mismo", "static")
        self.text_mode.addItem("Campo variable · cambia en Producción", "variable")
        self.variable_name = QLineEdit()
        self.variable_name.setPlaceholderText("Ej.: nombre, numero_mesa, codigo")
        self.mode_help = QLabel()
        self.mode_help.setWordWrap(True)
        self.mode_help.setStyleSheet("color:#64748b;")
        type_form.addRow("Uso", self.text_mode)
        type_form.addRow("Nombre del campo", self.variable_name)
        type_form.addRow("", self.mode_help)
        root.addWidget(type_box)

        content_box = QGroupBox("Contenido")
        content_layout = QVBoxLayout(content_box)
        self.template = QTextEdit(); self.template.setFixedHeight(82)
        content_layout.addWidget(self.template)
        root.addWidget(content_box)

        style_box = QGroupBox("Texto")
        form = QFormLayout(style_box)
        self.font_family = QComboBox(); self.font_family.setEditable(True); self.font_family.addItems(QFontDatabase.families())
        self.font_size = QSpinBox(); self.font_size.setRange(1, 500)
        self.bold = QCheckBox("Negrita")
        self.italic = QCheckBox("Cursiva")
        toggles = QHBoxLayout(); toggles.addWidget(self.bold); toggles.addWidget(self.italic); toggles.addStretch()
        self.color_button = QPushButton("Elegir color")
        self.color_button.clicked.connect(self._pick_color)
        self.h_align = QComboBox(); self.h_align.addItem("Izquierda", "left"); self.h_align.addItem("Centrado", "center"); self.h_align.addItem("Derecha", "right")
        form.addRow("Fuente", self.font_family)
        form.addRow("Tamaño", self.font_size)
        form.addRow("Estilo", toggles)
        form.addRow("Color", self.color_button)
        form.addRow("Alineación", self.h_align)
        root.addWidget(style_box)

        geometry = QGroupBox("Posición y tamaño")
        geo = QFormLayout(geometry)
        self.x = QSpinBox(); self.x.setRange(-100000, 100000)
        self.y = QSpinBox(); self.y.setRange(-100000, 100000)
        self.w = QSpinBox(); self.w.setRange(1, 100000)
        self.h = QSpinBox(); self.h.setRange(1, 100000)
        self.opacity = QDoubleSpinBox(); self.opacity.setRange(0, 100); self.opacity.setSuffix(" %"); self.opacity.setDecimals(0)
        self.rotation = QDoubleSpinBox(); self.rotation.setRange(-360, 360); self.rotation.setSuffix("°"); self.rotation.setDecimals(1)
        xy = QWidget(); xyl = QHBoxLayout(xy); xyl.setContentsMargins(0, 0, 0, 0); xyl.addWidget(QLabel("X")); xyl.addWidget(self.x); xyl.addWidget(QLabel("Y")); xyl.addWidget(self.y)
        wh = QWidget(); whl = QHBoxLayout(wh); whl.setContentsMargins(0, 0, 0, 0); whl.addWidget(QLabel("Ancho")); whl.addWidget(self.w); whl.addWidget(QLabel("Alto")); whl.addWidget(self.h)
        geo.addRow(xy); geo.addRow(wh); geo.addRow("Opacidad", self.opacity); geo.addRow("Rotación", self.rotation)
        root.addWidget(geometry)

        advanced = QPushButton("Más opciones de texto…")
        advanced.clicked.connect(self.advancedRequested.emit)
        root.addWidget(advanced)
        root.addStretch()

        self.text_mode.currentIndexChanged.connect(self._mode_changed)
        self.variable_name.textChanged.connect(self._apply)
        self.template.textChanged.connect(self._apply)
        self.font_family.currentTextChanged.connect(self._apply)
        self.font_size.valueChanged.connect(self._apply)
        self.bold.toggled.connect(self._apply)
        self.italic.toggled.connect(self._apply)
        self.h_align.currentIndexChanged.connect(self._apply)
        for spin in (self.x, self.y, self.w, self.h, self.opacity, self.rotation):
            spin.valueChanged.connect(self._apply)

    def set_field(self, field: TextField | None) -> None:
        self.field = field
        self.setEnabled(field is not None)
        if not field:
            return
        self._syncing = True
        index = self.text_mode.findData(field.text_mode)
        self.text_mode.setCurrentIndex(max(0, index))
        self.variable_name.setText(field.variable_name or field.variable_key())
        self.template.setPlainText(field.template if not field.is_variable() else "")
        self.font_family.setCurrentText(field.style.font_family)
        self.font_size.setValue(field.style.font_size)
        self.bold.setChecked(field.style.bold)
        self.italic.setChecked(field.style.italic)
        index = self.h_align.findData(field.style.h_align)
        self.h_align.setCurrentIndex(max(0, index))
        self.x.setValue(field.x); self.y.setValue(field.y); self.w.setValue(field.width); self.h.setValue(field.height)
        self.opacity.setValue(round(field.opacity * 100))
        self.rotation.setValue(field.style.rotation)
        self._update_color_button(field.style.color)
        self._syncing = False
        self._update_mode_ui()

    def _mode_changed(self, *_args) -> None:
        if self._syncing or not self.field:
            return
        new_mode = str(self.text_mode.currentData())
        if new_mode == "variable":
            self.field.text_mode = "variable"
            if not self.variable_name.text().strip():
                self._syncing = True
                self.variable_name.setText(self._safe_key(self.field.name if self.field.name != "Texto fijo" else "campo"))
                self._syncing = False
            self.field.variable_name = self._safe_key(self.variable_name.text())
            self.field.name = self.field.name if self.field.name != "Texto fijo" else "Campo variable"
            self.field.source_column = self.field.source_column or self.field.variable_key()
            self.field.sync_variable_template()
        else:
            self.field.text_mode = "static"
            if self.field.template.startswith("{{") and self.field.template.endswith("}}"):
                self.field.template = "Escribe aquí"
            self._syncing = True
            self.template.setPlainText(self.field.template)
            self._syncing = False
        self._update_mode_ui()
        self.changed.emit()

    def _update_mode_ui(self) -> None:
        variable = bool(self.field and self.field.is_variable())
        self.variable_name.setVisible(variable)
        label = self.variable_name.parentWidget()
        self.template.setEnabled(not variable)
        if variable:
            self.mode_help.setText("En Producción podrás elegir si este campo se llena desde una columna/lista o con numeración automática.")
            self.template.setPlaceholderText("El contenido se asigna en Producción")
        else:
            self.mode_help.setText("Este texto se imprimirá exactamente igual en todas las salidas.")
            self.template.setPlaceholderText("Escribe el texto fijo")

    @staticmethod
    def _safe_key(value: str) -> str:
        key = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip()).strip("_").lower()
        return key or "campo"

    def _pick_color(self) -> None:
        if not self.field:
            return
        color = QColorDialog.getColor(QColor(self.field.style.color), self, "Color del texto")
        if color.isValid():
            self.field.style.color = color.name()
            self._update_color_button(color.name())
            self.changed.emit()

    def _update_color_button(self, color: str) -> None:
        self.color_button.setText(color)
        self.color_button.setStyleSheet(f"background: {color}; color: {'white' if QColor(color).lightness() < 140 else '#0f172a'};")

    def _apply(self, *_args) -> None:
        if self._syncing or not self.field:
            return
        field = self.field
        if field.is_variable():
            field.variable_name = self._safe_key(self.variable_name.text())
            field.source_column = field.source_column or field.variable_key()
            field.sync_variable_template()
        else:
            field.template = self.template.toPlainText()
        field.style.font_family = self.font_family.currentText().strip() or "Arial"
        field.style.font_size = self.font_size.value()
        field.style.bold = self.bold.isChecked()
        field.style.italic = self.italic.isChecked()
        field.style.h_align = str(self.h_align.currentData())
        field.x = self.x.value(); field.y = self.y.value(); field.width = self.w.value(); field.height = self.h.value()
        field.opacity = self.opacity.value() / 100.0
        field.style.rotation = self.rotation.value()
        self._update_mode_ui()
        self.changed.emit()
