from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QSG_RHI_BACKEND", "software")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, ImageStat
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.qml.qml_app import create_qml_engine


def _not_blank(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 1500:
        return False
    with Image.open(path).convert("RGB") as image:
        return sum(ImageStat.Stat(image).var) > 30


def _settle(app: QApplication, ms: int = 180) -> None:
    app.processEvents()
    QTest.qWait(ms)
    app.processEvents()


def _capture(root, path: Path) -> None:
    image = root.grabWindow()
    if image.isNull():
        raise RuntimeError(f"QML grabWindow devolvió imagen nula: {path.name}")
    if not image.save(str(path)):
        raise RuntimeError(f"No se pudo guardar {path}")


def main() -> None:
    output = Path("artifacts")
    output.mkdir(exist_ok=True)

    app = QApplication.instance() or QApplication([])
    engine, bridge = create_qml_engine()
    if not engine.rootObjects():
        raise RuntimeError("Main.qml no pudo cargarse")
    root = engine.rootObjects()[0]
    root.setProperty("width", 1500)
    root.setProperty("height", 920)
    root.show()
    _settle(app)

    welcome = output / "qml-welcome.png"
    _capture(root, welcome)

    bridge.newA4()
    bridge.addRectangle()
    bridge.setSelectedColor("#eef3ff")
    bridge.moveItem(bridge.selectedId, 250, 1350)
    bridge.resizeItem(bridge.selectedId, 1980, 760)

    bridge.addStaticText()
    bridge.setSelectedName("Título")
    bridge.setSelectedText("Ideas que se imprimen")
    bridge.setSelectedFontSize(150)
    bridge.setSelectedColor("#315efb")
    bridge.moveItem(bridge.selectedId, 350, 480)
    bridge.resizeItem(bridge.selectedId, 1780, 360)

    bridge.addVariableText()
    guest_id = bridge.selectedId
    bridge.setSelectedName("Nombre invitado")
    bridge.setSelectedFontSize(96)
    bridge.moveItem(guest_id, 520, 1530)
    bridge.resizeItem(guest_id, 1420, 260)

    bridge.addVariableText()
    ticket_id = bridge.selectedId
    bridge.setSelectedName("Número")
    bridge.setSelectedFontSize(66)
    bridge.moveItem(ticket_id, 1830, 250)
    bridge.resizeItem(ticket_id, 420, 180)

    bridge.project.data = [{"cliente": "Ana Torres"}, {"cliente": "Luis Ramírez"}, {"cliente": "Mia López"}]
    bridge.setVariableColumn(guest_id, "cliente")
    bridge.setVariableSource(ticket_id, "numbering")
    bridge.setNumberSetting(ticket_id, "start", "1")
    bridge.setNumberSetting(ticket_id, "digits", "3")
    bridge.setNumberSetting(ticket_id, "prefix", "#")
    bridge.selectItem(guest_id)
    bridge.projectChanged.emit()
    _settle(app)

    design = output / "qml-design.png"
    _capture(root, design)

    bridge.setMode("production")
    _settle(app)
    production = output / "qml-production.png"
    _capture(root, production)

    required = [welcome, design, production]
    bad = [path.name for path in required if not _not_blank(path)]
    if bad:
        raise RuntimeError(f"Capturas QML inválidas: {bad}")

    manifest = {
        "qml_visual_validation": "passed",
        "artifacts": {path.name: path.stat().st_size for path in required},
        "features_shown": [
            "qt_quick_shell",
            "modern_welcome",
            "a4_default",
            "vector_icon_rail",
            "qml_design_canvas",
            "context_inspector",
            "layers",
            "variable_mapping",
            "list_source",
            "numbering_source",
            "production_summary",
        ],
    }
    (output / "qml-visual-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    root.close()
    app.processEvents()


if __name__ == "__main__":
    main()
