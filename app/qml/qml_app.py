from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine
# Imported explicitly so PyInstaller's Qt hooks collect the Quick/Controls runtime.
from PySide6 import QtQuick, QtQuickControls2  # noqa: F401

from .studio_bridge import StudioBridge


def resource_path(relative: str) -> Path:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return Path(bundle_root) / relative
    return Path(__file__).resolve().parents[2] / relative


def _load_qml_source(path: Path) -> bytes:
    """Load the QML shell and normalize layout-only spacing for supported Qt 6 builds.

    Qt Quick Controls expose padding on Controls, while ColumnLayout itself does not.
    Keeping the visual spacing as x/width offsets lets the same QML run on the PySide6
    versions used by Linux CI and the packaged Windows app.
    """
    source = path.read_text(encoding="utf-8")
    source = source.replace(
        "width: parent.width\n                                spacing: 14\n                                leftPadding: 16; rightPadding: 16; topPadding: 16; bottomPadding: 20",
        "x: 16\n                                width: Math.max(0, parent.width - 32)\n                                spacing: 14",
    )
    source = source.replace(
        "width: parent.width\n                            spacing: 10\n                            leftPadding: 2; rightPadding: 8; topPadding: 4; bottomPadding: 10",
        "x: 2\n                            width: Math.max(0, parent.width - 10)\n                            spacing: 10",
    )
    return source.encode("utf-8")


def create_qml_engine() -> tuple[QQmlApplicationEngine, StudioBridge]:
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        os.environ.setdefault("QSG_RHI_BACKEND", "software")
        os.environ.setdefault("QT_QUICK_BACKEND", "software")

    engine = QQmlApplicationEngine()
    bridge = StudioBridge()
    engine.rootContext().setContextProperty("studio", bridge)
    qml_path = resource_path("app/qml/Main.qml")
    engine.loadData(_load_qml_source(qml_path), QUrl.fromLocalFile(str(qml_path.parent) + "/"))
    return engine, bridge
