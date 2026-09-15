import QtQuick

Canvas {
    id: root

    property string shapeType: "rectangle"
    property color fillColor: "#eef2ff"
    property color strokeColor: "#c7d2fe"
    property real strokeWidth: 2
    property real cornerRadius: 0

    antialiasing: true

    onShapeTypeChanged: requestPaint()
    onFillColorChanged: requestPaint()
    onStrokeColorChanged: requestPaint()
    onStrokeWidthChanged: requestPaint()
    onCornerRadiusChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        var w = Math.max(1, width)
        var h = Math.max(1, height)
        var sw = Math.max(0, strokeWidth)
        var inset = Math.max(1, sw / 2)
        var type = shapeType || "rectangle"

        ctx.fillStyle = fillColor
        ctx.strokeStyle = strokeColor
        ctx.lineWidth = sw
        ctx.lineJoin = "round"
        ctx.lineCap = "round"

        function finishClosed() {
            ctx.closePath()
            ctx.fill()
            if (sw > 0) ctx.stroke()
        }

        if (type === "ellipse" || type === "circle") {
            ctx.beginPath()
            ctx.ellipse(inset, inset, Math.max(1, w - inset * 2), Math.max(1, h - inset * 2))
            ctx.fill()
            if (sw > 0) ctx.stroke()
        } else if (type === "triangle") {
            ctx.beginPath()
            ctx.moveTo(w / 2, inset)
            ctx.lineTo(w - inset, h - inset)
            ctx.lineTo(inset, h - inset)
            finishClosed()
        } else if (type === "diamond") {
            ctx.beginPath()
            ctx.moveTo(w / 2, inset)
            ctx.lineTo(w - inset, h / 2)
            ctx.lineTo(w / 2, h - inset)
            ctx.lineTo(inset, h / 2)
            finishClosed()
        } else if (type === "line") {
            ctx.beginPath()
            ctx.moveTo(inset, h / 2)
            ctx.lineTo(w - inset, h / 2)
            if (sw > 0) ctx.stroke()
        } else if (type === "rounded_rectangle" || cornerRadius > 0) {
            var radius = Math.max(0, Math.min(cornerRadius, w / 2, h / 2))
            ctx.beginPath()
            ctx.roundedRect(inset, inset, Math.max(1, w - inset * 2), Math.max(1, h - inset * 2), radius, radius)
            ctx.fill()
            if (sw > 0) ctx.stroke()
        } else {
            ctx.beginPath()
            ctx.rect(inset, inset, Math.max(1, w - inset * 2), Math.max(1, h - inset * 2))
            ctx.fill()
            if (sw > 0) ctx.stroke()
        }
    }
}
