from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


def studio_icon(name: str, size: int = 24, color: str = "#334155") -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), max(1.5, size / 12), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    s = float(size)

    if name == "text":
        painter.drawLine(QPointF(s*.22, s*.22), QPointF(s*.78, s*.22))
        painter.drawLine(QPointF(s*.5, s*.22), QPointF(s*.5, s*.8))
        painter.drawLine(QPointF(s*.34, s*.8), QPointF(s*.66, s*.8))
    elif name == "image":
        painter.drawRoundedRect(QRectF(s*.16, s*.2, s*.68, s*.58), s*.08, s*.08)
        painter.drawEllipse(QPointF(s*.36, s*.38), s*.07, s*.07)
        path = QPainterPath(QPointF(s*.2, s*.68)); path.lineTo(s*.42, s*.5); path.lineTo(s*.54, s*.6); path.lineTo(s*.66, s*.46); path.lineTo(s*.8, s*.68)
        painter.drawPath(path)
    elif name == "shape":
        painter.drawRoundedRect(QRectF(s*.18, s*.2, s*.58, s*.52), s*.08, s*.08)
        painter.drawEllipse(QRectF(s*.48, s*.48, s*.34, s*.34))
    elif name == "templates":
        for x, y in ((.16,.18),(.52,.18),(.16,.54),(.52,.54)):
            painter.drawRoundedRect(QRectF(s*x, s*y, s*.26, s*.26), s*.04, s*.04)
    elif name == "background":
        painter.drawRoundedRect(QRectF(s*.16, s*.16, s*.68, s*.68), s*.08, s*.08)
        painter.drawLine(QPointF(s*.24,s*.7), QPointF(s*.7,s*.24))
    elif name == "duplicate":
        painter.drawRoundedRect(QRectF(s*.3,s*.2,s*.48,s*.48), s*.05,s*.05)
        painter.drawRoundedRect(QRectF(s*.18,s*.34,s*.48,s*.48), s*.05,s*.05)
    elif name in {"front", "back"}:
        painter.drawRoundedRect(QRectF(s*.22,s*.34,s*.44,s*.4), s*.04,s*.04)
        painter.drawRoundedRect(QRectF(s*.36,s*.2,s*.44,s*.4), s*.04,s*.04)
        y = s*.12 if name == "front" else s*.88
        painter.drawLine(QPointF(s*.16,y), QPointF(s*.34,y))
    elif name == "lock":
        painter.drawRoundedRect(QRectF(s*.24,s*.43,s*.52,s*.4), s*.05,s*.05)
        painter.drawArc(QRectF(s*.32,s*.15,s*.36,s*.42), 0, 180*16)
    elif name == "delete":
        painter.drawLine(QPointF(s*.28,s*.3), QPointF(s*.72,s*.3))
        painter.drawLine(QPointF(s*.36,s*.22), QPointF(s*.64,s*.22))
        painter.drawRoundedRect(QRectF(s*.34,s*.34,s*.32,s*.46), s*.04,s*.04)
    elif name == "fit":
        for a,b in [((.18,.38),(.18,.18)),((.18,.18),(.38,.18)),((.62,.18),(.82,.18)),((.82,.18),(.82,.38)),((.18,.62),(.18,.82)),((.18,.82),(.38,.82)),((.62,.82),(.82,.82)),((.82,.62),(.82,.82))]:
            painter.drawLine(QPointF(s*a[0],s*a[1]), QPointF(s*b[0],s*b[1]))
    elif name == "new":
        painter.drawRoundedRect(QRectF(s*.2,s*.14,s*.5,s*.68), s*.04,s*.04)
        painter.drawLine(QPointF(s*.64,s*.58), QPointF(s*.84,s*.58)); painter.drawLine(QPointF(s*.74,s*.48), QPointF(s*.74,s*.68))
    elif name == "open":
        path = QPainterPath(QPointF(s*.14,s*.38)); path.lineTo(s*.32,s*.38); path.lineTo(s*.4,s*.28); path.lineTo(s*.82,s*.28); path.lineTo(s*.7,s*.76); path.lineTo(s*.18,s*.76); path.closeSubpath(); painter.drawPath(path)
    elif name == "save":
        painter.drawRoundedRect(QRectF(s*.18,s*.16,s*.64,s*.68), s*.04,s*.04)
        painter.drawRect(QRectF(s*.3,s*.18,s*.34,s*.22)); painter.drawRect(QRectF(s*.3,s*.54,s*.4,s*.24))
    elif name == "export":
        painter.drawRoundedRect(QRectF(s*.16,s*.32,s*.54,s*.48), s*.05,s*.05)
        painter.drawLine(QPointF(s*.52,s*.18), QPointF(s*.84,s*.18)); painter.drawLine(QPointF(s*.84,s*.18), QPointF(s*.84,s*.5)); painter.drawLine(QPointF(s*.56,s*.46), QPointF(s*.84,s*.18))
    elif name == "import":
        painter.drawRoundedRect(QRectF(s*.18,s*.2,s*.64,s*.58), s*.05,s*.05)
        painter.drawLine(QPointF(s*.5,s*.14), QPointF(s*.5,s*.58)); painter.drawLine(QPointF(s*.36,s*.44), QPointF(s*.5,s*.58)); painter.drawLine(QPointF(s*.64,s*.44), QPointF(s*.5,s*.58))
    elif name == "paste":
        painter.drawRoundedRect(QRectF(s*.26,s*.26,s*.5,s*.58), s*.05,s*.05)
        painter.drawRoundedRect(QRectF(s*.36,s*.14,s*.28,s*.18), s*.04,s*.04)
    elif name == "add":
        painter.drawEllipse(QRectF(s*.16,s*.16,s*.68,s*.68)); painter.drawLine(QPointF(s*.5,s*.3), QPointF(s*.5,s*.7)); painter.drawLine(QPointF(s*.3,s*.5), QPointF(s*.7,s*.5))
    elif name == "preview":
        path = QPainterPath(QPointF(s*.1,s*.5)); path.cubicTo(s*.28,s*.22,s*.72,s*.22,s*.9,s*.5); path.cubicTo(s*.72,s*.78,s*.28,s*.78,s*.1,s*.5); painter.drawPath(path); painter.drawEllipse(QPointF(s*.5,s*.5),s*.11,s*.11)
    elif name == "pdf":
        painter.drawRoundedRect(QRectF(s*.22,s*.14,s*.56,s*.7), s*.04,s*.04); painter.drawLine(QPointF(s*.32,s*.38),QPointF(s*.68,s*.38)); painter.drawLine(QPointF(s*.32,s*.52),QPointF(s*.64,s*.52)); painter.drawLine(QPointF(s*.32,s*.66),QPointF(s*.58,s*.66))
    else:
        painter.drawEllipse(QRectF(s*.2,s*.2,s*.6,s*.6))

    painter.end()
    return QIcon(pixmap)
