from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine

from .studio_bridge import StudioBridge


def resource_path(relative: str) -> Path:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return Path(bundle_root) / relative
    return Path(__file__).resolve().parents[2] / relative


def create_qml_engine() -> tuple[QQmlApplicationEngine, StudioBridge]:
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        os.environ.setdefault("QSG_RHI_BACKEND", "software")
        os.environ.setdefault("QT_QUICK_BACKEND", "software")

    engine = QQmlApplicationEngine()
    bridge = StudioBridge()
    engine.rootContext().setContextProperty("studio", bridge)
    qml_path = resource_path("app/qml/Main.qml")
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    return engine, bridge
