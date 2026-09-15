import QtQuick
import QtQuick.Controls

ComboBox {
    id: control

    property color ink: "#111827"
    property color muted: "#64748b"
    property color borderColor: "#e5e7eb"
    property color accent: "#4f46e5"
    property color accentSoft: "#eef2ff"
    property color surface: "#ffffff"
    property color fieldSurface: "#f8fafc"

    hoverEnabled: true
    implicitHeight: 40
    leftPadding: 12
    rightPadding: 38
    topPadding: 0
    bottomPadding: 0
    font.pixelSize: 13

    contentItem: Text {
        leftPadding: 0
        rightPadding: 0
        text: control.displayText
        color: control.enabled ? control.ink : "#94a3b8"
        font.pixelSize: 13
        font.weight: Font.Medium
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    indicator: Item {
        width: 32
        height: control.height
        x: control.width - width - 2
        y: 0

        Canvas {
            id: chevron
            anchors.centerIn: parent
            width: 14
            height: 14
            rotation: control.popup.visible ? 180 : 0

            Behavior on rotation {
                NumberAnimation { duration: 120; easing.type: Easing.OutCubic }
            }

            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                ctx.strokeStyle = control.enabled ? control.muted : "#94a3b8"
                ctx.lineWidth = 1.7
                ctx.lineCap = "round"
                ctx.lineJoin = "round"
                ctx.beginPath()
                ctx.moveTo(width * 0.24, height * 0.40)
                ctx.lineTo(width * 0.50, height * 0.66)
                ctx.lineTo(width * 0.76, height * 0.40)
                ctx.stroke()
            }

            onRotationChanged: requestPaint()
        }
    }

    background: Rectangle {
        radius: 10
        color: control.enabled
            ? (control.pressed || control.popup.visible ? "#ffffff" : (control.hovered ? "#ffffff" : control.fieldSurface))
            : "#f1f5f9"
        border.width: 1
        border.color: control.activeFocus || control.popup.visible
            ? control.accent
            : (control.hovered ? "#cbd5e1" : control.borderColor)

        Behavior on color { ColorAnimation { duration: 100 } }
        Behavior on border.color { ColorAnimation { duration: 100 } }
    }

    delegate: ItemDelegate {
        id: option
        width: ListView.view ? ListView.view.width : control.width
        height: 40
        hoverEnabled: true
        highlighted: control.highlightedIndex === index
        leftPadding: 11
        rightPadding: 11

        contentItem: Text {
            text: modelData
            color: option.highlighted ? control.accent : control.ink
            font.pixelSize: 13
            font.weight: option.highlighted ? Font.DemiBold : Font.Normal
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        background: Rectangle {
            radius: 8
            color: option.highlighted ? control.accentSoft : (option.hovered ? "#f8fafc" : "transparent")
        }
    }

    popup: Popup {
        y: control.height + 6
        width: control.width
        implicitHeight: Math.min(contentItem.implicitHeight + 10, 260)
        padding: 5

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            spacing: 2
            ScrollIndicator.vertical: ScrollIndicator { }
        }

        background: Rectangle {
            radius: 12
            color: control.surface
            border.width: 1
            border.color: control.borderColor
        }

        enter: Transition {
            ParallelAnimation {
                NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 110 }
                NumberAnimation { property: "scale"; from: 0.98; to: 1; duration: 110; easing.type: Easing.OutCubic }
            }
        }

        exit: Transition {
            NumberAnimation { property: "opacity"; from: 1; to: 0; duration: 80 }
        }
    }
}
