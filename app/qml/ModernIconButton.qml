import QtQuick
import QtQuick.Controls

ToolButton {
    id: root
    property string iconKind: "circle"
    property string tip: ""
    property bool accent: false
    property bool active: false
    implicitWidth: 42
    implicitHeight: 42
    hoverEnabled: true

    contentItem: StudioIcon {
        anchors.centerIn: parent
        width: 21
        height: 21
        kind: root.iconKind
        stroke: root.accent ? "#ffffff" : (root.active || root.hovered ? "#4f46e5" : "#334155")
    }

    background: Rectangle {
        radius: 12
        color: root.accent ? (root.down ? "#4338ca" : "#4f46e5") : (root.active ? "#eef2ff" : (root.hovered ? "#f8fafc" : "transparent"))
        border.width: root.active ? 1 : 0
        border.color: "#c7d2fe"
        Behavior on color { ColorAnimation { duration: 120 } }
    }

    ToolTip.visible: root.hovered && root.tip.length > 0
    ToolTip.text: root.tip
    ToolTip.delay: 380
}
