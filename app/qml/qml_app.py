from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine
# Imported explicitly so PyInstaller's Qt hooks collect the Quick/Controls runtime.
from PySide6 import QtQuick, QtQuickControls2  # noqa: F401

from .modern_bridge import ModernStudioBridge


def resource_path(relative: str) -> Path:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return Path(bundle_root) / relative
    return Path(__file__).resolve().parents[2] / relative


def qml_entrypoint() -> Path:
    """Return the modern shell, with an opt-in fallback to the first QML shell."""
    if os.environ.get("PLANTILLAPRO_QML_LEGACY") == "1":
        return resource_path("app/qml/Main.qml")
    return resource_path("app/qml/PolishedMain.qml")


def _load_qml_source(path: Path) -> bytes:
    source = path.read_text(encoding="utf-8")
    if path.name == "PolishedMain.qml":
        # QML object children do not use JavaScript-style semicolon separators. The
        # polished shell deliberately keeps many tiny controls compact on one line;
        # normalize `}; NextType {` / `}; onSignal:` forms before parsing.
        source = source.replace("};", "}")

        # When at least one variable is driven by a data list, those rows determine
        # the copy count. Keep the 4-column numbering grid aligned, but make the count
        # read-only and explicitly show that it comes from the list.
        list_drives_count = "studio.dataRowCount > 0 && studio.variableMappings.some(function(entry) { return entry.source === 'column' })"
        source = source.replace(
            'Text{text:"Cantidad";color:root.muted;font.pixelSize:10}',
            f'Text{{text:({list_drives_count}) ? "Copias (por lista)" : "Cantidad";color:root.muted;font.pixelSize:10}}',
        )
        source = source.replace(
            'FieldBox{text:String(modelData.count);Layout.fillWidth:true;onEditingFinished:studio.setNumberSetting(modelData.id,"count",text)}',
            f'FieldBox{{text:String(({list_drives_count}) ? studio.dataRowCount : modelData.count);enabled:!({list_drives_count});Layout.fillWidth:true;onEditingFinished:studio.setNumberSetting(modelData.id,"count",text)}}',
        )

        # Qt Quick's platform ComboBox clashes with the otherwise custom visual
        # language. Route every selector in the polished shell through ModernSelect,
        # which owns the closed state, hover/focus, chevron and popup styling.
        source = source.replace(
            'ComboBox { model:["Lista / columna","Numeración automática"];',
            'ComboBox { Layout.preferredWidth: 190; model:["Lista / columna","Numeración automática"];',
        )
        source = source.replace("ComboBox {", "ModernSelect {")
        source = source.replace("ComboBox{", "ModernSelect{")
    return source.encode("utf-8")


def create_qml_engine() -> tuple[QQmlApplicationEngine, ModernStudioBridge]:
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        os.environ.setdefault("QSG_RHI_BACKEND", "software")
        os.environ.setdefault("QT_QUICK_BACKEND", "software")

    engine = QQmlApplicationEngine()
    bridge = ModernStudioBridge()
    engine.rootContext().setContextProperty("studio", bridge)
    qml_path = qml_entrypoint()
    engine.loadData(_load_qml_source(qml_path), QUrl.fromLocalFile(str(qml_path.parent) + "/"))
    return engine, bridge
