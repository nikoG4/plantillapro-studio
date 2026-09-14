from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QGroupBox, QLabel, QLineEdit, QSpinBox, QVBoxLayout, QWidget,
)

from app.core.models import TextField
from app.core.production import (
    build_production_rows, filename_preview, source_columns, suggested_filename_pattern, variable_fields,
)


class ProductionMappingPanel(QWidget):
    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.fields: list[TextField] = []
        self.rows: list[dict[str, str]] = []
        self.export_settings = None
        self._syncing = False
        self._cards: dict[str, dict[str, QWidget]] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        intro = QLabel(
            "Aquí decides de dónde sale cada campo variable del diseño. "
            "Los textos fijos no aparecen porque nunca cambian."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color:#64748b; padding:8px 2px;")
        root.addWidget(intro)

        self.empty = QLabel("No hay campos variables. En Diseño agrega un ‘Campo variable’ para usar listas o numeración.")
        self.empty.setWordWrap(True)
        self.empty.setStyleSheet("padding:14px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px;")
        root.addWidget(self.empty)

        self.cards_host = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_host)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        root.addWidget(self.cards_host)

        file_box = QGroupBox("Nombre de los archivos generados")
        file_form = QFormLayout(file_box)
        self.filename_mode = QComboBox()
        self.filename_mode.addItem("Número consecutivo · 001.png", "number")
        self.filename_mode.addItem("Usar un campo variable · Ana.png", "field")
        self.filename_mode.addItem("Número + campo · 001_Ana.png", "number_field")
        self.filename_mode.addItem("Personalizado", "custom")
        self.filename_field = QComboBox()
        self.filename_custom = QLineEdit()
        self.filename_custom.setPlaceholderText("Ej.: invitacion_{{nombre}}_{{numero}}")
        self.filename_preview = QLabel("Ejemplo: 001.png")
        self.filename_preview.setStyleSheet("color:#475569; font-weight:600;")
        file_form.addRow("Cómo nombrar", self.filename_mode)
        file_form.addRow("Campo usado", self.filename_field)
        file_form.addRow("Patrón", self.filename_custom)
        file_form.addRow("", self.filename_preview)
        root.addWidget(file_box)
        root.addStretch()

        self.filename_mode.currentIndexChanged.connect(self._filename_changed)
        self.filename_field.currentIndexChanged.connect(self._filename_changed)
        self.filename_custom.textChanged.connect(self._filename_changed)

    def set_context(self, fields: list[TextField], rows: list[dict[str, str]], export_settings) -> None:
        self._syncing = True
        self.fields = fields
        self.rows = rows
        self.export_settings = export_settings
        self._rebuild_cards()
        self._refresh_filename_fields()
        mode_index = self.filename_mode.findData(export_settings.filename_mode)
        self.filename_mode.setCurrentIndex(max(0, mode_index))
        if export_settings.filename_field_id:
            field_index = self.filename_field.findData(export_settings.filename_field_id)
            if field_index >= 0:
                self.filename_field.setCurrentIndex(field_index)
        self.filename_custom.setText(export_settings.filename_custom)
        self._syncing = False
        self._filename_changed()

    def _rebuild_cards(self) -> None:
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._cards.clear()

        variables = variable_fields(self.fields)
        self.empty.setVisible(not variables)
        columns = source_columns(self.rows)

        for field in variables:
            box = QGroupBox(f"Campo variable · {field.name}")
            form = QFormLayout(box)
            key = QLabel(field.variable_key())
            key.setStyleSheet("font-family:monospace; color:#2563eb; font-weight:700;")
            source = QComboBox()
            source.addItem("Lista / columna de datos", "column")
            source.addItem("Numeración automática", "numbering")
            column = QComboBox()
            for name in columns:
                column.addItem(name)
            if field.source_column and column.findText(field.source_column) < 0:
                column.addItem(field.source_column)
            if column.count() == 0:
                column.addItem("(sin columnas)")
            start = self._spin(-999999999, 999999999, field.number_start)
            count = self._spin(1, 1000000, field.number_count)
            step = self._spin(-999999, 999999, field.number_step)
            digits = self._spin(0, 20, field.number_digits)
            prefix = QLineEdit(field.number_prefix)
            suffix = QLineEdit(field.number_suffix)
            help_label = QLabel()
            help_label.setWordWrap(True)
            help_label.setStyleSheet("color:#64748b;")

            form.addRow("Identificador", key)
            form.addRow("Rellenar con", source)
            form.addRow("Columna", column)
            form.addRow("Número inicial", start)
            form.addRow("Cantidad", count)
            form.addRow("Incremento", step)
            form.addRow("Dígitos", digits)
            form.addRow("Prefijo", prefix)
            form.addRow("Sufijo", suffix)
            form.addRow("", help_label)
            self.cards_layout.addWidget(box)

            widgets = {
                "source": source, "column": column, "start": start, "count": count,
                "step": step, "digits": digits, "prefix": prefix, "suffix": suffix,
                "help": help_label,
            }
            self._cards[field.id] = widgets
            source.setCurrentIndex(max(0, source.findData(field.production_source)))
            if field.source_column:
                column.setCurrentText(field.source_column)

            source.currentIndexChanged.connect(lambda _=0, f=field: self._apply_field(f))
            column.currentTextChanged.connect(lambda _="", f=field: self._apply_field(f))
            start.valueChanged.connect(lambda _=0, f=field: self._apply_field(f))
            count.valueChanged.connect(lambda _=0, f=field: self._apply_field(f))
            step.valueChanged.connect(lambda _=0, f=field: self._apply_field(f))
            digits.valueChanged.connect(lambda _=0, f=field: self._apply_field(f))
            prefix.textChanged.connect(lambda _="", f=field: self._apply_field(f))
            suffix.textChanged.connect(lambda _="", f=field: self._apply_field(f))
            self._apply_field(field, emit=False)

    @staticmethod
    def _spin(minimum: int, maximum: int, value: int) -> QSpinBox:
        spin = QSpinBox(); spin.setRange(minimum, maximum); spin.setValue(value)
        return spin

    def _apply_field(self, field: TextField, emit: bool = True) -> None:
        widgets = self._cards.get(field.id)
        if not widgets:
            return
        source: QComboBox = widgets["source"]  # type: ignore[assignment]
        column: QComboBox = widgets["column"]  # type: ignore[assignment]
        field.production_source = str(source.currentData())
        if column.currentText() != "(sin columnas)":
            field.source_column = column.currentText()
        field.number_start = widgets["start"].value()  # type: ignore[attr-defined]
        field.number_count = widgets["count"].value()  # type: ignore[attr-defined]
        field.number_step = widgets["step"].value()  # type: ignore[attr-defined]
        field.number_digits = widgets["digits"].value()  # type: ignore[attr-defined]
        field.number_prefix = widgets["prefix"].text()  # type: ignore[attr-defined]
        field.number_suffix = widgets["suffix"].text()  # type: ignore[attr-defined]

        numbering = field.production_source == "numbering"
        list_drives_count = bool(self.rows) and any(
            candidate.production_source == "column" for candidate in variable_fields(self.fields)
        )
        column.setEnabled(not numbering)
        for key in ("start", "step", "digits", "prefix", "suffix"):
            widgets[key].setEnabled(numbering)
        widgets["count"].setEnabled(numbering and not list_drives_count)
        help_label: QLabel = widgets["help"]  # type: ignore[assignment]
        if numbering:
            sample = str(field.number_start).zfill(field.number_digits) if field.number_digits else str(field.number_start)
            example = f"{field.number_prefix}{sample}{field.number_suffix}"
            if list_drives_count:
                help_label.setText(
                    f"Ejemplo: {example}. La lista define la cantidad: {len(self.rows)} copia(s)."
                )
            else:
                help_label.setText(f"Ejemplo: {example}. Aquí la cantidad define cuántas copias se generan.")
        else:
            source_name = field.source_column or "ninguna"
            help_label.setText(f"Cada fila de la columna ‘{source_name}’ genera una copia.")
        if emit and not self._syncing:
            for other in variable_fields(self.fields):
                if other.id != field.id and other.id in self._cards:
                    self._apply_field(other, emit=False)
            self.changed.emit()
            self._filename_changed()

    def _refresh_filename_fields(self) -> None:
        self.filename_field.clear()
        for field in variable_fields(self.fields):
            self.filename_field.addItem(field.name, field.id)

    def _filename_changed(self, *_args) -> None:
        if self.export_settings is None:
            return
        mode = str(self.filename_mode.currentData())
        field_id = str(self.filename_field.currentData() or "")
        custom = self.filename_custom.text()
        pattern = suggested_filename_pattern(self.fields, mode, field_id, custom)
        self.export_settings.filename_mode = mode
        self.export_settings.filename_field_id = field_id
        self.export_settings.filename_custom = custom
        self.export_settings.filename_pattern = pattern
        mapped_rows = build_production_rows(self.fields, self.rows)
        self.filename_field.setEnabled(mode in {"field", "number_field"} and self.filename_field.count() > 0)
        self.filename_custom.setEnabled(mode == "custom")
        self.filename_preview.setText(f"Ejemplo: {filename_preview(pattern, mapped_rows)}.png")
        if not self._syncing:
            self.changed.emit()
