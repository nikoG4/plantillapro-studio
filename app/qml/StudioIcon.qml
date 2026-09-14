import QtQuick

Canvas {
    id: root
    property string kind: "circle"
    property color stroke: "#172033"
    property real lineWidth: 1.8
    implicitWidth: 22
    implicitHeight: 22

    onKindChanged: requestPaint()
    onStrokeChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        var p = getContext("2d")
        p.reset()
        p.strokeStyle = stroke
        p.fillStyle = stroke
        p.lineWidth = lineWidth
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
        } else if (kind === "plus") {
            line(.5,.22,.5,.78); line(.22,.5,.78,.5)
        } else if (kind === "trash") {
            line(.28,.3,.72,.3); line(.37,.22,.63,.22); rect(.34,.35,.32,.45,.04)
        } else if (kind === "layers") {
            p.beginPath(); p.moveTo(w*.18,h*.37); p.lineTo(w*.5,h*.2); p.lineTo(w*.82,h*.37); p.lineTo(w*.5,h*.54); p.closePath(); p.stroke();
            p.beginPath(); p.moveTo(w*.18,h*.52); p.lineTo(w*.5,h*.69); p.lineTo(w*.82,h*.52); p.stroke();
            p.beginPath(); p.moveTo(w*.18,h*.67); p.lineTo(w*.5,h*.84); p.lineTo(w*.82,h*.67); p.stroke()
        } else if (kind === "settings") {
            p.beginPath(); p.arc(w*.5,h*.5,w*.14,0,Math.PI*2); p.stroke();
            for (var i=0;i<8;i++){ var a=i*Math.PI/4; line(.5+.25*Math.cos(a),.5+.25*Math.sin(a),.5+.34*Math.cos(a),.5+.34*Math.sin(a)) }
        } else {
            p.beginPath(); p.arc(w*.5,h*.5,w*.28,0,Math.PI*2); p.stroke()
        }
    }
}
