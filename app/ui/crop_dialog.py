from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLabel, QVBoxLayout

from app.core.models import ImageElement


class CropDialog(QDialog):
    def __init__(self, element: ImageElement, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Recorte no destructivo")
        root = QVBoxLayout(self)
        root.addWidget(QLabel("Porcentaje a recortar desde cada borde. La imagen original no se modifica."))
        form = QFormLayout()
        self.left = self._spin(element.crop_left * 100)
        self.top = self._spin(element.crop_top * 100)
        self.right = self._spin(element.crop_right * 100)
        self.bottom = self._spin(element.crop_bottom * 100)
        form.addRow("Izquierda %", self.left)
        form.addRow("Arriba %", self.top)
        form.addRow("Derecha %", self.right)
        form.addRow("Abajo %", self.bottom)
        root.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Reset)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self._reset)
        root.addWidget(buttons)

    @staticmethod
    def _spin(value: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0, 45)
        spin.setDecimals(1)
        spin.setSingleStep(1)
        spin.setValue(value)
        return spin

    def values(self) -> tuple[float, float, float, float]:
        return tuple(spin.value() / 100 for spin in (self.left, self.top, self.right, self.bottom))

    def _reset(self) -> None:
        for spin in (self.left, self.top, self.right, self.bottom):
            spin.setValue(0)
