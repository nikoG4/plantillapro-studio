from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QSG_RHI_BACKEND", "software")

from PySide6.QtWidgets import QApplication

from app.qml.studio_bridge import StudioBridge


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_qml_bridge_starts_a4_and_edits_objects() -> None:
    _app()
    bridge = StudioBridge()
    assert bridge.mode == "welcome"
    bridge.newA4()
    assert bridge.mode == "design"
    assert (bridge.documentWidth, bridge.documentHeight) == (2480, 3508)

    bridge.addStaticText()
    selected = bridge.selectedData
    assert selected["kind"] == "text"
    item_id = selected["id"]
    bridge.setSelectedText("Título principal")
    bridge.moveItem(item_id, 320, 440)
    assert bridge.selectedData["template"] == "Título principal"
    assert bridge.selectedData["x"] == 320
    assert bridge.selectedData["y"] == 440

    bridge.addRectangle()
    assert bridge.selectedData["kind"] == "shape"
    bridge.resizeItem(bridge.selectedId, 800, 500)
    assert bridge.selectedData["width"] == 800
    assert bridge.selectedData["height"] == 500


def test_qml_bridge_variable_mapping_and_rows() -> None:
    _app()
    bridge = StudioBridge()
    bridge.newA4()
    bridge.addVariableText()
    field_id = bridge.selectedId
    assert bridge.variableMappings[0]["source"] == "column"

    bridge.project.data = [{"nombre": "Ana"}, {"nombre": "Luis"}]
    bridge.setVariableColumn(field_id, "nombre")
    assert bridge.productionCount == 2
    assert bridge.variableMappings[0]["column"] == "nombre"

    bridge.setVariableSource(field_id, "numbering")
    bridge.setNumberSetting(field_id, "start", "10")
    bridge.setNumberSetting(field_id, "step", "5")
    bridge.setNumberSetting(field_id, "digits", "3")
    mapping = bridge.variableMappings[0]
    assert mapping["source"] == "numbering"
    assert mapping["start"] == 10
    assert mapping["step"] == 5
    assert mapping["digits"] == 3

    bridge.deleteDataRow(0)
    assert bridge.dataRowCount == 1
