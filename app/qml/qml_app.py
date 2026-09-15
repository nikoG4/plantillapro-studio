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

        # Static text should preview on the artboard while the user types. The bridge
        # emits only projectChanged for the live path so the TextArea keeps its focus
        # and cursor; losing focus performs the normal committed update.
        source = source.replace(
            'onEditingFinished:studio.setSelectedText(text)',
            'onTextChanged: { if (activeFocus) studio.previewSelectedText(text) } '
            'onActiveFocusChanged: { if (!activeFocus && visible) studio.setSelectedText(text) }',
        )

        # The design rail exposes a palette instead of hard-wiring one rectangle.
        source = source.replace(
            'ModernIconButton { Layout.alignment: Qt.AlignHCenter; iconKind: "shape"; tip: "Rectángulo"; onClicked: studio.addRectangle() }',
            'ShapeToolButton { Layout.alignment: Qt.AlignHCenter }',
        )

        # Use the same shape renderer in the QML canvas that export uses conceptually,
        # including triangles, diamonds and lines rather than a rectangle fallback.
        source = source.replace(
            'Rectangle { anchors.fill: parent; visible: modelData.kind === "shape"; color: modelData.fillColor || "#eef2ff"; border.color: modelData.strokeColor || "#c7d2fe"; border.width: Math.max(0, Number(modelData.strokeWidth || 0)*workspace.docScale); radius: modelData.shapeType === "ellipse" ? width/2 : Math.min(20, Number(modelData.cornerRadius || 0)*workspace.docScale) }',
            'ShapePreview { anchors.fill: parent; visible: modelData.kind === "shape"; shapeType: modelData.shapeType || "rectangle"; fillColor: modelData.fillColor || "#eef2ff"; strokeColor: modelData.strokeColor || "#c7d2fe"; strokeWidth: Math.max(1, Number(modelData.strokeWidth || 0)*workspace.docScale); cornerRadius: Number(modelData.cornerRadius || 0)*workspace.docScale }',
        )
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
