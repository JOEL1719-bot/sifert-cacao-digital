"""SIFERT CACAO DIGITAL V11.5 — interfaz única para agricultor y técnico.
No emite prescripciones de fertilización sin calibración agronómica local.
"""
import streamlit as st
import pandas as pd
import math

def crear_ficha_pdf(productor, fecha_analisis, area_ha, plantas, balance, compra, gramos, ficha=None):
    """Genera la ficha final de fertilización en PDF, sin alterar los cálculos."""
    from io import BytesIO
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.units import mm
    from xml.sax.saxutils import escape

    ficha = ficha or {}
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=15*mm,
                            rightMargin=15*mm, topMargin=14*mm, bottomMargin=14*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CeldaSifert', parent=styles['Normal'], fontSize=7.4, leading=9.5))
    styles.add(ParagraphStyle(name='CabSifert', parent=styles['CeldaSifert'], textColor=colors.white))
    styles.add(ParagraphStyle(name='TitSifert', parent=styles['Heading1'], fontSize=16, leading=19, spaceAfter=10))
    from reportlab.platypus import PageBreak
    from reportlab.lib.enums import TA_LEFT
    styles.add(ParagraphStyle(name='EjecutivoTitulo', parent=styles['Heading1'], fontSize=20, leading=25,
                              textColor=colors.HexColor('#14543B'), spaceAfter=12))
    styles.add(ParagraphStyle(name='EjecutivoSub', parent=styles['Heading2'], fontSize=12, leading=15,
                              textColor=colors.HexColor('#14543B'), spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name='EjecutivoNota', parent=styles['Normal'], fontSize=9, leading=13))
    contenido = [Paragraph('PLAN DE FERTILIZACIÓN DEL CACAO', styles['EjecutivoTitulo']),
                 Paragraph('GUÍA PRÁCTICA PARA EL PRODUCTOR | SIFERT CACAO DIGITAL', styles['Normal']),
                 Spacer(1, 5*mm),
                 Paragraph('<b>Productor:</b> '+escape(str(productor))+'  |  <b>Área:</b> '+f'{area_ha:,.2f}'+
                           ' ha  |  <b>Plantas en la parcela:</b> '+str(int(plantas))+'  |  <b>Fecha del análisis:</b> '+escape(str(fecha_analisis)), styles['EjecutivoNota']),
                 Spacer(1, 5*mm),
                 Paragraph('1. FERTILIZANTES QUE DEBE COMPRAR', styles['EjecutivoSub'])]
    compras_limpias = [r for r in compra if str(r.get('Fertilizante','')).upper() != 'TOTAL']
    resumen_compra = [['Fertilizante', 'Cantidad (kg)', 'Sacos a comprar']]
    for r in compras_limpias:
        resumen_compra.append([str(r.get('Fertilizante','')), str(r.get('Comprar (kg)','')),
                               str(r.get('Sacos a comprar',''))])
    total_compra = next((r for r in compra if str(r.get('Fertilizante','')).upper() == 'TOTAL'), None)
    if total_compra:
        resumen_compra.append(['TOTAL', str(total_compra.get('Comprar (kg)','')),
                               str(total_compra.get('Sacos a comprar',''))])
    def tabla_ejecutiva(filas, anchos):
        t = Table([[Paragraph(escape(str(c)), styles['CeldaSifert']) for c in fila] for fila in filas],
                  colWidths=anchos, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#D8EBDD')),
                               ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F5F9F4')]),
                               ('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#CEDCD1')),
                               ('VALIGN',(0,0),(-1,-1),'TOP'),
                               ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        return t
    ancho_util = landscape(A4)[0]-30*mm
    contenido.append(tabla_ejecutiva(resumen_compra, [ancho_util*.62, ancho_util*.19, ancho_util*.19]))
    contenido.append(Paragraph('2. CANTIDAD PARA CADA ABONAMIENTO', styles['EjecutivoSub']))
    contenido.append(Paragraph('Distribución propuesta: <b>primera aplicación 50 %</b>, '
                              '<b>segunda 32 %</b> y <b>tercera 18 %</b>. '
                              'Las fechas deben definirse según las condiciones de la parcela.', styles['EjecutivoNota']))
    filas_uso = [['Producto', '1.º (kg/parcela)', '2.º (kg/parcela)', '3.º (kg/parcela)']]
    for r in compras_limpias:
        filas_uso.append([str(r.get('Fertilizante','')), str(r.get('1.º abonamiento (kg)','')),
                         str(r.get('2.º abonamiento (kg)','')), str(r.get('3.º abonamiento (kg)',''))])
    contenido.append(Spacer(1, 3*mm))
    contenido.append(tabla_ejecutiva(filas_uso, [ancho_util*.49, ancho_util*.17, ancho_util*.17, ancho_util*.17]))
    if gramos:
        r=next((x for x in gramos if str(x.get('Fertilizante', x.get('Producto', ''))).upper() == 'TOTAL'), gramos[-1])
        contenido.append(Spacer(1, 4*mm))
        contenido.append(Paragraph('3. DOSIS TOTAL POR PLANTA', styles['EjecutivoSub']))
        contenido.append(Paragraph('<b>Sumando los fertilizantes seleccionados:</b> 1.º abonamiento: '+
                                  escape(str(r.get('1.º (g/planta)',''))) + ' g; 2.º: '+
                                  escape(str(r.get('2.º (g/planta)',''))) + ' g; 3.º: '+
                                  escape(str(r.get('3.º (g/planta)',''))) + ' g.', styles['EjecutivoNota']))
    contenido.append(Spacer(1, 5*mm))
    contenido.append(Paragraph('4. RECOMENDACIONES Y VALIDACIÓN TÉCNICA', styles['EjecutivoSub']))
    contenido.append(Paragraph('<b>IMPORTANTE:</b> Este plan es una simulación técnica. Antes de comprar o aplicar, '
                              'el responsable técnico debe validar las dosis, los productos, el análisis de suelo '
                              'y la necesidad de micronutrientes. No mezcle ni aplique productos sin asesoría.',
                              styles['EjecutivoNota']))
    contenido.append(Spacer(1, 6*mm))
    contenido.append(Paragraph('<b>Responsable técnico:</b> '+escape(str(ficha.get('ingeniero') or 'Por completar')),
                              styles['EjecutivoNota']))
    contenido.append(Spacer(1, 8*mm))
    contenido.append(Paragraph('_______________________________  Firma del responsable técnico', styles['EjecutivoNota']))
    contenido.append(PageBreak())
    contenido.append(Paragraph('ANEXO TÉCNICO | Sustento de la recomendación', styles['TitSifert']))
    contenido.append(Paragraph(f'<b>Productor:</b> {escape(str(productor))}   |   '
                               f'<b>Fecha del análisis:</b> {escape(str(fecha_analisis))}   |   '
                               f'<b>Área:</b> {area_ha:,.2f} ha   |   '
                               f'<b>Plantas:</b> {int(plantas):,}', styles['Normal']))
    contenido.append(Spacer(1, 8*mm))
    def ficha_valor(clave):
        valor = ficha.get(clave, '')
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            return 'No registrado'
        return str(valor).strip() or 'No registrado'

    def agregar_datos(titulo, campos):
        contenido.append(Paragraph(escape(titulo), styles['Heading2']))
        filas = []
        for i in range(0, len(campos), 2):
            fila = []
            for etiqueta, clave in campos[i:i+2]:
                fila.extend([Paragraph('<b>'+escape(etiqueta)+'</b>', styles['CeldaSifert']),
                             Paragraph(escape(ficha_valor(clave)), styles['CeldaSifert'])])
            while len(fila) < 4:
                fila.append('')
            filas.append(fila)
        ancho = landscape(A4)[0] - 30*mm
        tabla = Table(filas, colWidths=[ancho*.16, ancho*.34, ancho*.16, ancho*.34], hAlign='LEFT')
        tabla.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.25,colors.HexColor('#CBD5D1')),
                                   ('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(0,-1),colors.HexColor('#F0F5F3')),
                                   ('BACKGROUND',(2,0),(2,-1),colors.HexColor('#F0F5F3')),
                                   ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        contenido.append(tabla)
        contenido.append(Spacer(1, 4*mm))

    agregar_datos('1. Identificación del productor y parcela', [
        ('Código', 'codigo'), ('Caserío', 'caserio'), ('Distrito', 'distrito'),
        ('Provincia', 'provincia'), ('Edad del cacao (años)', 'edad'),
        ('Etapa del cultivo', 'etapa'), ('Plantas por hectárea', 'densidad'),
        ('Meta de producción (kg/ha/año)', 'meta'), ('Manejo de cáscaras', 'cascaras')])
    agregar_datos('2. Análisis de suelo', [('Laboratorio', 'laboratorio'), ('Fecha de muestreo/análisis', 'fecha_suelo'),
        ('pH', 'ph'), ('Materia orgánica (%)', 'mo'), ('Fósforo (P)', 'p'), ('Potasio (K₂O)', 'k2o'),
        ('Calcio intercambiable', 'ca'), ('Magnesio intercambiable', 'mg'),
        ('Saturación de aluminio (%)', 'sat_al'), ('CICe (cmol(+)/kg)', 'cice'),
        ('Arena – Ao (%)', 'arena'), ('Limo – Lo (%)', 'limo'), ('Arcilla – Arc (%)', 'arcilla')])
    agregar_datos('3. Enmienda y compost', [('Enmienda simulada', 'enmienda'),
        ('Dosis calculada (kg/ha)', 'enmienda_kg_ha'), ('Cantidad por parcela (kg)', 'enmienda_kg_parcela'),
        ('Sacos de 50 kg', 'enmienda_sacos'), ('¿Confirmó aplicación?', 'enmienda_aplicada'),
        ('Compost (kg/ha)', 'compost_kg_ha')])

    def agregar_tabla(titulo, df, anchos=None):
        contenido.append(Paragraph(escape(titulo), styles['Heading2']))
        columnas = list(df.columns)
        filas = [[Paragraph(escape(str(c)), styles['CabSifert']) for c in columnas]]
        for _, fila in df.iterrows():
            filas.append([Paragraph(escape('—' if pd.isna(v) else str(v)), styles['CeldaSifert']) for v in fila])
        ancho = landscape(A4)[0] - 30*mm
        tabla = Table(filas, colWidths=anchos or [ancho/len(columnas)]*len(columnas), repeatRows=1, hAlign='LEFT')
        tabla.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1C5646')),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F0F5F3')]),
            ('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#CBD5D1')),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ]))
        contenido.append(tabla)
        contenido.append(Spacer(1, 6*mm))

    agregar_tabla('Balance nutricional NPK', pd.DataFrame(balance))
    contenido.append(Paragraph('Cáscaras de cacao: el reciclaje potencial de NPK se informa por separado; no se descuenta como disponibilidad anual sin validación.', styles['Normal']))
    contenido.append(Spacer(1, 3*mm))
    contenido.append(Paragraph('Nota del anexo: simulación técnica preliminar. Validar los resultados del análisis, la composición '
                               'de los productos y las recomendaciones agronómicas locales antes de aplicar.',
                               styles['Normal']))
    doc.build(contenido)
    return buf.getvalue()


st.set_page_config(page_title='SIFERT CACAO DIGITAL', page_icon='🌱', layout='wide')
st.title('🌱 CÁLCULO DE ANÁLISIS DE SUELOS')
st.caption('V10.3 · Balance NPK · Ficha final de fertilización en PDF · Simulación técnica')
st.markdown('\n<style>\n/* SIFERT V8.8 · identidad visual cacao y suelo */\n:root { --sifert-green:#1b6249; --sifert-gold:#d8a43c; --sifert-ink:#203c31; }\n.stApp { background: linear-gradient(145deg,#f5f8f0 0%,#edf4e9 45%,#fff8e9 100%); }\n.block-container { padding-top:4.5rem; }\nh1 { margin-top:0.5rem !important; padding-top:0.4rem !important; line-height:1.25 !important; }\n@media(max-width:700px){.block-container{padding-top:3.5rem;}}\nh1 { color:#174e3a !important; font-weight:800 !important; letter-spacing:-.025em; }\ndiv[data-baseweb="tab-list"] { background:#e4efe5; padding:7px; border-radius:17px; gap:5px; border:1px solid #d1e2d0; }\nbutton[data-baseweb="tab"] { border-radius:11px !important; padding:11px 15px !important; font-weight:700 !important; color:#315444 !important; }\nbutton[data-baseweb="tab"][aria-selected="true"] { background:linear-gradient(120deg,#166447,#318b5c) !important; color:white !important; box-shadow:0 4px 12px #134f3929; }\ndiv[data-baseweb="tab-highlight"] { background:transparent !important; }\n/* Panel themes rely on marker elements, not positional selectors. */\ndiv[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {align-items:end; gap:1rem;}\ndiv[data-testid="stForm"] div[data-testid="stColumn"] {min-width:0;}\ndiv[data-testid="stForm"] div[data-testid="stWidgetLabel"] {min-height:1.35rem;}\ndiv[data-baseweb="tab-panel"]:has(.sifert-inicio-marker) {\n background:linear-gradient(145deg,rgba(247,255,246,.93),rgba(229,247,223,.92)),\n radial-gradient(circle at 95% 8%,#94bd72 0%,transparent 36%);\n border:1px solid #c5ddbd; border-radius:20px; padding:1.3rem 1.5rem 2rem;\n box-shadow:0 8px 28px #225b3420;\n}\ndiv[data-baseweb="tab-panel"]:has(.sifert-suelo-marker) {\n background:linear-gradient(140deg,rgba(255,252,242,.96),rgba(242,235,214,.94)),\n radial-gradient(circle at 95% 8%,#e8b96a 0%,transparent 35%);\n border:1px solid #e3d2ad; border-radius:20px; padding:1.3rem 1.5rem 2rem;\n box-shadow:0 8px 28px #7b5a2420;\n}\ndiv[data-baseweb="tab-panel"]:has(.sifert-inicio-marker) h3,\ndiv[data-baseweb="tab-panel"]:has(.sifert-suelo-marker) h3 {color:#234c36 !important; font-weight:800 !important; padding:.65rem .8rem; background:#ffffffb8; border-left:5px solid #2f8959; border-radius:8px; margin-top:1.5rem; }\ndiv[data-baseweb="tab-panel"]:has(.sifert-suelo-marker) h3 {border-left-color:#c28b37;}\ndiv[data-baseweb="tab-panel"] [data-testid="stForm"],\ndiv[data-baseweb="tab-panel"] [data-testid="stExpander"] {background:#ffffffd9; border:1px solid #d8e4d4; border-radius:14px; padding:.35rem;}\ndiv[data-baseweb="tab-panel"] [data-testid="stMetric"] {background:#fffefa; padding:.75rem; border:1px solid #e3e8da; border-radius:12px;}\ndiv[data-baseweb="tab-panel"] div[data-testid="stDataFrame"] {border-radius:12px; overflow:hidden;}\ndiv[data-baseweb="tab-panel"] label {color:#244b38 !important; font-weight:600 !important;}\ndiv[data-baseweb="tab-panel"] .stButton > button[kind="primary"],\ndiv[data-baseweb="tab-panel"] .stFormSubmitButton button {background:#23734f; color:white; border-color:#23734f; border-radius:10px; font-weight:700;}\n.sifert-hero {position:relative; overflow:hidden; display:flex; align-items:center; justify-content:space-between; gap:12px; border-radius:17px; padding:22px 25px; margin:4px 0 20px; color:white; box-shadow:0 6px 20px #0000001c;}\n.sifert-hero.inicio {background:linear-gradient(110deg,#104f37,#297f4b 64%,#6a9e46);}\n.sifert-hero.suelo {background:linear-gradient(110deg,#654221,#997038 64%,#b89452);}\n.sifert-hero h2 {font-size:clamp(1.25rem,2.2vw,1.9rem); margin:0 0 6px; font-weight:800; color:#fff !important;}\n.sifert-hero p {margin:0; font-size:.96rem; color:#f7f9e9;}\n.sifert-hero .art {font-size:clamp(2.6rem,5vw,4.7rem); line-height:1; filter:drop-shadow(0 3px 4px #0004); white-space:nowrap;}\n@media(max-width:700px){ div[data-baseweb="tab-panel"]:has(.sifert-inicio-marker),div[data-baseweb="tab-panel"]:has(.sifert-suelo-marker){padding:.65rem;} .sifert-hero{padding:15px 14px;} .sifert-hero .art{font-size:2.5rem;} }\n</style>\n', unsafe_allow_html=True)
st.info('Ingrese los resultados de su análisis de suelo y la producción de cacao seco que desea alcanzar. No necesita modificar fórmulas.')

# Parámetros de referencia internos. Son bibliográficos, NO una calibración local
# ni equivalentes a demanda total o dosis de fertilización.
EXTRACCION_GRANO_KG_T = {'N': 22.0, 'P₂O₅': 6.87, 'K₂O': 10.8,
                          'CaO': 1.3, 'MgO': 5.3}
# Umbrales provisionales del archivo original, sujetos a método de laboratorio.
UMBRALES = {'mo': (2.0, 4.0), 'n': (0.10, 0.20), 'p': (15.0, 30.0),
            'k_cmol': (0.30, 0.60), 'ca': (3.0, 6.0), 'mg': (0.50, 1.00)}
CAMPOS = [
    ('ph','pH',''), ('mo','Materia orgánica','%'), ('n','Nitrógeno total','%'),
    ('p','Fósforo disponible','ppm'), ('k2o','K₂O reportado','ppm'),
    ('k_cmol','Potasio intercambiable','cmol(+)/kg'),
    ('ca','Calcio intercambiable','cmol(+)/kg'), ('mg','Magnesio intercambiable','cmol(+)/kg'),
    ('al','Aluminio intercambiable','cmol(+)/kg'), ('h','Hidrógeno intercambiable','cmol(+)/kg'),
    ('na','Sodio intercambiable','cmol(+)/kg'), ('cice','CIC efectiva (CICe)','cmol(+)/kg'),
    ('sat_al','Saturación de aluminio','%'), ('ce','Conductividad eléctrica','dS/m'),
    ('arena','Arena – Ao','%'),
    ('limo','Limo – Lo','%'), ('arcilla','Arcilla – Arc','%')]


# Biblioteca inicial recuperada de SIFERT V6 (26 entradas) + MOLIMAX 20-20-20.
# Valores porcentuales son los almacenados en V6; comprobar etiqueta antes de prescribir.
# Ca y Mg de V6 no se convierten automáticamente a CaO/MgO.
BIBLIOTECA_V6 = [('Urea (46-0-0)', 'N', 46, 0, 0, 0, 0, 0), ('Nitrato de amonio (33-0-0)', 'N', 33, 0, 0, 0, 0, 0), ('Fosfato diamónico (18-46-0)', 'P', 18, 46, 0, 0, 0, 0), ('Fosfato monoamónico (11-52-0)', 'P', 11, 52, 0, 0, 0, 0), ('Superfosfato triple (0-46-0 + 14% Ca)', 'P', 0, 46, 0, 14, 0, 0), ('NPK soluble (20-20-20)', 'P', 20, 20, 20, 0, 0, 0), ('Cloruro de potasio (0-0-60)', 'K', 0, 0, 60, 0, 0, 0), ('Nitrato de potasio (13-0-46)', 'K', 13, 0, 46, 0, 0, 0), ('Guano de isla (10-10-2; referencial)', 'Org', 10, 10, 2, 0, 0, 0), ('Gallinaza compostada (2.5-2.5-2; referencial)', 'Org', 2.5, 2.5, 2, 0, 0, 0), ('Humus de lombriz (1.5-1-1; referencial)', 'Org', 1.5, 1, 1, 0, 0, 0), ('Roca fosfórica (0-28-0 + 30% Ca; referencial)', 'Natural', 0, 28, 0, 30, 0, 0), ('Sulfato de potasio (0-0-50 + 18% S)', 'Natural', 0, 0, 50, 0, 0, 18), ('Sulfato de magnesio (0-0-0 + 9.6% Mg + 13% S)', 'Natural', 0, 0, 0, 0, 9.6, 13), ('Kieserita (27% MgO + 22% S; referencial)', 'Natural', 0, 0, 0, 0, 27*24.305/40.304, 22), ('Sulfato de potasio y magnesio (0-0-22 + 11% Mg + 22% S)', 'Natural', 0, 0, 22, 0, 11, 22), ('Sulfato de cobre (0-0-0; CuSO4·5H2O)', 'Micro', 0, 0, 0, 0, 0, 0), ('Sulfato de zinc (0-0-0; Zn)', 'Micro', 0, 0, 0, 0, 0, 0), ('Sulfato de manganeso (0-0-0; Mn)', 'Micro', 0, 0, 0, 0, 0, 0), ('Ulexita (0-0-0; 10–13% B)', 'Micro', 0, 0, 0, 0, 0, 0)]

# Ficha comercial ODINSU: los porcentajes de CaO/MgO y carbonatos son
# declaraciones en formas químicas distintas; no sumarlos. PRNT no acreditado.
FICHAS_ENMIENDAS = {
    'Dolomita (cal agrícola local; CaO 28-32 %, MgO 20-23 %)': {
        'CaO_pct_rango': (28, 32), 'MgO_pct_rango': (20, 23),
        'CaCO3_pct_rango': (50, 56), 'MgCO3_pct_rango': (44, 48),
        'PRNT': None, 'fuente': 'Ficha comercial ODINSU identificada por el usuario',
        'observacion': 'PRNT sin verificar; no calcular dosis de encalado automáticamente.'
    }
}

def guardar_edicion_sacos(fuentes):
    """Conserva las ediciones del usuario antes de que Streamlit reconstruya la tabla."""
    cambios = st.session_state.get('tabla_sacos_v68', {}).get('edited_rows', {})
    for indice, columnas in cambios.items():
        i = int(indice)
        if 0 <= i < len(fuentes):
            producto = fuentes[i]
            if 'Presentación (kg/saco)' in columnas:
                st.session_state['presentacion_v66_'+producto] = float(columnas['Presentación (kg/saco)'])
            if 'Sacos' in columnas:
                st.session_state['cantidad_v66_'+producto] = float(columnas['Sacos'])


def clasificar_origen_producto(nombre, tipo):
    if tipo in ('Org', 'Natural', 'Micro'):
        return 'Orgánicos / minerales naturales' if tipo != 'Org' else 'Orgánico'
    return 'Químico (mineral)'


def catalogo_v6():
    return {nombre: {'tipo':tipo, 'N':n/100, 'P₂O₅':p/100, 'K₂O':k/100,
                     'Ca_reportado':ca, 'Mg_reportado':mg, 'S_reportado':azufre}
            for nombre,tipo,n,p,k,ca,mg,azufre in BIBLIOTECA_V6}

def resolver_sistema(matriz, vector):
    """Resuelve un sistema cuadrado pequeño sin dependencias adicionales."""
    n = len(vector)
    a = [list(map(float, matriz[i])) + [float(vector[i])] for i in range(n)]
    for i in range(n):
        pivot = max(range(i, n), key=lambda j: abs(a[j][i]))
        if abs(a[pivot][i]) < 1e-10:
            return None
        a[i], a[pivot] = a[pivot], a[i]
        z = a[i][i]
        a[i] = [v / z for v in a[i]]
        for j in range(n):
            if j != i:
                z = a[j][i]
                a[j] = [a[j][k] - z * a[i][k] for k in range(n + 1)]
    return [a[i][-1] for i in range(n)]


def optimizar_fuentes(productos, catalogo, objetivo):
    """Mezcla no negativa que cubre NPK, admitiendo excedentes explícitos.

    Enumeración de vértices con hasta tres productos: cobertura >= objetivo.
    Minimiza primero excedente relativo ponderado y luego masa de producto.
    No es una optimización agronómica ni de costo.
    """
    from itertools import combinations
    nutrientes = ('N', 'P₂O₅', 'K₂O')
    activos = [k for k in nutrientes if objetivo[k] > 1e-8]
    if not activos:
        return {x: 0.0 for x in productos}, None
    faltan = [k for k in activos if all(catalogo[x][k] <= 0 for x in productos)]
    if faltan:
        return {x: 0.0 for x in productos}, 'No hay fuente para: ' + ', '.join(faltan) + '. Marque un fertilizante que aporte esos nutrientes.'
    candidatos = [x for x in productos if any(catalogo[x][k] > 0 for k in activos)]
    mejor, mejor_puntaje = None, (float('inf'), float('inf'))
    # En un problema lineal con tres nutrientes basta examinar vértices de
    # hasta tres fuentes. Cada vértice fija tantas restricciones como fuentes.
    for cantidad in range(1, min(3, len(candidatos)) + 1):
        for grupo in combinations(candidatos, cantidad):
            for filas in combinations(activos, cantidad):
                matriz = [[catalogo[x][k] for x in grupo] for k in filas]
                valores = resolver_sistema(matriz, [objetivo[k] for k in filas])
                if valores is None or any(v < -1e-7 for v in valores):
                    continue
                valores = [max(0.0, v) for v in valores]
                aportes = {k:sum(valores[i]*catalogo[x][k] for i,x in enumerate(grupo)) for k in nutrientes}
                if any(aportes[k] < objetivo[k] - max(0.0001, objetivo[k]*1e-6) for k in activos):
                    continue
                excedente = sum(max(0.0, aportes[k]-objetivo[k])/max(objetivo[k], 1.0) for k in activos)
                # Penaliza excedentes, después masa; no oculta exceso.
                puntaje = (excedente, sum(valores))
                if mejor is None or puntaje < mejor_puntaje:
                    mejor_puntaje = puntaje
                    mejor = dict(zip(grupo, valores))
    if mejor is None:
        return {x: 0.0 for x in productos}, 'No se encontró una mezcla viable con las fuentes seleccionadas.'
    return {x: mejor.get(x, 0.0) for x in productos}, None


def distribuir_abonamientos(plan, catalogo, objetivo, total_plantas):
    """Distribuye P en primera etapa y fuentes restantes entre tres etapas.
    Mantiene suma exacta de productos; no promete tercios exactos de N/K.
    """
    etapas = [{x: 0.0 for x in plan} for _ in range(3)]
    for x, kg in plan.items():
        if catalogo[x]['P₂O₅'] > 0:
            etapas[0][x] = kg
        else:
            for i in range(3):
                etapas[i][x] = kg / 3
    filas=[]
    for i,detalle in enumerate(etapas):
        masa = sum(detalle.values())
        fila = {'Abonamiento': f'{i+1}.º', 'Mezcla total kg/parcela': round(masa, 2),
                'Dosis TOTAL g/planta': round(masa*1000/total_plantas, 1)}
        fila.update({x+' (kg)': round(kg, 2) for x,kg in detalle.items() if plan[x] > 1e-7})
        filas.append(fila)
    return filas, etapas


def leer_numero(texto, nombre):
    t = str(texto).strip().replace(',', '.')
    if not t:
        return None
    try:
        n = float(t)
    except ValueError:
        raise ValueError(f'{nombre}: escriba un número válido o deje vacío si no fue medido.')
    if not (0 <= n < float('inf')):
        raise ValueError(f'{nombre}: el valor debe ser no negativo y finito.')
    return n

def textura_usda(arena, limo, arcilla):
    """Triángulo textural USDA; porcentajes en masa que suman aproximadamente 100."""
    if any(x is None for x in (arena, limo, arcilla)):
        return None
    if abs(arena + limo + arcilla - 100) > 2:
        return None
    # Normalizar desviaciones pequeñas de redondeo.
    total = arena + limo + arcilla
    arena, limo, arcilla = [100 * x / total for x in (arena, limo, arcilla)]
    if limo + 1.5 * arcilla < 15: return 'Arenoso'
    if limo + 1.5 * arcilla >= 15 and limo + 2 * arcilla < 30: return 'Arenoso franco'
    if (7 <= arcilla < 20 and arena > 52 and limo + 2 * arcilla >= 30) or (arcilla < 7 and limo < 50 and arena > 43): return 'Franco arenoso'
    if 7 <= arcilla < 27 and 28 <= limo < 50 and arena <= 52: return 'Franco'
    if limo >= 50 and 12 <= arcilla < 27 or (50 <= limo < 80 and arcilla < 12): return 'Franco limoso'
    if limo >= 80 and arcilla < 12: return 'Limoso'
    if 20 <= arcilla < 35 and limo < 28 and arena > 45: return 'Franco arcillo arenoso'
    if 27 <= arcilla < 40 and arena > 20 and arena <= 45: return 'Franco arcilloso'
    if 27 <= arcilla < 40 and arena <= 20: return 'Franco arcillo limoso'
    if arcilla >= 35 and arena > 45: return 'Arcillo arenoso'
    if arcilla >= 40 and limo >= 40: return 'Arcillo limoso'
    if arcilla >= 40: return 'Arcilloso'
    return 'Franco (verificar clasificación textural)'

def clasificar(k, v, metodo_p='Bray I'):
    if v is None:
        return 'No determinado'
    if k == 'ph':
        if not 0 < v <= 14: return 'Revisar resultado'
        if v < 4.5: return 'Suelo ácido (técnicamente: extremadamente ácido)'
        if v < 5.0: return 'Muy fuertemente ácido'
        if v < 5.5: return 'Fuertemente ácido'
        if v < 6.5: return 'Moderadamente ácido'
        if v <= 7.3: return 'Cercano a neutro'
        return 'Alcalino'
    if k == 'sat_al':
        if v > 100: return 'Revisar resultado'
        return 'Adecuado para cacao (<20 %)' if v < 20 else 'Supera el límite adecuado para cacao (≥20 %)'
    if k == 'p':
        if metodo_p in ('Olsen modificado', 'Olsen'):
            # UNAS (2008): intervalos operativos continuos; >40 es extensión acordada.
            return 'Muy bajo' if v < 5 else 'Bajo' if v <= 15 else 'Normal' if v <= 30 else 'Alto' if v <= 40 else 'Muy alto'
        return 'Bajo' if v < 15 else 'Medio' if v <= 30 else 'Alto'
    if k == 'k_cmol':
        return 'Muy bajo' if v < 0.20 else 'Bajo' if v <= 0.30 else 'Medio' if v <= 0.60 else 'Alto'
    if k == 'mg':
        return 'Por debajo del rango adecuado para cacao' if v < 1.0 else 'Adecuado para cacao' if v <= 1.5 else 'Por encima del rango adecuado para cacao'
    if k == 'ca':
        return 'Por debajo del rango adecuado para cacao' if v < 4 else 'Adecuado para cacao' if v <= 5 else 'Por encima del rango adecuado para cacao'
    if k in UMBRALES:
        if v == 0: return 'Revisar: cero reportado'
        bajo, alto = UMBRALES[k]
        return 'Bajo' if v < bajo else 'Medio' if v <= alto else 'Alto'
    return 'Registrado, sin umbral validado'


# Almacenamiento compatible con la estructura de las versiones V3/V4 anteriores.
import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from io import BytesIO

try:
    DB_URL = st.secrets.get('DATABASE_URL', os.getenv('DATABASE_URL', ''))
except Exception:
    DB_URL = os.getenv('DATABASE_URL', '')
IS_POSTGRES = bool(DB_URL)
if IS_POSTGRES:
    import psycopg
else:
    st.warning('Almacenamiento local temporal (SQLite): los registros pueden perderse al reiniciar Streamlit Cloud. Configure DATABASE_URL con PostgreSQL para conservarlos. No registre datos personales reales en modo temporal.')

@contextmanager
def connect():
    conn = psycopg.connect(DB_URL) if IS_POSTGRES else sqlite3.connect('sifert_local.db')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def execute(query, params=(), fetch=False):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(query.replace('?', '%s') if IS_POSTGRES else query, params)
        if fetch:
            return pd.DataFrame(cur.fetchall(), columns=[d[0] for d in cur.description])

def init_db():
    ident = 'BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY' if IS_POSTGRES else 'INTEGER PRIMARY KEY AUTOINCREMENT'
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(f'''CREATE TABLE IF NOT EXISTS participantes (
            id {ident}, codigo TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL,
            caserio TEXT, area_ha REAL, plantas_ha INTEGER, edad_anios REAL, manejo_cascaras TEXT, retiro_pct REAL, meta_kg_ha REAL, creado TEXT, dni TEXT, distrito TEXT, provincia TEXT, parcela TEXT, etapa TEXT, ingeniero TEXT, cip TEXT)''')
        cur.execute(f'''CREATE TABLE IF NOT EXISTS analisis (
            id {ident}, participante_id INTEGER NOT NULL, fecha TEXT NOT NULL,
            ph REAL, mo REAL, n REAL, p REAL, k2o REAL, k_cmol REAL,
            ca REAL, mg REAL, al REAL, h REAL, na REAL, cice REAL,
            sat_al REAL, ce REAL, dap REAL, arena REAL, limo REAL, arcilla REAL,
            textura TEXT, observaciones TEXT, meta_produccion REAL,
            FOREIGN KEY(participante_id) REFERENCES participantes(id))''')
        cur.execute(f'''CREATE TABLE IF NOT EXISTS aplicaciones (
            id {ident}, participante_id INTEGER NOT NULL, fecha TEXT NOT NULL,
            producto TEXT NOT NULL, tipo TEXT, numero INTEGER,
            dosis_recomendada REAL, dosis_real REAL, unidad TEXT,
            area_ha REAL, observaciones TEXT,
            FOREIGN KEY(participante_id) REFERENCES participantes(id))''')
        # Migración no destructiva para participantes existentes.
        nuevas = {'manejo_cascaras':'TEXT', 'retiro_pct':'REAL', 'meta_kg_ha':'REAL', 'dni':'TEXT', 'distrito':'TEXT', 'provincia':'TEXT', 'parcela':'TEXT', 'etapa':'TEXT', 'ingeniero':'TEXT', 'cip':'TEXT'}
        if IS_POSTGRES:
            for columna, tipo in nuevas.items():
                cur.execute(f'ALTER TABLE participantes ADD COLUMN IF NOT EXISTS {columna} {tipo}')
        else:
            cur.execute('PRAGMA table_info(participantes)')
            existentes = {r[1] for r in cur.fetchall()}
            for columna, tipo in nuevas.items():
                if columna not in existentes:
                    cur.execute(f'ALTER TABLE participantes ADD COLUMN {columna} {tipo}')
        if IS_POSTGRES:
            cur.execute('ALTER TABLE analisis ADD COLUMN IF NOT EXISTS dap REAL')
        else:
            cur.execute('PRAGMA table_info(analisis)')
            if 'dap' not in {r[1] for r in cur.fetchall()}:
                cur.execute('ALTER TABLE analisis ADD COLUMN dap REAL')

# La meta de producción pertenece a cada análisis de suelo.
        if IS_POSTGRES:
            cur.execute('ALTER TABLE analisis ADD COLUMN IF NOT EXISTS meta_produccion REAL')
        else:
            cur.execute('PRAGMA table_info(analisis)')
            if 'meta_produccion' not in {r[1] for r in cur.fetchall()}:
                cur.execute('ALTER TABLE analisis ADD COLUMN meta_produccion REAL')
        # Migración compatible con Neon y SQLite: metadatos analíticos persistentes.
        for campo in ('laboratorio', 'metodo_fosforo', 'dap_origen'):
            if IS_POSTGRES:
                cur.execute(f'ALTER TABLE analisis ADD COLUMN IF NOT EXISTS {campo} TEXT')
            else:
                cur.execute('PRAGMA table_info(analisis)')
                if campo not in {r[1] for r in cur.fetchall()}:
                    cur.execute(f'ALTER TABLE analisis ADD COLUMN {campo} TEXT')

if not st.session_state.get('_esquema_db_inicializado_v111', False):
    init_db()
    st.session_state['_esquema_db_inicializado_v111'] = True
FIELD_KEYS = [c[0] for c in CAMPOS]

def participantes():
    return execute('SELECT * FROM participantes ORDER BY nombre', fetch=True)

def elegir_participante(df, key, permitir_ninguno=False):
    if df.empty:
        st.info('Registre primero un participante en la pestaña Inicio.')
        return None
    opciones = {f"{r['codigo']} · {r['nombre']}": int(r['id']) for _, r in df.iterrows()}
    if permitir_ninguno:
        opciones = {'Solo evaluar (sin guardar)': None, **opciones}
    return opciones[st.selectbox('Participante', list(opciones), key=key)]

secciones = st.tabs(['🏠 Registro y análisis', '🌱 Resultados del suelo', '💾 Análisis guardados',
                     '📈 Comparación histórica', '📥 Exportar / importar'])

with secciones[0]:
    st.markdown('<div class="sifert-inicio-marker sifert-hero inicio"><div><h2>🌿 Registro de productores de cacao</h2><p>Datos de la parcela y del responsable técnico</p></div><span class="art">🌳🍫</span></div>', unsafe_allow_html=True)
    st.subheader('1. Registrar participante y datos de la parcela')
    st.caption('Registre los datos del productor y, a continuación, complete su análisis de suelo.')
    # Al abrir la aplicación, iniciar con un formulario nuevo y sin propietario implícito.
    registros_inicio = participantes()
    if st.session_state.pop('_actualizacion_exitosa', False):
        st.session_state.pop('selector_inicio', None)
        st.session_state['_selector_inicio_objetivo'] = st.session_state.get('_productor_evaluacion_anterior')
    opciones_inicio = {'➕ Nuevo productor y nuevo análisis': None}
    opciones_inicio.update({f"{r['codigo']} · {r['nombre']}": int(r['id']) for _, r in registros_inicio.iterrows()})
    objetivo = st.session_state.pop('_selector_inicio_objetivo', None)
    if objetivo is not None:
        for etiqueta, identificador in opciones_inicio.items():
            if identificador == objetivo:
                st.session_state['selector_inicio'] = etiqueta
                break
    if st.session_state.pop('_ultimo_guardado_mensaje', None):
        st.success('Cambios guardados. Productor y laboratorio sincronizados con la base de datos.')
    seleccion_inicio = st.selectbox('Productor para registrar o consultar', list(opciones_inicio), key='selector_inicio')
    productor_existente_id = opciones_inicio[seleccion_inicio]
    # Hidratar todos los widgets desde la base de datos al cambiar la selección.
    # Se hace antes de instanciar cualquier widget y se conserva lo editado durante reruns.
    fila_productor = (registros_inicio[registros_inicio['id'] == productor_existente_id].iloc[0]
                      if productor_existente_id is not None else None)
    if st.session_state.get('_selector_inicio_previo') != productor_existente_id:
        st.session_state['_selector_inicio_previo'] = productor_existente_id
        st.session_state['_datos_productor_cargado'] = productor_existente_id
        mapeo = {'codigo':'codigo','nombre':'nombre','caserio':'caserio','area':'area_ha',
                 'plantas':'plantas_ha','edad':'edad_anios','manejo':'manejo_cascaras',
                 'distrito':'distrito','provincia':'provincia','etapa':'etapa',
                 'ingeniero':'ingeniero','retiro':'retiro_pct'}
        predeterminados = {'codigo':'','nombre':'','caserio':'','area':1.0,'plantas':1100,
                           'edad':5.0,'manejo':'Permanecen en la parcela','distrito':'',
                           'provincia':'Leoncio Prado','etapa':'No especificada',
                           'ingeniero':'','retiro':0.0}
        for widget, columna in mapeo.items():
            valor = fila_productor.get(columna) if fila_productor is not None else None
            if valor is None or pd.isna(valor):
                valor = predeterminados[widget]
            if widget == 'plantas':
                valor = int(valor)
            elif widget in ('area','edad','retiro'):
                valor = float(valor)
            else:
                valor = str(valor)
            st.session_state['registro_' + widget] = valor
        for k in FIELD_KEYS:
            st.session_state.pop('dato_' + k, None)
        st.session_state.pop('evaluacion_pendiente', None)
        st.session_state.pop('_consulta_id_cargado', None)
        st.session_state.pop('selector_analisis_inicio', None)
        st.session_state.pop('_historial_productor_previo', None)
        st.session_state.pop('_analisis_inicio_previo', None)
        # El rerun asegura que Streamlit reconstruya widgets con valores hidratados.
        st.rerun()
    # Elegir explícitamente uno de los análisis del productor.
    analisis_inicio_id = None
    if productor_existente_id is not None:
        historial_inicio = execute('SELECT * FROM analisis WHERE participante_id=? ORDER BY fecha DESC, id DESC',
                                   (productor_existente_id,), True)
        opciones_historial = {'➕ Nuevo análisis para este productor': None}
        for numero, (_, fila_h) in enumerate(historial_inicio.iterrows(), start=1):
            opciones_historial[f"{fila_h['fecha']} · Análisis {numero} (registro {int(fila_h['id'])})"] = int(fila_h['id'])
        # Al cambiar de productor, cargar inicialmente su análisis más reciente.
        if st.session_state.get('_historial_productor_previo') != productor_existente_id:
            st.session_state['_historial_productor_previo'] = productor_existente_id
            st.session_state.pop('selector_analisis_inicio', None)
        etiqueta_historial = st.selectbox('Seleccione el análisis de suelo del productor',
                                         list(opciones_historial),
                                         index=1 if len(opciones_historial) > 1 else 0,
                                         key='selector_analisis_inicio')
        analisis_inicio_id = opciones_historial[etiqueta_historial]
    if st.session_state.get('_analisis_inicio_previo') != (productor_existente_id, analisis_inicio_id):
        st.session_state['_analisis_inicio_previo'] = (productor_existente_id, analisis_inicio_id)
        for k in FIELD_KEYS:
            st.session_state.pop('dato_' + k, None)
        for k in ('fecha_evaluacion','meta_evaluacion','laboratorio_evaluacion','metodo_fosforo_evaluacion','dap_evaluacion','dap_origen_evaluacion'):
            st.session_state.pop(k, None)
        st.session_state.pop('evaluacion_pendiente', None)
        if analisis_inicio_id is not None:
            fila_h = historial_inicio[historial_inicio['id'] == analisis_inicio_id].iloc[0]
            for k in FIELD_KEYS:
                v = fila_h.get(k)
                st.session_state['dato_' + k] = '' if pd.isna(v) else str(v)
            try:
                st.session_state['fecha_evaluacion'] = date.fromisoformat(str(fila_h['fecha'])[:10])
            except (ValueError, TypeError):
                st.session_state['fecha_evaluacion'] = date.today()
            meta_h = fila_h.get('meta_produccion')
            st.session_state['meta_evaluacion'] = float(meta_h) if pd.notna(meta_h) else 1000.0
            import re
            observacion_h = str(fila_h.get('observaciones') or '')
            coincidencia_lab = re.search(r'laboratorio:\s*([^;]+)', observacion_h, flags=re.IGNORECASE)
            lab_h = fila_h.get('laboratorio')
            st.session_state['laboratorio_evaluacion'] = (str(lab_h).strip() if pd.notna(lab_h) and str(lab_h).strip() else (coincidencia_lab.group(1).strip() if coincidencia_lab else ''))
            st.session_state['dap_evaluacion'] = float(fila_h.get('dap')) if pd.notna(fila_h.get('dap')) and float(fila_h.get('dap')) > 0 else 1.33
            st.session_state['dap_origen_evaluacion'] = fila_h.get('dap_origen') if fila_h.get('dap_origen') in ('Medida en laboratorio','Estimada / referencial') else 'Estimada / referencial'
            st.session_state['metodo_fosforo_evaluacion'] = ('Olsen modificado' if fila_h.get('metodo_fosforo') == 'Olsen' else str(fila_h.get('metodo_fosforo')) if pd.notna(fila_h.get('metodo_fosforo')) and fila_h.get('metodo_fosforo') in ('Bray I','Olsen modificado') else 'Bray I')
            st.session_state['evaluacion_pendiente'] = {
                'datos': {k: (float(fila_h[k]) if pd.notna(fila_h[k]) else None) for k in FIELD_KEYS},
                'rendimiento': st.session_state['meta_evaluacion'],
                'participante_id': productor_existente_id,
                'fecha': str(fila_h['fecha'])[:10],
                'laboratorio': st.session_state['laboratorio_evaluacion'],
                'metodo_fosforo': st.session_state['metodo_fosforo_evaluacion'],
                'dap': st.session_state['dap_evaluacion'], 'dap_origen': st.session_state['dap_origen_evaluacion']}
    if analisis_inicio_id is not None:
        st.caption('Análisis recuperado. Puede consultar sus resultados en la segunda pestaña o editarlo y guardar los cambios con el botón inferior.')

    registro_actual = (registros_inicio[registros_inicio['id'] == productor_existente_id].iloc[0]
                       if productor_existente_id is not None else None)
    def campo_actual(nombre, predeterminado=''):
        if registro_actual is None:
            return predeterminado
        v = registro_actual.get(nombre)
        return predeterminado if pd.isna(v) or v is None else v
    c1,c2,c3=st.columns(3)
    codigo=c1.text_input('Código único (evite DNI)', disabled=productor_existente_id is not None, key='registro_codigo')
    nombre=c2.text_input('Nombre o identificación interna', key='registro_nombre')
    caserio=c3.text_input('Caserío', key='registro_caserio')
    area=c1.number_input('Área (ha)', min_value=0.0, key='registro_area')
    plantas=c2.number_input('Plantas por ha', min_value=1, key='registro_plantas')
    edad=c3.number_input('Edad del cacao (años)', min_value=0.0, key='registro_edad')
    st.markdown('**Datos complementarios del productor y parcela para la ficha PDF**')
    c4,c5,c6=st.columns(3)
    manejos=['Permanecen en la parcela','Se retiran completamente','Retiro parcial']
    manejo_actual=str(campo_actual('manejo_cascaras', manejos[0]))
    manejo=c4.selectbox('Manejo de cáscaras', manejos, key='registro_manejo')
    distrito=c5.text_input('Distrito', key='registro_distrito')
    provincia=c6.text_input('Provincia', key='registro_provincia')
    c7,c8=st.columns([1,2])
    etapas=['No especificada','Crecimiento','Producción']
    etapa_actual=str(campo_actual('etapa', etapas[0]))
    etapa=c7.selectbox('Etapa del cultivo', etapas, key='registro_etapa')
    ingeniero=c8.text_input('Responsable técnico', key='registro_ingeniero')
    retiro=c4.number_input('Porcentaje retirado (%)', min_value=0.0, max_value=100.0, step=5.0, key='registro_retiro') if manejo=='Retiro parcial' else (100.0 if manejo=='Se retiran completamente' else 0.0)
    st.caption('Complete los datos del productor y el análisis de suelo. Ambos se guardarán con el único botón al final del formulario.')
    st.markdown('<div class="sifert-suelo-marker sifert-hero suelo"><div><h2>🌱 Evaluación de suelo y fertilización</h2><p>Análisis químico · balance NPK · plan de abonamiento</p></div><span class="art">🪴🔬</span></div>', unsafe_allow_html=True)
    # No seleccionar automáticamente el último productor ni cargar su análisis en un formulario nuevo.
    pid_guardar = productor_existente_id
    st.session_state['_productor_evaluacion_anterior'] = pid_guardar
    st.session_state.setdefault('meta_evaluacion', 1000.0)
    for clave in FIELD_KEYS:
        st.session_state.setdefault('dato_' + clave, '')

    # Datos generales del análisis, antes de los resultados del laboratorio.
    st.markdown('### Datos generales del análisis de suelo')
    col_fecha, col_meta, col_lab = st.columns(3)
    fecha_guardar = col_fecha.date_input('Fecha del análisis', value=date.today(), key='fecha_evaluacion')
    rendimiento = col_meta.number_input('Meta de cacao seco (kg/ha/año)', min_value=0.0, max_value=10000.0, step=100.0, key='meta_evaluacion', help='En crecimiento de 0 a 2 años, este dato no interviene en la demanda vegetativa. En producción indique una meta positiva.')
    if etapa == 'Crecimiento':
        st.caption('Crecimiento: la meta de cosecha no interviene en la demanda vegetativa de los dos primeros años.')
    laboratorio_analisis = col_lab.text_input('Laboratorio del análisis de suelo', key='laboratorio_evaluacion')
    with st.form('evaluacion'):
        st.subheader('1. Copie los valores de su análisis de suelo')
        st.caption('Si el laboratorio no midió un indicador, déjelo vacío. No coloque cero para representar un dato faltante.')
        datos_texto = {}
        # El método analítico se ubica exactamente al costado del valor P.
        # Ambos widgets pertenecen al mismo formulario y se guardan conjuntamente.
        for j in range(0, len(CAMPOS), 3):
            columnas = st.columns(3)
            for columna, (clave, nombre, unidad) in zip(columnas, CAMPOS[j:j+3]):
                if clave == 'p':
                    sub_p, sub_metodo = columna.columns([1, 1.15])
                    datos_texto[clave] = sub_p.text_input('Fósforo disponible (ppm)',
                        placeholder='No medido', key='dato_p')
                    metodo_fosforo = sub_metodo.selectbox('Método de fósforo',
                        ['Bray I', 'Olsen modificado'], key='metodo_fosforo_evaluacion',
                        help='Seleccione el método reportado por el laboratorio; no se deduce del pH.')
                else:
                    datos_texto[clave] = columna.text_input(f'{nombre} ({unidad})' if unidad else nombre,
                        placeholder='No medido: dejar vacío', key='dato_'+clave)
        # La escala Olsen modificado está documentada en la tabla UNAS (2008),
        # excepto >40 ppm, ampliación operativa solicitada por el usuario.
        st.markdown('**Densidad aparente del suelo (0–20 cm)**')
        c_dap, c_origen = st.columns(2)
        dap_evaluacion = c_dap.number_input('Densidad aparente (g/cm³)', min_value=0.50, max_value=2.50, value=1.33, step=0.01, key='dap_evaluacion')
        dap_origen = c_origen.selectbox('Procedencia de densidad aparente', ['Estimada / referencial', 'Medida en laboratorio'], key='dap_origen_evaluacion')
        st.caption('1.33 g/cm³ es una referencia inicial, no una medición UNAS. La densidad aparente del compost NO es la del suelo.')
        calcular = st.form_submit_button('💾 Guardar productor y análisis de suelo', type='primary', use_container_width=True)

    if calcular:
        try:
            if not codigo.strip() or not nombre.strip():
                raise ValueError('Complete el código y el nombre del productor.')
            valores = {clave: leer_numero(datos_texto[clave], etiqueta) for clave, etiqueta, _ in CAMPOS}
            if not any(v is not None for v in valores.values()):
                raise ValueError('Ingrese al menos un resultado del laboratorio.')
            for clave in ('mo','n','sat_al','arena','limo','arcilla'):
                if valores[clave] is not None and not 0 <= valores[clave] <= 100:
                    raise ValueError(f'{clave}: porcentaje fuera de 0–100.')
            if valores['ph'] is not None and not (0 < valores['ph'] <= 14):
                raise ValueError('El pH debe estar entre 0 y 14.')
            # Guardar productor y análisis en una sola transacción: sin registros parciales.
            with connect() as conn:
                cur = conn.cursor()
                q = lambda sql: sql.replace('?', '%s') if IS_POSTGRES else sql
                cur.execute(q('SELECT id FROM participantes WHERE codigo=?'), (codigo.strip(),))
                anterior = cur.fetchone()
                if anterior:
                    pid_guardar = int(anterior[0])
                    cur.execute(q('UPDATE participantes SET nombre=?,caserio=?,area_ha=?,plantas_ha=?,edad_anios=?,manejo_cascaras=?,retiro_pct=?,meta_kg_ha=?,distrito=?,provincia=?,etapa=?,ingeniero=? WHERE id=?'),
                        (nombre.strip(),caserio.strip(),area,plantas,edad,manejo,retiro,float(rendimiento),distrito.strip(),provincia.strip(),etapa,ingeniero.strip(),pid_guardar))
                else:
                    cur.execute(q('INSERT INTO participantes(codigo,nombre,caserio,area_ha,plantas_ha,edad_anios,manejo_cascaras,retiro_pct,meta_kg_ha,creado,dni,distrito,provincia,parcela,etapa,ingeniero,cip) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'),
                        (codigo.strip(),nombre.strip(),caserio.strip(),area,plantas,edad,manejo,retiro,float(rendimiento),date.today().isoformat(),'',distrito.strip(),provincia.strip(),'',etapa,ingeniero.strip(),''))
                    cur.execute(q('SELECT id FROM participantes WHERE codigo=?'), (codigo.strip(),))
                    pid_guardar = int(cur.fetchone()[0])
                columnas = ['participante_id', 'fecha'] + FIELD_KEYS + ['dap','textura','observaciones','meta_produccion','laboratorio','metodo_fosforo','dap_origen']
                parametros = [pid_guardar, fecha_guardar.isoformat()] + [valores[k] for k in FIELD_KEYS] + [
                    float(dap_evaluacion), textura_usda(valores['arena'],valores['limo'],valores['arcilla']),
                    f'Meta de evaluación: {rendimiento:g} kg/ha/año; laboratorio: {laboratorio_analisis}', float(rendimiento), laboratorio_analisis, metodo_fosforo, dap_origen]
                if analisis_inicio_id is None:
                    cur.execute(q(f"INSERT INTO analisis({','.join(columnas)}) VALUES ({','.join('?' for _ in columnas)})"), parametros)
                else:
                    campos_update = [c for c in columnas if c != 'participante_id']
                    valores_update = [parametros[columnas.index(c)] for c in campos_update]
                    cur.execute(q(f"UPDATE analisis SET {','.join(c + '=?' for c in campos_update)} WHERE id=? AND participante_id=?"),
                                valores_update + [analisis_inicio_id, pid_guardar])
            st.session_state['_productor_evaluacion_anterior'] = pid_guardar
            st.session_state['evaluacion_pendiente'] = {
                'datos': valores.copy(), 'rendimiento': float(rendimiento),
                'participante_id': pid_guardar, 'fecha': fecha_guardar.isoformat(),
                'laboratorio': laboratorio_analisis, 'metodo_fosforo': metodo_fosforo,
                'dap': float(dap_evaluacion), 'dap_origen': dap_origen}
            # Sincronizar inmediatamente el selector tras actualizar el nombre en Neon.
            st.session_state['_selector_inicio_previo'] = pid_guardar
            st.session_state['_actualizacion_exitosa'] = True
            # Forzar reconstrucción del selector desde Neon tras confirmar COMMIT.
            # El análisis existente mantiene su ID; no se inserta un duplicado.
            st.session_state['_ultimo_guardado_mensaje'] = (
                'Productor, laboratorio y análisis actualizados en la base de datos.'
                if analisis_inicio_id is not None else 'Productor y análisis guardados en la base de datos.')
            st.rerun()
        except Exception as e:
            st.error(f'No se pudo guardar: {e}')


with secciones[1]:
    st.markdown('<div class="sifert-suelo-marker sifert-hero suelo"><div><h2>🌱 Resultados del suelo y fertilización</h2><p>Diagnóstico químico · balance NPK · plan de abonamiento</p></div><span class="art">🪴🔬</span></div>', unsafe_allow_html=True)
    # Resultados sincronizados con la selección de Registro; sin segundo selector.
    pid_guardar = st.session_state.get('_productor_evaluacion_anterior')
    if pid_guardar is None:
        st.info('Seleccione un productor y su análisis en la pestaña Registro.')
    fecha_guardar = date.fromisoformat(st.session_state['evaluacion_pendiente']['fecha']) if st.session_state.get('evaluacion_pendiente') else date.today()
    laboratorio_analisis = st.session_state.get('evaluacion_pendiente', {}).get('laboratorio', '')
    rendimiento = st.session_state.get('evaluacion_pendiente', {}).get('rendimiento', 1000.0)
    _participantes_resultados = participantes()
    _coincidencias_resultados = _participantes_resultados[_participantes_resultados['id'] == pid_guardar] if pid_guardar is not None else pd.DataFrame()
    fila_parcela = _coincidencias_resultados.iloc[0] if not _coincidencias_resultados.empty else None
    if st.session_state.get('evaluacion_pendiente') is None:
        st.info('Primero registre al productor y guarde los resultados del laboratorio en la pestaña Inicio. Aquí aparecerán los resultados calculados.')
    if st.session_state.get('evaluacion_pendiente') is not None:
        try:
            # La evaluación pendiente es una instantánea inmutable hasta guardar.
            # Los reruns de botones, pestañas y descargas no deben sobrescribirla.
            datos = st.session_state['evaluacion_pendiente']['datos'].copy()
            datos['dap'] = float(st.session_state['evaluacion_pendiente'].get('dap') or 1.33)
            st.caption(f'Densidad aparente del suelo: {datos["dap"]:.2f} g/cm³ · {st.session_state["evaluacion_pendiente"].get("dap_origen", "Estimada / referencial")}')
            for clave in ['mo','n','sat_al','arena','limo','arcilla']:
                if datos[clave] is not None and datos[clave] > 100:
                    raise ValueError(f'{clave}: el porcentaje no puede superar 100.')
            if datos['dap'] is not None and not (0 < datos['dap'] <= 2.5):
                raise ValueError('Densidad aparente: verifique que esté entre 0 y 2.5 g/cm³.')
            fracciones = [datos[k] for k in ['arena','limo','arcilla']]
            if all(v is not None for v in fracciones) and abs(sum(fracciones)-100)>2:
                st.warning('Arena + limo + arcilla no suman aproximadamente 100 %. Revise la transcripción.')
            st.divider()
            st.subheader('3. Resultado de su evaluación')
            tabla = []
            fuentes_inia = {
                'ph': 'INIA (2025), tabla 5',
                'mo': 'INIA (2025), tabla 7',
                'n': 'INIA (2025), tabla 9',
                'k_cmol': 'INIA (2025), tabla 15',
                'ca': 'INIA (2025), tabla 27 (cacao)',
                'mg': 'INIA (2025), tabla 27 (cacao)',
                'sat_al': 'INIA (2025), tabla 27 (cacao)',
            }
            metodo_p_resultado = st.session_state['evaluacion_pendiente'].get('metodo_fosforo', 'Bray I')
            fuentes_inia['p'] = ('INIA (2025), tabla 11 (Bray I)' if metodo_p_resultado == 'Bray I'
                                 else 'UNAS (2008), Olsen modificado; >40: criterio operativo')
            # Mostrar solo indicadores con interpretación agronómica orientativa.
            # Los demás resultados permanecen en datos para verificaciones internas.
            indicadores_visibles = {'ph', 'mo', 'n', 'p', 'k_cmol', 'ca', 'mg', 'sat_al'}
            for clave, nombre, unidad in CAMPOS:
                if clave not in indicadores_visibles or datos[clave] is None:
                    continue
                tabla.append({'Indicador':nombre, 'Resultado': datos[clave] if datos[clave] is not None else 'No medido',
                              'Unidad':unidad, 'Interpretación orientativa':clasificar(clave, datos[clave], metodo_p_resultado), 'Sustento técnico':fuentes_inia.get(clave, '')})
            textura = textura_usda(datos['arena'], datos['limo'], datos['arcilla'])
            if textura:
                tabla.append({'Indicador': 'Textura del suelo',
                              'Resultado': textura, 'Unidad': '',
                              'Interpretación orientativa': 'Clase textural USDA', 'Sustento técnico':'USDA (triángulo textural)'})
            if tabla:
                st.dataframe(pd.DataFrame(tabla), hide_index=True, use_container_width=True)
            else:
                st.info('Ingrese resultados de suelo para mostrar el diagnóstico.')
            if datos['al'] is not None and datos['cice'] is not None and datos['cice'] > 0:
                sat_calculada = datos['al'] / datos['cice'] * 100
                if datos['sat_al'] is not None and abs(sat_calculada - datos['sat_al']) > 0.5:
                    st.warning(f'Compruebe la saturación de aluminio: Al/CICe × 100 = {sat_calculada:.2f} %, frente al {datos["sat_al"]:.2f} % ingresado. Verifique la metodología del laboratorio.')
            st.caption('Fósforo: Bray I — INIA (2025), tabla 11; Olsen modificado — UNAS (2008), con >40 ppm como ampliación operativa. Otros indicadores: INIA (2025), tablas 5, 7, 9, 15 y 27.')
            ph, al, mg = datos['ph'], datos['sat_al'], datos['mg']
            if ph is not None and (ph < 5.5 or (al is not None and al >= 20)):
                st.warning('Suelo ácido o con señal de aluminio: conviene evaluar una corrección de acidez con asistencia técnica. No se calcula dosis de cal o dolomita sin datos adicionales.')
            elif al is not None and al >= 20:
                st.warning('Saturación de aluminio elevada: solicite evaluación técnica de acidez.')
            if mg is not None and 0 < mg < 0.5:
                st.info('Magnesio intercambiable bajo según criterio provisional. Verificar antes de seleccionar una enmienda.')
            st.subheader('4. Diagnóstico de encalado y relación Ca/Mg')
            st.caption('Secuencia: primero necesidad de neutralizar acidez y aluminio; después Ca y Mg para orientar el tipo de enmienda. No usar rangos Ca/Mg como prescripción automática.')
            ca_val, mg_val = datos.get('ca'), datos.get('mg')
            relacion = ca_val / mg_val if ca_val is not None and mg_val is not None and mg_val > 0 else None
            sat_val = datos.get('sat_al')
            ph_val = datos.get('ph')
            requiere_revision = (ph_val is not None and ph_val < 5.5) or (sat_val is not None and sat_val >= 20)
            if relacion is not None:
                st.metric('Relación Ca/Mg (cmol(+)/kg)', f'{relacion:.2f}:1')
                st.caption(f'Ca: {ca_val:g} cmol(+)/kg · Mg: {mg_val:g} cmol(+)/kg. Una relación por sí sola no determina el producto.')
            else:
                st.info('Para evaluar Ca/Mg ingrese calcio y magnesio intercambiables; Mg debe ser mayor que cero.')
            st.caption('Valores orientativos para cacao (verificar método analítico y rangos INIA 2025): pH 5.5–6.5; saturación Al < 20 %; Ca 4–5 y Mg 1.0–1.5 cmol(+)/kg. La relación Ca/Mg es complementaria.')
            if relacion is not None and requiere_revision:
                if 3 <= relacion <= 4:
                    st.info('Enmienda orientativa: cal agrícola (criterio de capacitación Ca/Mg 3–4). Confirmar necesidad y dosis de encalado.')
                elif 4 < relacion <= 7:
                    st.info('Enmienda orientativa: dolomita (criterio de capacitación Ca/Mg >4–7). Confirmar necesidad y dosis.')
                elif 7 < relacion <= 12 and ph_val is not None and 4 <= ph_val <= 5.5:
                    st.info('Enmienda orientativa: dolomita (criterio de capacitación Ca/Mg >7–12 y pH 4–5.5). Si persiste déficit de Mg, evaluar una fuente complementaria como Magnocal según su composición.')
                else:
                    st.info('La relación Ca/Mg no encaja en los rangos operativos definidos; el técnico debe evaluar la enmienda.')
            elif not requiere_revision:
                st.info('No se identifica automáticamente necesidad de encalado con los indicadores disponibles. Verificar acidez intercambiable.')
            st.caption('Selección orientativa basada en una guía de capacitación; los intervalos Ca/Mg no están atribuidos al INIA 2025. La dosis se evalúa por separado.')
            st.info('El técnico selecciona la enmienda según su evaluación de campo y la ficha técnica del producto.')
            plantas_encalado = int(fila_parcela['plantas_ha']) if fila_parcela is not None and pd.notna(fila_parcela['plantas_ha']) and fila_parcela['plantas_ha'] > 0 else 1100
            area_encalado = float(fila_parcela['area_ha']) if fila_parcela is not None and pd.notna(fila_parcela['area_ha']) and fila_parcela['area_ha'] > 0 else 1.0
            import math
            st.markdown('**Simulación de dosis de encalado (revisar antes de aplicar)**')
            ec1, ec2, ec3 = st.columns(3)
            radio_int = ec1.number_input('Radio interior encalado (m)', min_value=0.0, value=0.80, step=0.05, key='encalado_radio_int')
            radio_ext = ec2.number_input('Radio exterior encalado (m)', min_value=0.05, value=1.20, step=0.05, key='encalado_radio_ext')
            prof_enc = ec3.number_input('Profundidad de suelo considerada (cm)', min_value=1.0, max_value=40.0, value=20.0, step=1.0, key='encalado_prof')
            e1, e2 = st.columns(2)
            kg_ha_encalado_calculado = None
            producto_enc = e1.selectbox('Tipo de enmienda', ['Dolomita', 'Cal agrícola', 'No aplicar'], key='encalado_producto')
            prnt_inicial = 108.0 if producto_enc == 'Dolomita' else 135.0
            if st.session_state.get('_encalado_tipo_anterior') != producto_enc:
                st.session_state['_encalado_tipo_anterior'] = producto_enc
                st.session_state['encalado_prnt'] = prnt_inicial
            prnt_pct = e2.number_input('PRNT del producto (%)', min_value=1.0, max_value=250.0,
                                       value=prnt_inicial, step=1.0, key='encalado_prnt',
                                       disabled=producto_enc == 'No aplicar')
            prnt = prnt_pct / 100.0
            st.caption('PRNT inicial referencial y editable: dolomita 108 %; cal agrícola 135 %. Reemplace por el valor de la ficha técnica de su producto.')
            # Mostrar siempre el valor medido y la meta separadamente.
            # Corregir el estado persistente de versiones anteriores que dejaba la meta en 0 %.
            sat_actual = datos.get('sat_al')
            if sat_actual is None and datos.get('al') is not None and datos.get('cice') and datos['cice'] > 0:
                sat_actual = 100.0 * datos['al'] / datos['cice']
            if st.session_state.get('encalado_meta_al') is not None:
                try:
                    meta_previa = float(st.session_state['encalado_meta_al'])
                except (TypeError, ValueError):
                    meta_previa = 20.0
                if not (1.0 <= meta_previa <= 100.0):
                    st.session_state['encalado_meta_al'] = 20.0
            col_actual_al, col_meta_al = st.columns(2)
            col_actual_al.metric('Saturación de aluminio actual (análisis)',
                f'{sat_actual:.2f} %' if sat_actual is not None else 'Sin análisis')
            sat_meta = col_meta_al.number_input('Saturación de aluminio objetivo (%)',
                min_value=1.0, max_value=100.0, value=20.0, step=1.0, key='encalado_meta_al')
            if sat_actual is not None:
                diferencia_sat = max(0.0, sat_actual - sat_meta)
                st.caption(f'Reducción requerida: {diferencia_sat:.2f} puntos porcentuales. '
                           'La dosis se recalcula al cambiar el objetivo; 20 % es la meta inicial editable.')
                if sat_actual <= sat_meta:
                    st.info('La saturación actual ya está en la meta o por debajo; no hay exceso de aluminio por neutralizar con este criterio.')
            if relacion is not None:
                st.info(f'Relación Ca/Mg obligatoria: {relacion:.2f}:1. La selección debe considerar también Mg absoluto, Ca absoluto y necesidad de encalado.')
            if producto_enc == 'No aplicar':
                st.info('No se calculará dosis de encalado porque el técnico seleccionó No aplicar.')
            elif radio_ext <= radio_int:
                st.error('El radio exterior debe superar el radio interior.')
            elif any(datos.get(k) is None for k in ('al','cice','ca','mg')) or datos['cice'] <= 0 or datos['dap'] <= 0 or relacion is None:
                st.warning('Para calcular, ingrese Al intercambiable, CICe, densidad aparente, Ca y Mg.')
            else:
                exceso_al = max(0., datos['al'] - sat_meta / 100 * datos['cice'])
                area_anillo = math.pi * (radio_ext**2 - radio_int**2)
                area_ha = area_anillo * plantas_encalado
                if area_ha > 10000:
                    st.error('La suma de anillos supera una hectárea; revise los radios y la densidad de plantas.')
                else:
                    masa_suelo = area_ha * prof_enc / 100 * datos['dap'] * 1000
                    # 1 cmol(+) de carga por kg requiere 0.5 g CaCO3/kg (peso equivalente 50 g/eq).
                    kg_equiv = exceso_al * 0.5 * masa_suelo / 1000
                    kg_ha = kg_equiv / prnt
                    kg_ha_encalado_calculado = kg_ha
                    kg_parcela = kg_ha * area_encalado
                    g_planta = kg_ha * 1000 / plantas_encalado
                    sacos = math.ceil(kg_parcela / 50)
                    st.dataframe(pd.DataFrame([{'Producto':producto_enc, 'Ca/Mg':round(relacion,2), 'Exceso Al (cmol(+)/kg)':round(exceso_al,3), 'kg/ha':round(kg_ha,2), 'kg/parcela':round(kg_parcela,2), 'g/planta':round(g_planta,1), 'Sacos de 50 kg':sacos}]), hide_index=True, use_container_width=True)
                    st.caption(f'Área tratada: {area_ha:,.1f} m²/ha. Masa de suelo: {masa_suelo:,.0f} kg/ha. Equivalente CaCO₃: {kg_equiv:,.1f} kg/ha. Ajuste por PRNT: {prnt:.2f}.')
                    st.caption('Referencia metodológica: INIA (2025), Manual técnico de encalado y fertilización para café y cacao, pp. 91–99 (neutralización de aluminio). Cálculo de SIFERT: estimación referencial; validar la dosis con el ejemplo del manual antes de aplicarla.')
                    if producto_enc.startswith('Dolomita'):
                        st.caption(f'Aporte químico teórico de la dolomita (sin estimar disponibilidad): CaO {kg_ha*0.30:.2f} kg/ha; MgO {kg_ha*0.215:.2f} kg/ha. Composición referencial editable; confirmar con la ficha del lote.')
                    else:
                        st.caption('La cal agrícola aporta principalmente calcio; para cuantificar CaO y MgO se requiere su composición real. No se presupone que carezca de magnesio.')
                    st.caption('Estos aportes de Ca y Mg solo serían efectivos si se aplicara la enmienda. No equivalen a nutrientes inmediatamente disponibles ni a una dosis aprobada.')
                    st.caption('Dosis referencial por neutralización de aluminio: verificar con el método y ejemplo INIA antes de recomendar la aplicación.')
            st.markdown('**Balance complementario de calcio y magnesio (Ca/Mg)**')
            st.caption('Enfoque INIA (2025): evaluar Ca y Mg intercambiables frente a valores de referencia; el encalado se calcula por neutralización de aluminio. No se presume disponibilidad inmediata de la enmienda.')
            enm_aplicada = st.checkbox('Sí aplicó (cal o dolomita)', value=False, key='enm_aplicada_v72')
            ca_total_aportado = 0.0
            mg_total_aportado = 0.0
            if enm_aplicada and (producto_enc == 'No aplicar' or kg_ha_encalado_calculado is None):
                st.warning('Seleccione una enmienda y complete los datos necesarios para obtener su dosis.')
            elif enm_aplicada:
                dosis_real_enm = float(kg_ha_encalado_calculado)
                st.caption(f'Enmienda: {producto_enc}. Dosis tomada automáticamente del cálculo de encalado: {dosis_real_enm:,.2f} kg/ha.')
                col_ca, col_mg = st.columns(2)
                if producto_enc == 'Dolomita':
                    cao_pct = col_ca.number_input('CaO del producto (%)', min_value=0.0, max_value=100.0,
                        value=30.0, step=0.5, key='enm_cao_pct_camg')
                    mgo_pct = col_mg.number_input('MgO del producto (%)', min_value=0.0, max_value=100.0,
                        value=21.5, step=0.5, key='enm_mgo_pct_camg')
                else:
                    cao_pct = col_ca.number_input('CaO del producto (%) según ficha', min_value=0.0, max_value=100.0,
                        value=0.0, step=0.5, key='enm_cao_pct_cal_camg')
                    mgo_pct = col_mg.number_input('MgO del producto (%) según ficha', min_value=0.0, max_value=100.0,
                        value=0.0, step=0.5, key='enm_mgo_pct_cal_camg')
                if cao_pct + mgo_pct > 100:
                    st.error('CaO + MgO supera 100 %. Revise la ficha técnica del producto.')
                    cao_pct, mgo_pct = 0.0, 0.0
                ca_total_aportado = dosis_real_enm * cao_pct / 100 * (40.078 / 56.077)
                mg_total_aportado = dosis_real_enm * mgo_pct / 100 * (24.305 / 40.304)
                st.caption(f'Aporte químico potencial (no disponibilidad inmediata): Ca {ca_total_aportado:.2f} y Mg {mg_total_aportado:.2f} kg/ha.')
            st.subheader('5. Compost aplicado y manejo de residuos de poda')
            st.caption('INIA: 2–5 kg/planta como referencia orientativa, no dosis obligatoria. El técnico registra la dosis real que aplica el agricultor.')
            mo_val = datos.get('mo')
            if mo_val is not None:
                st.metric('Materia orgánica actual del suelo', f'{mo_val:.2f} %')
            st.caption('Meta orientativa de recuperación progresiva de materia orgánica: 4 %. No se calcula una dosis automática para alcanzar esa meta.')
            plantas_compost = int(fila_parcela['plantas_ha']) if fila_parcela is not None and pd.notna(fila_parcela['plantas_ha']) and fila_parcela['plantas_ha'] > 0 else 1100
            area_compost = float(fila_parcela['area_ha']) if fila_parcela is not None and pd.notna(fila_parcela['area_ha']) and fila_parcela['area_ha'] > 0 else 1.0
            c1, c2 = st.columns(2)
            dosis_compost = c1.number_input('Compost aplicado (kg/planta/año)', min_value=0.0, max_value=100.0, value=0.0, step=0.5, key='compost_dosis_real')
            saco_compost = c2.number_input('Presentación del compost (kg/saco)', min_value=1.0, value=50.0, key='saco_compost_proyeccion')
            kg_compost_ha_anual = dosis_compost * plantas_compost
            kg_compost_parcela_anual = kg_compost_ha_anual * area_compost
            r1, r2, r3 = st.columns(3)
            r1.metric('Compost por hectárea', f'{kg_compost_ha_anual:,.1f} kg')
            r2.metric('Compost en la parcela', f'{kg_compost_parcela_anual:,.1f} kg')
            r3.metric('Sacos para la parcela', f'{math.ceil(kg_compost_parcela_anual/saco_compost):,}')
            st.markdown('**Residuos de poda: práctica habitual de campo**')
            st.caption('Cada planta conserva sus hojas y ramas de poda cortadas en trozos pequeños debajo de su propia copa. Esta cobertura contribuye al reciclaje gradual de nutrientes y a la protección del suelo.')
            st.caption('Por falta de mediciones locales de biomasa y estabilización, los residuos de poda NO se descuentan del balance NPK ni se convierten en un incremento numérico de materia orgánica. Se elimina el supuesto del 20 %.')
            st.caption('El NPK del compost aplicado sí se calcula con la dosis ingresada y la disponibilidad del primer año; no se duplica en el balance mineral.')

            st.subheader('6. Balance nutricional NPK · simulación técnica preliminar')
            st.caption('Referencia bibliográfica: INIA (2025).')
            n_total, p_ppm, k_cmol, dap = datos.get('n'), datos.get('p'), datos.get('k_cmol'), datos.get('dap')
            if any(v is None for v in (n_total,p_ppm,k_cmol,dap)) or dap <= 0:
                st.info('Para simular NPK ingrese N total (%), P disponible (ppm), K intercambiable (cmol(+)/kg) y densidad aparente positiva.')
            else:
                masa = 2_000_000 * dap
                # Coeficientes del ejemplo INIA, provisionales; P y K convertidos a óxidos.
                oferta = {
                    'N': masa*n_total/100*0.03*0.40,
                    'P₂O₅': masa*p_ppm/1_000_000*2.291*0.25,
                    'K₂O': masa*k_cmol*391/1_000_000*1.205*0.40,
                }
                etapa_balance = str(fila_parcela.get('etapa') or '') if fila_parcela is not None else ''
                edad_balance = float(fila_parcela.get('edad_anios') or 0) if fila_parcela is not None else 0.0
                densidad_balance = int(fila_parcela.get('plantas_ha') or 1100) if fila_parcela is not None else 1100
                if etapa_balance == 'Crecimiento' and 0 <= edad_balance <= 2:
                    # Vasquez-Zambrano et al. (2025), Tabla 1 y Apéndice B.1:
                    # incremento de biomasa seca 1500 (año 1), 3000 (año 2) kg/ha/año,
                    # para 1111 plantas/ha; madera+raíces 60/80 %, hojas 40/20 %.
                    # Concentraciones elementales en madera: N 0.69 %, P 0.12 %, K 1.55 %;
                    # hojas: N 2.50 %, P 0.20 %, K 1.80 %.
                    # P y K se convierten a P2O5 y K2O con 2.291 y 1.205.
                    anio_crecimiento = 1 if edad_balance <= 1 else 2
                    biomasa_base = 1500.0 if anio_crecimiento == 1 else 3000.0
                    fraccion_hojas = 0.40 if anio_crecimiento == 1 else 0.20
                    biomasa = biomasa_base * densidad_balance / 1111.0
                    madera = biomasa * (1.0 - fraccion_hojas)
                    hojas = biomasa * fraccion_hojas
                    demanda = {
                        'N': madera*0.0069 + hojas*0.025,
                        'P₂O₅': (madera*0.0012 + hojas*0.0020)*2.291,
                        'K₂O': (madera*0.0155 + hojas*0.0180)*1.205,
                    }
                    st.success(f'Cacao en crecimiento · año {anio_crecimiento}: demanda vegetativa estimada por biomasa y edad, ajustada a {densidad_balance:,} plantas/ha.')
                    st.caption('Fuente: Vasquez-Zambrano et al. (2025), European Journal of Agronomy, DOI: 10.1016/j.eja.2024.127463. Demanda por inmovilización vegetativa, NO dosis de fertilizante validada para Leoncio Prado.')
                elif etapa_balance == 'Crecimiento':
                    demanda = None
                    st.error('Crecimiento de más de 2 años: todavía no hay un modelo local validado. No se calculará una dosis automática; seleccione Producción solo si la plantación realmente produce.')
                elif etapa_balance == 'Producción' and rendimiento <= 0:
                    demanda = None
                    st.error('En Producción ingrese una meta de cacao seco mayor que cero.')
                else:
                    # INIA (2025), tabla 28: extracción elemental N=70, P=16, K=90 kg/t de cacao seco.
                    # Convertir P y K a óxidos antes de compararlos con oferta y fertilizantes.
                    demanda = {'N': 70*rendimiento/1000,
                               'P₂O₅': 16*2.29*rendimiento/1000,
                               'K₂O': 90*1.205*rendimiento/1000}
                    if etapa_balance == 'No especificada':
                        st.warning('Etapa no especificada: se aplica provisionalmente el modelo de producción. Confirme la etapa antes de usar el resultado.')
                if demanda is None:
                    st.stop()
                eficiencia = {'N':0.60,'P₂O₅':0.25,'K₂O':0.70}
                dosis = {nut:max(0,demanda[nut]-oferta[nut])/eficiencia[nut] for nut in demanda}
                # Balance inicial exclusivo de N, P₂O₅ y K₂O.
                filas_balance_suelo = [
                    {'Nutriente': nut,
                     'Requerimiento / objetivo (kg/ha)': round(demanda[nut], 2),
                     'Resultado del suelo (kg/ha)': round(oferta[nut], 2),
                     'Déficit / diferencia (kg/ha)': round(max(0, demanda[nut] - oferta[nut]), 2)}
                    for nut in demanda
                ]
                st.dataframe(pd.DataFrame(filas_balance_suelo), hide_index=True, use_container_width=True)
                st.caption('NPK: requerimiento y aporte anual estimados. El calcio y el magnesio se evalúan por separado en el módulo de encalado.')
                st.caption('El cuadro inicial muestra la necesidad antes de descontar compost. La sección 7 descuenta el compost y calcula el aporte aprovechable de cada fertilizante.')
                st.caption('La oferta del suelo es una aproximación no calibrada localmente. En Producción, la demanda escala con rendimiento; en Crecimiento (0–2 años), con biomasa y edad. No interpretar las dosis como prescripción validada.')

                # Las dosis complementarias son referenciales y se presentan en la tabla
                # de fertilizantes, nunca como una segunda prescripción independiente.
                micro_ref = [('Sulfato de cobre (0-0-0; CuSO4·5H2O)', 2., 0., 0.),
                             ('Sulfato de zinc (0-0-0; Zn)', 3., 0., 0.),
                             ('Sulfato de magnesio (0-0-0 + 9.6% Mg + 13% S)', 5., 0., 0.),
                             ('Sulfato de manganeso (0-0-0; Mn)', 1., 0., 0.),
                             ('Ulexita (0-0-0; 10–13% B)', 30., 20., 0.)]
                st.subheader('7. Fertilización NPK y microelementos en tres abonamientos')
                st.caption('El balance compara nutrientes aprovechables: suelo + compost + fertilizantes. Las eficiencias minerales se aplican una sola vez a su aporte; los orgánicos utilizan sus factores propios de disponibilidad.')
                area_real = float(fila_parcela['area_ha']) if fila_parcela is not None and pd.notna(fila_parcela['area_ha']) and fila_parcela['area_ha'] > 0 else 1.0
                plantas = int(fila_parcela['plantas_ha']) if fila_parcela is not None and pd.notna(fila_parcela['plantas_ha']) and fila_parcela['plantas_ha'] > 0 else 1100
                total_plantas = area_real * plantas
                st.caption(f'Parcela: {area_real:g} ha · {plantas:,} plantas/ha · {total_plantas:,.0f} plantas estimadas.')
                catalogo = catalogo_v6()
                st.caption(f'Biblioteca de {len(catalogo)} productos, sin duplicar el compost del módulo de materia orgánica. Las enmiendas se evalúan por separado.')
                with st.expander('📚 Consultar biblioteca de fertilizantes', expanded=False):
                    st.dataframe(pd.DataFrame([{'Producto':nombre,'Origen':clasificar_origen_producto(nombre, v['tipo']), 'N %':round(v['N']*100,2),
                        'P₂O₅ %':round(v['P₂O₅']*100,2),'K₂O %':round(v['K₂O']*100,2),
                        'Ca % (referencial)':v['Ca_reportado'],'Mg % (referencial)':v['Mg_reportado']} for nombre,v in catalogo.items()]),
                        hide_index=True,use_container_width=True)
                    st.caption('Los sulfatos y roca fosfórica se muestran junto a orgánicos por conveniencia, pero son sales o minerales, no materia orgánica. Verificar ficha y disponibilidad real.')
                with st.expander('➕ Registrar composición de un fertilizante comercial (simulación)'):
                    nom_nuevo = st.text_input('Nombre comercial exacto y fabricante', key='comercial_nuevo')
                    co1,co2,co3 = st.columns(3)
                    nn = co1.number_input('N (%)',0.0,100.0,0.0,key='comercial_n')
                    pp = co2.number_input('P₂O₅ (%)',0.0,100.0,0.0,key='comercial_p')
                    kk = co3.number_input('K₂O (%)',0.0,100.0,0.0,key='comercial_k')
                    if st.button('Agregar producto a la sesión', key='agregar_comercial'):
                        if not nom_nuevo.strip() or nn+pp+kk <= 0 or nn+pp+kk > 100:
                            st.error('Indique nombre y composición válida según etiqueta; N+P₂O₅+K₂O debe estar entre 0 y 100 %.')
                        else:
                            st.session_state.setdefault('catalogo_sifert',{})[nom_nuevo.strip()]={'tipo':'Personalizado','N':nn/100,'P₂O₅':pp/100,'K₂O':kk/100,'Ca_reportado':0,'Mg_reportado':0,'S_reportado':0}
                            st.success('Producto disponible en esta sesión. Verifique su ficha técnica antes de usarlo.')
                catalogo.update(st.session_state.get('catalogo_sifert',{}))
                st.markdown('**Selección manual de fertilizantes**')
                st.caption('Marque los productos que utilizará; luego edite la presentación y cantidad de sacos en la tabla única. El balance NPK se actualiza al cambiar los datos.')
                minerales = {x:v for x,v in catalogo.items()
                    if v['tipo'] not in ('Enm','Otro','Ca','Mg','Micro')
                    and (any(v[k] > 0 for k in ('N','P₂O₅','K₂O')) or (v['tipo']=='Natural' and (v.get('Ca_reportado',0)>0 or v.get('Mg_reportado',0)>0)))}
                organicos = [x for x,v in minerales.items() if v['tipo'] == 'Org']
                with st.expander('🌿 Composición y disponibilidad estimada de nutrientes orgánicos (editar)', expanded=False):
                    st.caption('Valores de simulación: sustituir por análisis del producto cuando exista. Los porcentajes de disponibilidad no son mediciones del lote.')
                    co_n,co_p,co_k=st.columns(3)
                    org_n=co_n.number_input('Disponibilidad anual N orgánico (%)',0,100,30,5,key='org_dispon_n')/100
                    org_p=co_p.number_input('Disponibilidad anual P₂O₅ orgánico (%)',0,100,30,5,key='org_dispon_p')/100
                    org_k=co_k.number_input('Disponibilidad anual K₂O orgánico (%)',0,100,70,5,key='org_dispon_k')/100
                    st.caption('Estos porcentajes editables corresponden únicamente a otros fertilizantes orgánicos del catálogo, no al compost DEVIDA registrado arriba.')
                    st.markdown('**Compost DEVIDA: disponibilidad aprobada para el primer año**')
                    st.caption('Etiqueta del compost: N 0.3–1.5 %, P 0.1–1.0 % y K 0.3–1.0 % (elementales). Valores iniciales dentro de esos rangos; edítelos según el análisis del lote. No son porcentajes garantizados de disponibilidad.')
                    c1,c2,c3=st.columns(3)
                    comp_n=c1.number_input('N elemental del compost (%)',0.0,20.0,0.9,0.1,key='compost_n_v67')/100
                    comp_p=c2.number_input('P elemental del compost (%)',0.0,20.0,0.55,0.05,key='compost_p_v67')/100*2.291
                    comp_k=c3.number_input('K elemental del compost (%)',0.0,20.0,0.65,0.05,key='compost_k_v67')/100*1.205
                # El compost DEVIDA tiene factores propios aprobados; no confundirlos con otros orgánicos.
                compost_disponibilidad = {'N':0.05, 'P₂O₅':0.40, 'K₂O':0.85}
                st.caption('Compost DEVIDA: N 5 %, P₂O₅ 40 %, K₂O 85 % disponibles el primer año (coeficientes referenciales, no análisis del lote).')
                st.caption('Confirmar si los porcentajes de la etiqueta están expresados en base húmeda o seca; hasta entonces el cálculo asume producto tal como se aplica.')
                minerales_efectivos={x:dict(v) for x,v in minerales.items()}
                for x in organicos:
                    for nutriente,factor in [('N',org_n),('P₂O₅',org_p),('K₂O',org_k)]:
                        minerales_efectivos[x][nutriente]*=factor
                fuentes=[]
                cols=st.columns(2)
                for col,titulo,tipos in [(cols[0],'QUÍMICOS',('N','P','K','Personalizado')),(cols[1],'ORGÁNICOS / MINERALES NATURALES',('Org','Natural'))]:
                    with col:
                        st.markdown('**'+titulo+'**')
                        for producto,comp in minerales.items():
                            if comp['tipo'] in tipos and st.checkbox(producto,value=False,key=f'check_fuente_v62_{producto}'):
                                fuentes.append(producto)
                # NPK del compost: se trae del módulo de materia orgánica, sin duplicar el compost como fertilizante seleccionable.
                compost_kg_ha=float(st.session_state.get('compost_dosis_real',0.0))*plantas
                compost_total={ 'N':compost_kg_ha*comp_n, 'P₂O₅':compost_kg_ha*comp_p, 'K₂O':compost_kg_ha*comp_k }
                compost_aprovechable={k:compost_total[k]*compost_disponibilidad[k] for k in ('N','P₂O₅','K₂O')}
                st.caption(f'Compost del módulo anterior: {compost_kg_ha:,.2f} kg/ha/año. Aporte estimado disponible: N {compost_aprovechable["N"]:.2f}, P₂O₅ {compost_aprovechable["P₂O₅"]:.2f}, K₂O {compost_aprovechable["K₂O"]:.2f} kg/ha/año.')
                st.caption('Compost: el aporte aprovechable se descuenta una sola vez del requerimiento del cultivo. La etiqueta declara N, P y K elementales; P y K se convierten a P₂O₅ y K₂O para compararlos con los fertilizantes. Valores referenciales sujetos a análisis, humedad y mineralización.')
                st.markdown('**Balance NPK: suelo y compost**')
                masa_suelo = masa
                # Por decisión del usuario, las cáscaras no se incluyen en el balance.
                potencial_cascaras = {'N': 0.0, 'P₂O₅': 0.0, 'K₂O': 0.0}
                resumen_descuento=[]
                for nutr in ('N','P₂O₅','K₂O'):
                    if nutr in ('N','P₂O₅','K₂O'):
                        objetivo_nutr=float(demanda[nutr])
                        suelo_nutr=float(oferta[nutr])
                        compost_nutr=float(compost_aprovechable[nutr])
                        enmienda_nutr=0.0
                    else:
                        conversion=200.39 if nutr=='Ca' else 121.53
                        meta=4.5 if nutr=='Ca' else 1.25
                        objetivo_nutr=meta*conversion*masa_suelo/1_000_000
                        analisis=datos.get(nutr.lower())
                        suelo_nutr=(float(analisis)*conversion*masa_suelo/1_000_000) if analisis is not None else None
                        compost_nutr=0.0  # Sin análisis de Ca/Mg del compost, no se inventa su aporte.
                        enmienda_nutr=enm_ca_kg_ha if nutr=='Ca' else enm_mg_kg_ha
                    restante=(max(0.,objetivo_nutr-suelo_nutr-compost_nutr-enmienda_nutr)
                              if suelo_nutr is not None else None)
                    resumen_descuento.append({
                        'Nutriente':nutr,
                        'Requerimiento / objetivo (kg/ha)':round(objetivo_nutr,2),
                        'Resultado del suelo (kg/ha)':round(suelo_nutr,2) if suelo_nutr is not None else 'Sin análisis',
                        'Aporte compost (kg/ha)':round(compost_nutr,2) if nutr in ('N','P₂O₅','K₂O') else 'Sin análisis',
                                                'Necesidad restante / diferencia (kg/ha)':round(restante,2) if restante is not None else 'No calculable'})
                st.dataframe(pd.DataFrame(resumen_descuento),hide_index=True,use_container_width=True)
                st.caption('Balance NPK: el compost se descuenta una sola vez. Las cáscaras no se consideran. El encalado se presenta por separado.')
                # Balance integrado Ca/Mg: leer los mismos controles de fertilizantes,
                # nunca solicitar una segunda cantidad de kieserita.
                st.markdown('**Balance integrado de calcio y magnesio (Ca/Mg)**')
                st.caption('Se actualiza al seleccionar productos y editar sus sacos en Fertilizantes. La diferencia es teórica; no equivale a disponibilidad inmediata ni a dosis recomendada.')
                area_camg = math.pi * max(0.0, radio_ext**2 - radio_int**2) * plantas_encalado
                masa_camg = min(area_camg, 10000.0) * (prof_enc / 100.0) * float(datos.get('dap') or 0.0) * 1000.0
                aportes_fert_ca = 0.0
                aportes_fert_mg = 0.0
                aportes_fert_kies_mg = 0.0
                aportes_fert_kies_s = 0.0
                detalle_aportes_camg = []
                for nombre_fert in fuentes:
                    peso_fert = float(st.session_state.get('peso_v69_'+nombre_fert, 50.0))
                    sacos_fert = float(st.session_state.get('sacos_v69_'+nombre_fert, 0.0))
                    kg_fert_ha = peso_fert * sacos_fert / area_real
                    if kg_fert_ha <= 0:
                        continue
                    comp_fert = minerales[nombre_fert]
                    ca_fert = kg_fert_ha * float(comp_fert.get('Ca_reportado') or 0) / 100.0
                    mg_fert = kg_fert_ha * float(comp_fert.get('Mg_reportado') or 0) / 100.0
                    aportes_fert_ca += ca_fert
                    aportes_fert_mg += mg_fert
                    if nombre_fert.startswith('Kieserita'):
                        aportes_fert_kies_mg += mg_fert
                        aportes_fert_kies_s += kg_fert_ha * float(comp_fert.get('S_reportado') or 22.0) / 100.0
                    if ca_fert or mg_fert:
                        detalle_aportes_camg.append({'Producto':nombre_fert, 'Ca elemental (kg/ha)':round(ca_fert,2), 'Mg elemental (kg/ha)':round(mg_fert,2)})
                filas_camg_integrado = []
                for nutr, meta, conversion, aporte_enmienda, aporte_fert in (
                    ('Ca', 4.5, 200.39, ca_total_aportado, aportes_fert_ca),
                    ('Mg', 1.25, 121.53, mg_total_aportado, aportes_fert_mg)):
                    medido = datos.get(nutr.lower())
                    deficit = (max(0.0,(meta-float(medido))*conversion*masa_camg/1_000_000)
                               if medido is not None and masa_camg > 0 else None)
                    filas_camg_integrado.append({
                        'Nutriente':nutr,
                        'Suelo (cmol(+)/kg)':round(float(medido),3) if medido is not None else 'Sin análisis',
                        'Objetivo provisional (cmol(+)/kg)':meta,
                        'Déficit localizado teórico (kg/ha)':round(deficit,2) if deficit is not None else 'No calculable',
                        'Enmienda aplicada (kg/ha)':round(aporte_enmienda,2),
                        'Fertilizantes seleccionados (kg/ha)':round(aporte_fert,2),
                        'Diferencia restante teórica (kg/ha)':round(max(0.0,deficit-aporte_enmienda-aporte_fert),2) if deficit is not None else 'No calculable'})
                st.dataframe(pd.DataFrame(filas_camg_integrado),hide_index=True,use_container_width=True)
                st.caption(f'Área de anillos: {min(area_camg,10000):,.1f} m²/ha de plantación · profundidad {prof_enc:g} cm. El Mg objetivo 1.25 cmol(+)/kg aún requiere validación. Solo se descuenta la enmienda cuando se declara aplicada.')
                if detalle_aportes_camg:
                    with st.expander('Ver aportes de Ca/Mg por fertilizante'):
                        st.dataframe(pd.DataFrame(detalle_aportes_camg),hide_index=True,use_container_width=True)
                st.caption(f'Kieserita seleccionada: Mg elemental {aportes_fert_kies_mg:.2f} kg/ha; S referencial {aportes_fert_kies_s:.2f} kg/ha. La cantidad proviene de los sacos seleccionados abajo, sin ingreso duplicado. Se asume aplicación en los anillos evaluados; si se distribuye fuera de ellos, el descuento no es válido.')
                st.caption('El aporte químico potencial de fertilizantes y enmiendas no implica que todo se incorpore al Mg/Ca intercambiable del suelo. No sumar nuevamente kieserita en Enmienda.')
                st.markdown('**Fertilizantes seleccionados y balance nutricional**')
                st.caption('Cambie los sacos o el peso de presentación: el balance, el total y la ficha PDF se actualizan automáticamente.')
                # Los number_input están fuera de st.form: cada edición produce un rerun
                # y recalcula inmediatamente todo el balance sin botón de confirmación.
                plan={}
                presentaciones={}
                if fuentes:
                    cab=st.columns([4,2,2,2])
                    for col,titulo in zip(cab,['**Fertilizante**','**Presentación (kg/saco)**','**Sacos (editar)**','**Total (kg)**']):
                        col.markdown(titulo)
                    for indice,x in enumerate(fuentes):
                        c_nombre,c_peso,c_sacos,c_total=st.columns([4,2,2,2],vertical_alignment='center')
                        c_nombre.write(x)
                        peso=c_peso.number_input('Presentación de '+x,min_value=0.1,value=50.0,step=1.0,format='%.2f',key='peso_v69_'+x,label_visibility='collapsed')
                        sacos=c_sacos.number_input('Sacos de '+x,min_value=0.0,value=0.0,step=0.5,format='%.2f',key='sacos_v69_'+x,label_visibility='collapsed')
                        presentaciones[x]=peso
                        plan[x]=peso*sacos
                        c_total.write(f'{plan[x]:,.2f}')
                    st.markdown(f'**TOTAL DE FERTILIZANTES: {sum(plan.values()):,.2f} kg**')
                else:
                    st.info('Seleccione al menos un fertilizante. El aporte del compost se mostrará en el balance aun sin productos seleccionados.')
                usados=[x for x in fuentes if plan.get(x,0)>0]
                aporte_fert={k:sum(plan[x]*minerales_efectivos[x][k]*(1.0 if minerales[x]['tipo']=='Org' else eficiencia[k]) for x in usados)/area_real for k in ('N','P₂O₅','K₂O')}
                # Comparación en unidades de nutrientes aprovechables: primero descontar suelo y compost,
                # luego aplicar eficiencia al fertilizante mineral. Orgánicos con factor de disponibilidad propio.
                filas_balance=[]
                for k in ('N','P₂O₅','K₂O'):
                    deficit=max(0.,demanda[k]-oferta[k])
                    objetivo_comercial=max(0.,deficit-compost_aprovechable[k])
                    aporte=aporte_fert[k]
                    diferencia=aporte-objetivo_comercial
                    tolerancia=max(0.000001,objetivo_comercial*0.05)  # ±5 % operativo; no norma INIA
                    estado='Equilibrado' if abs(diferencia)<=tolerancia else ('Exceso' if diferencia>0 else 'Déficit')
                    filas_balance.append({'Nutriente':k,'Necesidad de nutrientes (kg/ha)':round(objetivo_comercial,2),
                        'Aporte del fertilizante (kg/ha)':round(aporte,2),'Diferencia (kg/ha)':round(diferencia,2),'Estado':estado})
                # Vista unificada: filas de productos y filas NPK en un solo cuadro, manteniendo
                # explícita la diferencia entre fertilizante (kg) y nutriente (kg/ha).
                filas_unificadas=[]
                filas_unificadas.append({'Fertilizante / nutriente':'Compost aplicado (automático)',
                    'Presentación (kg/saco)':None,'Sacos':None,'Total (kg)':round(compost_kg_ha*area_real,2),
                    'Necesidad (kg/ha)':None,'Aporte (kg/ha)':None,'Diferencia (kg/ha)':None,'Estado':f'N {compost_aprovechable["N"]:.2f}; P₂O₅ {compost_aprovechable["P₂O₅"]:.2f}; K₂O {compost_aprovechable["K₂O"]:.2f} kg/ha aprovechables'})
                for r in filas_balance:
                    filas_unificadas.append({'Fertilizante / nutriente':'BALANCE '+r['Nutriente'],
                        'Presentación (kg/saco)':None,'Sacos':None,'Total (kg)':None,
                        'Necesidad (kg/ha)':r['Necesidad de nutrientes (kg/ha)'],
                        'Aporte (kg/ha)':r['Aporte del fertilizante (kg/ha)'],
                        'Diferencia (kg/ha)':r['Diferencia (kg/ha)'],'Estado':r['Estado']})
                st.dataframe(pd.DataFrame(filas_unificadas),hide_index=True,use_container_width=True)
                st.caption('Diferencia = aporte aprovechable del fertilizante − necesidad restante tras descontar suelo y compost. Las eficiencias minerales se aplican una sola vez al aporte; los orgánicos emplean disponibilidad anual estimada.')
                # Distribución operativa: 50 %, 32 %, 18 % por producto.
                filas_detalle=[]
                for x in usados:
                    total=plan[x]
                    a,b,c=total*0.50,total*0.32,total*0.18
                    filas_detalle.append((x,total,a,b,c))
                # No agregar automáticamente micronutrientes sin análisis ni diagnóstico.
                st.caption('Micronutrientes: no se agregan automáticamente; confirmar necesidad con análisis y asesoría, especialmente Cu y B.')
                st.markdown('**Fertilizantes requeridos y distribución en tres abonamientos**')
                filas_compra=[]
                for x,total,a,b,c in filas_detalle:
                    peso=presentaciones.get(x,50.)
                    filas_compra.append({'Fertilizante':x,'Comprar (kg)':round(total,2),
                        'Sacos a comprar':math.ceil(total/peso) if total>0 else 0,
                        '1.º abonamiento (kg)':round(a,2),'2.º abonamiento (kg)':round(b,2),'3.º abonamiento (kg)':round(c,2)})
                filas_compra.append({'Fertilizante':'TOTAL','Comprar (kg)':round(sum(r[1] for r in filas_detalle),2),
                    'Sacos a comprar':sum(r['Sacos a comprar'] for r in filas_compra),'1.º abonamiento (kg)':round(sum(r[2] for r in filas_detalle),2),
                    '2.º abonamiento (kg)':round(sum(r[3] for r in filas_detalle),2),'3.º abonamiento (kg)':round(sum(r[4] for r in filas_detalle),2)})
                st.dataframe(pd.DataFrame(filas_compra),hide_index=True,use_container_width=True)
                st.markdown('**Dosis en gramos por planta y abonamiento**')
                filas_gramos=[{'Fertilizante':'TOTAL','1.º (g/planta)':round(sum(r[2] for r in filas_detalle)*1000/total_plantas,2),
                    '2.º (g/planta)':round(sum(r[3] for r in filas_detalle)*1000/total_plantas,2),
                    '3.º (g/planta)':round(sum(r[4] for r in filas_detalle)*1000/total_plantas,2)}]
                st.dataframe(pd.DataFrame(filas_gramos),hide_index=True,use_container_width=True)
                st.caption('Distribución operativa 50 % / 32 % / 18 % para cada producto. Validar dosis, compatibilidad y necesidades específicas de micronutrientes antes de aplicar.')
                productor_pdf = str(fila_parcela['nombre']) if fila_parcela is not None else 'Sin participante seleccionado'
                def valor_pdf_parcela(campo):
                    if fila_parcela is None:
                        return ''
                    valor = fila_parcela.get(campo, '')
                    return '' if pd.isna(valor) else valor
                ficha_datos = {
                    'codigo': valor_pdf_parcela('codigo'), 'caserio': valor_pdf_parcela('caserio'),
                    'distrito': valor_pdf_parcela('distrito'), 'provincia': valor_pdf_parcela('provincia'),
                    'edad': valor_pdf_parcela('edad_anios'), 'etapa': valor_pdf_parcela('etapa'),
                    'densidad': plantas, 'meta': rendimiento, 'cascaras': valor_pdf_parcela('manejo_cascaras'),
                    'laboratorio': laboratorio_analisis, 'fecha_suelo': fecha_guardar,
                    'ingeniero': valor_pdf_parcela('ingeniero'), 'cip': valor_pdf_parcela('cip'), 'fecha_emision': date.today().isoformat(),
                    'enmienda': 'Dolomita' if producto_enc.startswith('Dolomita') else 'Cal agrícola',
                    'enmienda_kg_ha': f'{kg_ha_encalado_calculado:.2f}' if kg_ha_encalado_calculado is not None else 'No calculada',
                    'enmienda_kg_parcela': f'{kg_ha_encalado_calculado*area_real:.2f}' if kg_ha_encalado_calculado is not None else 'No calculada',
                    'enmienda_sacos': math.ceil(kg_ha_encalado_calculado*area_real/50) if kg_ha_encalado_calculado is not None else 'No calculada',
                    'enmienda_aplicada': 'Sí, declarado por el usuario' if enm_aplicada else 'No confirmada',
                    'compost_kg_ha': f'{compost_kg_ha:.2f}',
                }
                for clave in ('ph','mo','p','k2o','ca','mg','sat_al','cice','arena','limo','arcilla'):
                    ficha_datos[clave] = datos.get(clave)
                try:
                    ficha_pdf = crear_ficha_pdf(productor_pdf, fecha_guardar, area_real,
                                               total_plantas, filas_balance, filas_compra, filas_gramos, ficha_datos)
                    st.download_button('📄 Descargar ficha final de fertilización (PDF)',
                        data=ficha_pdf, file_name='SIFERT_CACAO_FICHA_FERTILIZACION.pdf',
                        mime='application/pdf', key='descarga_abonamientos_pdf')
                except ImportError:
                    st.error('Para descargar PDF, agregue reportlab a requirements.txt en GitHub.')
                st.warning('Simulación técnica preliminar. No aplicar sin validar análisis de suelo, composición de productos y recomendaciones locales.')
            st.caption('Encalado: se presenta por separado del balance NPK. La confirmación de aplicación no implica disponibilidad inmediata de Ca/Mg.')
        except ValueError as e:
            st.session_state.pop('evaluacion_pendiente', None)
            st.error(str(e))

    with st.expander('Información técnica y fuentes de referencia'):
        st.markdown('''**Criterios internos, no editables desde la interfaz.** Las referencias y rangos proceden de la versión V4.2 suministrada. Los coeficientes son heterogéneos y necesitan validación antes de usarse como base de prescripción.\n\n- CaO y MgO: cuadro IFA (2008) para grano, datos de Camerún.\n- NPK: coeficientes orientativos heredados de V4.2; comprobar las fuentes originales.\n- Las cáscaras de mazorca no se incorporan al balance de nutrientes de esta simulación.\n- Densidad aparente inicial referencial: 1.33 g/cm³ (0–20 cm), editable y registrada como medida o estimada.\n\n**Para guardar productor y análisis juntos, complete el formulario de la primera pestaña y pulse «Guardar productor y análisis».  Para persistencia en la nube configure PostgreSQL. No se exige inicio de sesión.**''')


with secciones[2]:
    st.subheader('Consultar, editar y eliminar análisis de suelo')
    dfp=participantes()
    pid=elegir_participante(dfp, 'p_guardados')
    if pid is not None:
        df=execute('SELECT * FROM analisis WHERE participante_id=? ORDER BY fecha DESC,id DESC',(pid,),True)
        if df.empty:
            st.info('No hay análisis guardados para este participante.')
        else:
            st.caption('Análisis registrados. Pulse ✕ a la derecha del análisis que desea eliminar. La eliminación es definitiva.')
            for _, registro in df.iterrows():
                c_fecha, c_detalle, c_borrar = st.columns([2, 6, 1], vertical_alignment='center')
                c_fecha.write(str(registro['fecha']))
                c_detalle.write(f"Análisis {int(registro['id'])} · pH: {registro['ph'] if pd.notna(registro['ph']) else '—'} · M.O.: {registro['mo'] if pd.notna(registro['mo']) else '—'} %")
                if c_borrar.button('✕', key=f"borrar_analisis_{int(registro['id'])}", help='Eliminar definitivamente este análisis'):
                    execute('DELETE FROM analisis WHERE id=? AND participante_id=?', (int(registro['id']), pid))
                    st.success('Análisis eliminado.')
                    st.rerun()
            with st.expander('Ver todos los resultados del laboratorio'):
                columnas_ocultas = ['id', 'participante_id']
                st.dataframe(df.drop(columns=columnas_ocultas, errors='ignore'), hide_index=True, use_container_width=True)
            opciones={f"{r['fecha']} · Análisis {int(r['id'])}":int(r['id']) for _,r in df.iterrows()}
            aid=opciones[st.selectbox('Registro para editar',list(opciones))]
            fila=df[df.id==aid].iloc[0]
            with st.form('editar_analisis'):
                fecha_ed=st.date_input('Fecha',value=pd.to_datetime(fila['fecha']).date())
                st.caption('Deje en blanco un valor que no fue medido.')
                cambios={}
                for i in range(0,len(CAMPOS),3):
                    cols=st.columns(3)
                    for col,(clave,nombre,unidad) in zip(cols,CAMPOS[i:i+3]):
                        actual=fila[clave]
                        cambios[clave]=col.text_input(nombre, value=str(float(actual)) if pd.notna(actual) else '',key='edit_'+clave)
                actualizar=st.form_submit_button('💾 Guardar modificaciones')
            if actualizar:
                try:
                    valores={clave:leer_numero(cambios[clave],nombre) for clave,nombre,_ in CAMPOS}
                    if not any(valores[k] is not None for k in FIELD_KEYS):
                        raise ValueError('No se puede guardar un análisis sin resultados del laboratorio.')
                    asignaciones=','.join([f'{k}=?' for k in FIELD_KEYS])
                    execute(f'UPDATE analisis SET fecha=?,{asignaciones} WHERE id=? AND participante_id=?',
                            [fecha_ed.isoformat()]+[valores[k] for k in FIELD_KEYS]+[aid,pid])
                    st.success('Análisis actualizado.')
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
            with st.expander('Eliminar análisis'):
                confirmar=st.checkbox('Confirmo la eliminación definitiva')
                if st.button('Eliminar definitivamente',disabled=not confirmar):
                    execute('DELETE FROM analisis WHERE id=? AND participante_id=?',(aid,pid))
                    st.success('Análisis eliminado.')
                    st.rerun()

with secciones[3]:
    st.subheader('Comparación histórica de análisis')
    pid=elegir_participante(participantes(),'p_comparar')
    if pid is not None:
        df=execute('SELECT * FROM analisis WHERE participante_id=? ORDER BY fecha,id',(pid,),True)
        if len(df)<2:
            st.info('Se necesitan al menos dos análisis del mismo participante.')
        else:
            opciones={f"{r['fecha']} · ID {int(r['id'])}":int(r['id']) for _,r in df.iterrows()}
            c1,c2=st.columns(2)
            primero=c1.selectbox('Análisis inicial',list(opciones),index=0)
            ultimo=c2.selectbox('Análisis final',list(opciones),index=len(opciones)-1)
            a=df[df.id==opciones[primero]].iloc[0]
            b=df[df.id==opciones[ultimo]].iloc[0]
            comparacion=[]
            for clave,nombre,unidad in CAMPOS:
                x,y=a[clave],b[clave]
                comparacion.append({'Indicador':nombre,'Inicial':x,'Final':y,
                                    'Cambio':round(float(y)-float(x),3) if pd.notna(x) and pd.notna(y) else None,'Unidad':unidad})
            st.dataframe(pd.DataFrame(comparacion),hide_index=True,use_container_width=True)
            st.caption('Las diferencias no demuestran por sí solas el efecto de una fertilización.')

with secciones[4]:
    st.subheader('Exportar respaldos')
    for nombre in ['participantes','analisis']:
        df=execute(f'SELECT * FROM {nombre}',fetch=True)
        st.download_button(f'Descargar {nombre} (CSV)',df.to_csv(index=False).encode('utf-8-sig'),
                           file_name=f'sifert_{nombre}.csv',mime='text/csv',key='csv_'+nombre)
    st.subheader('Importación de Excel (estructura V4 anterior)')
    st.caption('Importe primero participantes, luego análisis. Se admiten las columnas de las plantillas anteriores.')
    for tipo,campos in [('participantes',['codigo','nombre','caserio','area_ha','plantas_ha','edad_anios']),
                        ('analisis',['codigo','fecha']+FIELD_KEYS+['textura','observaciones'])]:
        b=BytesIO()
        with pd.ExcelWriter(b,engine='openpyxl') as w:
            pd.DataFrame(columns=campos).to_excel(w,index=False)
        st.download_button('Descargar plantilla '+tipo,b.getvalue(),file_name='plantilla_'+tipo+'.xlsx',
                           mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',key='plantilla_'+tipo)
        uploaded=st.file_uploader('Importar Excel '+tipo,type=['xlsx'],key='upload_'+tipo)
        if uploaded is not None:
            try:
                tabla=pd.read_excel(uploaded,dtype={'codigo':str})
                faltantes=[c for c in campos[:2] if c not in tabla.columns]
                if faltantes:
                    st.error('Faltan columnas: '+', '.join(faltantes))
                else:
                    st.dataframe(tabla.head(10),hide_index=True)
                    if st.button('Confirmar importación de '+tipo,key='confirmar_'+tipo):
                        exitos=0;errores=[]
                        for indice,fila in tabla.iterrows():
                            try:
                                if tipo=='participantes':
                                    execute('INSERT INTO participantes(codigo,nombre,caserio,area_ha,plantas_ha,edad_anios,creado) VALUES (?,?,?,?,?,?,?)',
                                            (str(fila['codigo']).strip(),str(fila['nombre']).strip(),
                                             None if pd.isna(fila.get('caserio')) else str(fila.get('caserio')),
                                             None if pd.isna(fila.get('area_ha')) else float(fila.get('area_ha')),
                                             1100 if pd.isna(fila.get('plantas_ha')) else int(fila.get('plantas_ha')),
                                             None if pd.isna(fila.get('edad_anios')) else float(fila.get('edad_anios')),
                                             date.today().isoformat()))
                                else:
                                    match=execute('SELECT id FROM participantes WHERE codigo=?',(str(fila['codigo']).strip(),),True)
                                    if match.empty: raise ValueError('Participante no encontrado')
                                    fecha=pd.to_datetime(fila['fecha']).date().isoformat()
                                    columnas=['participante_id','fecha']+FIELD_KEYS+['textura','observaciones']
                                    valores=[int(match.iloc[0]['id']),fecha]+[
                                        None if pd.isna(fila.get(k)) or str(fila.get(k)).strip()=='' else float(fila.get(k))
                                        for k in FIELD_KEYS]
                                    valores += [None if pd.isna(fila.get(k)) else str(fila.get(k)) for k in ['textura','observaciones']]
                                    execute(f"INSERT INTO analisis({','.join(columnas)}) VALUES ({','.join('?' for _ in columnas)})",valores)
                                exitos+=1
                            except Exception as e:
                                errores.append(f'Fila {indice+2}: {e}')
                        st.success(f'{exitos} registros importados.')
                        if errores: st.error('\n'.join(errores[:10]))
                        st.rerun()
            except Exception as e:
                st.error(f'No se pudo importar: {e}')
    st.info('Para persistencia entre reinicios o actualizaciones de Streamlit Cloud configure DATABASE_URL (PostgreSQL). Los CSV son respaldos manuales.')
