import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: root
    width: 1520
    height: 940
    minimumWidth: 1180
    minimumHeight: 720
    visible: true
    title: "PlantillaPro Studio"
    color: "#f6f7fb"

    readonly property color ink: "#111827"
    readonly property color muted: "#64748b"
    readonly property color border: "#e5e7eb"
    readonly property color primary: "#4f46e5"
    readonly property color primarySoft: "#eef2ff"
    readonly property color panel: "#ffffff"
    property string inspectorTab: "properties"

    component SoftButton: Button {
        id: c
        property bool active: false
        hoverEnabled: true
        implicitHeight: 38
        leftPadding: 15; rightPadding: 15
        contentItem: Text {
            text: c.text
            color: c.active ? root.primary : root.ink
            font.pixelSize: 13
            font.weight: c.active ? Font.DemiBold : Font.Medium
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            radius: 11
            color: c.active ? root.primarySoft : (c.hovered ? "#f8fafc" : "transparent")
        }
    }

    component PrimaryButton: Button {
        id: c
        property string iconKind: "export"
        property bool secondary: false
        hoverEnabled: true
        implicitHeight: 44
        contentItem: RowLayout {
            anchors.centerIn: parent
            spacing: 8
            StudioIcon { kind: c.iconKind; width: 18; height: 18; stroke: c.secondary ? root.ink : "white" }
            Text { text: c.text; color: c.secondary ? root.ink : "white"; font.pixelSize: 13; font.weight: Font.DemiBold }
        }
        background: Rectangle {
            radius: 12
            color: c.secondary ? (c.hovered ? "#f8fafc" : "white") : (c.hovered ? "#4338ca" : root.primary)
            border.width: c.secondary ? 1 : 0
            border.color: root.border
        }
    }

    component FieldBox: TextField {
        id: c
        implicitHeight: 40
        color: root.ink
        font.pixelSize: 13
        leftPadding: 11; rightPadding: 11
        background: Rectangle {
            radius: 10
            color: "#f8fafc"
            border.width: 1
            border.color: c.activeFocus ? root.primary : root.border
        }
    }

    component Card: Rectangle {
        color: root.panel
        radius: 16
        border.width: 1
        border.color: root.border
    }

    header: Rectangle {
        height: 70
        color: "#ffffff"
        border.width: 1
        border.color: root.border
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 22
            anchors.rightMargin: 20
            spacing: 10
            Rectangle {
                width: 38; height: 38; radius: 12; color: root.primary
                Text { anchors.centerIn: parent; text: "P"; color: "white"; font.pixelSize: 19; font.weight: Font.Bold }
            }
            ColumnLayout {
                spacing: 0
                Text { text: "PlantillaPro Studio"; color: root.ink; font.pixelSize: 15; font.weight: Font.DemiBold }
                Text { text: studio.projectName; color: root.muted; font.pixelSize: 10 }
            }
            Item { Layout.preferredWidth: 18 }
            Rectangle {
                width: 224; height: 42; radius: 13; color: "#f1f5f9"
                RowLayout {
                    anchors.fill: parent; anchors.margins: 4; spacing: 3
                    SoftButton { text: "Diseño"; active: studio.mode === "design"; Layout.fillWidth: true; onClicked: studio.setMode("design") }
                    SoftButton { text: "Producción"; active: studio.mode === "production"; Layout.fillWidth: true; onClicked: studio.setMode("production") }
                }
            }
            Item { Layout.fillWidth: true }
            ModernIconButton { iconKind: "new"; tip: "Nuevo A4"; onClicked: studio.newA4() }
            ModernIconButton { iconKind: "open"; tip: "Abrir proyecto"; onClicked: studio.openProject() }
            ModernIconButton { iconKind: "save"; tip: "Guardar proyecto"; onClicked: studio.saveProject() }
            Rectangle { width: 1; height: 28; color: root.border }
            ModernIconButton { iconKind: "export"; tip: "Ir a Producción"; accent: true; onClicked: studio.setMode("production") }
        }
    }

    StackLayout {
        anchors.fill: parent
        currentIndex: studio.mode === "welcome" ? 0 : (studio.mode === "design" ? 1 : 2)

        Item {
            Rectangle { anchors.fill: parent; color: "#f6f7fb" }
            ColumnLayout {
                anchors.centerIn: parent
                width: Math.min(parent.width - 90, 980)
                spacing: 24
                Text { Layout.alignment: Qt.AlignHCenter; text: "Empieza tu diseño"; color: root.ink; font.pixelSize: 36; font.weight: Font.Bold }
                Text { Layout.alignment: Qt.AlignHCenter; text: "Elige una base. Puedes cambiar tamaño, fondo y contenido después."; color: root.muted; font.pixelSize: 14 }
                RowLayout {
                    Layout.fillWidth: true; spacing: 16
                    Repeater {
                        model: [
                            {title:"Lienzo A4", sub:"2480 × 3508 px · 300 DPI", kind:"new", action:"a4"},
                            {title:"Desde imagen", sub:"Usa una imagen como base", kind:"image", action:"image"},
                            {title:"Abrir proyecto", sub:"Continúa un archivo existente", kind:"open", action:"open"}
                        ]
                        delegate: Rectangle {
                            required property var modelData
                            Layout.fillWidth: true; Layout.preferredHeight: 188
                            radius: 18; color: hover.containsMouse ? "#ffffff" : "#fbfcff"
                            border.width: 1; border.color: hover.containsMouse ? "#c7d2fe" : root.border
                            Behavior on color { ColorAnimation { duration: 120 } }
                            MouseArea {
                                id: hover; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    if (modelData.action === "a4") studio.newA4()
                                    else if (modelData.action === "open") studio.openProject()
                                    else { studio.newA4(); studio.loadBackground() }
                                }
                            }
                            Column {
                                anchors.centerIn: parent; spacing: 12
                                Rectangle { width: 58; height: 58; radius: 18; color: root.primarySoft; anchors.horizontalCenter: parent.horizontalCenter
                                    StudioIcon { anchors.centerIn: parent; kind: modelData.kind; width: 27; height: 27; stroke: root.primary }
                                }
                                Text { text: modelData.title; color: root.ink; font.pixelSize: 17; font.weight: Font.DemiBold; anchors.horizontalCenter: parent.horizontalCenter }
                                Text { text: modelData.sub; color: root.muted; font.pixelSize: 11; anchors.horizontalCenter: parent.horizontalCenter }
                            }
                        }
                    }
                }
                Text { text: "Tamaños rápidos"; color: root.ink; font.pixelSize: 13; font.weight: Font.DemiBold }
                RowLayout {
                    Layout.fillWidth: true; spacing: 9
                    Repeater {
                        model: [{n:"A4",w:2480,h:3508},{n:"A5",w:1748,h:2480},{n:"Tarjeta",w:1050,h:600},{n:"Post",w:1080,h:1080},{n:"Ticket",w:1200,h:600}]
                        delegate: Button {
                            required property var modelData
                            text: modelData.n; Layout.fillWidth: true; implicitHeight: 48
                            onClicked: studio.newDocument(modelData.w, modelData.h, "#ffffff", false)
                            contentItem: Text { text: parent.text; color: root.ink; font.pixelSize: 12; font.weight: Font.Medium; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                            background: Rectangle { radius: 12; color: parent.hovered ? root.primarySoft : "white"; border.width: 1; border.color: root.border }
                        }
                    }
                }
            }
        }

        RowLayout {
            spacing: 0
            Rectangle {
                Layout.preferredWidth: 82; Layout.fillHeight: true; color: "#ffffff"
                border.width: 1; border.color: root.border
                ColumnLayout {
                    anchors.fill: parent; anchors.topMargin: 14; anchors.bottomMargin: 14; spacing: 9
                    ModernIconButton { Layout.alignment: Qt.AlignHCenter; iconKind: "text"; tip: "Texto fijo"; onClicked: studio.addStaticText() }
                    ModernIconButton { Layout.alignment: Qt.AlignHCenter; iconKind: "variable"; tip: "Campo variable"; onClicked: studio.addVariableText() }
                    ModernIconButton { Layout.alignment: Qt.AlignHCenter; iconKind: "image"; tip: "Imagen"; onClicked: studio.addImage() }
                    ModernIconButton { Layout.alignment: Qt.AlignHCenter; iconKind: "shape"; tip: "Rectángulo"; onClicked: studio.addRectangle() }
                    Item { Layout.fillHeight: true }
                    ModernIconButton { Layout.alignment: Qt.AlignHCenter; iconKind: "image"; tip: "Imagen de fondo"; onClicked: studio.loadBackground() }
                }
            }

            Rectangle {
                id: workspace
                Layout.fillWidth: true; Layout.fillHeight: true; color: "#eef1f6"
                property real docScale: Math.max(0.04, Math.min((width - 150) / Math.max(1, studio.documentWidth), (height - 150) / Math.max(1, studio.documentHeight)))

                Rectangle {
                    visible: studio.selectedId !== ""
                    z: 2000; width: 232; height: 48; radius: 14
                    anchors.horizontalCenter: parent.horizontalCenter; anchors.top: parent.top; anchors.topMargin: 16
                    color: "#ffffff"; border.width: 1; border.color: root.border
                    RowLayout {
                        anchors.centerIn: parent; spacing: 3
                        ModernIconButton { iconKind:"duplicate"; tip:"Duplicar"; onClicked: studio.duplicateSelected() }
                        ModernIconButton { iconKind:"front"; tip:"Traer al frente"; onClicked: studio.bringSelectedToFront() }
                        ModernIconButton { iconKind:"back"; tip:"Enviar atrás"; onClicked: studio.sendSelectedToBack() }
                        ModernIconButton { iconKind:"lock"; tip:"Bloquear"; onClicked: studio.toggleSelectedLock() }
                        ModernIconButton { iconKind:"delete"; tip:"Eliminar"; onClicked: studio.deleteSelected() }
                    }
                }

                Rectangle {
                    id: shadow
                    width: artboard.width + 18; height: artboard.height + 18; radius: 10
                    anchors.centerIn: artboard
                    color: "#170f172a"
                }
                Item {
                    id: artboard
                    width: studio.documentWidth * workspace.docScale
                    height: studio.documentHeight * workspace.docScale
                    anchors.centerIn: parent
                    Rectangle { anchors.fill: parent; color: studio.documentTransparent ? "#ffffff" : studio.documentBackground; border.width: 1; border.color: "#d7dce5" }
                    Image { anchors.fill: parent; source: studio.backgroundSource; visible: source.toString().length > 0; fillMode: Image.Stretch; asynchronous: true }
                    Repeater {
                        model: studio.elements
                        delegate: Item {
                            id: objectItem
                            required property var modelData
                            x: modelData.x * workspace.docScale; y: modelData.y * workspace.docScale
                            width: Math.max(8, modelData.width * workspace.docScale); height: Math.max(8, modelData.height * workspace.docScale)
                            rotation: -Number(modelData.rotation || 0); opacity: Number(modelData.opacity === undefined ? 1 : modelData.opacity); z: Number(modelData.z || 0)
                            Rectangle { anchors.fill: parent; visible: modelData.kind === "shape"; color: modelData.fillColor || "#eef2ff"; border.color: modelData.strokeColor || "#c7d2fe"; border.width: Math.max(0, Number(modelData.strokeWidth || 0)*workspace.docScale); radius: modelData.shapeType === "ellipse" ? width/2 : Math.min(20, Number(modelData.cornerRadius || 0)*workspace.docScale) }
                            Image { anchors.fill: parent; visible: modelData.kind === "image"; source: modelData.source || ""; fillMode: modelData.fitMode === "contain" ? Image.PreserveAspectFit : (modelData.fitMode === "stretch" ? Image.Stretch : Image.PreserveAspectCrop); asynchronous: true }
                            Text { anchors.fill: parent; visible: modelData.kind === "text" || modelData.kind === "variable"; text: modelData.text || ""; color: modelData.color || root.ink; font.pixelSize: Math.max(7, Number(modelData.fontSize || 32)*workspace.docScale); font.bold: Boolean(modelData.bold); horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter; wrapMode: Text.WordWrap }
                            Rectangle { anchors.fill: parent; color:"transparent"; border.width: studio.selectedId === modelData.id ? 2 : 0; border.color: root.primary; radius: 4 }
                            MouseArea { anchors.fill: parent; enabled: !Boolean(modelData.locked); cursorShape: enabled ? Qt.SizeAllCursor : Qt.ArrowCursor; drag.target: objectItem; onPressed: studio.selectItem(modelData.id); onReleased: studio.moveItem(modelData.id, objectItem.x/workspace.docScale, objectItem.y/workspace.docScale) }
                            Rectangle { visible: studio.selectedId === modelData.id && !Boolean(modelData.locked); width: 12; height: 12; radius: 6; color: "white"; border.width: 2; border.color: root.primary; x: objectItem.width-width/2; y: objectItem.height-height/2; z: 100
                                MouseArea { anchors.fill: parent; cursorShape: Qt.SizeFDiagCursor; property real sw:0; property real sh:0; property real sx:0; property real sy:0; onPressed:function(m){sw=objectItem.width;sh=objectItem.height;sx=m.x;sy=m.y}; onPositionChanged:function(m){if(!pressed)return;objectItem.width=Math.max(24,sw+m.x-sx);objectItem.height=Math.max(24,sh+m.y-sy)}; onReleased: studio.resizeItem(modelData.id, objectItem.width/workspace.docScale, objectItem.height/workspace.docScale) }
                            }
                        }
                    }
                }
                Rectangle { anchors.left: parent.left; anchors.bottom: parent.bottom; anchors.margins: 14; width: 196; height: 32; radius: 10; color: "#f8ffffff"; border.width:1; border.color: root.border
                    Text { anchors.centerIn: parent; text: studio.documentWidth + " × " + studio.documentHeight + " px"; color: root.muted; font.pixelSize: 11 }
                }
            }

            Rectangle {
                Layout.preferredWidth: 360; Layout.fillHeight: true; color: "#ffffff"; border.width:1; border.color: root.border
                ColumnLayout {
                    anchors.fill: parent; spacing: 0
                    RowLayout { Layout.fillWidth: true; Layout.preferredHeight: 56; anchors.leftMargin: 8; anchors.rightMargin: 8
                        SoftButton { text:"Propiedades"; active: root.inspectorTab === "properties"; Layout.fillWidth:true; onClicked: root.inspectorTab="properties" }
                        SoftButton { text:"Capas"; active: root.inspectorTab === "layers"; Layout.fillWidth:true; onClicked: root.inspectorTab="layers" }
                    }
                    Rectangle { Layout.fillWidth:true; height:1; color:root.border }
                    StackLayout {
                        Layout.fillWidth:true; Layout.fillHeight:true; currentIndex: root.inspectorTab === "properties" ? 0 : 1
                        ScrollView {
                            clip:true
                            ColumnLayout {
                                x:16; width: Math.max(0,parent.width-32); spacing:12
                                Item { height:4 }
                                Text { text: studio.selectedId === "" ? "Lienzo" : (studio.selectedData.name || "Selección"); color:root.ink; font.pixelSize:20; font.weight:Font.Bold }
                                Text { visible: studio.selectedId === ""; text:"Ajustes del documento"; color:root.muted; font.pixelSize:11 }
                                Card {
                                    visible: studio.selectedId === ""; Layout.fillWidth:true; Layout.preferredHeight:152
                                    ColumnLayout { anchors.fill:parent; anchors.margins:14; spacing:8
                                        Text { text:"Tamaño"; color:root.muted; font.pixelSize:11 }
                                        Text { text:studio.documentWidth+" × "+studio.documentHeight+" px"; color:root.ink; font.pixelSize:13; font.weight:Font.Medium }
                                        Text { text:"Fondo"; color:root.muted; font.pixelSize:11 }
                                        FieldBox { Layout.fillWidth:true; text:studio.documentBackground; onEditingFinished: studio.setDocumentBackground(text) }
                                    }
                                }
                                Switch { visible: studio.selectedId === ""; text:"Transparente"; checked:studio.documentTransparent; onToggled:studio.setDocumentTransparent(checked) }
                                PrimaryButton { visible:studio.selectedId === ""; text:"Cambiar imagen de fondo"; iconKind:"image"; secondary:true; Layout.fillWidth:true; onClicked:studio.loadBackground() }

                                Rectangle { visible: studio.selectedId !== ""; implicitWidth: kindLabel.implicitWidth+18; implicitHeight:26; radius:8; color:root.primarySoft
                                    Text { id:kindLabel; anchors.centerIn:parent; text:studio.selectedData.kind === "variable" ? "CAMPO VARIABLE" : (studio.selectedData.kind === "text" ? "TEXTO FIJO" : (studio.selectedData.kind === "image" ? "IMAGEN" : "FORMA")); color:root.primary; font.pixelSize:10; font.weight:Font.DemiBold }
                                }
                                Text { visible:studio.selectedId !== ""; text:"Nombre"; color:root.muted; font.pixelSize:11 }
                                FieldBox { visible:studio.selectedId !== ""; Layout.fillWidth:true; text:studio.selectedData.name || ""; onEditingFinished:studio.setSelectedName(text) }
                                Text { visible:studio.selectedData.kind === "text"; text:"Contenido"; color:root.muted; font.pixelSize:11 }
                                TextArea { visible:studio.selectedData.kind === "text"; Layout.fillWidth:true; Layout.preferredHeight:84; text:studio.selectedData.template || ""; color:root.ink; font.pixelSize:13; wrapMode:TextEdit.Wrap; background:Rectangle{radius:10;color:"#f8fafc";border.width:1;border.color:root.border}; onEditingFinished:studio.setSelectedText(text) }
                                RowLayout { visible:studio.selectedData.kind === "text" || studio.selectedData.kind === "variable"; Layout.fillWidth:true; spacing:8
                                    ColumnLayout { Layout.fillWidth:true; Text{text:"Tamaño";color:root.muted;font.pixelSize:11}; SpinBox{from:6;to:500;editable:true;value:Number(studio.selectedData.fontSize||32);Layout.fillWidth:true;onValueModified:studio.setSelectedFontSize(value)} }
                                    ColumnLayout { Layout.fillWidth:true; Text{text:"Color";color:root.muted;font.pixelSize:11}; FieldBox{Layout.fillWidth:true;text:studio.selectedData.color||studio.selectedData.fillColor||"#000000";onEditingFinished:studio.setSelectedColor(text)} }
                                }
                                Text { visible:studio.selectedId !== ""; text:"Opacidad"; color:root.muted; font.pixelSize:11 }
                                Slider { visible:studio.selectedId !== ""; Layout.fillWidth:true; from:0;to:1;value:Number(studio.selectedData.opacity===undefined?1:studio.selectedData.opacity);onMoved:studio.setSelectedOpacity(value) }
                                Text { visible:studio.selectedId !== ""; text:"Rotación"; color:root.muted; font.pixelSize:11 }
                                SpinBox { visible:studio.selectedId !== ""; Layout.fillWidth:true; from:-360;to:360;editable:true;value:Math.round(Number(studio.selectedData.rotation||0));onValueModified:studio.setSelectedRotation(value) }
                                Item { height:10 }
                            }
                        }
                        ListView {
                            id:layersList; clip:true; model:studio.layers; spacing:6; leftMargin:10;rightMargin:10;topMargin:10;bottomMargin:10
                            delegate: Rectangle {
                                required property var modelData
                                width:layersList.width-20;height:54;radius:12;color:studio.selectedId===modelData.id?root.primarySoft:"white";border.width:1;border.color:studio.selectedId===modelData.id?"#c7d2fe":root.border
                                RowLayout { anchors.fill:parent;anchors.margins:10;spacing:9
                                    Rectangle{width:32;height:32;radius:9;color:"#f1f5f9";Text{anchors.centerIn:parent;text:modelData.kind==="variable"?"{}":(modelData.kind==="text"?"T":(modelData.kind==="image"?"I":"S"));color:root.ink;font.weight:Font.DemiBold}}
                                    Text{text:modelData.name;Layout.fillWidth:true;color:root.ink;font.pixelSize:12;elide:Text.ElideRight}
                                }
                                MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:studio.selectItem(modelData.id)}
                            }
                        }
                    }
                }
            }
        }

        RowLayout {
            spacing:0
            Rectangle {
                Layout.fillWidth:true;Layout.fillHeight:true;color:"#f6f7fb"
                ColumnLayout {
                    anchors.fill:parent;anchors.margins:22;spacing:14
                    Text{text:"Producción";color:root.ink;font.pixelSize:30;font.weight:Font.Bold}
                    Text{text:"Conecta cada campo variable con una lista o numeración. Después genera tus archivos.";color:root.muted;font.pixelSize:13}
                    RowLayout { Layout.fillWidth:true; spacing:10
                        Repeater { model:["1  Campos variables","2  Datos","3  Exportar"]; delegate:Rectangle{required property string modelData;Layout.fillWidth:true;height:42;radius:12;color:"white";border.width:1;border.color:root.border;Text{anchors.centerIn:parent;text:modelData;color:root.ink;font.pixelSize:12;font.weight:Font.DemiBold}} }
                    }
                    SplitView {
                        Layout.fillWidth:true;Layout.fillHeight:true;orientation:Qt.Horizontal
                        ScrollView {
                            SplitView.fillWidth:true;SplitView.minimumWidth:560;clip:true
                            ColumnLayout {
                                x:2;width:Math.max(540,parent.width-8);spacing:12
                                Repeater {
                                    model:studio.variableMappings
                                    delegate: Card {
                                        required property var modelData
                                        Layout.fillWidth:true;Layout.preferredHeight:modelData.source === "numbering" ? 250 : 164
                                        ColumnLayout { anchors.fill:parent;anchors.margins:15;spacing:8
                                            RowLayout { Layout.fillWidth:true
                                                ColumnLayout { Layout.fillWidth:true;spacing:1;Text{text:modelData.name;color:root.ink;font.pixelSize:15;font.weight:Font.DemiBold};Text{text:"Campo variable";color:root.muted;font.pixelSize:10} }
                                                ComboBox { model:["Lista / columna","Numeración automática"]; currentIndex:modelData.source === "numbering" ? 1 : 0; onActivated:studio.setVariableSource(modelData.id,index===1?"numbering":"column") }
                                            }
                                            RowLayout { visible:modelData.source !== "numbering";Layout.fillWidth:true;Text{text:"Columna";color:root.muted;font.pixelSize:11};ComboBox{Layout.fillWidth:true;model:modelData.columns;currentIndex:Math.max(0,modelData.columns.indexOf(modelData.column));onActivated:studio.setVariableColumn(modelData.id,currentText)} }
                                            GridLayout { visible:modelData.source === "numbering";columns:4;Layout.fillWidth:true;columnSpacing:8;rowSpacing:6
                                                Text{text:"Inicio";color:root.muted;font.pixelSize:10};Text{text:"Incremento";color:root.muted;font.pixelSize:10};Text{text:"Dígitos";color:root.muted;font.pixelSize:10};Text{text:"Cantidad";color:root.muted;font.pixelSize:10}
                                                FieldBox{text:String(modelData.start);Layout.fillWidth:true;onEditingFinished:studio.setNumberSetting(modelData.id,"start",text)}
                                                FieldBox{text:String(modelData.step);Layout.fillWidth:true;onEditingFinished:studio.setNumberSetting(modelData.id,"step",text)}
                                                FieldBox{text:String(modelData.digits);Layout.fillWidth:true;onEditingFinished:studio.setNumberSetting(modelData.id,"digits",text)}
                                                FieldBox{text:String(modelData.count);Layout.fillWidth:true;onEditingFinished:studio.setNumberSetting(modelData.id,"count",text)}
                                                Text{text:"Prefijo";color:root.muted;font.pixelSize:10};Text{text:"Sufijo";color:root.muted;font.pixelSize:10};Item{};Item{}
                                                FieldBox{text:modelData.prefix;Layout.fillWidth:true;onEditingFinished:studio.setNumberSetting(modelData.id,"prefix",text)}
                                                FieldBox{text:modelData.suffix;Layout.fillWidth:true;onEditingFinished:studio.setNumberSetting(modelData.id,"suffix",text)}
                                            }
                                        }
                                    }
                                }
                                Card { visible:studio.variableMappings.length===0;Layout.fillWidth:true;Layout.preferredHeight:120;Text{anchors.centerIn:parent;width:parent.width-40;horizontalAlignment:Text.AlignHCenter;wrapMode:Text.WordWrap;text:"No hay campos variables. Vuelve a Diseño y agrega uno con el icono {}.";color:root.muted;font.pixelSize:13} }
                            }
                        }
                        Rectangle {
                            SplitView.preferredWidth:420;SplitView.minimumWidth:360;color:"white";radius:16;border.width:1;border.color:root.border
                            ColumnLayout { anchors.fill:parent;anchors.margins:16;spacing:12
                                Text{text:"Datos";color:root.ink;font.pixelSize:18;font.weight:Font.Bold}
                                Text{text:studio.dataRowCount+" filas cargadas";color:root.muted;font.pixelSize:11}
                                RowLayout { ModernIconButton{iconKind:"data";tip:"Importar CSV / Excel";onClicked:studio.importData()};ModernIconButton{iconKind:"plus";tip:"Agregar fila";onClicked:studio.addEmptyDataRow()};Item{Layout.fillWidth:true} }
                                ListView { Layout.fillWidth:true;Layout.fillHeight:true;clip:true;model:studio.dataPreview;spacing:5
                                    delegate:Rectangle{required property string modelData;required property int index;width:ListView.view.width;height:40;radius:9;color:"#f8fafc";RowLayout{anchors.fill:parent;anchors.leftMargin:10;anchors.rightMargin:6;Text{text:modelData;Layout.fillWidth:true;color:root.ink;font.pixelSize:11;elide:Text.ElideRight};ModernIconButton{iconKind:"trash";tip:"Eliminar fila";implicitWidth:30;implicitHeight:30;onClicked:studio.deleteDataRow(index)}}}
                                }
                                Rectangle{Layout.fillWidth:true;height:1;color:root.border}
                                Text{text:"Resumen";color:root.ink;font.pixelSize:15;font.weight:Font.DemiBold}
                                Text{text:studio.productionSummary;color:root.muted;font.pixelSize:11;wrapMode:Text.WordWrap;Layout.fillWidth:true}
                                PrimaryButton{text:"Generar PDF";iconKind:"export";Layout.fillWidth:true;onClicked:studio.exportPdf()}
                                PrimaryButton{text:"Exportar imágenes";iconKind:"image";secondary:true;Layout.fillWidth:true;onClicked:studio.exportImages()}
                            }
                        }
                    }
                }
            }
        }
    }

    Connections {
        target: studio
        function onToast(message) { toastText.text = message; toastBox.visible = true; toastTimer.restart() }
    }
    Rectangle {
        id:toastBox;visible:false;z:9999;width:Math.min(420,toastText.implicitWidth+40);height:46;radius:13;color:"#111827";anchors.horizontalCenter:parent.horizontalCenter;anchors.bottom:parent.bottom;anchors.bottomMargin:24
        Text{id:toastText;anchors.centerIn:parent;color:"white";font.pixelSize:12}
    }
    Timer{id:toastTimer;interval:2600;onTriggered:toastBox.visible=false}
}
