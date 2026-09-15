import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    implicitWidth: 44
    implicitHeight: 44

    ModernIconButton {
        anchors.fill: parent
        iconKind: "shape"
        tip: "Formas"
        onClicked: palette.open()
    }

    Popup {
        id: palette
        parent: Overlay.overlay
        width: 292
        height: 318
        padding: 10
        modal: false
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        x: {
            var p = root.mapToItem(Overlay.overlay, root.width + 10, -34)
            return Math.min(p.x, Overlay.overlay.width - width - 12)
        }
        y: {
            var p = root.mapToItem(Overlay.overlay, root.width + 10, -34)
            return Math.max(12, Math.min(p.y, Overlay.overlay.height - height - 12))
        }

        background: Rectangle {
            radius: 16
            color: "#ffffff"
            border.width: 1
            border.color: "#e5e7eb"
        }

        contentItem: ColumnLayout {
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                Text {
                    text: "Formas"
                    color: "#111827"
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                    Layout.fillWidth: true
                }
                Text {
                    text: "Haz clic para insertar"
                    color: "#94a3b8"
                    font.pixelSize: 10
                }
            }

            GridLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                columns: 2
                columnSpacing: 8
                rowSpacing: 8

                Repeater {
                    model: [
                        { type: "rectangle", label: "Rectángulo" },
                        { type: "rounded_rectangle", label: "Redondeado" },
                        { type: "ellipse", label: "Elipse" },
                        { type: "circle", label: "Círculo" },
                        { type: "triangle", label: "Triángulo" },
                        { type: "diamond", label: "Rombo" },
                        { type: "line", label: "Línea" }
                    ]

                    delegate: Button {
                        id: option
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.preferredHeight: 62
                        hoverEnabled: true

                        onClicked: {
                            studio.addShape(modelData.type)
                            palette.close()
                        }

                        contentItem: RowLayout {
                            spacing: 10
                            ShapePreview {
                                Layout.preferredWidth: 28
                                Layout.preferredHeight: 28
                                shapeType: option.modelData.type
                                fillColor: option.modelData.type === "line" ? "#ffffff" : "#eef2ff"
                                strokeColor: option.hovered ? "#4f46e5" : "#64748b"
                                strokeWidth: option.modelData.type === "line" ? 3 : 1.8
                                cornerRadius: option.modelData.type === "rounded_rectangle" ? 7 : 0
                            }
                            Text {
                                text: option.modelData.label
                                color: "#111827"
                                font.pixelSize: 12
                                font.weight: Font.Medium
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }
                        }

                        background: Rectangle {
                            radius: 11
                            color: option.hovered ? "#eef2ff" : "#f8fafc"
                            border.width: 1
                            border.color: option.hovered ? "#c7d2fe" : "#eef2f7"
                            Behavior on color { ColorAnimation { duration: 90 } }
                            Behavior on border.color { ColorAnimation { duration: 90 } }
                        }
                    }
                }

                Item { Layout.fillWidth: true; Layout.fillHeight: true }
            }
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
