from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox,
    QLineEdit, QSpinBox, QVBoxLayout, QWidget,
)

from app.core.models import ImageElement, ShapeElement


class GraphicPropertiesPanel(QWidget):
    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.element: ImageElement | ShapeElement | None = None
        self._syncing = False
        root = QVBoxLayout(self)

        common = QGroupBox("Objeto gráfico")
        form = QFormLayout(common)
        self.name = QLineEdit()
        self.x = self._int_spin(-100000, 100000)
        self.y = self._int_spin(-100000, 100000)
        self.width = self._int_spin(1, 100000)
        self.height = self._int_spin(1, 100000)
        self.rotation = QDoubleSpinBox(); self.rotation.setRange(-360, 360); self.rotation.setDecimals(1)
        self.opacity = QDoubleSpinBox(); self.opacity.setRange(0, 1); self.opacity.setSingleStep(0.05); self.opacity.setDecimals(2)
        self.z_index = self._int_spin(-100000, 100000)
        self.visible = QCheckBox("Visible")
        self.locked = QCheckBox("Bloqueado")
        form.addRow("Nombre", self.name)
        form.addRow("X", self.x); form.addRow("Y", self.y)
        form.addRow("Ancho", self.width); form.addRow("Alto", self.height)
        form.addRow("Rotación", self.rotation); form.addRow("Opacidad", self.opacity)
        form.addRow("Orden Z", self.z_index); form.addRow(self.visible); form.addRow(self.locked)
        root.addWidget(common)

        self.image_group = QGroupBox("Imagen")
        image_form = QFormLayout(self.image_group)
        self.fit = QComboBox(); self.fit.addItems(["cover", "contain", "stretch"])
        self.flip_h = QCheckBox("Voltear horizontal")
        self.flip_v = QCheckBox("Voltear vertical")
        self.crop_left = self._percent_spin(); self.crop_top = self._percent_spin()
        self.crop_right = self._percent_spin(); self.crop_bottom = self._percent_spin()
        image_form.addRow("Ajuste", self.fit)
        image_form.addRow(self.flip_h); image_form.addRow(self.flip_v)
        image_form.addRow("Recorte izq. %", self.crop_left); image_form.addRow("Recorte sup. %", self.crop_top)
        image_form.addRow("Recorte der. %", self.crop_right); image_form.addRow("Recorte inf. %", self.crop_bottom)
        root.addWidget(self.image_group)

        self.shape_group = QGroupBox("Forma")
        shape_form = QFormLayout(self.shape_group)
        self.shape_type = QComboBox(); self.shape_type.addItems(["rectangle", "ellipse"])
        self.fill = QLineEdit(); self.stroke = QLineEdit()
        self.stroke_width = self._int_spin(0, 100)
        self.radius = self._int_spin(0, 10000)
        shape_form.addRow("Tipo", self.shape_type); shape_form.addRow("Relleno", self.fill)
        shape_form.addRow("Borde", self.stroke); shape_form.addRow("Grosor", self.stroke_width)
        shape_form.addRow("Radio esquinas", self.radius)
        root.addWidget(self.shape_group)
        root.addStretch()

        for widget in self.findChildren(QLineEdit):
            widget.textChanged.connect(self._apply)
        for widget in self.findChildren(QComboBox):
            widget.currentTextChanged.connect(self._apply)
        for widget in self.findChildren(QCheckBox):
            widget.toggled.connect(self._apply)
        for widget in [*self.findChildren(QSpinBox), *self.findChildren(QDoubleSpinBox)]:
            widget.valueChanged.connect(self._apply)
        self.set_element(None)

    @staticmethod
    def _int_spin(minimum: int, maximum: int) -> QSpinBox:
        spin = QSpinBox(); spin.setRange(minimum, maximum)
        return spin

    @staticmethod
    def _percent_spin() -> QDoubleSpinBox:
        spin = QDoubleSpinBox(); spin.setRange(0, 45); spin.setDecimals(1); spin.setSingleStep(1)
        return spin

    def set_element(self, element: ImageElement | ShapeElement | None) -> None:
        self.element = element
        self.setEnabled(element is not None)
        self.image_group.setVisible(isinstance(element, ImageElement))
        self.shape_group.setVisible(isinstance(element, ShapeElement))
        if element is None:
            return
        self._syncing = True
        self.name.setText(element.name)
        self.x.setValue(element.x); self.y.setValue(element.y)
        self.width.setValue(element.width); self.height.setValue(element.height)
        self.rotation.setValue(element.rotation); self.opacity.setValue(element.opacity)
        self.z_index.setValue(element.z_index); self.visible.setChecked(element.visible); self.locked.setChecked(element.locked)
        if isinstance(element, ImageElement):
            self.fit.setCurrentText(element.fit_mode)
            self.flip_h.setChecked(element.flip_horizontal); self.flip_v.setChecked(element.flip_vertical)
            self.crop_left.setValue(element.crop_left * 100); self.crop_top.setValue(element.crop_top * 100)
            self.crop_right.setValue(element.crop_right * 100); self.crop_bottom.setValue(element.crop_bottom * 100)
        else:
            self.shape_type.setCurrentText(element.shape_type)
            self.fill.setText(element.fill_color); self.stroke.setText(element.stroke_color)
            self.stroke_width.setValue(element.stroke_width); self.radius.setValue(element.corner_radius)
        self._syncing = False

    def _apply(self, *_args) -> None:
        if self._syncing or self.element is None:
            return
        element = self.element
        element.name = self.name.text().strip() or "objeto"
        element.x = self.x.value(); element.y = self.y.value()
        element.width = self.width.value(); element.height = self.height.value()
        element.rotation = self.rotation.value(); element.opacity = self.opacity.value()
        element.z_index = self.z_index.value(); element.visible = self.visible.isChecked(); element.locked = self.locked.isChecked()
        if isinstance(element, ImageElement):
            element.fit_mode = self.fit.currentText()
            element.flip_horizontal = self.flip_h.isChecked(); element.flip_vertical = self.flip_v.isChecked()
            element.crop_left = self.crop_left.value() / 100; element.crop_top = self.crop_top.value() / 100
            element.crop_right = self.crop_right.value() / 100; element.crop_bottom = self.crop_bottom.value() / 100
        else:
            element.shape_type = self.shape_type.currentText()
            element.fill_color = self.fill.text().strip() or "#ffffff"
            element.stroke_color = self.stroke.text().strip() or "#111827"
            element.stroke_width = self.stroke_width.value(); element.corner_radius = self.radius.value()
        self.changed.emit()
