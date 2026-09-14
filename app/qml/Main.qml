import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: root
    width: 1500
    height: 920
    minimumWidth: 1100
    minimumHeight: 700
    visible: true
    title: "PlantillaPro Studio"
    color: "#f5f7fb"

    property color ink: "#142033"
    property color muted: "#6b778c"
    property color border: "#e4e8f0"
    property color primary: "#315efb"
    property color primarySoft: "#eef3ff"
    property color panel: "#ffffff"
    property int radius: 14
    property string inspectorTab: "properties"

    component Card: Rectangle {
        color: root.panel
        radius: root.radius
        border.color: root.border
        border.width: 1
    }

    component IconGlyph: Canvas {
        property string kind: "circle"
        property color stroke: root.ink
        implicitWidth: 22
        implicitHeight: 22
        onKindChanged: requestPaint()
        onStrokeChanged: requestPaint()
        onPaint: {
            var p = getContext("2d")
            p.reset()
            p.strokeStyle = stroke
            p.fillStyle = stroke
            p.lineWidth = 1.8
            p.lineCap = "round"
            p.lineJoin = "round"
            var w = width, h = height
            function line(x1,y1,x2,y2){ p.beginPath(); p.moveTo(x1*w,y1*h); p.lineTo(x2*w,y2*h); p.stroke() }
            function rect(x,y,rw,rh,rr){ p.beginPath(); p.roundedRect(x*w,y*h,rw*w,rh*h,rr*w,rr*w); p.stroke() }
            if (kind === "text") {
                line(.22,.22,.78,.22); line(.5,.22,.5,.8); line(.34,.8,.66,.8)
            } else if (kind === "variable") {
                p.font = Math.max(10, w*.48) + "px sans-serif"; p.textAlign="center"; p.textBaseline="middle"; p.fillText("{}", w*.5, h*.52)
            } else if (kind === "image") {
                rect(.16,.2,.68,.58,.07); p.beginPath(); p.arc(w*.35,h*.37,w*.065,0,Math.PI*2); p.stroke();
                p.beginPath(); p.moveTo(w*.2,h*.68); p.lineTo(w*.42,h*.5); p.lineTo(w*.55,h*.6); p.lineTo(w*.67,h*.45); p.lineTo(w*.8,h*.68); p.stroke()
            } else if (kind === "shape") {
                rect(.18,.2,.56,.5,.08); p.beginPath(); p.arc(w*.67,h*.66,w*.16,0,Math.PI*2); p.stroke()
            } else if (kind === "new") {
                rect(.2,.15,.48,.66,.04); line(.68,.58,.86,.58); line(.77,.49,.77,.67)
            } else if (kind === "open") {
                p.beginPath(); p.moveTo(w*.14,h*.38); p.lineTo(w*.31,h*.38); p.lineTo(w*.4,h*.28); p.lineTo(w*.82,h*.28); p.lineTo(w*.7,h*.76); p.lineTo(w*.18,h*.76); p.closePath(); p.stroke()
            } else if (kind === "save") {
                rect(.18,.16,.64,.68,.04); p.strokeRect(w*.31,h*.18,w*.33,h*.21); p.strokeRect(w*.3,h*.54,w*.4,h*.24)
            } else if (kind === "export") {
                rect(.16,.34,.52,.45,.05); line(.54,.18,.84,.18); line(.84,.18,.84,.48); line(.57,.45,.84,.18)
            } else if (kind === "duplicate") {
                rect(.29,.2,.48,.47,.05); rect(.18,.34,.48,.47,.05)
            } else if (kind === "front" || kind === "back") {
                rect(.22,.35,.42,.38,.04); rect(.37,.2,.42,.38,.04); if(kind==="front"){line(.15,.12,.34,.12)}else{line(.15,.88,.34,.88)}
            } else if (kind === "lock") {
                rect(.24,.44,.52,.38,.05); p.beginPath(); p.arc(w*.5,h*.42,w*.18,Math.PI,0); p.stroke()
            } else if (kind === "delete") {
                line(.28,.3,.72,.3); line(.37,.22,.63,.22); rect(.34,.35,.32,.45,.04)
            } else if (kind === "fit") {
                line(.18,.38,.18,.18); line(.18,.18,.38,.18); line(.62,.18,.82,.18); line(.82,.18,.82,.38); line(.18,.62,.18,.82); line(.18,.82,.38,.82); line(.62,.82,.82,.82); line(.82,.62,.82,.82)
            } else if (kind === "data") {
                rect(.16,.2,.68,.58,.05); line(.25,.36,.75,.36); line(.25,.5,.75,.5); line(.25,.64,.75,.64)
            } else {
                p.beginPath(); p.arc(w*.5,h*.5,w*.28,0,Math.PI*2); p.stroke()
            }
        }
    }

    component IconButton: ToolButton {
        id: control
        property string iconKind: "circle"
        property string tip: ""
        property bool accent: false
        implicitWidth: 42
        implicitHeight: 42
        hoverEnabled: true
        contentItem: IconGlyph {
            kind: control.iconKind
            stroke: control.accent ? "#ffffff" : (control.hovered ? root.primary : root.ink)
            anchors.centerIn: parent
        }
        background: Rectangle {
            radius: 11
            color: control.accent ? root.primary : (control.hovered ? root.primarySoft : "transparent")
            border.color: control.accent ? root.primary : "transparent"
        }
        ToolTip.visible: hovered && tip.length > 0
        ToolTip.text: tip
        ToolTip.delay: 450
    }

    component PillButton: Button {
        id: control
        property bool active: false
        hoverEnabled: true
        leftPadding: 16; rightPadding: 16; topPadding: 9; bottomPadding: 9
        contentItem: Text {
            text: control.text
            color: control.active ? root.primary : root.muted
            font.pixelSize: 14
            font.weight: control.active ? Font.DemiBold : Font.Medium
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            radius: 11
            color: control.active ? "#ffffff" : (control.hovered ? "#f7f9fd" : "transparent")
            border.color: control.active ? root.border : "transparent"
        }
    }

    component PrimaryButton: Button {
        id: control
        property bool outlined: false
        property string iconKind: "circle"
        hoverEnabled: true
        leftPadding: 18; rightPadding: 18; topPadding: 12; bottomPadding: 12
        contentItem: RowLayout {
            spacing: 9
            IconGlyph { kind: control.iconKind; stroke: control.outlined ? root.ink : "#ffffff"; width: 18; height: 18 }
            Text { text: control.text; color: control.outlined ? root.ink : "#ffffff"; font.pixelSize: 14; font.weight: Font.DemiBold }
        }
        background: Rectangle {
            radius: 11
            color: control.outlined ? (control.hovered ? "#f8faff" : "#ffffff") : (control.hovered ? "#244ce5" : root.primary)
            border.color: control.outlined ? root.border : root.primary
        }
    }

    component SectionTitle: Text {
        color: root.ink
        font.pixelSize: 14
        font.weight: Font.DemiBold
    }

    component SoftField: TextField {
        id: control
        implicitHeight: 38
        color: root.ink
        selectionColor: root.primary
        selectedTextColor: "#ffffff"
        font.pixelSize: 13
        leftPadding: 11; rightPadding: 11
        background: Rectangle {
            radius: 9
            color: "#f8f9fc"
            border.color: control.activeFocus ? root.primary : root.border
        }
    }

    header: Rectangle {
        height: 66
        color: "#ffffff"
        border.color: root.border
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 20
            anchors.rightMargin: 20
            spacing: 12
            Rectangle {
                width: 34; height: 34; radius: 10; color: root.primary
                Text { anchors.centerIn: parent; text: "P"; color: "white"; font.bold: true; font.pixelSize: 18 }
            }
            ColumnLayout {
                spacing: -1
                Text { text: "PlantillaPro"; color: root.ink; font.pixelSize: 16; font.weight: Font.DemiBold }
                Text { text: studio.projectName; color: root.muted; font.pixelSize: 11 }
            }
            Item { Layout.preferredWidth: 18 }
            Rectangle {
                Layout.preferredWidth: 220
                height: 44
                radius: 13
                color: "#f3f5f9"
                RowLayout {
                    anchors.fill: parent; anchors.margins: 4; spacing: 2
                    PillButton { text: "Diseño"; active: studio.mode === "design"; Layout.fillWidth: true; onClicked: studio.setMode("design") }
                    PillButton { text: "Producción"; active: studio.mode === "production"; Layout.fillWidth: true; onClicked: studio.setMode("production") }
                }
            }
            Item { Layout.fillWidth: true }
            IconButton { iconKind: "new"; tip: "Nuevo A4"; onClicked: studio.newA4() }
            IconButton { iconKind: "open"; tip: "Abrir proyecto"; onClicked: studio.openProject() }
            IconButton { iconKind: "save"; tip: "Guardar proyecto"; onClicked: studio.saveProject() }
            Rectangle { width: 1; height: 28; color: root.border }
            IconButton { iconKind: "export"; tip: "Ir a Producción"; accent: true; onClicked: studio.setMode("production") }
        }
    }

    StackLayout {
        anchors.fill: parent
        currentIndex: studio.mode === "welcome" ? 0 : (studio.mode === "design" ? 1 : 2)

        // ---------------- Welcome -----------------------------------------
        Item {
            Rectangle { anchors.fill: parent; color: "#f5f7fb" }
            ColumnLayout {
                anchors.centerIn: parent
                width: Math.min(parent.width - 80, 980)
                spacing: 24
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Empieza tu diseño"
                    color: root.ink
                    font.pixelSize: 34
                    font.weight: Font.Bold
                }
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Crea desde un lienzo en blanco, una imagen o un proyecto existente."
                    color: root.muted
                    font.pixelSize: 15
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 16
                    Card {
                        Layout.fillWidth: true; Layout.preferredHeight: 190
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: studio.newA4() }
                        Column { anchors.centerIn: parent; spacing: 12
                            Rectangle { width: 56; height: 56; radius: 16; color: root.primarySoft; anchors.horizontalCenter: parent.horizontalCenter
                                IconGlyph { anchors.centerIn: parent; kind: "new"; stroke: root.primary; width: 26; height: 26 }
                            }
                            Text { text: "Lienzo A4 en blanco"; color: root.ink; font.pixelSize: 17; font.weight: Font.DemiBold; anchors.horizontalCenter: parent.horizontalCenter }
                            Text { text: "2480 × 3508 px · 300 DPI"; color: root.muted; font.pixelSize: 12; anchors.horizontalCenter: parent.horizontalCenter }
                        }
                    }
                    Card {
                        Layout.fillWidth: true; Layout.preferredHeight: 190
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: { studio.newA4(); studio.loadBackground() } }
                        Column { anchors.centerIn: parent; spacing: 12
                            Rectangle { width: 56; height: 56; radius: 16; color: "#f2efff"; anchors.horizontalCenter: parent.horizontalCenter
                                IconGlyph { anchors.centerIn: parent; kind: "image"; stroke: "#6d55d9"; width: 26; height: 26 }
                            }
                            Text { text: "Diseñar sobre imagen"; color: root.ink; font.pixelSize: 17; font.weight: Font.DemiBold; anchors.horizontalCenter: parent.horizontalCenter }
                            Text { text: "Carga una imagen como base"; color: root.muted; font.pixelSize: 12; anchors.horizontalCenter: parent.horizontalCenter }
                        }
                    }
                    Card {
                        Layout.fillWidth: true; Layout.preferredHeight: 190
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: studio.openProject() }
                        Column { anchors.centerIn: parent; spacing: 12
                            Rectangle { width: 56; height: 56; radius: 16; color: "#eaf8f1"; anchors.horizontalCenter: parent.horizontalCenter
                                IconGlyph { anchors.centerIn: parent; kind: "open"; stroke: "#24865f"; width: 26; height: 26 }
                            }
                            Text { text: "Abrir proyecto"; color: root.ink; font.pixelSize: 17; font.weight: Font.DemiBold; anchors.horizontalCenter: parent.horizontalCenter }
                            Text { text: "Continúa un archivo .json"; color: root.muted; font.pixelSize: 12; anchors.horizontalCenter: parent.horizontalCenter }
                        }
                    }
                }
                Text { text: "Tamaños rápidos"; color: root.ink; font.pixelSize: 14; font.weight: Font.DemiBold }
                RowLayout {
                    Layout.fillWidth: true; spacing: 10
                    Repeater {
                        model: [
                            {name:"A4", w:2480, h:3508}, {name:"A5", w:1748, h:2480},
                            {name:"Tarjeta", w:1050, h:600}, {name:"Post", w:1080, h:1080},
                            {name:"Ticket", w:1200, h:600}
                        ]
                        delegate: Button {
                            required property var modelData
                            text: modelData.name
                            Layout.fillWidth: true
                            implicitHeight: 54
                            onClicked: studio.newDocument(modelData.w, modelData.h, "#ffffff", false)
                            contentItem: Text { text: parent.text; color: root.ink; font.pixelSize: 13; font.weight: Font.Medium; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                            background: Rectangle { radius: 10; color: parent.hovered ? "#ffffff" : "#f8f9fc"; border.color: root.border }
                        }
                    }
                }
            }
        }

        // ---------------- Design ------------------------------------------
        RowLayout {
            spacing: 0
            Rectangle {
                Layout.preferredWidth: 76
                Layout.fillHeight: true
                color: "#ffffff"
                border.color: root.border
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 12; spacing: 10
                    IconButton { iconKind: "text"; tip: "Agregar texto fijo"; Layout.alignment: Qt.AlignHCenter; onClicked: studio.addStaticText() }
                    IconButton { iconKind: "variable"; tip: "Agregar campo variable"; Layout.alignment: Qt.AlignHCenter; onClicked: studio.addVariableText() }
                    IconButton { iconKind: "image"; tip: "Agregar imagen"; Layout.alignment: Qt.AlignHCenter; onClicked: studio.addImage() }
                    IconButton { iconKind: "shape"; tip: "Agregar rectángulo"; Layout.alignment: Qt.AlignHCenter; onClicked: studio.addRectangle() }
                    Item { Layout.fillHeight: true }
                    IconButton { iconKind: "image"; tip: "Cambiar imagen de fondo"; Layout.alignment: Qt.AlignHCenter; onClicked: studio.loadBackground() }
                }
            }

            Rectangle {
                id: workspace
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#eef1f6"

                property real docScale: Math.max(0.04, Math.min(
                    (width - 130) / Math.max(1, studio.documentWidth),
                    (height - 140) / Math.max(1, studio.documentHeight)
                ))

                // contextual floating actions
                Card {
                    visible: studio.selectedId !== ""
                    z: 1000
                    width: 230; height: 48
                    anchors.top: parent.top; anchors.topMargin: 16
                    anchors.horizontalCenter: parent.horizontalCenter
                    RowLayout {
                        anchors.centerIn: parent; spacing: 4
                        IconButton { iconKind: "duplicate"; tip: "Duplicar"; onClicked: studio.duplicateSelected() }
                        IconButton { iconKind: "front"; tip: "Traer al frente"; onClicked: studio.bringSelectedToFront() }
                        IconButton { iconKind: "back"; tip: "Enviar atrás"; onClicked: studio.sendSelectedToBack() }
                        IconButton { iconKind: "lock"; tip: "Bloquear / desbloquear"; onClicked: studio.toggleSelectedLock() }
                        IconButton { iconKind: "delete"; tip: "Eliminar"; onClicked: studio.deleteSelected() }
                    }
                }

                Item {
                    id: artboardHost
                    width: studio.documentWidth * workspace.docScale
                    height: studio.documentHeight * workspace.docScale
                    anchors.centerIn: parent

                    Rectangle {
                        anchors.fill: parent
                        color: studio.documentTransparent ? "#ffffff" : studio.documentBackground
                        radius: 2
                        border.color: "#d9dee8"
                        layer.enabled: true
                    }

                    // transparent checker hint
                    Canvas {
                        anchors.fill: parent
                        visible: studio.documentTransparent
                        opacity: .55
                        onPaint: {
                            var p = getContext("2d"); p.reset(); var cell=12
                            for(var y=0;y<height;y+=cell){ for(var x=0;x<width;x+=cell){ p.fillStyle=((x/cell+y/cell)%2<1)?"#ffffff":"#e9edf3"; p.fillRect(x,y,cell,cell) } }
                        }
                    }

                    Repeater {
                        model: studio.elements
                        delegate: Item {
                            id: designItem
                            required property var modelData
                            x: modelData.x * workspace.docScale
                            y: modelData.y * workspace.docScale
                            width: Math.max(8, modelData.width * workspace.docScale)
                            height: Math.max(8, modelData.height * workspace.docScale)
                            rotation: -Number(modelData.rotation || 0)
                            opacity: Number(modelData.opacity === undefined ? 1 : modelData.opacity)
                            z: Number(modelData.z || 0)

                            Rectangle {
                                anchors.fill: parent
                                visible: modelData.kind === "shape"
                                color: modelData.fillColor || "#eef2ff"
                                radius: modelData.shapeType === "ellipse" ? width/2 : Math.min(18, Number(modelData.cornerRadius || 0) * workspace.docScale)
                                border.color: modelData.strokeColor || "#c7d2fe"
                                border.width: Math.max(0, Number(modelData.strokeWidth || 0) * workspace.docScale)
                            }
                            Image {
                                anchors.fill: parent
                                visible: modelData.kind === "image"
                                source: modelData.source || ""
                                fillMode: modelData.fitMode === "contain" ? Image.PreserveAspectFit : (modelData.fitMode === "stretch" ? Image.Stretch : Image.PreserveAspectCrop)
                                asynchronous: true
                                cache: true
                            }
                            Text {
                                anchors.fill: parent
                                visible: modelData.kind === "text" || modelData.kind === "variable"
                                text: modelData.text || ""
                                color: modelData.color || root.ink
                                font.pixelSize: Math.max(7, Number(modelData.fontSize || 32) * workspace.docScale)
                                font.bold: Boolean(modelData.bold)
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                wrapMode: Text.WordWrap
                                elide: Text.ElideNone
                            }
                            Rectangle {
                                anchors.fill: parent
                                color: "transparent"
                                border.width: studio.selectedId === modelData.id ? 2 : 0
                                border.color: root.primary
                                radius: 3
                            }
                            MouseArea {
                                id: mover
                                anchors.fill: parent
                                enabled: !Boolean(modelData.locked)
                                cursorShape: enabled ? Qt.SizeAllCursor : Qt.ArrowCursor
                                drag.target: designItem
                                drag.axis: Drag.XAndYAxis
                                onPressed: studio.selectItem(modelData.id)
                                onReleased: studio.moveItem(modelData.id, designItem.x / workspace.docScale, designItem.y / workspace.docScale)
                            }
                            Rectangle {
                                id: resizeHandle
                                visible: studio.selectedId === modelData.id && !Boolean(modelData.locked)
                                width: 12; height: 12; radius: 3
                                color: root.primary
                                x: designItem.width - width/2
                                y: designItem.height - height/2
                                z: 100
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.SizeFDiagCursor
                                    property real startW: 0
                                    property real startH: 0
                                    property real startX: 0
                                    property real startY: 0
                                    onPressed: function(mouse) { startW = designItem.width; startH = designItem.height; startX = mouse.x; startY = mouse.y; mouse.accepted = true }
                                    onPositionChanged: function(mouse) {
                                        if (!pressed) return
                                        designItem.width = Math.max(24, startW + mouse.x - startX)
                                        designItem.height = Math.max(24, startH + mouse.y - startY)
                                    }
                                    onReleased: studio.resizeItem(modelData.id, designItem.width / workspace.docScale, designItem.height / workspace.docScale)
                                }
                            }
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        z: -1
                        onClicked: studio.clearSelection()
                    }
                }

                Rectangle {
                    anchors.left: parent.left; anchors.bottom: parent.bottom
                    anchors.margins: 14
                    width: 210; height: 34; radius: 9
                    color: "#ffffffcc"; border.color: root.border
                    Text { anchors.centerIn: parent; text: studio.documentWidth + " × " + studio.documentHeight + " px"; color: root.muted; font.pixelSize: 12 }
                }
            }

            Rectangle {
                Layout.preferredWidth: 344
                Layout.fillHeight: true
                color: "#ffffff"
                border.color: root.border
                ColumnLayout {
                    anchors.fill: parent; spacing: 0
                    Rectangle {
                        Layout.fillWidth: true; Layout.preferredHeight: 54; color: "#ffffff"
                        RowLayout { anchors.fill: parent; anchors.margins: 8; spacing: 4
                            PillButton { text: "Propiedades"; active: root.inspectorTab === "properties"; Layout.fillWidth: true; onClicked: root.inspectorTab = "properties" }
                            PillButton { text: "Capas"; active: root.inspectorTab === "layers"; Layout.fillWidth: true; onClicked: root.inspectorTab = "layers" }
                        }
                    }
                    Rectangle { Layout.fillWidth: true; height: 1; color: root.border }
                    StackLayout {
                        Layout.fillWidth: true; Layout.fillHeight: true
                        currentIndex: root.inspectorTab === "properties" ? 0 : 1
                        ScrollView {
                            clip: true
                            ColumnLayout {
                                width: parent.width
                                spacing: 14
                                leftPadding: 16; rightPadding: 16; topPadding: 16; bottomPadding: 20

                                ColumnLayout {
                                    visible: studio.selectedId === ""
                                    Layout.fillWidth: true; spacing: 12
                                    Text { text: "Lienzo"; color: root.ink; font.pixelSize: 20; font.weight: Font.Bold }
                                    Text { text: "Ajustes del documento"; color: root.muted; font.pixelSize: 12 }
                                    Card {
                                        Layout.fillWidth: true; Layout.preferredHeight: 150
                                        ColumnLayout { anchors.fill: parent; anchors.margins: 14; spacing: 10
                                            SectionTitle { text: "Tamaño" }
                                            Text { text: studio.documentWidth + " × " + studio.documentHeight + " px"; color: root.ink; font.pixelSize: 13 }
                                            SectionTitle { text: "Color de fondo" }
                                            SoftField { Layout.fillWidth: true; text: studio.documentBackground; onEditingFinished: studio.setDocumentBackground(text) }
                                        }
                                    }
                                    Switch { text: "Fondo transparente"; checked: studio.documentTransparent; onToggled: studio.setDocumentTransparent(checked) }
                                    PrimaryButton { text: "Cargar imagen de fondo"; iconKind: "image"; outlined: true; Layout.fillWidth: true; onClicked: studio.loadBackground() }
                                }

                                ColumnLayout {
                                    visible: studio.selectedId !== ""
                                    Layout.fillWidth: true; spacing: 12
                                    Text { text: studio.selectedData.name || "Selección"; color: root.ink; font.pixelSize: 20; font.weight: Font.Bold }
                                    Rectangle {
                                        implicitWidth: kindText.implicitWidth + 18; implicitHeight: 26; radius: 8
                                        color: root.primarySoft
                                        Text { id: kindText; anchors.centerIn: parent; color: root.primary; font.pixelSize: 11; font.weight: Font.DemiBold
                                            text: studio.selectedData.kind === "variable" ? "CAMPO VARIABLE" : (studio.selectedData.kind === "text" ? "TEXTO FIJO" : (studio.selectedData.kind === "image" ? "IMAGEN" : "FORMA"))
                                        }
                                    }
                                    SectionTitle { text: "Nombre" }
                                    SoftField { Layout.fillWidth: true; text: studio.selectedData.name || ""; onEditingFinished: studio.setSelectedName(text) }
                                    ColumnLayout {
                                        visible: studio.selectedData.kind === "text"
                                        Layout.fillWidth: true; spacing: 6
                                        SectionTitle { text: "Contenido" }
                                        TextArea {
                                            Layout.fillWidth: true; Layout.preferredHeight: 84
                                            text: studio.selectedData.template || ""
                                            color: root.ink; font.pixelSize: 13; wrapMode: TextEdit.Wrap
                                            background: Rectangle { radius: 9; color: "#f8f9fc"; border.color: root.border }
                                            onEditingFinished: studio.setSelectedText(text)
                                        }
                                    }
                                    RowLayout {
                                        visible: studio.selectedData.kind === "text" || studio.selectedData.kind === "variable"
                                        Layout.fillWidth: true; spacing: 8
                                        ColumnLayout { Layout.fillWidth: true; spacing: 5
                                            SectionTitle { text: "Tamaño" }
                                            SpinBox { from: 6; to: 500; value: Number(studio.selectedData.fontSize || 32); editable: true; Layout.fillWidth: true; onValueModified: studio.setSelectedFontSize(value) }
                                        }
                                        ColumnLayout { Layout.fillWidth: true; spacing: 5
                                            SectionTitle { text: studio.selectedData.kind === "shape" ? "Relleno" : "Color" }
                                            SoftField { Layout.fillWidth: true; text: studio.selectedData.color || studio.selectedData.fillColor || "#000000"; onEditingFinished: studio.setSelectedColor(text) }
                                        }
                                    }
                                    SectionTitle { text: "Opacidad" }
                                    Slider { Layout.fillWidth: true; from: 0; to: 1; value: Number(studio.selectedData.opacity === undefined ? 1 : studio.selectedData.opacity); onMoved: studio.setSelectedOpacity(value) }
                                    SectionTitle { text: "Rotación" }
                                    SpinBox { Layout.fillWidth: true; from: -360; to: 360; value: Math.round(Number(studio.selectedData.rotation || 0)); editable: true; onValueModified: studio.setSelectedRotation(value) }
                                    Rectangle { Layout.fillWidth: true; height: 1; color: root.border }
                                    RowLayout {
                                        Layout.fillWidth: true; spacing: 6
                                        IconButton { iconKind: "duplicate"; tip: "Duplicar"; onClicked: studio.duplicateSelected() }
                                        IconButton { iconKind: "front"; tip: "Traer al frente"; onClicked: studio.bringSelectedToFront() }
                                        IconButton { iconKind: "back"; tip: "Enviar atrás"; onClicked: studio.sendSelectedToBack() }
                                        Item { Layout.fillWidth: true }
                                        IconButton { iconKind: "delete"; tip: "Eliminar"; onClicked: studio.deleteSelected() }
                                    }
                                }
                            }
                        }
                        ScrollView {
                            clip: true
                            ListView {
                                id: layerList
                                model: studio.layers
                                spacing: 6
                                leftMargin: 10; rightMargin: 10; topMargin: 10; bottomMargin: 10
                                delegate: Rectangle {
                                    required property var modelData
                                    width: layerList.width - 20
                                    height: 54
                                    radius: 10
                                    color: studio.selectedId === modelData.id ? root.primarySoft : "#ffffff"
                                    border.color: studio.selectedId === modelData.id ? "#c9d6ff" : root.border
                                    RowLayout {
                                        anchors.fill: parent; anchors.margins: 10; spacing: 10
                                        Rectangle { width: 32; height: 32; radius: 8; color: "#f3f5f9"
                                            Text { anchors.centerIn: parent; text: modelData.kind === "variable" ? "{}" : (modelData.kind === "text" ? "T" : (modelData.kind === "image" ? "I" : "S")); color: root.ink; font.weight: Font.DemiBold }
                                        }
                                        ColumnLayout { Layout.fillWidth: true; spacing: 1
                                            Text { text: modelData.name; color: root.ink; font.pixelSize: 13; font.weight: Font.Medium; elide: Text.ElideRight; Layout.fillWidth: true }
                                            Text { text: modelData.kind === "variable" ? "Variable" : modelData.kind; color: root.muted; font.pixelSize: 10 }
                                        }
                                    }
                                    MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: studio.selectItem(modelData.id) }
                                }
                            }
                        }
                    }
                }
            }
        }

        // ---------------- Production --------------------------------------
        RowLayout {
            spacing: 16
            Item { Layout.preferredWidth: 8 }
            ColumnLayout {
                Layout.fillWidth: true; Layout.fillHeight: true
                spacing: 12
                Item { Layout.preferredHeight: 8 }
                Text { text: "Producción"; color: root.ink; font.pixelSize: 30; font.weight: Font.Bold }
                Text { text: "Elige de dónde sale cada campo variable. Los textos fijos no aparecen aquí."; color: root.muted; font.pixelSize: 14 }
                Rectangle {
                    Layout.fillWidth: true; Layout.preferredHeight: 52; radius: 12; color: "#ffffff"; border.color: root.border
                    Text { anchors.centerIn: parent; text: "1  Campos variables    →    2  Datos    →    3  Revisar    →    4  Exportar"; color: root.ink; font.pixelSize: 13; font.weight: Font.DemiBold }
                }
                SplitView {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    orientation: Qt.Vertical
                    ScrollView {
                        SplitView.fillWidth: true; SplitView.preferredHeight: 430
                        clip: true
                        ColumnLayout {
                            width: parent.width
                            spacing: 10
                            leftPadding: 2; rightPadding: 8; topPadding: 4; bottomPadding: 10
                            Text { text: "1. Campos variables"; color: root.ink; font.pixelSize: 16; font.weight: Font.DemiBold }
                            Text { visible: studio.variableMappings.length === 0; text: "No hay campos variables. Vuelve a Diseño y agrega un campo variable."; color: root.muted; font.pixelSize: 13 }
                            Repeater {
                                model: studio.variableMappings
                                delegate: Card {
                                    required property var modelData
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: modelData.source === "numbering" ? 205 : 150
                                    ColumnLayout {
                                        anchors.fill: parent; anchors.margins: 14; spacing: 9
                                        RowLayout {
                                            Layout.fillWidth: true
                                            ColumnLayout { Layout.fillWidth: true; spacing: 1
                                                Text { text: modelData.name; color: root.ink; font.pixelSize: 15; font.weight: Font.DemiBold }
                                                Text { text: modelData.key; color: root.muted; font.pixelSize: 11 }
                                            }
                                            Rectangle { width: 90; height: 26; radius: 8; color: root.primarySoft
                                                Text { anchors.centerIn: parent; text: "VARIABLE"; color: root.primary; font.pixelSize: 10; font.weight: Font.DemiBold }
                                            }
                                        }
                                        RowLayout {
                                            spacing: 6
                                            PillButton { text: "Lista / columna"; active: modelData.source === "column"; onClicked: studio.setVariableSource(modelData.id, "column") }
                                            PillButton { text: "Numeración"; active: modelData.source === "numbering"; onClicked: studio.setVariableSource(modelData.id, "numbering") }
                                            Item { Layout.fillWidth: true }
                                        }
                                        ComboBox {
                                            visible: modelData.source === "column"
                                            Layout.fillWidth: true
                                            model: modelData.columns
                                            currentIndex: Math.max(0, modelData.columns.indexOf(modelData.column))
                                            onActivated: studio.setVariableColumn(modelData.id, currentText)
                                        }
                                        RowLayout {
                                            visible: modelData.source === "numbering"
                                            Layout.fillWidth: true; spacing: 8
                                            ColumnLayout { Layout.fillWidth: true; spacing: 4
                                                Text { text: "Inicio"; color: root.muted; font.pixelSize: 11 }
                                                SoftField { Layout.fillWidth: true; text: String(modelData.start); onEditingFinished: studio.setNumberSetting(modelData.id,"start",text) }
                                            }
                                            ColumnLayout { Layout.fillWidth: true; spacing: 4
                                                Text { text: "Paso"; color: root.muted; font.pixelSize: 11 }
                                                SoftField { Layout.fillWidth: true; text: String(modelData.step); onEditingFinished: studio.setNumberSetting(modelData.id,"step",text) }
                                            }
                                            ColumnLayout { Layout.fillWidth: true; spacing: 4
                                                Text { text: "Dígitos"; color: root.muted; font.pixelSize: 11 }
                                                SoftField { Layout.fillWidth: true; text: String(modelData.digits); onEditingFinished: studio.setNumberSetting(modelData.id,"digits",text) }
                                            }
                                        }
                                        RowLayout {
                                            visible: modelData.source === "numbering"
                                            Layout.fillWidth: true; spacing: 8
                                            SoftField { Layout.fillWidth: true; placeholderText: "Prefijo"; text: modelData.prefix; onEditingFinished: studio.setNumberSetting(modelData.id,"prefix",text) }
                                            SoftField { Layout.fillWidth: true; placeholderText: "Sufijo"; text: modelData.suffix; onEditingFinished: studio.setNumberSetting(modelData.id,"suffix",text) }
                                            SoftField { visible: studio.dataRowCount === 0; Layout.preferredWidth: 95; placeholderText: "Cantidad"; text: String(modelData.count); onEditingFinished: studio.setNumberSetting(modelData.id,"count",text) }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    Card {
                        SplitView.fillWidth: true; SplitView.fillHeight: true
                        ColumnLayout {
                            anchors.fill: parent; anchors.margins: 14; spacing: 10
                            RowLayout {
                                Layout.fillWidth: true
                                ColumnLayout { spacing: 1
                                    Text { text: "2. Datos"; color: root.ink; font.pixelSize: 16; font.weight: Font.DemiBold }
                                    Text { text: studio.dataRowCount + " filas"; color: root.muted; font.pixelSize: 11 }
                                }
                                Item { Layout.fillWidth: true }
                                IconButton { iconKind: "data"; tip: "Importar CSV / Excel / TXT"; onClicked: studio.importData() }
                                IconButton { iconKind: "new"; tip: "Agregar fila vacía"; onClicked: studio.addEmptyDataRow() }
                            }
                            Rectangle { Layout.fillWidth: true; height: 1; color: root.border }
                            Text { visible: studio.dataPreview.length === 0; text: "Importa una lista para rellenar campos variables desde columnas."; color: root.muted; font.pixelSize: 13 }
                            ListView {
                                Layout.fillWidth: true; Layout.fillHeight: true
                                model: studio.dataPreview
                                spacing: 4
                                clip: true
                                delegate: Rectangle {
                                    required property string modelData
                                    required property int index
                                    width: ListView.view.width; height: 38; radius: 8
                                    color: index % 2 ? "#fafbfc" : "#ffffff"
                                    RowLayout { anchors.fill: parent; anchors.leftMargin: 10; anchors.rightMargin: 8
                                        Text { text: (index + 1) + "."; color: root.muted; font.pixelSize: 11; Layout.preferredWidth: 30 }
                                        Text { text: modelData; color: root.ink; font.pixelSize: 12; elide: Text.ElideRight; Layout.fillWidth: true }
                                        IconButton { iconKind: "delete"; tip: "Eliminar fila"; implicitWidth: 30; implicitHeight: 30; onClicked: studio.deleteDataRow(index) }
                                    }
                                }
                            }
                        }
                    }
                }
                Item { Layout.preferredHeight: 8 }
            }
            Card {
                Layout.preferredWidth: 360
                Layout.fillHeight: true
                Layout.topMargin: 16; Layout.bottomMargin: 16; Layout.rightMargin: 16
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 18; spacing: 14
                    Text { text: "Resumen de producción"; color: root.ink; font.pixelSize: 18; font.weight: Font.Bold }
                    Text { text: studio.productionSummary; color: root.muted; font.pixelSize: 13; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Rectangle { Layout.fillWidth: true; height: 1; color: root.border }
                    Text { text: "Diseño"; color: root.muted; font.pixelSize: 11 }
                    Text { text: studio.documentWidth + " × " + studio.documentHeight + " px"; color: root.ink; font.pixelSize: 13; font.weight: Font.Medium }
                    Text { text: "Copias a generar"; color: root.muted; font.pixelSize: 11 }
                    Text { text: String(studio.productionCount); color: root.primary; font.pixelSize: 28; font.weight: Font.Bold }
                    Rectangle { Layout.fillWidth: true; height: 1; color: root.border }
                    Text { text: "Exportar"; color: root.ink; font.pixelSize: 14; font.weight: Font.DemiBold }
                    PrimaryButton { text: "Generar PDF"; iconKind: "export"; Layout.fillWidth: true; onClicked: studio.exportPdf() }
                    PrimaryButton { text: "Exportar imágenes"; iconKind: "image"; outlined: true; Layout.fillWidth: true; onClicked: studio.exportImages() }
                    Item { Layout.fillHeight: true }
                    Text { text: "Los textos fijos se mantienen iguales. Solo los campos variables cambian entre copias."; color: root.muted; font.pixelSize: 11; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                }
            }
        }
    }

    // Toast
    Rectangle {
        id: toastBox
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 22
        width: Math.min(560, toastText.implicitWidth + 36)
        height: 44
        radius: 12
        color: "#182033ee"
        opacity: 0
        z: 5000
        Text { id: toastText; anchors.centerIn: parent; color: "white"; font.pixelSize: 12 }
        Behavior on opacity { NumberAnimation { duration: 160 } }
        Timer { id: toastTimer; interval: 2800; onTriggered: toastBox.opacity = 0 }
    }

    Connections {
        target: studio
        function onToast(message) {
            toastText.text = message
            toastBox.opacity = 1
            toastTimer.restart()
        }
    }
}
