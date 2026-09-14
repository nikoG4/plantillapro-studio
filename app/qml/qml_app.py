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


def _load_qml_source(path: Path) -> bytes:
    """Load the QML shell with small compatibility/layout normalizations."""
    source = path.read_text(encoding="utf-8")

    # ColumnLayout does not expose padding on the Qt versions used by CI/Windows.
    source = source.replace(
        "width: parent.width\n                                spacing: 14\n                                leftPadding: 16; rightPadding: 16; topPadding: 16; bottomPadding: 20",
        "x: 16\n                                width: Math.max(0, parent.width - 32)\n                                spacing: 14",
    )
    source = source.replace(
        "width: parent.width\n                            spacing: 10\n                            leftPadding: 2; rightPadding: 8; topPadding: 4; bottomPadding: 10",
        "x: 2\n                            width: Math.max(0, parent.width - 10)\n                            spacing: 10",
    )

    # Repeater children are inserted into the mapping ColumnLayout. Give the cards an
    # explicit width so ScrollView implicit sizing cannot collapse them to their content.
    source = source.replace(
        "delegate: Card {\n                                    required property var modelData\n                                    Layout.fillWidth: true",
        "delegate: Card {\n                                    required property var modelData\n                                    width: Math.max(520, parent ? parent.width : 800)\n                                    Layout.fillWidth: true",
    )

    # The document is independent from a background image, but when one exists QML must
    # display the same base that the Pillow/PDF renderers use.
    artboard_marker = '''                    Rectangle {\n                        anchors.fill: parent\n                        color: studio.documentTransparent ? "#ffffff" : studio.documentBackground\n                        radius: 2\n                        border.color: "#d9dee8"\n                        layer.enabled: true\n                    }'''
    artboard_with_background = artboard_marker + '''\n\n                    Image {\n                        anchors.fill: parent\n                        source: studio.backgroundSource\n                        visible: source.toString().length > 0\n                        fillMode: Image.Stretch\n                        asynchronous: true\n                        cache: true\n                    }'''
    source = source.replace(artboard_marker, artboard_with_background)

    return source.encode("utf-8")


def create_qml_engine() -> tuple[QQmlApplicationEngine, ModernStudioBridge]:
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        os.environ.setdefault("QSG_RHI_BACKEND", "software")
        os.environ.setdefault("QT_QUICK_BACKEND", "software")

    engine = QQmlApplicationEngine()
    bridge = ModernStudioBridge()
    engine.rootContext().setContextProperty("studio", bridge)
    qml_path = resource_path("app/qml/Main.qml")
    engine.loadData(_load_qml_source(qml_path), QUrl.fromLocalFile(str(qml_path.parent) + "/"))
    return engine, bridge
