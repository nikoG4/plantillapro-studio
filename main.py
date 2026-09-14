from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _classic_requested() -> bool:
    return "--classic" in sys.argv or os.environ.get("PLANTILLAPRO_CLASSIC") == "1"


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PlantillaPro Studio")
    app.setOrganizationName("PlantillaPro")

    icon_path = ROOT / "assets" / "plantillapro_logo.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    if _classic_requested():
        from app.ui.refined_studio_main_window import RefinedStudioMainWindow
        window = RefinedStudioMainWindow()
        window.show()
        return app.exec()

    from app.qml.qml_app import create_qml_engine
    engine, bridge = create_qml_engine()
    # Keep Python-owned QML objects alive for the lifetime of the application.
    app._plantillapro_engine = engine  # type: ignore[attr-defined]
    app._plantillapro_bridge = bridge  # type: ignore[attr-defined]
    if not engine.rootObjects():
        print("No se pudo cargar la interfaz QML. Usa --classic para abrir la interfaz anterior.", file=sys.stderr)
        return 2
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
