from __future__ import annotations

from app.qml.qml_app import _load_qml_source, resource_path


def test_polished_shell_routes_native_combo_boxes_to_modern_select() -> None:
    shell = resource_path("app/qml/PolishedMain.qml")
    source = _load_qml_source(shell).decode("utf-8")

    assert "ModernSelect {" in source or "ModernSelect{" in source
    assert "ComboBox {" not in source
    assert "ComboBox{" not in source


def test_modern_select_owns_field_and_popup_visuals() -> None:
    component = resource_path("app/qml/ModernSelect.qml")
    source = component.read_text(encoding="utf-8")

    assert "ComboBox {" in source
    assert "popup: Popup" in source
    assert "radius: 10" in source
    assert "radius: 12" in source
    assert "accentSoft" in source
    assert "option.highlighted" in source
