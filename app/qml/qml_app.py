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


def create_qml_engine() -> tuple[QQmlApplicationEngine, ModernStudioBridge]:
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        os.environ.setdefault("QSG_RHI_BACKEND", "software")
        os.environ.setdefault("QT_QUICK_BACKEND", "software")

    engine = QQmlApplicationEngine()
    bridge = ModernStudioBridge()
    engine.rootContext().setContextProperty("studio", bridge)
    qml_path = qml_entrypoint()
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    return engine, bridge
