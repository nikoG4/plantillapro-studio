from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.core.models import DocumentSettings, ExportSettings, TemplateProject, TextField, project_from_dict, project_to_dict
from app.core.production import build_production_rows, production_errors, suggested_filename_pattern
from app.ui.data_table import DataTableWidget
from app.ui.new_document_dialog import NewDocumentDialog


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_a4_is_default_document_and_dialog_preset() -> None:
    project = TemplateProject()
    assert project.document.width == 2480
    assert project.document.height == 3508
    assert project.document.preset == "a4"

    app = _app()
    dialog = NewDocumentDialog()
    try:
        choice = dialog.choice()
        assert choice.preset == "a4"
        assert (choice.width, choice.height) == (2480, 3508)
    finally:
        dialog.close()
        app.processEvents()


def test_static_and_variable_fields_round_trip_and_legacy_upgrade() -> None:
    static = TextField(id="static", name="Saludo", template="Feliz cumpleaños", text_mode="static")
    variable = TextField(id="variable", name="Nombre", text_mode="variable", variable_name="nombre", source_column="clientes")
    variable.sync_variable_template()
    project = TemplateProject(fields=[static, variable])
    restored = project_from_dict(project_to_dict(project))

    assert restored.fields[0].text_mode == "static"
    assert restored.fields[0].template == "Feliz cumpleaños"
    assert restored.fields[1].text_mode == "variable"
    assert restored.fields[1].variable_name == "nombre"
    assert restored.fields[1].template == "{{nombre}}"

    legacy = project_from_dict({"fields": [{"id": "old", "name": "nombre", "template": "{{nombre}}", "style": {}}]})
    assert legacy.fields[0].text_mode == "variable"
    assert legacy.fields[0].variable_name == "nombre"


def test_variable_can_map_to_data_column() -> None:
    field = TextField(
        id="name", name="Nombre invitado", text_mode="variable", variable_name="invitado",
        production_source="column", source_column="cliente",
    )
    field.sync_variable_template()
    rows = [{"cliente": "Ana"}, {"cliente": "Luis"}]
    produced = build_production_rows([field], rows)
    assert [row["invitado"] for row in produced] == ["Ana", "Luis"]
    assert production_errors([field], rows) == []


def test_variable_can_generate_numbering_without_data_rows() -> None:
    field = TextField(
        id="ticket", name="Número de ticket", text_mode="variable", variable_name="ticket",
        production_source="numbering", number_start=7, number_count=3, number_step=2,
        number_digits=3, number_prefix="T-",
    )
    field.sync_variable_template()
    produced = build_production_rows([field], [])
    assert [row["ticket"] for row in produced] == ["T-007", "T-009", "T-011"]
    assert [row["numero"] for row in produced] == ["1", "2", "3"]


def test_filename_modes_are_explicit() -> None:
    field = TextField(id="name", name="Nombre", text_mode="variable", variable_name="nombre")
    assert suggested_filename_pattern([field], "number") == "{{numero}}"
    assert suggested_filename_pattern([field], "field", field.id) == "{{nombre}}"
    assert suggested_filename_pattern([field], "number_field", field.id) == "{{numero}}_{{nombre}}"


def test_data_table_deletes_selected_rows() -> None:
    app = _app()
    table = DataTableWidget()
    try:
        table.set_rows([{"nombre": "Ana"}, {"nombre": "Luis"}, {"nombre": "Marta"}])
        table.selectRow(1)
        assert table.delete_selected_rows() == 1
        assert [row["nombre"] for row in table.rows()] == ["Ana", "Marta"]
    finally:
        table.close()
        app.processEvents()
