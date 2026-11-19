"""Arma las hojas Campo, Cuaderno y Sala de la planilla Gestión apícola.
Genera el pedido en JSON; se envía al código de la planilla con curl."""
import json, os, sys

def V(h): return f"«Visitas|{h}»"
def T(h): return f"«Tambores|{h}»"
def P(h): return f"«Precios|{h}»"

VERDE, VERDE_S = "#3f6b1f", "#e3ecd8"
MIEL, MIEL_S = "#9a6500", "#f7ebcd"
GRIS, LINEA = "#5d6654", "#cfd5c4"
AMAR, ROJO_S, ROJO = "#fff1c2", "#f8dedb", "#b3261e"
FUENTE = "Roboto"

C, F, CR = V("Colmenar"), V("Fecha"), V("Creado")
N = 60  # filas para colmenares

def ult(col, cond):
    """Valor de la última visita del colmenar x que cumple cond."""
    return f'IFERROR(INDEX(SORT(FILTER({{{col},{F},{CR}}},{C}=x,{cond}),2,FALSE,3,FALSE),1,1),"")'

def por_colmenar(expr):
    return f'=MAP($A$9:$A${8+N},LAMBDA(x,IF(x="","",{expr})))'

BAJAS = ["Bajas: muertas", "Bajas: zanganeras", "Bajas: huérfanas", "Bajas: loque", "Bajas: cría yesificada", "Bajas: otra causa"]
ALZ_M, ALZ_S = V("Alzas melarias: 1/2"), V("Alzas melarias: alzas")
INI = "$B$2"

def titulo(a1, texto, color, tam=22):
    return {"a1": a1, "v": texto, "negrita": True, "tam": tam, "colorTexto": color}

def kpis(fila, items, color_s):
    """items: [(etiqueta, formula, formato)] en columnas A, B, C..."""
    cel = []
    for i, (et, fo, fmt) in enumerate(items):
        L = chr(65 + i)
        cel.append({"a1": f"{L}{fila}", "v": et, "tam": 9, "colorTexto": GRIS, "fondo": color_s, "ajustar": True, "valinear": "bottom"})
        cel.append({"a1": f"{L}{fila+1}", "v": fo, "tam": 16, "negrita": True, "fondo": color_s, "formato": fmt, "alinear": "left"})
    return cel

def encab(a1, nombres, fondo, color):
    return {"en": a1.split(":")[0], "a1": a1, "v": [nombres], "negrita": True, "fondo": fondo, "colorTexto": color, "ajustar": True, "valinear": "middle",
            "borde": {"abajo": True, "color": color, "estilo": "SOLID_MEDIUM"}}

# ---------------- CAMPO ----------------
campo_cols = [
    ("Colmenar", None, 190, "@"),
    ("Colmenas", f'IFERROR(LET(r,SORT(FILTER({{{V("Colmenas")},{F},{CR}}},{C}=x,{V("Colmenas")}>0),2,FALSE,3,FALSE),lf,INDEX(r,1,2),lc,INDEX(r,1,3),INDEX(r,1,1)+IFERROR(SUM(FILTER({V("Traslado: colmenas")},{V("Traslado: destino")}=x,({F}>lf)+(({F}=lf)*({CR}>lc)))),0)),0)', 80, "0"),
    ("Última visita", f"MAXIFS({F},{C},x)", 90, "dd/mm/yy"),
    ("Días sin ir", f"TODAY()-MAXIFS({F},{C},x)", 70, "0"),
    ("Alzas puestas", ult(ALZ_S, f"((LEN({ALZ_S})+LEN({ALZ_M}))>0)*({F}>={INI})"), 70, "0"),
    ("½ alzas puestas", ult(ALZ_M, f"((LEN({ALZ_S})+LEN({ALZ_M}))>0)*({F}>={INI})"), 70, "0"),
    ("Néctar", ult(V("Néctar"), f'{V("Néctar")}<>""'), 85, "@"),
    ("Polen", ult(V("Polen"), f'{V("Polen")}<>""'), 85, "@"),
    ("Última cura", f'LET(m,MAXIFS({F},{C},x,{V("Tareas")},"*Cura*"),IF(m=0,"sin registro",m))', 95, "dd/mm/yy"),
    ("Producto", ult(V("Cura: productos"), f'ISNUMBER(SEARCH("Cura",{V("Tareas")}))'), 110, "@"),
    ("Varroa %", ult(V("Varroa %"), f'{V("Varroa %")}<>""'), 65, "0.0"),
    ("Enjambres a cámara", f'SUMIFS({V("Altas: enjambres a cámara")},{C},x,{F},">="&{INI})', 80, "0"),
    ("Bajas", "+".join(f'SUMIFS({V(b)},{C},x,{F},">="&{INI})' for b in BAJAS), 60, "0"),
    ("Última observación", ult(V("Observaciones"), f'{V("Observaciones")}<>""'), 380, "@"),
]
CL = [chr(65 + i) for i in range(len(campo_cols))]
FIN = 8 + N
cel = [
    titulo("A1", "CAMPO", VERDE),
    {"a1": "B1", "v": '="Campaña "&TEXT(B2,"yy")&"-"&TEXT(EDATE(B2,12),"yy")', "tam": 12, "colorTexto": GRIS, "valinear": "bottom"},
    {"a1": "A2", "v": "Campaña desde", "colorTexto": GRIS, "tam": 9},
    {"a1": "B2", "v": "=DATE(IF(MONTH(TODAY())>=5,YEAR(TODAY()),YEAR(TODAY())-1),5,1)", "formato": "dd/mm/yyyy", "tam": 9, "colorTexto": GRIS, "alinear": "left"},
]
suma6 = "+".join(f'SUMIFS({V(b)},{F},">="&{INI})' for b in BAJAS)
cel += kpis(4, [
    ("Colmenas hoy", f"=SUM(B9:B{FIN})", "0"),
    ("Colmenares", f'=COUNTIF(A9:A{FIN},"?*")', "0"),
    ("Enjambres a cámara", f'=SUMIFS({V("Altas: enjambres a cámara")},{F},">="&{INI})', "0"),
    ("Bajas", "=" + suma6, "0"),
    ("Núcleos armados", f'=SUMIFS({V("Multiplicación: núcleos")},{F},">="&{INI})', "0"),
    ("Colmenas trasladadas", f'=SUMIFS({V("Traslado: colmenas")},{F},">="&{INI})', "0"),
    ("Alzas puestas", f"=SUM(E9:E{FIN})", "0"),
    ("½ alzas puestas", f"=SUM(F9:F{FIN})", "0"),
    ("Jarabe (L)", f'=SUMIFS({V("Jarabe (L)")},{F},">="&{INI})', "#,##0"),
    ("Torta (kg)", f'=SUMIFS({V("Torta (kg)")},{F},">="&{INI})', "#,##0"),
    ("Curas", f'=COUNTIFS({V("Tareas")},"*Cura*",{F},">="&{INI})', "0"),
], VERDE_S)
cel.append(titulo("A7", "ESTADO DE CADA COLMENAR", VERDE, 12))
cel.append(encab(f"A8:{CL[-1]}8", [c[0] for c in campo_cols], VERDE_S, VERDE))
cel.append({"a1": "A9", "v": f'=LET(c,{C},f,{F},u,UNIQUE(FILTER(c,c<>"",NOT(REGEXMATCH(LOWER(c),"^galp")),f>=$B$2)),SORT(u,MAP(u,LAMBDA(x,MAXIFS(f,c,x))),FALSE))', "negrita": True})
for i, (nom, expr, ancho, fmt) in enumerate(campo_cols):
    if expr:
        cel.append({"a1": f"{CL[i]}9", "v": por_colmenar(expr)})
    cel.append({"a1": f"{CL[i]}9:{CL[i]}{FIN}", "formato": fmt, "valinear": "top"})
cel.append({"a1": f"N9:N{FIN}", "ajustar": True})
cel.append({"a1": f"B9:M{FIN}", "alinear": "center"})
cel.append({"a1": f"A9:{CL[-1]}{FIN}", "borde": {"medio": True, "abajo": True, "color": "#e3e7dc"}})

campo = {
    "hoja": "Campo", "limpiar": True, "posicion": 1, "color": VERDE, "sinCuadricula": True, "fuente": FUENTE,
    "filas": FIN + 5, "columnas": len(campo_cols),
    "anchos": {CL[i]: c[2] for i, c in enumerate(campo_cols)},
    "altos": {"1": 36, "4": 30, "5": 32, "8": 40},
    "celdas": cel, "congelarFilas": 8, "congelarColumnas": 1,
    "condicionales": [
        {"a1": f"D9:D{FIN}", "formula": '=AND($A9<>"",$D9>=10)', "fondo": ROJO_S, "colorTexto": ROJO},
        {"a1": f"D9:D{FIN}", "formula": '=AND($A9<>"",$D9>=4)', "fondo": AMAR},
        {"a1": f"K9:K{FIN}", "formula": '=AND(ISNUMBER($K9),$K9>=3)', "fondo": ROJO_S, "colorTexto": ROJO, "negrita": True},
        {"a1": f"I9:I{FIN}", "formula": '=$I9="sin registro"', "colorTexto": "#9aa18f"},
        {"a1": f"M9:M{FIN}", "formula": '=AND(ISNUMBER($M9),$M9>0)', "colorTexto": ROJO, "negrita": True},
    ],
}

# ---------------- CUADERNO ----------------
def si(cond, txt): return f'IF({cond},{txt},"")'
partes = [
    V("Tareas"),
    si(f'{V("Altas: enjambres a cámara")}>0', f'" · +"&{V("Altas: enjambres a cámara")}&" enjambres a cámara"'),
    si(f'{V("Altas: núcleos a cámara")}>0', f'" · +"&{V("Altas: núcleos a cámara")}&" núcleos a cámara"'),
    si(f'{V("Altas: compradas")}>0', f'" · +"&{V("Altas: compradas")}&" compradas"'),
    si("(" + "+".join(V(b) for b in BAJAS) + ")>0", '" · −"&(' + "+".join(V(b) for b in BAJAS) + ')&" bajas"'),
    si(f'{V("Traslado: colmenas")}>0', f'" · "&{V("Traslado: colmenas")}&" colmenas llevadas a "&{V("Traslado: destino")}'),
    si(f'{V("Multiplicación: núcleos")}>0', f'" · "&{V("Multiplicación: núcleos")}&" núcleos armados"'),
    si(f'{V("Jarabe (L)")}>0', f'" · jarabe "&{V("Jarabe (L)")}&" L"'),
    si(f'{V("Torta (kg)")}>0', f'" · torta "&{V("Torta (kg)")}&" kg"'),
    si(f'{V("Néctar")}<>""', f'" · néctar "&LOWER({V("Néctar")})'),
    si(f'{V("Polen")}<>""', f'" · polen "&LOWER({V("Polen")})'),
    si(f'{V("Cura: productos")}<>""', f'" · cura: "&{V("Cura: productos")}'),
    si(f'{V("Varroa %")}<>""', f'" · varroa "&{V("Varroa %")}&"%"'),
    si(f'(LEN({V("Nuevo armado: nucleros")})+LEN({V("Nuevo armado: cámaras")})+LEN({V("Nuevo armado: ½ alzas")})+LEN({V("Nuevo armado: alzas")}))>0', f'" · material nuevo armado: +"&IF({V("Nuevo armado: alzas")}="",0,{V("Nuevo armado: alzas")})&" alzas, +"&IF({V("Nuevo armado: ½ alzas")}="",0,{V("Nuevo armado: ½ alzas")})&" ½, +"&IF({V("Nuevo armado: cámaras")}="",0,{V("Nuevo armado: cámaras")})&" cámaras, +"&IF({V("Nuevo armado: nucleros")}="",0,{V("Nuevo armado: nucleros")})&" nucleros"'),
    si(f'({V("Puse: alzas")}+{V("Puse: ½ alzas")})>0', f'" · puse "&IF({V("Puse: alzas")}="",0,{V("Puse: alzas")})&" alzas y "&IF({V("Puse: ½ alzas")}="",0,{V("Puse: ½ alzas")})&" ½ ("&IF({V("Puse: desde")}="apilado","del apilado","del galpón")&")"'),
    si(f'{ALZ_S}>0', f'" · "&{ALZ_S}&" alzas puestas"'),
    si(f'{ALZ_M}>0', f'" · "&{ALZ_M}&" ½ alzas puestas"'),
    si(f'({V("Cosecha: alzas")}+{V("Cosecha: 1/2 alzas")})>0', f'" · cosecha "&{V("Cosecha: alzas")}&" alzas y "&{V("Cosecha: 1/2 alzas")}&" ½"'),
]
QUE = 'REGEXREPLACE(' + "&".join(partes) + ',"^ · ","")'
cuaderno = {
    "hoja": "Cuaderno", "limpiar": True, "posicion": 2, "color": VERDE, "sinCuadricula": True, "fuente": FUENTE,
    "filas": 1000, "columnas": 5,
    "anchos": {"A": 80, "B": 180, "C": 75, "D": 360, "E": 380},
    "altos": {"1": 36},
    "celdas": [
        titulo("A1", "CUADERNO DE VISITAS", VERDE),
        {"a1": "A2", "v": "Las más nuevas arriba. Para ver un solo colmenar, usá el filtro (el ícono de la fila 3, en Colmenar).", "colorTexto": GRIS, "tam": 9},
        encab("A3:E3", ["Fecha", "Colmenar", "Colmenas", "Qué se hizo", "Observaciones"], VERDE_S, VERDE),
        {"a1": "A4", "v": f'=ARRAYFORMULA(IFERROR(CHOOSECOLS(SORT(FILTER({{{F},{C},{V("Colmenas")},{QUE},{V("Observaciones")},{CR}}},{C}<>""),1,FALSE,6,FALSE),1,2,3,4,5),""))'},
        {"a1": "A4:A1000", "formato": "dd/mm/yy", "valinear": "top"},
        {"a1": "B4:E1000", "valinear": "top"},
        {"a1": "C4:C1000", "alinear": "center"},
        {"a1": "D4:E1000", "ajustar": True},
        {"a1": "A4:E1000", "borde": {"medio": True, "abajo": True, "color": "#e3e7dc"}},
    ],
    "congelarFilas": 3, "filtro": "A3:E1000",
}

# ---------------- SALA ----------------
TA, TP, TD, TK, TT, TL = T("Campaña (año de inicio)"), T("Productor"), T("Destino / estado"), T("Neto (kg)"), T("Tipo"), T("Color")
KG = f'IF({TK}<>"",{TK},IF({TT}="Petizo",300,340))'
MM = f'IFERROR(VALUE(REGEXEXTRACT(TO_TEXT({TL}),"[0-9]+")),0)'
PROPIO = f'({TA}=$B$2)*({TP}="Propio")'
OSC, CLA = f"({MM}>50)", f"({MM}<=50)"
def sp(*f): return "=ARRAYFORMULA(SUMPRODUCT(" + "*".join(f) + "))"
PCL = f'IFERROR(INDEX(SORT(FILTER({{{P("Clara ($/kg)")},{P("Fecha")}}},{P("Comprador")}<>""),2,FALSE),1,1),0)'
POS = f'IFERROR(INDEX(SORT(FILTER({{{P("Oscura ($/kg)")},{P("Fecha")}}},{P("Comprador")}<>""),2,FALSE),1,1),0)'

sala = [
    titulo("A1", "SALA", MIEL),
    {"a1": "B1", "v": '="Campaña "&RIGHT(B2,2)&"-"&RIGHT(B2+1,2)', "tam": 12, "colorTexto": GRIS, "valinear": "bottom"},
    {"a1": "A2", "v": "Campaña (año de inicio)", "colorTexto": GRIS, "tam": 9},
    {"a1": "B2", "v": "=IF(MONTH(TODAY())>=5,YEAR(TODAY()),YEAR(TODAY())-1)", "tam": 9, "colorTexto": GRIS, "alinear": "left", "formato": "0"},
]
sala += kpis(4, [
    ("Tambores propios", f'=COUNTIFS({TA},$B$2,{TP},"Propio")', "0"),
    ("Kg de miel", sp(PROPIO, KG), "#,##0"),
    ("Sin pesar (se cuentan 340/300 kg)", f'=COUNTIFS({TA},$B$2,{TP},"Propio",{TK},"")', "0"),
    ("Kg por colmena", "=IFERROR(B5/Campo!A5,0)", "0.0"),
    ("Clara (kg)", sp(PROPIO, CLA, KG), "#,##0"),
    ("Oscura (kg)", sp(PROPIO, OSC, KG), "#,##0"),
    ("Tambores de terceros", f'=COUNTIFS({TA},$B$2,{TP},"<>Propio",{TP},"<>")', "0"),
], MIEL_S)

# Balance de miel por destino
sala.append(titulo("A7", "BALANCE DE MIEL (TAMBORES PROPIOS)", MIEL, 12))
sala.append(encab("A8:E8", ["", "Clara (kg)", "Oscura (kg)", "Total (kg)", "Valor ($)"], MIEL_S, MIEL))
dests = ["En sala", "Cargado a Villamora", "Envasado", "Canje", "Vendido", "Otro"]
filas = [["Producida", sp(PROPIO, CLA, KG), sp(PROPIO, OSC, KG), "=B9+C9", "=B9*$B$17+C9*$C$17"]]
for i, d in enumerate(dests):
    r = 10 + i
    filas.append([d, sp(PROPIO, f'({TD}="{d}")', CLA, KG), sp(PROPIO, f'({TD}="{d}")', OSC, KG), f"=B{r}+C{r}", f"=B{r}*$B$17+C{r}*$C$17"])
sala.append({"en": "A9", "v": filas})
sala += [
    {"a1": "A9:A15", "negrita": False}, {"a1": "A9:E9", "negrita": True, "borde": {"abajo": True, "color": LINEA}},
    {"a1": "B9:D15", "formato": "#,##0;-#,##0;—"}, {"a1": "E9:E15", "formato": "$ #,##0;-$ #,##0;—"},
    {"a1": "A10:A15", "colorTexto": GRIS},
    {"a1": "A17", "v": "Precio por kg (último de Villamora)", "colorTexto": GRIS, "tam": 9},
    {"a1": "B17", "v": "=" + PCL, "formato": "$ #,##0", "tam": 9, "colorTexto": GRIS},
    {"a1": "C17", "v": "=" + POS, "formato": "$ #,##0", "tam": 9, "colorTexto": GRIS},
]

# Tambores
TR = 20
sala.append(titulo(f"A{TR}", "TAMBORES DE LA CAMPAÑA", MIEL, 12))
tcols = ["N°", "Etiqueta", "Colmenar", "Lote", "Tipo", "Neto (kg)", "Color", "Productor", "Destino", "Observaciones"]
sala.append(encab(f"A{TR+1}:J{TR+1}", tcols, MIEL_S, MIEL))
sala.append({"a1": f"A{TR+2}", "v": f'=ARRAYFORMULA(IFERROR(SORT(FILTER({{{T("N° de llenado")},{T("Etiqueta")},{T("Colmenar")},{T("Lote de extracción")},{TT},IF({TK}<>"",{TK},"≈ "&IF({TT}="Petizo",300,340)),{TL},IF({TP}="Propio","Mío",{TP}),{TD},{T("Observaciones")}}},{TA}=$B$2),1,FALSE),"Todavía no hay tambores cargados en esta campaña. Se cargan en la app: Campo → Tambores."))'})
sala += [
    {"a1": f"A{TR+2}:J1000", "valinear": "top", "borde": {"medio": True, "abajo": True, "color": "#ece6d6"}},
    {"a1": f"A{TR+2}:A1000", "alinear": "center"}, {"a1": f"D{TR+2}:F1000", "alinear": "center"},
    {"a1": f"J{TR+2}:J1000", "ajustar": True},
]

# Lotes, a la derecha
LC = "L"
sala.append(titulo(f"L{TR}", "LOTES DE EXTRACCIÓN", MIEL, 12))
sala.append(encab(f"L{TR+1}:S{TR+1}", ["Lote", "Fecha", "Colmenar", "Alzas", "½ alzas", "Estimado (kg)", "Tambores", "Real (kg)"], MIEL_S, MIEL))
CS, CM, CP, LO = V("Cosecha: alzas"), V("Cosecha: 1/2 alzas"), V("Cosecha: llenado %"), V("Lote de extracción")
PP = f"IF({CP}>0,{CP},100)/100"
sala.append({"a1": f"L{TR+2}", "v": f'=ARRAYFORMULA(IFERROR(SORT(FILTER({{TO_TEXT({LO}),{F},{C},{CS},{CM},ROUND(({CS}*19+{CM}*11)*{PP})&"–"&ROUND(({CS}*25+{CM}*13)*{PP})}},{LO}<>"",{F}>=DATE($B$2,5,1),{F}<DATE($B$2+1,5,1)),2,FALSE),"Sin cosechas cargadas en esta campaña"))'})
LR = f"$L${TR+2}:$L${TR+60}"
TLO = T("Lote de extracción")
sala.append({"a1": f"R{TR+2}", "v": f'=MAP({LR},LAMBDA(l,IF(OR(l="",LEFT(l,3)="Sin"),"",IFERROR(TEXTJOIN(", ",TRUE,FILTER("N° "&{T("N° de llenado")},TO_TEXT({TLO})=l,{TA}=$B$2)),"—"))))'})
sala.append({"a1": f"S{TR+2}", "v": f'=MAP({LR},LAMBDA(l,IF(OR(l="",LEFT(l,3)="Sin"),"",ARRAYFORMULA(SUMPRODUCT((TO_TEXT({TLO})=l)*({TA}=$B$2)*{KG})))))'})
sala += [
    {"a1": f"M{TR+2}:M{TR+60}", "formato": "dd/mm/yy"}, {"a1": f"S{TR+2}:S{TR+60}", "formato": "#,##0;-#,##0;—"},
    {"a1": f"L{TR+2}:S{TR+60}", "valinear": "top", "borde": {"medio": True, "abajo": True, "color": "#ece6d6"}},
    {"a1": f"L{TR+2}:L{TR+60}", "alinear": "center"}, {"a1": f"O{TR+2}:Q{TR+60}", "alinear": "center"},
]
sala_spec = {
    "hoja": "Sala", "limpiar": True, "posicion": 3, "color": MIEL, "sinCuadricula": True, "fuente": FUENTE,
    "filas": 1000, "columnas": 19,
    "anchos": {"A": 150, "B": 95, "C": 170, "D": 80, "E": 95, "F": 85, "G": 100, "H": 90, "I": 140, "J": 220, "K": 30,
               "L": 55, "M": 75, "N": 170, "O": 60, "P": 60, "Q": 100, "R": 120, "S": 80},
    "altos": {"1": 36, "4": 30, "5": 32},
    "celdas": sala, "congelarFilas": 2,
    "condicionales": [
        {"a1": f"F{TR+2}:F1000", "formula": f'=LEFT(TO_TEXT($F{TR+2}),1)="≈"', "fondo": AMAR},
    ],
}


# ---------------- MATERIAL ----------------
AP = [V("Material: nucleros"), V("Material: cámaras"), V("Material: 1/2 alzas"), V("Material: alzas")]
INI_M = "DATE(IF(MONTH(TODAY())>=5,YEAR(TODAY()),YEAR(TODAY())-1),5,1)"
CONTADO_G = "(" + "+".join(f"LEN({a})" for a in AP) + ")>0"
CONTADO = f"({CONTADO_G})*({F}>={INI_M})"
PUESTO = f"((LEN({ALZ_S})+LEN({ALZ_M}))>0)*({F}>={INI_M})"
NO_WA = f'({V("Origen")}<>"WhatsApp")'
NM = 40; MF = 10 + NM
def gal_calc(col, nuevo, cos=None, puse=None):
    """Galpón: último conteo + material nuevo armado después + lo cosechado después en los colmenares − lo que salió del galpón después."""
    desp = f"((({F}>gf)+(({F}=gf)*({CR}>gc)))>0)"
    g = f'REGEXMATCH(LOWER({C}),"^galp")'
    f = (f'LET(gf,{ult(F, CONTADO_G)},gc,{ult(CR, CONTADO_G)},b,{ult(col, CONTADO_G)},IF(gf="","",b'
         f'+SUMPRODUCT({desp}*{g}*{nuevo})')
    if cos: f += f'+SUMPRODUCT({desp}*NOT({g})*{NO_WA}*{cos})'
    if puse: f += f'-SUMPRODUCT({desp}*({V("Puse: desde")}="galpon")*{puse})'
    return f + '))'
def gal_o_ult(col, nuevo, cos=None, puse=None):
    return f'IF(REGEXMATCH(LOWER(x),"^galp"),{gal_calc(col, nuevo, cos, puse)},{ult(col, CONTADO)})'
def por_lugar(expr): return f'=MAP($A$11:$A${MF},LAMBDA(x,IF(x="","",{expr})))'
mcols = [
    ("Lugar", None, 190, "@"),
    ("Conteo del", f'IF(REGEXMATCH(LOWER(x),"^galp"),{ult(F, CONTADO_G)},{ult(F, CONTADO)})', 85, "dd/mm/yy"),
    ("Días", f'LET(d,IF(REGEXMATCH(LOWER(x),"^galp"),{ult(F, CONTADO_G)},{ult(F, CONTADO)}),IF(d="","",TODAY()-d))', 55, "0"),
    ("Colmenas", 'IF(REGEXMATCH(LOWER(x),"^galp"),"",IFERROR(VLOOKUP(x,Campo!$A$9:$B$68,2,FALSE),""))', 75, "0"),
    ("½ alzas puestas", ult(ALZ_M, PUESTO), 75, "0"),
    ("Alzas puestas", ult(ALZ_S, PUESTO), 75, "0"),
    ("Nucleros", gal_o_ult(AP[0], V("Nuevo armado: nucleros")), 75, "0"),
    ("Cámaras", gal_o_ult(AP[1], V("Nuevo armado: cámaras")), 75, "0"),
    ("½ alzas", gal_o_ult(AP[2], V("Nuevo armado: ½ alzas"), V("Cosecha: 1/2 alzas"), V("Puse: ½ alzas")), 75, "0"),
    ("Alzas", gal_o_ult(AP[3], V("Nuevo armado: alzas"), V("Cosecha: alzas"), V("Puse: alzas")), 75, "0"),
]
ML = [chr(65 + i) for i in range(len(mcols))]
mc = [
    titulo("A1", "MATERIAL", VERDE),
    {"a1": "A2", "v": "Último conteo de cada lugar con visitas en la campaña actual. Puesto = en las colmenas. Apilado = guardado en el colmenar o en el galpón.", "colorTexto": GRIS, "tam": 9},
]
R = f"$11:$" + str(MF)
def S(L): return f"SUM({L}11:{L}{MF})"
def SG(L): return f'SUMPRODUCT(REGEXMATCH(LOWER($A$11:$A${MF}),"^galp")*IFERROR({L}11:{L}{MF}*1,0))'
tot = [
    ("Cámaras", f"={S('D')}+{S('H')}", f'="en colmenas "&TEXT({S("D")},"0")&" · apiladas "&TEXT({S("H")},"0")'),
    ("½ alzas", f"={S('E')}+{S('I')}", f'="puestas "&TEXT({S("E")},"0")&" · apiladas "&TEXT({S("I")},"0")'),
    ("Alzas", f"={S('F')}+{S('J')}", f'="puestas "&TEXT({S("F")},"0")&" · apiladas "&TEXT({S("J")},"0")'),
    ("Nucleros apilados", f"={S('G')}", '=""'),
]
for i, (et, fo, det) in enumerate(tot):
    L = chr(65 + i)
    mc += [
        {"a1": f"{L}4", "v": et, "tam": 9, "colorTexto": GRIS, "fondo": VERDE_S},
        {"a1": f"{L}5", "v": fo, "tam": 16, "negrita": True, "fondo": VERDE_S, "formato": "#,##0", "alinear": "left"},
        {"a1": f"{L}6", "v": det, "tam": 8, "colorTexto": GRIS, "fondo": VERDE_S, "ajustar": True},
    ]
mc.append({"a1": "F4", "v": "En el galpón", "tam": 9, "colorTexto": GRIS})
mc.append({"a1": "F5", "v": f'=ARRAYFORMULA(IF(COUNTIF(A11:A{MF},"galp*")=0,"Todavía sin conteo",TEXT({SG("H")},"0")&" cámaras · "&TEXT({SG("I")},"0")&" ½ alzas · "&TEXT({SG("J")},"0")&" alzas · "&TEXT({SG("G")},"0")&" nucleros"))', "tam": 11, "negrita": True})
mc.append({"a1": "F5:J5", "combinar": True})
mc.append({"a1": "F6", "v": "Se calcula solo: último conteo + material nuevo armado + alzas cosechadas − alzas que salieron del galpón.", "tam": 8, "colorTexto": GRIS})
mc.append(titulo("A8", "DÓNDE ESTÁ EL MATERIAL", VERDE, 12))
mc.append({"en": "E9", "a1": "E9:F9", "v": [["PUESTO EN COLMENAS", ""]], "tam": 8, "negrita": True, "colorTexto": GRIS, "combinar": True, "alinear": "center"})
mc.append({"en": "G9", "a1": "G9:J9", "v": [["APILADO", "", "", ""]], "tam": 8, "negrita": True, "colorTexto": GRIS, "combinar": True, "alinear": "center"})
mc.append(encab(f"A10:{ML[-1]}10", [c[0] for c in mcols], VERDE_S, VERDE))
mc.append({"a1": "A11", "v": f'=LET(c,{C},f,{F},u,UNIQUE(FILTER(c,c<>"",(f>=DATE(IF(MONTH(TODAY())>=5,YEAR(TODAY()),YEAR(TODAY())-1),5,1))+REGEXMATCH(LOWER(c),"^galp"))),g,MAP(u,LAMBDA(x,IF(REGEXMATCH(LOWER(x),"^galp"),1,0))),SORT(u,g,TRUE,u,TRUE))', "negrita": True})
for i, (nom, expr, ancho, fmt) in enumerate(mcols):
    if expr: mc.append({"a1": f"{ML[i]}11", "v": por_lugar(expr)})
    mc.append({"a1": f"{ML[i]}11:{ML[i]}{MF}", "formato": fmt})
mc += [
    {"a1": f"B11:J{MF}", "alinear": "center"},
    {"a1": f"A11:J{MF}", "borde": {"medio": True, "abajo": True, "color": "#e3e7dc"}},
    {"a1": f"G10:J{MF}", "borde": {"izq": True, "color": LINEA}},
]
cond_m = [
    {"a1": f"A11:J{MF}", "formula": '=REGEXMATCH(LOWER($A11),"^galp")', "fondo": "#f1f3ec", "negrita": True},
    {"a1": f"C11:C{MF}", "formula": '=AND(ISNUMBER($C11),$C11>=30)', "fondo": ROJO_S, "colorTexto": ROJO},
    {"a1": f"C11:C{MF}", "formula": '=AND(ISNUMBER($C11),$C11>=15)', "fondo": AMAR},
]
for L in "GHIJ":
    cond_m.append({"a1": f"{L}11:{L}{MF}", "formula": f'=AND(ISNUMBER(${L}11),${L}11>0,${L}11=MAX(${L}$11:${L}${MF}))', "fondo": "#cfe3b8", "negrita": True})
material_spec = {
    "hoja": "Material", "limpiar": True, "posicion": 3, "color": VERDE, "sinCuadricula": True, "fuente": FUENTE,
    "filas": MF + 5, "columnas": len(mcols),
    "anchos": {ML[i]: c[2] for i, c in enumerate(mcols)},
    "altos": {"1": 36, "4": 26, "5": 32, "6": 30, "10": 36},
    "celdas": mc, "congelarFilas": 10, "congelarColumnas": 1, "condicionales": cond_m,
}
sala_spec["posicion"] = 4

# ---------------- REPOSICIÓN ----------------
RI = "Campo!$B$2"
TIPO, CANT, PROV = V("Altas: compradas (tipo)"), V("Altas: compradas"), V("Altas: proveedor")
OLM = "Olmos (Savegnago)"
rc = [
    titulo("A1", "REPOSICIÓN 26-27", VERDE),
    {"a1": "A2", "v": "Cómo se rearman las colmenas en esta campaña. La tabla de compras (filas 9 a 20) la podés editar a mano; lo demás se calcula con lo que cargás en la app.", "colorTexto": GRIS, "tam": 9},
]
rc += kpis(4, [
    ("Núcleos comprados (recibidos + por llegar)", '=SUMIFS(D9:D20,C9:C20,"Núcleos",E9:E20,"Recibido")+SUMIFS(D9:D20,C9:C20,"Núcleos",E9:E20,"Por llegar")', "#,##0"),
    ("Recibidos (cargados en la app)", f'=SUMIFS({CANT},{TIPO},"nucleos",{F},">="&{RI})', "#,##0"),
    ("Por llegar", '=SUMIFS(D9:D20,E9:E20,"Por llegar")', "#,##0"),
    ("A confirmar", '=SUMIFS(D9:D20,E9:E20,"A confirmar")', "#,##0"),
    ("Enjambres a cámara", f'=SUMIFS({V("Altas: enjambres a cámara")},{F},">="&{RI})', "#,##0"),
    ("Colmenas hoy", "=Campo!A5", "#,##0"),
], VERDE_S)
rc.append(titulo("A7", "COMPRAS", VERDE, 12))
rc.append(encab("A8:F8", ["Fecha", "Proveedor", "Tipo", "Cantidad", "Estado", "Nota"], VERDE_S, VERDE))
rc += [
    {"a1": "A9:A20", "formato": "dd/mm/yy"}, {"a1": "D9:D20", "formato": "#,##0", "alinear": "center"},
    {"a1": "C9:C20", "lista": ["Núcleos", "Colmenas"]}, {"a1": "E9:E20", "lista": ["Recibido", "Por llegar", "A confirmar", "Cancelado"]},
    {"a1": "A9:F20", "borde": {"medio": True, "abajo": True, "color": "#e3e7dc"}, "valinear": "top"},
    {"a1": "F9:F20", "ajustar": True},
]
rc.append(titulo("A23", "DE DÓNDE SALEN LAS COLMENAS DE LA CAMPAÑA", VERDE, 12))
orig = [
    ["Núcleos comprados (recibidos)", f'=SUMIFS({CANT},{TIPO},"nucleos",{F},">="&{RI})'],
    ["Colmenas compradas", f'=SUMIFS({CANT},{TIPO},"colmenas",{F},">="&{RI})'],
    ["Compradas sin tipo", f'=SUMIFS({CANT},{TIPO},"",{F},">="&{RI})'],
    ["Enjambres pasados a cámara", f'=SUMIFS({V("Altas: enjambres a cámara")},{F},">="&{RI})'],
    ["Núcleos propios pasados a cámara", f'=SUMIFS({V("Altas: núcleos a cámara")},{F},">="&{RI})'],
    ["Bajas", "=-Campo!D5"],
    ["Total", "=SUM(B24:B29)"],
    ["Colmenas hoy (hoja Campo)", "=Campo!A5"],
]
rc.append({"en": "A24", "v": orig})
rc += [
    {"a1": "B24:B31", "formato": "#,##0;-#,##0;—", "alinear": "center"},
    {"a1": "A30:B30", "negrita": True, "borde": {"arriba": True, "color": VERDE}},
    {"a1": "A31:B31", "colorTexto": GRIS},
    {"a1": "A32", "v": "Si Total y Colmenas hoy no coinciden, falta cargar alguna alta, baja o compra (o hay colmenas de antes de la campaña).", "tam": 8, "colorTexto": GRIS},
]
rc.append(titulo("D23", "DESDE OLMOS (BASE)", VERDE, 12))
rc.append(encab("D24:E24", ["Llevadas a", "Colmenas"], VERDE_S, VERDE))
TD_, TC_ = V("Traslado: destino"), V("Traslado: colmenas")
rc.append({"a1": "D25", "v": f'=IFERROR(LET(d,FILTER({TD_},{C}="{OLM}",{TC_}>0,{F}>={RI}),u,UNIQUE(d),HSTACK(u,MAP(u,LAMBDA(x,SUMIFS({TC_},{C},"{OLM}",{TD_},x,{F},">="&{RI}))))),"Todavía no hay traslados desde Olmos")'})
rc += [
    {"a1": "E25:E40", "formato": "#,##0", "alinear": "center"},
    {"a1": "D25:E40", "borde": {"medio": True, "abajo": True, "color": "#e3e7dc"}},
    {"a1": "D42", "v": "Total llevadas", "negrita": True}, {"a1": "E42", "v": "=SUM(E25:E40)", "negrita": True, "formato": "#,##0", "alinear": "center"},
    {"a1": "D43", "v": "Quedan en Olmos", "colorTexto": GRIS}, {"a1": "E43", "v": f'=IFERROR(VLOOKUP("{OLM}",Campo!$A$9:$B$68,2,FALSE),0)', "formato": "#,##0", "alinear": "center", "colorTexto": GRIS},
]
reposicion_spec = {
    "hoja": "Reposición 26-27", "limpiar": False, "posicion": 2, "color": VERDE, "sinCuadricula": True, "fuente": FUENTE,
    "filas": 60, "columnas": 6,
    "anchos": {"A": 230, "B": 230, "C": 90, "D": 190, "E": 100, "F": 260},
    "altos": {"1": 36, "4": 30, "5": 32, "8": 30},
    "celdas": rc, "congelarFilas": 2,
}
for _k in ("cuaderno", "material_spec", "sala_spec"):
    pass
cuaderno["posicion"] = 3; material_spec["posicion"] = 4; sala_spec["posicion"] = 5

def local(f):
    """Pasa una fórmula escrita con comas al formato de la planilla (Argentina): ; entre argumentos y \\ entre columnas de {}."""
    if not isinstance(f, str) or not f.startswith("="):
        return f
    out, pila, en_txt, en_ph = [], [], False, False
    for ch in f:
        if en_txt:
            out.append(ch); en_txt = ch != '"'; continue
        if en_ph:
            out.append(ch); en_ph = ch != "»"; continue
        if ch == '"': en_txt = True
        elif ch == "«": en_ph = True
        elif ch in "({": pila.append(ch)
        elif ch in ")}": pila and pila.pop()
        elif ch == ",":
            ch = "\\" if pila and pila[-1] == "{" else ";"
        out.append(ch)
    return "".join(out)

def localizar(spec):
    for c in spec.get("celdas", []):
        if "v" in c:
            if isinstance(c["v"], list): c["v"] = [[local(x) for x in fila] for fila in c["v"]]
            else: c["v"] = local(c["v"])
    for k in spec.get("condicionales", []): k["formula"] = local(k["formula"])
    return spec

for _s in (campo, reposicion_spec, cuaderno, material_spec, sala_spec): localizar(_s)
pedido = {"clave": os.environ["CLAVE"], "armar": [campo, reposicion_spec, cuaderno, material_spec, sala_spec],
          "mirar": [{"hoja": "Campo", "a1": "A4:N18"}, {"hoja": "Material", "a1": "A1:J22"}]}
json.dump(pedido, open(sys.argv[1], "w"), ensure_ascii=False)
print("ok", len(json.dumps(pedido)))
