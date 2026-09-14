from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QUrl, Signal

from .studio_bridge import StudioBridge


class ModernStudioBridge(StudioBridge):
    """QML-specific view properties layered over the stable StudioBridge model API."""

    backgroundChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        # PySide6 can crash when a subclass Property uses an inherited Signal descriptor
        # directly as its notify signal. Mirror project changes through a local signal.
        self.projectChanged.connect(self.backgroundChanged.emit)

    def _background_source(self) -> str:
        path = (self.project.image_path or "").strip()
        if not path:
            return ""
        candidate = Path(path)
        if not candidate.exists():
            return ""
        return QUrl.fromLocalFile(str(candidate.resolve())).toString()

    backgroundSource = Property(str, _background_source, notify=backgroundChanged)
