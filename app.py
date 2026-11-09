"""SIFERT CACAO DIGITAL V9.3 — interfaz única para agricultor y técnico.
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
                              '<b>segunda 30 %</b> y <b>tercera 20 %</b>. '
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
st.caption('V10.1 · Balance NPK · Ficha final de fertilización en PDF · Simulación técnica')
st.markdown('\n<style>\n/* SIFERT V8.8 · identidad visual cacao y suelo */\n:root { --sifert-green:#1b6249; --sifert-gold:#d8a43c; --sifert-ink:#203c31; }\n.stApp { background: linear-gradient(145deg,#f5f8f0 0%,#edf4e9 45%,#fff8e9 100%); }\n.block-container { padding-top:4.5rem; }\nh1 { margin-top:0.5rem !important; padding-top:0.4rem !important; line-height:1.25 !important; }\n@media(max-width:700px){.block-container{padding-top:3.5rem;}}\nh1 { color:#174e3a !important; font-weight:800 !important; letter-spacing:-.025em; }\ndiv[data-baseweb="tab-list"] { background:#e4efe5; padding:7px; border-radius:17px; gap:5px; border:1px solid #d1e2d0; }\nbutton[data-baseweb="tab"] { border-radius:11px !important; padding:11px 15px !important; font-weight:700 !important; color:#315444 !important; }\nbutton[data-baseweb="tab"][aria-selected="true"] { background:linear-gradient(120deg,#166447,#318b5c) !important; color:white !important; box-shadow:0 4px 12px #134f3929; }\ndiv[data-baseweb="tab-highlight"] { background:transparent !important; }\n/* Panel themes rely on marker elements, not positional selectors. */\ndiv[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {align-items:end; gap:1rem;}\ndiv[data-testid="stForm"] div[data-testid="stColumn"] {min-width:0;}\ndiv[data-testid="stForm"] div[data-testid="stWidgetLabel"] {min-height:1.35rem;}\ndiv[data-baseweb="tab-panel"]:has(.sifert-inicio-marker) {\n background:linear-gradient(145deg,rgba(247,255,246,.93),rgba(229,247,223,.92)),\n radial-gradient(circle at 95% 8%,#94bd72 0%,transparent 36%);\n border:1px solid #c5ddbd; border-radius:20px; padding:1.3rem 1.5rem 2rem;\n box-shadow:0 8px 28px #225b3420;\n}\ndiv[data-baseweb="tab-panel"]:has(.sifert-suelo-marker) {\n background:linear-gradient(140deg,rgba(255,252,242,.96),rgba(242,235,214,.94)),\n radial-gradient(circle at 95% 8%,#e8b96a 0%,transparent 35%);\n border:1px solid #e3d2ad; border-radius:20px; padding:1.3rem 1.5rem 2rem;\n box-shadow:0 8px 28px #7b5a2420;\n}\ndiv[data-baseweb="tab-panel"]:has(.sifert-inicio-marker) h3,\ndiv[data-baseweb="tab-panel"]:has(.sifert-suelo-marker) h3 {color:#234c36 !important; font-weight:800 !important; padding:.65rem .8rem; background:#ffffffb8; border-left:5px solid #2f8959; border-radius:8px; margin-top:1.5rem; }\ndiv[data-baseweb="tab-panel"]:has(.sifert-suelo-marker) h3 {border-left-color:#c28b37;}\ndiv[data-baseweb="tab-panel"] [data-testid="stForm"],\ndiv[data-baseweb="tab-panel"] [data-testid="stExpander"] {background:#ffffffd9; border:1px solid #d8e4d4; border-radius:14px; padding:.35rem;}\ndiv[data-baseweb="tab-panel"] [data-testid="stMetric"] {background:#fffefa; padding:.75rem; border:1px solid #e3e8da; border-radius:12px;}\ndiv[data-baseweb="tab-panel"] div[data-testid="stDataFrame"] {border-radius:12px; overflow:hidden;}\ndiv[data-baseweb="tab-panel"] label {color:#244b38 !important; font-weight:600 !important;}\ndiv[data-baseweb="tab-panel"] .stButton > button[kind="primary"],\ndiv[data-baseweb="tab-panel"] .stFormSubmitButton button {background:#23734f; color:white; border-color:#23734f; border-radius:10px; font-weight:700;}\n.sifert-hero {position:relative; overflow:hidden; display:flex; align-items:center; justify-content:space-between; gap:12px; border-radius:17px; padding:22px 25px; margin:4px 0 20px; color:white; box-shadow:0 6px 20px #0000001c;}\n.sifert-hero.inicio {background:linear-gradient(110deg,#104f37,#297f4b 64%,#6a9e46);}\n.sifert-hero.suelo {background:linear-gradient(110deg,#654221,#997038 64%,#b89452);}\n.sifert-hero h2 {font-size:clamp(1.25rem,2.2vw,1.9rem); margin:0 0 6px; font-weight:800; color:#fff !important;}\n.sifert-hero p {margin:0; font-size:.96rem; color:#f7f9e9;}\n.sifert-hero .art {font-size:clamp(2.6rem,5vw,4.7rem); line-height:1; filter:drop-shadow(0 3px 4px #0004); white-space:nowrap;}\n@media(max-width:700px){ div[data-baseweb="tab-panel"]:has(.sifert-inicio-marker),div[data-baseweb="tab-panel"]:has(.sifert-suelo-marker){padding:.65rem;} .sifert-hero{padding:15px 14px;} .sifert-hero .art{font-size:2.5rem;} }\n</style>\n', unsafe_allow_html=True)
st.info('Ingrese los resultados de su análisis de suelo y la producción de cacao seco que desea alcanzar. No necesita modificar fórmulas.')

# Parámetros de referencia internos. Son bibliográficos, NO una calibración local
# ni equivalentes a demanda total o dosis de fertilización.
EXTRACCION_GRANO_KG_T = {'N': 22.0, 'P₂O₅': 6.87, 'K₂O': 10.8,
                          'CaO': 1.3, 'MgO': 5.3}
# Umbrales provisionales del archivo original, sujetos a método de laboratorio.
UMBRALES = {'mo': (2.0, 4.0), 'n': (0.10, 0.20), 'p': (7.0, 14.0),
            'k_cmol': (0.20, 0.40), 'ca': (3.0, 6.0), 'mg': (0.50, 1.00)}
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
BIBLIOTECA_V6 = [('Urea (46-0-0)', 'N', 46, 0, 0, 0, 0, 0), ('Nitrato de amonio (33-0-0)', 'N', 33, 0, 0, 0, 0, 0), ('Fosfato diamónico (18-46-0)', 'P', 18, 46, 0, 0, 0, 0), ('Fosfato monoamónico (11-52-0)', 'P', 11, 52, 0, 0, 0, 0), ('Superfosfato triple (0-46-0 + 14% Ca)', 'P', 0, 46, 0, 14, 0, 0), ('NPK soluble (20-20-20)', 'P', 20, 20, 20, 0, 0, 0), ('Cloruro de potasio (0-0-60)', 'K', 0, 0, 60, 0, 0, 0), ('Nitrato de potasio (13-0-46)', 'K', 13, 0, 46, 0, 0, 0), ('Guano de isla (10-10-2; referencial)', 'Org', 10, 10, 2, 0, 0, 0), ('Gallinaza compostada (2.5-2.5-2; referencial)', 'Org', 2.5, 2.5, 2, 0, 0, 0), ('Humus de lombriz (1.5-1-1; referencial)', 'Org', 1.5, 1, 1, 0, 0, 0), ('Roca fosfórica (0-28-0 + 30% Ca; referencial)', 'Natural', 0, 28, 0, 30, 0, 0), ('Sulfato de potasio (0-0-50 + 18% S)', 'Natural', 0, 0, 50, 0, 0, 18), ('Sulfato de magnesio (0-0-0 + 9.6% Mg + 13% S)', 'Natural', 0, 0, 0, 0, 9.6, 13), ('Sulfato de potasio y magnesio (0-0-22 + 11% Mg + 22% S)', 'Natural', 0, 0, 22, 0, 11, 22), ('Sulfato de cobre (0-0-0; CuSO4·5H2O)', 'Micro', 0, 0, 0, 0, 0, 0), ('Sulfato de zinc (0-0-0; Zn)', 'Micro', 0, 0, 0, 0, 0, 0), ('Sulfato de manganeso (0-0-0; Mn)', 'Micro', 0, 0, 0, 0, 0, 0), ('Ulexita (0-0-0; 10–13% B)', 'Micro', 0, 0, 0, 0, 0, 0)]

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

def clasificar(k, v):
    """Comparación orientativa con rangos de referencia para cacao (INIA 2025).
    No equivale a recomendación de dosis ni a calibración local del laboratorio.
    """
    if v is None:
        return 'No determinado'
    if k == 'ph' and not 0 < v <= 14:
        return 'Revisar resultado'
    if k == 'sat_al' and not 0 <= v <= 100:
        return 'Revisar resultado'
    if v < 0:
        return 'Revisar resultado'
    rangos = {
        'ph': (5.5, 6.5), 'mo': (4.0, None), 'n': (0.20, None),
        'p': (10.0, None), 'k_cmol': (0.20, 0.30),
        'ca': (4.0, 5.0), 'mg': (1.0, 1.5),
        'sat_al': (None, 20.0),
    }
    if k not in rangos:
        return 'Registrado'
    minimo, maximo = rangos[k]
    if minimo is not None and v < minimo:
        return 'Inferior al rango adecuado'
    if maximo is not None and (v > maximo if k != 'sat_al' else v >= maximo):
        return 'Superior al rango adecuado'
    return 'Dentro del rango adecuado'


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

init_db()
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
    opciones_inicio = {'➕ Nuevo productor y nuevo análisis': None}
    opciones_inicio.update({f"{r['codigo']} · {r['nombre']}": int(r['id']) for _, r in registros_inicio.iterrows()})
    seleccion_inicio = st.selectbox('Productor para registrar o consultar', list(opciones_inicio), key='selector_inicio')
    productor_existente_id = opciones_inicio[seleccion_inicio]
    if st.session_state.get('_selector_inicio_previo') != seleccion_inicio:
        st.session_state['_selector_inicio_previo'] = seleccion_inicio
        for k in ('codigo','nombre','caserio','area','plantas','edad','manejo','distrito','provincia','etapa','ingeniero','retiro'):
            st.session_state.pop('registro_' + k, None)
        for k in FIELD_KEYS:
            st.session_state.pop('dato_' + k, None)
        st.session_state.pop('evaluacion_pendiente', None)
        st.session_state.pop('_consulta_id_cargado', None)
    registro_actual = (registros_inicio[registros_inicio['id'] == productor_existente_id].iloc[0]
                       if productor_existente_id is not None else None)
    def campo_actual(nombre, predeterminado=''):
        if registro_actual is None:
            return predeterminado
        v = registro_actual.get(nombre)
        return predeterminado if pd.isna(v) or v is None else v
    c1,c2,c3=st.columns(3)
    codigo=c1.text_input('Código único (evite DNI)', value=str(campo_actual('codigo')),
                         disabled=productor_existente_id is not None, key='registro_codigo')
    nombre=c2.text_input('Nombre o identificación interna', value=str(campo_actual('nombre')), key='registro_nombre')
    caserio=c3.text_input('Caserío', value=str(campo_actual('caserio')), key='registro_caserio')
    area=c1.number_input('Área (ha)', min_value=0.0, value=float(campo_actual('area_ha',1.0)), key='registro_area')
    plantas=c2.number_input('Plantas por ha', min_value=1, value=int(campo_actual('plantas_ha',1100)), key='registro_plantas')
    edad=c3.number_input('Edad del cacao (años)', min_value=0.0, value=float(campo_actual('edad_anios',5.0)), key='registro_edad')
    st.markdown('**Datos complementarios del productor y parcela para la ficha PDF**')
    c4,c5,c6=st.columns(3)
    manejos=['Permanecen en la parcela','Se retiran completamente','Retiro parcial']
    manejo_actual=str(campo_actual('manejo_cascaras', manejos[0]))
    manejo=c4.selectbox('Manejo de cáscaras', manejos, index=manejos.index(manejo_actual) if manejo_actual in manejos else 0, key='registro_manejo')
    distrito=c5.text_input('Distrito', value=str(campo_actual('distrito')), key='registro_distrito')
    provincia=c6.text_input('Provincia', value=str(campo_actual('provincia','Leoncio Prado')), key='registro_provincia')
    c7,c8=st.columns([1,2])
    etapas=['No especificada','Crecimiento','Producción']
    etapa_actual=str(campo_actual('etapa', etapas[0]))
    etapa=c7.selectbox('Etapa del cultivo', etapas, index=etapas.index(etapa_actual) if etapa_actual in etapas else 0, key='registro_etapa')
    ingeniero=c8.text_input('Responsable técnico', value=str(campo_actual('ingeniero')), key='registro_ingeniero')
    retiro=c4.number_input('Porcentaje retirado (%)', min_value=0.0, max_value=100.0, value=float(campo_actual('retiro_pct',50.0)), step=5.0, key='registro_retiro') if manejo=='Retiro parcial' else (100.0 if manejo=='Se retiran completamente' else 0.0)
    st.caption('Complete los datos del productor y el análisis de suelo. Ambos se guardarán con el único botón al final del formulario.')
    st.subheader('Participantes registrados')
    df_participantes = participantes()
    if df_participantes.empty:
        st.info('Aún no hay participantes registrados.')
    else:
        columnas_visibles = {
            'codigo': 'Código', 'nombre': 'Productor', 'caserio': 'Caserío',
            'distrito': 'Distrito', 'provincia': 'Provincia',
            'area_ha': 'Área (ha)', 'plantas_ha': 'Plantas/ha',
            'edad_anios': 'Edad (años)', 'manejo_cascaras': 'Manejo de cáscaras',
            'etapa': 'Etapa', 'ingeniero': 'Responsable técnico'
        }
        disponibles = [c for c in columnas_visibles if c in df_participantes.columns]
        tabla_participantes = df_participantes[disponibles].rename(columns=columnas_visibles).copy()
        for col in tabla_participantes.select_dtypes(include=['object']).columns:
            tabla_participantes[col] = tabla_participantes[col].replace(['None', 'nan', 'NaN', ''], pd.NA).fillna('Por completar')
        st.dataframe(tabla_participantes, hide_index=True, use_container_width=True)
        st.caption('“Por completar” indica información no registrada en ese código. Los datos del formulario superior solo se guardan en el código indicado al pulsar «Guardar participante».')
        st.info('Para completar datos de un código anterior, abra «Completar o corregir datos de un participante» y seleccione ese código. El sistema no une automáticamente códigos distintos aunque el nombre sea parecido.')
        with st.expander('✏️ Completar o corregir datos de un participante'):
            opciones_editar = {f"{r['codigo']} · {r['nombre']}": int(r['id']) for _, r in df_participantes.iterrows()}
            sel_editar = st.selectbox('Seleccione el participante', list(opciones_editar), key='sel_editar_part')
            fila_editar = df_participantes[df_participantes['id'] == opciones_editar[sel_editar]].iloc[0]
            def valor_existente(campo):
                v = fila_editar.get(campo, '')
                return '' if pd.isna(v) or str(v).strip().lower() in ('none', 'nan') else str(v)
            with st.form('form_editar_participante'):
                e1, e2, e3 = st.columns(3)
                nuevo_nombre = e1.text_input('Productor', value=valor_existente('nombre'))
                nuevo_caserio = e2.text_input('Caserío', value=valor_existente('caserio'))
                nuevo_distrito = e3.text_input('Distrito', value=valor_existente('distrito'))
                e4, e5, e6 = st.columns(3)
                nueva_provincia = e4.text_input('Provincia', value=valor_existente('provincia'))
                etapas = ['No especificada', 'Crecimiento', 'Producción']
                etapa_actual = valor_existente('etapa')
                nueva_etapa = e5.selectbox('Etapa del cultivo', etapas, index=etapas.index(etapa_actual) if etapa_actual in etapas else 0)
                nuevo_ingeniero = e6.text_input('Responsable técnico', value=valor_existente('ingeniero'))
                guardar_correccion = st.form_submit_button('Guardar correcciones')
            if guardar_correccion:
                if not nuevo_nombre.strip():
                    st.error('El nombre del productor es obligatorio.')
                else:
                    execute('UPDATE participantes SET nombre=?, caserio=?, distrito=?, provincia=?, etapa=?, ingeniero=? WHERE id=?',
                            (nuevo_nombre.strip(), nuevo_caserio.strip(), nuevo_distrito.strip(), nueva_provincia.strip(), nueva_etapa, nuevo_ingeniero.strip(), int(fila_editar['id'])))
                    st.success('Datos del participante actualizados.')
                    st.rerun()

        with st.expander('🗑️ Eliminar un participante registrado'):
            st.warning('Esta acción elimina definitivamente el participante. Si tiene análisis de suelo o aplicaciones vinculadas, primero debe eliminar esos registros desde sus módulos correspondientes.')
            opciones_borrar = {
                f"{fila['codigo']} · {fila['nombre']}": int(fila['id'])
                for _, fila in df_participantes.iterrows()
            }
            etiqueta_borrar = st.selectbox('Seleccione el participante que desea eliminar',
                                          list(opciones_borrar), key='participante_a_borrar')
            id_borrar = opciones_borrar[etiqueta_borrar]
            vinculados_analisis = execute('SELECT COUNT(*) AS total FROM analisis WHERE participante_id=?',
                                          (id_borrar,), True)
            vinculados_aplicaciones = execute('SELECT COUNT(*) AS total FROM aplicaciones WHERE participante_id=?',
                                              (id_borrar,), True)
            n_analisis = int(vinculados_analisis.iloc[0]['total'])
            n_aplicaciones = int(vinculados_aplicaciones.iloc[0]['total'])
            if n_analisis or n_aplicaciones:
                st.error(f'No se puede eliminar todavía: tiene {n_analisis} análisis y {n_aplicaciones} aplicaciones asociadas.')
            confirmar_borrado = st.checkbox('Confirmo que deseo eliminar definitivamente este participante',
                                           key='confirmar_borrado_participante')
            if st.button('Eliminar participante', key='borrar_participante',
                         disabled=not confirmar_borrado or bool(n_analisis or n_aplicaciones)):
                try:
                    # Comprobación dentro de la misma transacción para no dejar registros huérfanos.
                    with connect() as conn:
                        cur = conn.cursor()
                        placeholder = '%s' if IS_POSTGRES else '?'
                        for tabla in ('analisis', 'aplicaciones'):
                            cur.execute(f'SELECT COUNT(*) FROM {tabla} WHERE participante_id={placeholder}',
                                        (id_borrar,))
                            if cur.fetchone()[0]:
                                raise ValueError('El participante tiene registros asociados. Elimínelos primero.')
                        cur.execute(f'DELETE FROM participantes WHERE id={placeholder}', (id_borrar,))
                    st.success('Participante eliminado correctamente.')
                    st.rerun()
                except Exception as e:
                    st.error(f'No se pudo eliminar: {e}')



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
    rendimiento = col_meta.number_input('Meta de cacao seco (kg/ha/año)', min_value=100.0, max_value=10000.0, step=100.0, key='meta_evaluacion', help='Producción esperada utilizada en los cálculos de fertilización.')
    laboratorio_analisis = col_lab.text_input('Laboratorio del análisis de suelo', key='laboratorio_evaluacion')
    with st.form('evaluacion'):
        st.subheader('1. Copie los valores de su análisis de suelo')
        st.caption('Si el laboratorio no midió un indicador, déjelo vacío. No coloque cero para representar un dato faltante.')
        datos_texto = {}
        for j in range(0, len(CAMPOS), 3):
            columnas = st.columns(3)
            for columna, (clave, nombre, unidad) in zip(columnas, CAMPOS[j:j+3]):
                datos_texto[clave] = columna.text_input(f'{nombre} ({unidad})' if unidad else nombre,
                                                       placeholder='No medido: dejar vacío', key='dato_'+clave)
        st.caption('Densidad aparente referencial automática: 1.33 g/cm³ (0–20 cm).')
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
                columnas = ['participante_id', 'fecha'] + FIELD_KEYS + ['dap','textura','observaciones','meta_produccion']
                parametros = [pid_guardar, fecha_guardar.isoformat()] + [valores[k] for k in FIELD_KEYS] + [
                    1.33, textura_usda(valores['arena'],valores['limo'],valores['arcilla']),
                    f'Meta de evaluación: {rendimiento:g} kg/ha/año; laboratorio: {laboratorio_analisis}', float(rendimiento)]
                cur.execute(q(f"INSERT INTO analisis({','.join(columnas)}) VALUES ({','.join('?' for _ in columnas)})"), parametros)
            st.session_state['_productor_evaluacion_anterior'] = pid_guardar
            st.session_state['evaluacion_pendiente'] = {
                'datos': valores.copy(), 'rendimiento': float(rendimiento),
                'participante_id': pid_guardar, 'fecha': fecha_guardar.isoformat(),
                'laboratorio': laboratorio_analisis}
            st.success('Productor y análisis guardados juntos. Consulte los resultados en la segunda pestaña.')
        except Exception as e:
            st.error(f'No se pudo guardar: {e}')


with secciones[1]:
    st.markdown('<div class="sifert-suelo-marker sifert-hero suelo"><div><h2>🌱 Resultados del suelo y fertilización</h2><p>Diagnóstico químico · balance NPK · plan de abonamiento</p></div><span class="art">🪴🔬</span></div>', unsafe_allow_html=True)
    registros_resultados = participantes()
    if not registros_resultados.empty:
        opciones_res = {f"{r['codigo']} · {r['nombre']}": int(r['id']) for _, r in registros_resultados.iterrows()}
        etiqueta_res = st.selectbox('Consultar productor guardado', list(opciones_res), index=None,
                                    placeholder='Seleccione un productor para ver sus resultados', key='consulta_productor')
        pid_consulta = opciones_res[etiqueta_res] if etiqueta_res else None
        if pid_consulta is not None:
            analisis_disponibles = execute('SELECT * FROM analisis WHERE participante_id=? ORDER BY fecha DESC,id DESC', (pid_consulta,), True)
            if not analisis_disponibles.empty:
                opciones_analisis = {f"{r['fecha']} · Análisis {i+1}": i for i, (_,r) in enumerate(analisis_disponibles.iterrows())}
                etiqueta_analisis = st.selectbox('Análisis guardado', list(opciones_analisis), key='consulta_analisis')
                registro_analisis = analisis_disponibles.iloc[opciones_analisis[etiqueta_analisis]]
                identificador = int(registro_analisis['id'])
                if st.session_state.get('_consulta_id_cargado') != identificador:
                    st.session_state['_consulta_id_cargado'] = identificador
                    st.session_state['_productor_evaluacion_anterior'] = pid_consulta
                    st.session_state['evaluacion_pendiente'] = {
                        'datos': {k: (float(registro_analisis[k]) if pd.notna(registro_analisis[k]) else None) for k in FIELD_KEYS},
                        'rendimiento': float(registro_analisis['meta_produccion']) if pd.notna(registro_analisis.get('meta_produccion')) else 1000.0,
                        'participante_id': pid_consulta, 'fecha': str(registro_analisis['fecha']),
                        'laboratorio': ''}
            else:
                st.info('Este productor todavía no tiene análisis registrados.')
    pid_guardar = pid_consulta if not registros_resultados.empty and pid_consulta is not None else st.session_state.get('_productor_evaluacion_anterior')
    fecha_guardar = date.fromisoformat(st.session_state['evaluacion_pendiente']['fecha']) if st.session_state.get('evaluacion_pendiente') else date.today()
    laboratorio_analisis = st.session_state.get('evaluacion_pendiente', {}).get('laboratorio', '')
    rendimiento = st.session_state.get('evaluacion_pendiente', {}).get('rendimiento', 1000.0)
    fila_parcela = participantes().query('id == @pid_guardar').iloc[0] if pid_guardar is not None and not participantes().query('id == @pid_guardar').empty else None
    if st.session_state.get('evaluacion_pendiente') is None:
        st.info('Primero registre al productor y guarde los resultados del laboratorio en la pestaña Inicio. Aquí aparecerán los resultados calculados.')
    if st.session_state.get('evaluacion_pendiente') is not None:
        try:
            # La evaluación pendiente es una instantánea inmutable hasta guardar.
            # Los reruns de botones, pestañas y descargas no deben sobrescribirla.
            datos = st.session_state['evaluacion_pendiente']['datos'].copy()
            datos['dap'] = 1.33  # Densidad aparente fija, referencial (g/cm³)
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
            # Mostrar solo indicadores con interpretación agronómica orientativa.
            # Los demás resultados permanecen en datos para verificaciones internas.
            indicadores_visibles = {'ph', 'mo', 'n', 'p', 'k_cmol', 'ca', 'mg', 'sat_al'}
            for clave, nombre, unidad in CAMPOS:
                if clave not in indicadores_visibles or datos[clave] is None:
                    continue
                tabla.append({'Indicador':nombre, 'Resultado': datos[clave] if datos[clave] is not None else 'No medido',
                              'Unidad':unidad, 'Respecto al rango de referencia':clasificar(clave, datos[clave])})
            textura = textura_usda(datos['arena'], datos['limo'], datos['arcilla'])
            if textura:
                tabla.append({'Indicador': 'Textura del suelo',
                              'Resultado': textura, 'Unidad': '',
                              'Respecto al rango de referencia': 'Clase textural USDA'})
            if tabla:
                st.dataframe(pd.DataFrame(tabla), hide_index=True, use_container_width=True)
            else:
                st.info('Ingrese resultados de suelo para mostrar el diagnóstico.')
            if datos['al'] is not None and datos['cice'] is not None and datos['cice'] > 0:
                sat_calculada = datos['al'] / datos['cice'] * 100
                if datos['sat_al'] is not None and abs(sat_calculada - datos['sat_al']) > 0.5:
                    st.warning(f'Compruebe la saturación de aluminio: Al/CICe × 100 = {sat_calculada:.2f} %, frente al {datos["sat_al"]:.2f} % ingresado. Verifique la metodología del laboratorio.')
            st.subheader('4. Diagnóstico de encalado y relación Ca/Mg')
            st.caption('Consulte los indicadores y seleccione la enmienda según la evaluación técnica de campo.')
            ca_val, mg_val = datos.get('ca'), datos.get('mg')
            relacion = ca_val / mg_val if ca_val is not None and mg_val is not None and mg_val > 0 else None
            sat_val = datos.get('sat_al')
            ph_val = datos.get('ph')
            requiere_revision = (ph_val is not None and ph_val < 5.5) or (sat_val is not None and sat_val >= 20)
            if relacion is not None:
                st.metric('Relación Ca/Mg (cmol(+)/kg)', f'{relacion:.2f}:1')
                st.caption(f'Ca: {ca_val:g} · Mg: {mg_val:g} cmol(+)/kg. La relación es un indicador complementario.')
            else:
                st.info('Para evaluar Ca/Mg ingrese calcio y magnesio intercambiables; Mg debe ser mayor que cero.')
            st.dataframe(pd.DataFrame([{'Indicador':'pH', 'Resultado': f"{ph_val:.2f}" if ph_val is not None else '—', 'Referencia para cacao':'5.5–6.5'}, {'Indicador':'Saturación Al (%)', 'Resultado':f"{sat_val:.2f}" if sat_val is not None else '—', 'Referencia para cacao':'< 20'}, {'Indicador':'Calcio (cmol(+)/kg)', 'Resultado':f"{ca_val:.2f}" if ca_val is not None else '—', 'Referencia para cacao':'4–5'}, {'Indicador':'Magnesio (cmol(+)/kg)', 'Resultado':f"{mg_val:.2f}" if mg_val is not None else '—', 'Referencia para cacao':'1.0–1.5'}]), hide_index=True, use_container_width=True)
            st.caption('Referencias orientativas para cacao atribuidas al INIA (2025); verificar tabla original y método del laboratorio antes de utilizarlas como umbrales definitivos.')
            plantas_encalado = int(fila_parcela['plantas_ha']) if fila_parcela is not None and pd.notna(fila_parcela['plantas_ha']) and fila_parcela['plantas_ha'] > 0 else 1100
            area_encalado = float(fila_parcela['area_ha']) if fila_parcela is not None and pd.notna(fila_parcela['area_ha']) and fila_parcela['area_ha'] > 0 else 1.0
            import math
            st.markdown('**Dosis estimada de encalado en el anillo de aplicación**')
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
            st.caption('PRNT editable: confirme el porcentaje con la ficha técnica del producto.')
            sat_meta = st.number_input('Saturación de aluminio objetivo (%)', min_value=0.0, max_value=40.0, value=20.0, step=1.0, key='encalado_meta_al')
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
                    st.caption(f'Anillo tratado: {area_ha:,.1f} m²/ha. Dosis teórica ajustada al PRNT ingresado ({prnt_pct:g} %).')
                    if producto_enc.startswith('Dolomita'):
                        st.caption(f'Aporte teórico según composición referencial ODINSU: CaO {kg_ha*0.30:.2f} y MgO {kg_ha*0.215:.2f} kg/ha. Verificar composición real del producto.')
                    else:
                        st.caption('Para estimar CaO y MgO de la cal, consultar la composición del producto.')
                    st.caption('Los aportes químicos son teóricos; no equivalen a nutrientes inmediatamente disponibles.')
                    st.caption('Dosis orientativa, no validada para aplicación directa. Confirmar con evaluación técnica de campo.')
            st.subheader('5. Compost y poda: proyección de materia orgánica')
            st.caption('El agricultor elige cuánto compost aplicará. SIFERT estima por separado el aporte del compost y el de los residuos de poda que permanecen en el anillo.')
            mo_val = datos.get('mo')
            if mo_val is None:
                st.info('Ingrese el porcentaje de materia orgánica del análisis para activar la simulación.')
            else:
                import math
                plantas_compost = int(fila_parcela['plantas_ha']) if fila_parcela is not None and pd.notna(fila_parcela['plantas_ha']) and fila_parcela['plantas_ha'] > 0 else 1100
                area_compost = float(fila_parcela['area_ha']) if fila_parcela is not None and pd.notna(fila_parcela['area_ha']) and fila_parcela['area_ha'] > 0 else 1.0
                dap_compost = datos.get('dap')
                st.metric('Materia orgánica actual del suelo', f'{mo_val:.2f} %')
                c1, c2, c3 = st.columns(3)
                dosis_compost = c1.number_input('Compost que aplicará (kg/planta/año)', min_value=0.0, max_value=100.0, value=2.0, step=0.5, key='compost_dosis_real')
                anios_mo = c2.selectbox('Años de aplicación de compost', [1, 2, 3, 4, 5], index=0, key='compost_anios_proyeccion')
                saco_compost = c3.number_input('Presentación (kg/saco)', min_value=1.0, value=50.0, key='saco_compost_proyeccion')
                c4, c5 = st.columns(2)
                radio_in = c4.number_input('Radio interior del anillo (m)', min_value=0.0, value=0.80, step=0.05, key='compost_radio_in')
                radio_out = c5.number_input('Radio exterior del anillo (m)', min_value=0.05, value=1.20, step=0.05, key='compost_radio_out')
                profundidad = 20.0  # Profundidad fija de evaluación (0–20 cm)
                with st.expander('⚙️ Parámetros técnicos y supuestos editables', expanded=False):
                    p1, p2, p3 = st.columns(3)
                    carbono_poda = p1.number_input('Carbono anual de poda (t C/ha/año)', min_value=0.0, value=3.45, step=0.05, key='compost_carbono_poda')
                    retencion_poda = p2.number_input('Estabilización estimada de poda (%)', min_value=0.0, max_value=100.0, value=20.0, step=5.0, key='compost_retencion_poda')
                    residuos_anillo = p3.number_input('Poda depositada en anillos (%)', min_value=0.0, max_value=100.0, value=100.0, step=5.0, key='compost_residuos_anillo')
                    p4, p5, p6 = st.columns(3)
                    mo_compost = p4.number_input('M.O. del compost (%)', min_value=0.1, max_value=100.0, value=30.0, step=1.0, key='compost_mo_producto')
                    retencion_compost = p5.number_input('Estabilización estimada del compost (%)', min_value=0.0, max_value=100.0, value=20.0, step=5.0, key='compost_retencion_producto')
                    humedad_compost = p6.number_input('Humedad del compost (%)', min_value=0.0, max_value=99.0, value=25.0, step=1.0, key='compost_humedad')
                    base_mo = st.radio('Base de la M.O. declarada en etiqueta', ['Producto tal como se vende (base húmeda)', 'Materia seca (base seca)'], horizontal=True, key='compost_base_mo')
                    st.caption('La etiqueta comercial declara 20–40 % de M.O. y 15–35 % de humedad. Verificar base con el proveedor. Los coeficientes del 20 % son supuestos provisionales, no tasas medidas en Leoncio Prado.')
                kg_compost_ha_anual = dosis_compost * plantas_compost
                kg_compost_parcela_anual = kg_compost_ha_anual * area_compost
                r1, r2 = st.columns(2)
                r1.metric('Compost anual por hectárea', f'{kg_compost_ha_anual:,.0f} kg')
                r2.metric('Sacos de compost al año (parcela)', f'{math.ceil(kg_compost_parcela_anual/saco_compost):,}')
                if dap_compost is None or dap_compost <= 0:
                    st.warning('Para proyectar el cambio porcentual de M.O., ingrese la densidad aparente medida en el análisis. La cantidad de compost y los sacos sí pueden calcularse sin ella.')
                elif radio_out <= radio_in:
                    st.error('El radio exterior debe superar el radio interior.')
                else:
                    area_anillo_planta = math.pi * (radio_out**2 - radio_in**2)
                    area_anillos_ha = area_anillo_planta * plantas_compost
                    if area_anillos_ha > 10000:
                        st.error('Los anillos suman más de 1 ha; revise los radios o la densidad de plantas.')
                    else:
                        masa_suelo_ha = area_anillos_ha * profundidad / 100 * dap_compost * 1000
                        fraccion_mo = mo_compost / 100
                        if base_mo.startswith('Materia seca'):
                            fraccion_mo *= (1 - humedad_compost / 100)
                        aporte_compost_anual = kg_compost_ha_anual * fraccion_mo * retencion_compost / 100
                        aporte_poda_anual = carbono_poda * 1000 * 1.724 * retencion_poda / 100 * residuos_anillo / 100
                        aporte_total_anual = aporte_compost_anual + aporte_poda_anual
                        incremento_anual = 100 * aporte_total_anual / masa_suelo_ha
                        incremento_horizonte = incremento_anual * anios_mo
                        mo_proyectada = mo_val + incremento_horizonte
                        st.caption(f'Anillos: {area_anillo_planta:.3f} m²/planta · {area_anillos_ha:,.1f} m²/ha de plantación · Profundidad 0–{profundidad:g} cm · DAP {dap_compost:g} g/cm³.')
                        st.dataframe(pd.DataFrame([
                            {'Concepto':'Aporte estimado de compost por año','Aporte de M.O. (kg/ha/año)':round(aporte_compost_anual,1),'Aumento estimado de M.O. (puntos %/año)':f'{100*aporte_compost_anual/masa_suelo_ha:.4f}'},
                            {'Concepto':'Aporte estimado de poda por año','Aporte de M.O. (kg/ha/año)':round(aporte_poda_anual,1),'Aumento estimado de M.O. (puntos %/año)':f'{100*aporte_poda_anual/masa_suelo_ha:.4f}'},
                            {'Concepto':'TOTAL anual (compost + poda)','Aporte de M.O. (kg/ha/año)':round(aporte_total_anual,1),'Aumento estimado de M.O. (puntos %/año)':f'{mo_val:.2f} + {incremento_anual:.4f} = {mo_val + incremento_anual:.2f} %'},
                        ]), hide_index=True, use_container_width=True)
                        a, b, c = st.columns(3)
                        a.metric('M.O. inicial', f'{mo_val:.3f} %')
                        b.metric(f'Aumento teórico ({anios_mo} año/s)', f'+{incremento_horizonte:.3f} puntos %')
                        c.metric('M.O. proyectada (sin pérdidas)', f'{mo_proyectada:.3f} %')
                        st.caption(f'Compost acumulado en {anios_mo} año(s): {kg_compost_parcela_anual*anios_mo:,.0f} kg/parcela. Se supone la misma dosis y el mismo aporte de poda cada año.')
                        st.warning('IMPORTANTE: esta cifra es un escenario de aportes acumulados, NO una predicción validada del análisis de suelo. No descuenta mineralización de la M.O. preexistente ni pérdidas posteriores del carbono añadido; tampoco demuestra que todo el carbono de poda se incorpore a 0–20 cm. La M.O. real podría aumentar menos, mantenerse o disminuir. Verificar con análisis anuales de suelo.')
                        st.caption('Poda: referencia exploratoria de Schneidewind et al. (2019), Bolivia. Conversión C→M.O.: factor convencional 1.724. Estabilizaciones de 20 %: supuestos editables sin validación local. Compost: composición declarada en etiqueta DEVIDA.')
                        st.markdown('**🌿 Beneficios potenciales del incremento de materia orgánica**')
                        st.markdown('''- **CIC:** puede mejorar la capacidad del suelo para retener nutrientes.
- **Nitrógeno:** aumenta potencialmente la reserva orgánica; su disponibilidad depende de la mineralización.
- **Fósforo, potasio, calcio y magnesio:** puede favorecer su reciclaje o retención, según el suelo.
- **Aluminio:** los compuestos orgánicos pueden disminuir su toxicidad, sin garantizar una reducción de la saturación de Al.
- **Estructura y agua:** puede favorecer la agregación, la infiltración y la retención de humedad.''')
                        st.caption('Estos beneficios son posibles, no aumentos cuantificados ni garantizados. SIFERT no modifica automáticamente CIC, N, P, K, pH ni saturación de Al; se requieren nuevos análisis para comprobar cambios.')
            st.info('El compost registrado se considera una sola vez en el balance NPK, utilizando composición y disponibilidad anuales estimadas y editables en la sección de fertilización.')

            st.subheader('6. Balance nutricional NPK · simulación técnica preliminar')
            st.warning('Cálculos exploratorios basados en los coeficientes del ejemplo INIA 2025 discutidos durante el desarrollo. NO constituyen una recomendación agronómica validada. Verificar método de extracción de P, calibración local y demanda por edad y manejo de cáscaras antes de aplicar.')
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
                demanda = {'N': 70*rendimiento/1000, 'P₂O₅': 16*rendimiento/1000, 'K₂O': 90*rendimiento/1000}
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
                st.caption('La estimación de oferta del suelo no es una medición de absorción anual. El modelo de demanda escala linealmente con rendimiento y no incorpora aún una calibración independiente por edad ni cáscaras.')

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
                st.caption('Biblioteca de 19 productos, sin duplicar el compost del módulo de materia orgánica. Las enmiendas se evalúan por separado.')
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
                    and any(v[k] > 0 for k in ('N','P₂O₅','K₂O'))}
                organicos = [x for x,v in minerales.items() if v['tipo'] == 'Org']
                with st.expander('🌿 Composición y disponibilidad estimada de nutrientes orgánicos (editar)', expanded=False):
                    st.caption('Valores de simulación: sustituir por análisis del producto cuando exista. Los porcentajes de disponibilidad no son mediciones del lote.')
                    co_n,co_p,co_k=st.columns(3)
                    org_n=co_n.number_input('Disponibilidad anual N orgánico (%)',0,100,30,5,key='org_dispon_n')/100
                    org_p=co_p.number_input('Disponibilidad anual P₂O₅ orgánico (%)',0,100,30,5,key='org_dispon_p')/100
                    org_k=co_k.number_input('Disponibilidad anual K₂O orgánico (%)',0,100,70,5,key='org_dispon_k')/100
                    st.info('Nota técnica: Coeficientes referenciales de disponibilidad anual para simulación. El INIA reconoce la liberación gradual de nutrientes del compost; sin embargo, los porcentajes específicos de N (30 %), P₂O₅ (30 %) y K₂O (70 %) no han sido validados para el compost utilizado por DEVIDA. Los valores son editables.')
                    st.markdown('**Compost registrado en el módulo de materia orgánica**')
                    st.caption('Etiqueta del compost: N 0.3–1.5 %, P 0.1–1.0 % y K 0.3–1.0 % (elementales). Valores iniciales dentro de esos rangos; edítelos según el análisis del lote. No son porcentajes garantizados de disponibilidad.')
                    c1,c2,c3=st.columns(3)
                    comp_n=c1.number_input('N elemental del compost (%)',0.0,20.0,0.9,0.1,key='compost_n_v67')/100
                    comp_p=c2.number_input('P elemental del compost (%)',0.0,20.0,0.55,0.05,key='compost_p_v67')/100*2.291
                    comp_k=c3.number_input('K elemental del compost (%)',0.0,20.0,0.65,0.05,key='compost_k_v67')/100*1.205
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
                compost_aprovechable={k:compost_total[k]*f for k,f in [('N',org_n),('P₂O₅',org_p),('K₂O',org_k)]}
                st.caption(f'Compost del módulo anterior: {compost_kg_ha:,.2f} kg/ha/año. Aporte estimado disponible: N {compost_aprovechable["N"]:.2f}, P₂O₅ {compost_aprovechable["P₂O₅"]:.2f}, K₂O {compost_aprovechable["K₂O"]:.2f} kg/ha/año.')
                st.caption('Compost: el aporte aprovechable se descuenta una sola vez del requerimiento del cultivo. La etiqueta declara N, P y K elementales; P y K se convierten a P₂O₅ y K₂O para compararlos con los fertilizantes. Valores referenciales sujetos a análisis, humedad y mineralización.')
                st.markdown('**Balance NPK: suelo, compost y cáscaras**')
                st.markdown('**Enmienda realmente aplicada (Ca y Mg)**')
                st.caption('Solo se contabiliza una enmienda cuando se confirma su aplicación. No se descuenta por una dosis meramente simulada o recomendada.')
                enm_aplicada=st.checkbox('Sí aplicó (cal o dolomita)', value=False, key='enm_aplicada_v72')
                enm_ca_kg_ha=0.0
                enm_mg_kg_ha=0.0
                if enm_aplicada:
                    if kg_ha_encalado_calculado is None:
                        st.warning('No se pudo calcular la dosis de encalado. Revise los datos de suelo del módulo anterior.')
                    else:
                        tipo_enm='Dolomita' if producto_enc.startswith('Dolomita') else 'Cal agrícola'
                        st.write(f'**Enmienda declarada como aplicada:** {tipo_enm} · **Dosis calculada:** {kg_ha_encalado_calculado:,.2f} kg/ha')
                        if tipo_enm == 'Dolomita':
                            ca_teorico=kg_ha_encalado_calculado*0.30*(40.078/56.077)
                            mg_teorico=kg_ha_encalado_calculado*0.215*(24.305/40.304)
                            st.caption(f'Aporte químico teórico: Ca {ca_teorico:.2f} kg/ha; Mg {mg_teorico:.2f} kg/ha (sin coeficiente de disponibilidad). Composición referencial: CaO 30 %, MgO 21.5 %.')
                        else:
                            st.caption('Para la cal agrícola no se cuantifica Ca/Mg sin análisis de composición del producto.')
                        st.info('El aporte teórico no se descuenta del balance de Ca/Mg: falta un coeficiente sustentado de incorporación a la fracción intercambiable. La casilla confirma aplicación, no disponibilidad.')
                # El aporte teórico no se equipara con un incremento de Ca/Mg intercambiables.
                # Por ello, hasta contar con un coeficiente validado, no se descuenta Ca/Mg.
                # Ca/Mg: objetivo de concentración intercambiable del suelo, no extracción anual.
                # La enmienda se descuenta solo cuando se confirma aplicación y se especifica su composición.
                masa_suelo=masa
                # Reciclaje potencial de cáscaras por t de cacao seco; NO se confunde con disponibilidad anual.
                factor_cascaras = 0.0
                if fila_parcela is not None:
                    manejo_actual = str(fila_parcela.get('manejo_cascaras') or '')
                    if manejo_actual == 'Permanecen en la parcela':
                        factor_cascaras = 1.0
                    elif manejo_actual == 'Retiro parcial':
                        retiro_actual = fila_parcela.get('retiro_pct')
                        factor_cascaras = max(0.0, 1.0 - float(retiro_actual)/100.0) if pd.notna(retiro_actual) else 0.0
                potencial_cascaras = {k: rendimiento/1000.0 * coef * factor_cascaras
                                      for k,coef in {'N':2.0,'P₂O₅':5.0,'K₂O':24.0}.items()}
                st.caption('Cáscaras: reciclaje POTENCIAL estimado por tonelada de cacao seco (N 2, P₂O₅ 5, K₂O 24 kg/t), proporcional a la fracción que permanece. No se descuenta del déficit efectivo sin coeficiente de liberación validado.')
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
                        'Cáscaras: aporte potencial (kg/ha)':round(potencial_cascaras[nutr],2),
                        'Necesidad restante / diferencia (kg/ha)':round(restante,2) if restante is not None else 'No calculable'})
                st.dataframe(pd.DataFrame(resumen_descuento),hide_index=True,use_container_width=True)
                st.caption('Balance NPK: el compost se descuenta una sola vez. Las cáscaras se muestran como aporte potencial, sin descuento efectivo hasta validar su liberación. El encalado se presenta por separado.')
                st.markdown('**Fertilizantes seleccionados y balance nutricional**')
                st.caption('Ingrese la presentación y el número de sacos. Al terminar, pulse «Actualizar cálculo de fertilizantes» para aplicar los cambios sin recálculos por cada clic.')
                # Entradas nativas: cada fertilizante conserva sus propios valores en session_state.
                # Evita que st.data_editor reinicie ediciones al reconstruir el DataFrame.
                plan={}
                presentaciones={}
                if fuentes:
                    # Los controles dentro del formulario no disparan un rerun por cada +/-.
                    # Al confirmar se actualizan juntos el balance, las compras y el PDF.
                    with st.form('form_fertilizantes_v98', clear_on_submit=False):
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
                        confirmar_fertilizantes=st.form_submit_button('🔄 Actualizar cálculo de fertilizantes',type='primary',use_container_width=True)
                    # Durante otros reruns conservar el último plan confirmado,
                    # para que la tabla y el PDF no reflejen cambios sin confirmar.
                    if confirmar_fertilizantes:
                        st.session_state['plan_confirmado_v98']=dict(plan)
                        st.session_state['presentaciones_confirmadas_v98']=dict(presentaciones)
                    plan_guardado=st.session_state.get('plan_confirmado_v98',{})
                    pesos_guardados=st.session_state.get('presentaciones_confirmadas_v98',{})
                    plan={x:float(plan_guardado.get(x,0.0)) for x in fuentes}
                    presentaciones={x:float(pesos_guardados.get(x,50.0)) for x in fuentes}
                    st.markdown(f'**TOTAL DE FERTILIZANTES CONFIRMADOS: {sum(plan.values()):,.2f} kg**')
                    if not confirmar_fertilizantes and not plan_guardado:
                        st.info('Después de ingresar los sacos, pulse «Actualizar cálculo de fertilizantes» para ver el balance y el PDF actualizados.')
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
                    tolerancia=max(0.1,objetivo_comercial*0.01)
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
                # Distribución operativa: 50 %, 30 %, 20 % por producto.
                filas_detalle=[]
                for x in usados:
                    total=plan[x]
                    a,b,c=total*0.50,total*0.30,total*0.20
                    filas_detalle.append((x,total,a,b,c))
                for nombre,a,b,c in micro_ref:
                    if nombre in usados: continue
                    total_micro=(a+b+c)*area_real
                    filas_detalle.append((nombre,total_micro,total_micro*0.50,total_micro*0.30,total_micro*0.20))
                st.warning('Microelementos y sulfato de magnesio: dosis referenciales, no derivadas del análisis. Confirmar necesidad antes de aplicar, especialmente Cu y B.')
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
                st.caption('Distribución operativa 50 % / 30 % / 20 % para cada producto. Validar dosis, compatibilidad y necesidades específicas de micronutrientes antes de aplicar.')
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
        st.markdown('''**Criterios internos, no editables desde la interfaz.** Las referencias y rangos proceden de la versión V4.2 suministrada. Los coeficientes son heterogéneos y necesitan validación antes de usarse como base de prescripción.\n\n- CaO y MgO: cuadro IFA (2008) para grano, datos de Camerún.\n- NPK: coeficientes orientativos heredados de V4.2; comprobar las fuentes originales.\n- Las cáscaras de mazorca, aunque se retiren, representan una exportación adicional.\n- Densidad aparente fija referencial: 1.33 g/cm³ (0–20 cm); no equivale a medición de laboratorio.\n\n**Para guardar productor y análisis juntos, complete el formulario de la primera pestaña y pulse «Guardar productor y análisis».  Para persistencia en la nube configure PostgreSQL. No se exige inicio de sesión.**''')


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
