from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout,
)


@dataclass(frozen=True)
class DocumentChoice:
    width: int
    height: int
    background_color: str
    transparent: bool
    preset: str


PRESETS = {
    "A4 · 300 dpi": (2480, 3508, "a4"),
    "Flyer · A5": (1748, 2480, "a5"),
    "Ticket · 7 × 3 cm": (827, 354, "ticket"),
    "Sticker · 5 × 5 cm": (591, 591, "sticker"),
    "Tarjeta · 9 × 5 cm": (1063, 591, "card"),
    "Post cuadrado · 1080 px": (1080, 1080, "social-square"),
    "Personalizado": (2480, 3508, "custom"),
}


class NewDocumentDialog(QDialog):
    def __init__(self, parent=None, preset: str | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nuevo diseño")
        self.setMinimumWidth(430)
        self._background_color = "#ffffff"

        root = QVBoxLayout(self)
        title = QLabel("Crear lienzo en blanco")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        subtitle = QLabel("A4 es el formato predeterminado. Puedes elegir otro tamaño o agregar una imagen de fondo después.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #64748b;")
        root.addWidget(title)
        root.addWidget(subtitle)

        form = QFormLayout()
        self.preset = QComboBox()
        for label in PRESETS:
            self.preset.addItem(label)
        self.width = QSpinBox(); self.width.setRange(32, 30000)
        self.height = QSpinBox(); self.height.setRange(32, 30000)
        self.width.setValue(2480); self.height.setValue(3508)
        self.transparent = QCheckBox("Fondo transparente")
        self.color_button = QPushButton("#ffffff")
        self.color_button.clicked.connect(self._choose_color)
        form.addRow("Formato", self.preset)
        form.addRow("Ancho (px)", self.width)
        form.addRow("Alto (px)", self.height)
        form.addRow("Fondo", self.color_button)
        form.addRow("", self.transparent)
        root.addLayout(form)

        hint = QLabel("A4 a 300 dpi = 2480 × 3508 px. Para impresión puedes configurar imposición y hoja en Producción.")
        hint.setWordWrap(True)
        hint.setStyleSheet("padding: 10px; background: #f8fafc; border-radius: 8px; color: #475569;")
        root.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Crear diseño")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.preset.currentTextChanged.connect(self._preset_changed)
        self.transparent.toggled.connect(self.color_button.setDisabled)
        if preset:
            index = next((i for i, label in enumerate(PRESETS) if PRESETS[label][2] == preset), -1)
            if index >= 0:
                self.preset.setCurrentIndex(index)
        self._preset_changed(self.preset.currentText())

    def _preset_changed(self, label: str) -> None:
        width, height, preset = PRESETS[label]
        self.width.setValue(width)
        self.height.setValue(height)
        custom = preset == "custom"
        self.width.setEnabled(custom)
        self.height.setEnabled(custom)

    def _choose_color(self) -> None:
        color = QColorDialog.getColor(QColor(self._background_color), self, "Color del lienzo")
        if color.isValid():
            self._background_color = color.name()
            self.color_button.setText(self._background_color)
            self.color_button.setStyleSheet(f"background: {self._background_color};")

    def choice(self) -> DocumentChoice:
        preset = PRESETS[self.preset.currentText()][2]
        return DocumentChoice(
            width=self.width.value(),
            height=self.height.value(),
            background_color=self._background_color,
            transparent=self.transparent.isChecked(),
            preset=preset,
        )
