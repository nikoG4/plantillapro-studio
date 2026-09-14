from __future__ import annotations

import os

from app.qml.modern_bridge import ModernStudioBridge
from app.qml.qml_app import qml_entrypoint


def test_polished_qml_shell_is_default(monkeypatch):
    monkeypatch.delenv("PLANTILLAPRO_QML_LEGACY", raising=False)
    path = qml_entrypoint()
    assert path.name == "PolishedMain.qml"
    assert path.exists()
    source = path.read_text(encoding="utf-8")
    assert "ModernIconButton" in source
    assert "Producción" in source
    assert "Campo variable" in source


def test_legacy_qml_shell_can_still_be_selected(monkeypatch):
    monkeypatch.setenv("PLANTILLAPRO_QML_LEGACY", "1")
    assert qml_entrypoint().name == "Main.qml"


def test_bridge_supports_modern_design_and_production_flow():
    bridge = ModernStudioBridge()
    bridge.newA4()
    assert bridge.documentWidth == 2480
    assert bridge.documentHeight == 3508

    bridge.addStaticText()
    static_id = bridge.selectedId
    assert bridge.selectedData["kind"] == "text"

    bridge.addVariableText()
    variable_id = bridge.selectedId
    assert bridge.selectedData["kind"] == "variable"

    bridge.project.data = [{"cliente": "Ana"}, {"cliente": "Luis"}]
    bridge.setVariableColumn(variable_id, "cliente")
    assert bridge.variableMappings[0]["source"] == "column"
    assert bridge.productionCount == 2

    bridge.selectItem(static_id)
    bridge.setSelectedText("Texto fijo")
    assert bridge.selectedData["template"] == "Texto fijo"
