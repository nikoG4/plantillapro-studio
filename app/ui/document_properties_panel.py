from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QFormLayout, QGroupBox, QLabel, QPushButton,
    QSpinBox, QVBoxLayout, QWidget,
)

from app.core.models import TemplateProject


class DocumentPropertiesPanel(QWidget):
    def __init__(self, on_changed, parent=None) -> None:
        super().__init__(parent)
        self._project: TemplateProject | None = None
        self._syncing = False
        self._on_changed = on_changed

        root = QVBoxLayout(self)
        title = QLabel("Documento")
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        subtitle = QLabel("Propiedades del lienzo")
        subtitle.setStyleSheet("color: #64748b;")
        root.addWidget(title)
        root.addWidget(subtitle)

        group = QGroupBox("Lienzo")
        form = QFormLayout(group)
        self.width = QSpinBox(); self.width.setRange(32, 30000)
        self.height = QSpinBox(); self.height.setRange(32, 30000)
        self.color = QPushButton("#ffffff")
        self.transparent = QCheckBox("Transparente")
        form.addRow("Ancho", self.width)
        form.addRow("Alto", self.height)
        form.addRow("Fondo", self.color)
        form.addRow("", self.transparent)
        root.addWidget(group)

        info = QLabel("La imagen de fondo es opcional. Puedes usar el lienzo vacío y agregar imágenes como capas.")
        info.setWordWrap(True)
        info.setStyleSheet("padding: 10px; background: #f8fafc; color: #475569; border-radius: 8px;")
        root.addWidget(info)
        root.addStretch()

        self.width.valueChanged.connect(self._apply)
        self.height.valueChanged.connect(self._apply)
        self.transparent.toggled.connect(self._apply)
        self.color.clicked.connect(self._choose_color)

    def set_project(self, project: TemplateProject) -> None:
        self._project = project
        self._syncing = True
        width, height = project.document_size()
        self.width.setValue(width)
        self.height.setValue(height)
        self.transparent.setChecked(project.document.transparent)
        self.color.setText(project.document.background_color)
        self.color.setEnabled(not project.document.transparent)
        self._syncing = False

    def _choose_color(self) -> None:
        if not self._project:
            return
        color = QColorDialog.getColor(QColor(self._project.document.background_color), self, "Color del lienzo")
        if not color.isValid():
            return
        self._project.document.background_color = color.name()
        self.color.setText(color.name())
        self._on_changed()

    def _apply(self, *_args) -> None:
        if self._syncing or not self._project:
            return
        self._project.document.width = self.width.value()
        self._project.document.height = self.height.value()
        self._project.document.transparent = self.transparent.isChecked()
        self.color.setEnabled(not self._project.document.transparent)
        self._on_changed()
