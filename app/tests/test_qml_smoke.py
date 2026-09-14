from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QSG_RHI_BACKEND", "software")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

from PySide6.QtWidgets import QApplication

from app.qml.qml_app import create_qml_engine


def test_qml_shell_loads_offscreen() -> None:
    app = QApplication.instance() or QApplication([])
    engine, bridge = create_qml_engine()
    app.processEvents()
    assert engine.rootObjects(), "Main.qml no pudo cargarse"
    root = engine.rootObjects()[0]
    assert root.property("title") == "PlantillaPro Studio"
    bridge.newA4()
    app.processEvents()
    assert bridge.mode == "design"
    root.close()
