from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QUrl

from .studio_bridge import StudioBridge


class ModernStudioBridge(StudioBridge):
    """QML-specific view properties layered over the stable StudioBridge model API."""

    def _background_source(self) -> str:
        path = (self.project.image_path or "").strip()
        if not path:
            return ""
        candidate = Path(path)
        if not candidate.exists():
            return ""
        return QUrl.fromLocalFile(str(candidate.resolve())).toString()

    backgroundSource = Property(str, _background_source, notify=StudioBridge.projectChanged)
