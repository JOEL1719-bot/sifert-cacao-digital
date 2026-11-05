"""SIFERT CACAO DIGITAL V5.9 · AVANCE — interfaz única para agricultor y técnico.
No emite prescripciones de fertilización sin calibración agronómica local.
"""
import streamlit as st
import pandas as pd

st.set_page_config(page_title='SIFERT CACAO DIGITAL', page_icon='🌱', layout='wide')
st.title('🌱 SIFERT CACAO DIGITAL')
st.caption('V6.2 · AVANCE INTEGRADO · Diagnóstico y simulación de fertilización')
st.info('Ingrese los resultados de su análisis de suelo y la producción de cacao seco que desea alcanzar. No necesita modificar fórmulas.')

# Parámetros de referencia internos. Son bibliográficos, NO una calibración local
# ni equivalentes a demanda total o dosis de fertilización.
EXTRACCION_GRANO_KG_T = {'N': 22.0, 'P₂O₅': 6.87, 'K₂O': 10.8,
                          'CaO': 1.3, 'MgO': 5.3, 'S': 0.9}
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
    ('dap','Densidad aparente','g/cm³'), ('arena','Arena','%'),
    ('limo','Limo','%'), ('arcilla','Arcilla','%')]


# Biblioteca inicial recuperada de SIFERT V6 (26 entradas) + MOLIMAX 20-20-20.
# Valores porcentuales son los almacenados en V6; comprobar etiqueta antes de prescribir.
# Ca y Mg de V6 no se convierten automáticamente a CaO/MgO.
BIBLIOTECA_V6 = [('Urea (46-0-0)', 'N', 46, 0, 0, 0, 0, 0), ('Nitrato de amonio (33-0-0)', 'N', 33, 0, 0, 0, 0, 0), ('Fosfato diamónico (18-46-0)', 'P', 18, 46, 0, 0, 0, 0), ('Fosfato monoamónico (11-52-0)', 'P', 11, 52, 0, 0, 0, 0), ('Superfosfato triple (0-46-0 + 14% Ca)', 'P', 0, 46, 0, 14, 0, 0), ('NPK soluble (20-20-20)', 'P', 20, 20, 20, 0, 0, 0), ('Cloruro de potasio (0-0-60)', 'K', 0, 0, 60, 0, 0, 0), ('Nitrato de potasio (13-0-46)', 'K', 13, 0, 46, 0, 0, 0), ('Guano de isla (10-10-2; referencial)', 'Org', 10, 10, 2, 0, 0, 0), ('Compost (2-1-1.5; referencial)', 'Org', 2, 1, 1.5, 0, 0, 0), ('Gallinaza compostada (2.5-2.5-2; referencial)', 'Org', 2.5, 2.5, 2, 0, 0, 0), ('Humus de lombriz (1.5-1-1; referencial)', 'Org', 1.5, 1, 1, 0, 0, 0), ('Roca fosfórica (0-28-0 + 30% Ca; referencial)', 'Natural', 0, 28, 0, 30, 0, 0), ('Sulfato de potasio (0-0-50 + 18% S)', 'Natural', 0, 0, 50, 0, 0, 18), ('Sulfato de magnesio (0-0-0 + 9.6% Mg + 13% S)', 'Natural', 0, 0, 0, 0, 9.6, 13), ('Sulfato de potasio y magnesio (0-0-22 + 11% Mg + 22% S)', 'Natural', 0, 0, 22, 0, 11, 22), ('Sulfato de cobre (0-0-0; CuSO4·5H2O)', 'Micro', 0, 0, 0, 0, 0, 0), ('Sulfato de zinc (0-0-0; Zn)', 'Micro', 0, 0, 0, 0, 0, 0), ('Sulfato de manganeso (0-0-0; Mn)', 'Micro', 0, 0, 0, 0, 0, 0), ('Ulexita (0-0-0; 10–13% B)', 'Micro', 0, 0, 0, 0, 0, 0)]

# Ficha comercial ODINSU: los porcentajes de CaO/MgO y carbonatos son
# declaraciones en formas químicas distintas; no sumarlos. PRNT no acreditado.
FICHAS_ENMIENDAS = {
    'Dolomita ODINSU (cal agrícola local; CaO 28-32 %, MgO 20-23 %)': {
        'CaO_pct_rango': (28, 32), 'MgO_pct_rango': (20, 23),
        'CaCO3_pct_rango': (50, 56), 'MgCO3_pct_rango': (44, 48),
        'PRNT': None, 'fuente': 'Ficha comercial ODINSU identificada por el usuario',
        'observacion': 'PRNT sin verificar; no calcular dosis de encalado automáticamente.'
    }
}

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
    if v is None:
        return 'No determinado'
    if k == 'ph':
        if not 0 < v <= 14: return 'Revisar resultado'
        if v < 4.5: return 'Suelo ácido (técnicamente: extremadamente ácido)'
        if v < 5.5: return 'Fuertemente ácido'
        if v < 6.5: return 'Moderadamente ácido'
        if v <= 7.3: return 'Cercano a neutro'
        return 'Alcalino'
    if k == 'sat_al':
        if v > 100: return 'Revisar resultado'
        if v < 10: return 'Riesgo bajo (orientativo)'
        if v < 20: return 'Riesgo moderado (orientativo)'
        return 'Riesgo elevado (orientativo)'
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
            caserio TEXT, area_ha REAL, plantas_ha INTEGER, edad_anios REAL, manejo_cascaras TEXT, retiro_pct REAL, meta_kg_ha REAL, creado TEXT)''')
        cur.execute(f'''CREATE TABLE IF NOT EXISTS analisis (
            id {ident}, participante_id INTEGER NOT NULL, fecha TEXT NOT NULL,
            ph REAL, mo REAL, n REAL, p REAL, k2o REAL, k_cmol REAL,
            ca REAL, mg REAL, al REAL, h REAL, na REAL, cice REAL,
            sat_al REAL, ce REAL, dap REAL, arena REAL, limo REAL, arcilla REAL,
            textura TEXT, observaciones TEXT,
            FOREIGN KEY(participante_id) REFERENCES participantes(id))''')
        cur.execute(f'''CREATE TABLE IF NOT EXISTS aplicaciones (
            id {ident}, participante_id INTEGER NOT NULL, fecha TEXT NOT NULL,
            producto TEXT NOT NULL, tipo TEXT, numero INTEGER,
            dosis_recomendada REAL, dosis_real REAL, unidad TEXT,
            area_ha REAL, observaciones TEXT,
            FOREIGN KEY(participante_id) REFERENCES participantes(id))''')
        # Migración no destructiva para participantes existentes.
        nuevas = {'manejo_cascaras':'TEXT', 'retiro_pct':'REAL', 'meta_kg_ha':'REAL'}
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

secciones = st.tabs(['🏠 Inicio', '🌱 Evaluar suelo', '💾 Análisis guardados',
                     '📈 Comparación histórica', '🌿 Aplicaciones', '📥 Exportar / importar'])

with secciones[0]:
    st.subheader('1. Registrar participante y datos de la parcela')
    st.caption('Registre una sola vez al participante. Después seleccione su código en Evaluar suelo.')
    with st.form('nuevo_participante'):
        c1,c2,c3=st.columns(3)
        codigo=c1.text_input('Código único (evite DNI)')
        nombre=c2.text_input('Nombre o identificación interna')
        caserio=c3.text_input('Caserío')
        area=c1.number_input('Área (ha)', min_value=0.0, value=1.0)
        plantas=c2.number_input('Plantas por ha', min_value=1, value=1100)
        edad=c3.number_input('Edad del cacao (años)', min_value=0.0, value=5.0)
        meta=c1.number_input('Meta de cacao seco (kg/ha/año)', min_value=100.0, max_value=10000.0, value=1000.0, step=100.0)
        manejo=c2.selectbox('Manejo de cáscaras', ['Permanecen en la parcela','Se retiran completamente','Retiro parcial'])
        retiro=c3.number_input('Porcentaje retirado (%)', min_value=0.0, max_value=100.0, value=50.0, step=5.0) if manejo=='Retiro parcial' else (100.0 if manejo=='Se retiran completamente' else 0.0)
        crear=st.form_submit_button('Guardar participante')
    if crear:
        try:
            if not codigo.strip() or not nombre.strip():
                raise ValueError('Código y nombre son obligatorios.')
            execute('INSERT INTO participantes(codigo,nombre,caserio,area_ha,plantas_ha,edad_anios,manejo_cascaras,retiro_pct,meta_kg_ha,creado) VALUES (?,?,?,?,?,?,?,?,?,?)',
                    (codigo.strip(),nombre.strip(),caserio.strip(),area,plantas,edad,manejo,retiro,meta,date.today().isoformat()))
            st.success('Participante guardado.')
            st.rerun()
        except Exception as e:
            st.error(str(e))
    st.dataframe(participantes(), hide_index=True, use_container_width=True)


with secciones[1]:
    p_guardar = participantes()
    pid_guardar = elegir_participante(p_guardar, "elegir_para_evaluar", permitir_ninguno=True) if not p_guardar.empty else None
    # Al cambiar de productor, recuperar automáticamente su último análisis.
    # Los campos se actualizan ANTES de crear los widgets de Streamlit.
    anterior = st.session_state.get('_productor_evaluacion_anterior', '__inicial__')
    if anterior != pid_guardar:
        st.session_state['_productor_evaluacion_anterior'] = pid_guardar
        st.session_state.pop('evaluacion_pendiente', None)
        for clave in FIELD_KEYS:
            st.session_state['dato_' + clave] = ''
        st.session_state['rendimiento_evaluacion'] = 1000.0
        if pid_guardar is not None:
            ultimos = execute('SELECT * FROM analisis WHERE participante_id=? ORDER BY fecha DESC,id DESC LIMIT 1', (pid_guardar,), True)
            if not ultimos.empty:
                ultimo = ultimos.iloc[0]
                for clave in FIELD_KEYS:
                    v = ultimo[clave]
                    st.session_state['dato_' + clave] = f'{float(v):g}' if pd.notna(v) else ''
                st.session_state['_analisis_cargado'] = f"Último análisis cargado: {ultimo['fecha']} (registro {int(ultimo['id'])})"
            else:
                st.session_state['_analisis_cargado'] = 'Este participante todavía no tiene análisis guardados.'
            fila_meta = p_guardar[p_guardar['id'] == pid_guardar].iloc[0]
            if pd.notna(fila_meta['meta_kg_ha']):
                st.session_state['rendimiento_evaluacion'] = float(fila_meta['meta_kg_ha'])
        else:
            st.session_state['_analisis_cargado'] = ''

    fecha_guardar = st.date_input("Fecha del análisis", value=date.today(), key="fecha_evaluacion")
    st.caption("Seleccione un participante registrado para guardar el análisis; también puede evaluar sin guardar.")
    fila_parcela = p_guardar[p_guardar['id'] == pid_guardar].iloc[0] if pid_guardar is not None else None
    if fila_parcela is not None:
        st.caption(f"Parcela: {fila_parcela['plantas_ha'] or 1100} plantas/ha · Edad: {fila_parcela['edad_anios']} años · Cáscaras: {fila_parcela['manejo_cascaras'] or 'No registrado'} · Retiro: {fila_parcela['retiro_pct'] if pd.notna(fila_parcela['retiro_pct']) else 'No registrado'} %")
        if st.session_state.get('_analisis_cargado'):
            st.info(st.session_state['_analisis_cargado'])
        historico = execute('SELECT * FROM analisis WHERE participante_id=? ORDER BY fecha DESC,id DESC', (pid_guardar,), True)
        if not historico.empty:
            etiquetas = {f"{r['fecha']} · Análisis {int(r['id'])}": int(r['id']) for _, r in historico.iterrows()}
            elegido = st.selectbox('Cargar un análisis guardado', list(etiquetas), key='analisis_para_cargar')
            if st.button('📂 Cargar análisis seleccionado', key='boton_cargar_analisis'):
                registro = historico[historico['id'] == etiquetas[elegido]].iloc[0]
                for clave in FIELD_KEYS:
                    valor = registro[clave]
                    st.session_state['dato_' + clave] = f'{float(valor):g}' if pd.notna(valor) else ''
                st.session_state.pop('evaluacion_pendiente', None)
                st.session_state['_analisis_cargado'] = f"Análisis cargado: {registro['fecha']} (registro {int(registro['id'])})"
                st.rerun()
        else:
            st.caption('Ingrese los resultados del primer análisis de este participante.')
    with st.form('evaluacion'):
        st.subheader('1. ¿Cuánto cacao seco desea producir?')
        rendimiento = st.number_input('Producción esperada (kg de grano seco por hectárea y año)',
                                      min_value=100.0, max_value=10000.0, step=100.0, key='rendimiento_evaluacion')
        st.subheader('2. Copie los valores de su análisis de suelo')
        st.caption('Si el laboratorio no midió un indicador, déjelo vacío. No coloque cero para representar un dato faltante.')
        datos_texto = {}
        for j in range(0, len(CAMPOS), 3):
            columnas = st.columns(3)
            for columna, (clave, nombre, unidad) in zip(columnas, CAMPOS[j:j+3]):
                datos_texto[clave] = columna.text_input(f'{nombre} ({unidad})' if unidad else nombre,
                                                       placeholder='No medido: dejar vacío', key='dato_'+clave)
        calcular = st.form_submit_button('🌱 Evaluar mi suelo', type='primary', use_container_width=True)

    if calcular or st.session_state.get('evaluacion_pendiente') is not None:
        try:
            datos = {clave: leer_numero(datos_texto[clave], nombre) for clave, nombre, _ in CAMPOS}
            for clave in ['mo','n','sat_al','arena','limo','arcilla']:
                if datos[clave] is not None and datos[clave] > 100:
                    raise ValueError(f'{clave}: el porcentaje no puede superar 100.')
            if datos['dap'] is not None and not (0 < datos['dap'] <= 2.5):
                raise ValueError('Densidad aparente: verifique que esté entre 0 y 2.5 g/cm³.')
            fracciones = [datos[k] for k in ['arena','limo','arcilla']]
            if all(v is not None for v in fracciones) and abs(sum(fracciones)-100)>2:
                st.warning('Arena + limo + arcilla no suman aproximadamente 100 %. Revise la transcripción.')
            st.session_state['evaluacion_pendiente'] = {'datos': datos.copy(), 'rendimiento': float(rendimiento)}
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
                              'Unidad':unidad, 'Interpretación orientativa':clasificar(clave, datos[clave])})
            textura = textura_usda(datos['arena'], datos['limo'], datos['arcilla'])
            if textura:
                tabla.append({'Indicador': 'Textura del suelo',
                              'Resultado': textura, 'Unidad': '',
                              'Interpretación orientativa': 'Clase textural USDA'})
            if tabla:
                st.dataframe(pd.DataFrame(tabla), hide_index=True, use_container_width=True)
            else:
                st.info('Ingrese resultados de suelo para mostrar el diagnóstico.')
            if datos['al'] is not None and datos['cice'] is not None and datos['cice'] > 0:
                sat_calculada = datos['al'] / datos['cice'] * 100
                if datos['sat_al'] is not None and abs(sat_calculada - datos['sat_al']) > 0.5:
                    st.warning(f'Compruebe la saturación de aluminio: Al/CICe × 100 = {sat_calculada:.2f} %, frente al {datos["sat_al"]:.2f} % ingresado. Verifique la metodología del laboratorio.')
            st.caption('Los umbrales son provisionales y requieren contrastarse con el método analítico del laboratorio y la calibración para cacao local.')
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
            if requiere_revision:
                st.warning('La acidez o saturación de aluminio justifican evaluar encalado mediante el método del INIA.')
                if ca_val is None or mg_val is None:
                    st.info('Faltan Ca y/o Mg para orientar el tipo de enmienda.')
                elif mg_val < 0.5 and (ca_val >= 3 or (relacion is not None and relacion > 4)):
                    st.info('**Producto orientativo: dolomita ODINSU**, por Mg bajo. Confirmar necesidad y aporte de Mg con análisis y ficha.')
                elif mg_val >= 1.0 and ca_val < 3:
                    st.info('**Producto orientativo: cal agrícola con bajo Mg**, si la ficha demuestra bajo aporte de Mg. La cal de Tarapoto también contiene Mg: verificar su composición.')
                else:
                    st.info('**Tipo de enmienda por confirmar:** evaluar concentraciones absolutas de Ca/Mg y composición real de ambas fuentes; no elegir por relación aislada.')
            elif ph_val is not None and sat_val is not None:
                st.success('Los indicadores ingresados no activan el criterio preliminar de revisión por acidez; no se recomienda encalado automático.')
            else:
                st.info('Faltan pH y/o saturación de aluminio para descartar necesidad de encalado.')
            st.caption('Referencia: enfoque de neutralización de Al intercambiable. Esta simulación estequiométrica NO equivale a una dosis de campo validada por INIA; verificar método y respuesta local antes de aplicar.')
            st.caption('Dolomita ODINSU: PRNT supuesto 108 %. Cal agrícola: PRNT supuesto 135 %. Valores elegidos para simulación, NO certificados de los lotes.')
            plantas_encalado = int(fila_parcela['plantas_ha']) if fila_parcela is not None and pd.notna(fila_parcela['plantas_ha']) and fila_parcela['plantas_ha'] > 0 else 1100
            area_encalado = float(fila_parcela['area_ha']) if fila_parcela is not None and pd.notna(fila_parcela['area_ha']) and fila_parcela['area_ha'] > 0 else 1.0
            import math
            st.markdown('**Simulación de dosis de encalado (revisar antes de aplicar)**')
            ec1, ec2, ec3 = st.columns(3)
            radio_int = ec1.number_input('Radio interior encalado (m)', min_value=0.0, value=0.80, step=0.05, key='encalado_radio_int')
            radio_ext = ec2.number_input('Radio exterior encalado (m)', min_value=0.05, value=1.20, step=0.05, key='encalado_radio_ext')
            prof_enc = ec3.number_input('Profundidad de suelo considerada (cm)', min_value=1.0, max_value=40.0, value=20.0, step=1.0, key='encalado_prof')
            e1, e2 = st.columns(2)
            producto_enc = e1.selectbox('Enmienda para simular', ['Dolomita ODINSU (PRNT 108 % supuesto)', 'Cal agrícola (PRNT 135 % supuesto)'], key='encalado_producto')
            sat_meta = e2.number_input('Meta ilustrativa de saturación de Al (%)', min_value=0.0, max_value=40.0, value=20.0, step=1.0, key='encalado_meta_al')
            prnt = 1.08 if producto_enc.startswith('Dolomita') else 1.35
            if relacion is not None:
                st.info(f'Relación Ca/Mg obligatoria: {relacion:.2f}:1. La selección debe considerar también Mg absoluto, Ca absoluto y necesidad de encalado.')
            if radio_ext <= radio_int:
                st.error('El radio exterior debe superar el radio interior.')
            elif any(datos.get(k) is None for k in ('al','cice','dap','ca','mg')) or datos['cice'] <= 0 or datos['dap'] <= 0 or relacion is None:
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
                    kg_parcela = kg_ha * area_encalado
                    g_planta = kg_ha * 1000 / plantas_encalado
                    sacos = math.ceil(kg_parcela / 50)
                    st.dataframe(pd.DataFrame([{'Producto':producto_enc, 'Ca/Mg':round(relacion,2), 'Exceso Al (cmol(+)/kg)':round(exceso_al,3), 'kg/ha':round(kg_ha,2), 'kg/parcela':round(kg_parcela,2), 'g/planta':round(g_planta,1), 'Sacos de 50 kg':sacos}]), hide_index=True, use_container_width=True)
                    st.caption(f'Área tratada: {area_ha:,.1f} m²/ha. Masa de suelo: {masa_suelo:,.0f} kg/ha. Equivalente CaCO₃: {kg_equiv:,.1f} kg/ha. Ajuste por PRNT supuesto: {prnt:.2f}.')
                    st.warning('RESULTADO SOLO DE SIMULACIÓN: neutralización estequiométrica de exceso de Al, no una recomendación de aplicación de campo validada por INIA. La neutralización real depende de acidez de reserva, reactividad, incorporación superficial, condiciones de suelo y calidad de la enmienda. No comprar ni aplicar basándose únicamente en esta cifra.')
            st.subheader('4. Nutrientes extraídos por la cosecha de cacao')
            st.caption('Extracción estimada por grano seco. El efecto de las cáscaras se registra, pero aún no se cuantifica sin un coeficiente de biomasa validado.')
            extraccion = pd.DataFrame([{'Macronutriente': nutriente,
                                        'Exportación estimada en grano (kg/ha/año)': round(rendimiento*coef/1000, 2)}
                                       for nutriente, coef in EXTRACCION_GRANO_KG_T.items()])
            st.dataframe(extraccion, hide_index=True, use_container_width=True)
            st.caption('Coeficientes bibliográficos orientativos de V4.2 (N 22; P₂O₅ 6.87; K₂O 10.8; CaO 1.3; MgO 5.3; S 0.9 kg/t). No validados localmente. Las cáscaras retiradas exportan nutrientes adicionales que aquí no se cuantifican.')
            if fila_parcela is not None:
                st.info(f"Manejo de cáscaras registrado: {fila_parcela['manejo_cascaras'] or 'No definido'}. La extracción adicional por cáscaras y el crecimiento vegetativo aún están pendientes de validación; no se asignan dosis.")
            st.subheader('5. Contenido analítico del suelo y aporte anual')
            st.caption('Se utilizan directamente los resultados de suelo ingresados arriba. El contenido analítico de la capa 0–20 cm no es equivalente al suministro anual aprovechable por las raíces.')
            dap = datos.get('dap')
            if dap is None or dap <= 0:
                st.info('Para convertir las concentraciones a kg/ha, ingrese la densidad aparente (DAP) medida en el análisis de suelo. No se asigna una DAP supuesta.')
            else:
                masa = 10000 * 0.20 * dap * 1000
                st.metric('Masa estimada de suelo, 0–20 cm (kg/ha)', f'{masa:,.0f}')
                st.caption(f'10 000 m²/ha × 0.20 m × {dap:.3f} t/m³ × 1 000 = {masa:,.0f} kg/ha.')
                # ppm = mg/kg. Los cationes se convierten por peso equivalente;
                # P extraíble y bases intercambiables NO son nutrientes totales.
                conversiones = [
                    ('N total', 'n', 'N', lambda v: masa * v / 100, 'Reserva de N total; no es N disponible al año'),
                    ('P extraíble', 'p', 'P₂O₅', lambda v: masa * v / 1e6 * 2.291, 'P extraíble expresado como P₂O₅; no es P total'),
                    ('K intercambiable', 'k_cmol', 'K₂O', lambda v: masa * v * 391 / 1e6 * 1.205, 'K intercambiable expresado como K₂O'),
                    ('Ca intercambiable', 'ca', 'CaO', lambda v: masa * v * 200.4 / 1e6 * 1.399, 'Ca intercambiable expresado como CaO'),
                    ('Mg intercambiable', 'mg', 'MgO', lambda v: masa * v * 121.5 / 1e6 * 1.658, 'Mg intercambiable expresado como MgO'),
                ]
                filas_contenido = []
                for nombre, clave, oxido, convertir, alcance in conversiones:
                    v = datos.get(clave)
                    filas_contenido.append({
                        'Indicador de suelo': nombre,
                        'Expresado como': oxido,
                        'Contenido analítico (kg/ha)': round(convertir(v), 2) if v is not None else 'No medido',
                        'Aporte anual aprovechable (kg/ha/año)': 'No determinado',
                        'Alcance': alcance,
                    })
                st.dataframe(pd.DataFrame(filas_contenido), hide_index=True, use_container_width=True)
                k2o_ppm = datos.get('k2o')
                if k2o_ppm is not None:
                    st.caption(f'K₂O reportado directamente por de suelo: {masa * k2o_ppm / 1e6:.2f} kg/ha de la fracción analizada (vía alternativa). No se suma al K intercambiable ni se multiplica nuevamente por 1.205.')
                st.caption('Los valores en kg/ha son conversiones del resultado analítico para 0–20 cm; no son reservas totales de P, K, Ca o Mg ni dosis de fertilizante. El azufre no se estima porque no se ingresó un análisis de S.')
            st.markdown('**¿Cuánto aporta el suelo durante el año?** Todavía no se puede determinar con confiabilidad a partir de estos resultados únicamente. Se requiere una relación calibrada entre los métodos de suelo, la dinámica del suelo y la absorción del cacao.')
            st.info('El déficit de fertilización no se calcula aún: también faltan la demanda completa del cultivo, las cáscaras retiradas y la eficiencia de los fertilizantes. No se deben restar directamente los kg/ha analíticos de la extracción del grano.')

            st.subheader('6. Compost y poda: proyección de materia orgánica')
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
                anios_mo = c2.selectbox('Horizonte de simulación (años)', [1, 2, 3, 4, 5], index=0, key='compost_anios_proyeccion')
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
                    mo_compost = p4.number_input('M.O. del compost DEVIDA (%)', min_value=0.1, max_value=100.0, value=30.0, step=1.0, key='compost_mo_producto')
                    retencion_compost = p5.number_input('Estabilización estimada del compost (%)', min_value=0.0, max_value=100.0, value=20.0, step=5.0, key='compost_retencion_producto')
                    humedad_compost = p6.number_input('Humedad del compost (%)', min_value=0.0, max_value=99.0, value=25.0, step=1.0, key='compost_humedad')
                    base_mo = st.radio('Base de la M.O. declarada en etiqueta', ['Producto tal como se vende (base húmeda)', 'Materia seca (base seca)'], horizontal=True, key='compost_base_mo')
                    st.caption('La etiqueta comercial declara 20–40 % de M.O. y 15–35 % de humedad. Verificar base con el proveedor. Los coeficientes del 20 % son supuestos provisionales, no tasas medidas en Leoncio Prado.')
                kg_compost_ha_anual = dosis_compost * plantas_compost
                kg_compost_parcela_anual = kg_compost_ha_anual * area_compost
                r1, r2, r3 = st.columns(3)
                r1.metric('Compost anual por hectárea', f'{kg_compost_ha_anual:,.0f} kg')
                r2.metric('Compost anual por parcela', f'{kg_compost_parcela_anual:,.0f} kg')
                r3.metric('Sacos de compost al año', f'{math.ceil(kg_compost_parcela_anual/saco_compost):,}')
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
                            {'Concepto':'Aporte estimado de compost por año','M.O. equivalente (kg/ha/año)':round(aporte_compost_anual,1),'Incremento teórico (puntos %/año)':round(100*aporte_compost_anual/masa_suelo_ha,4)},
                            {'Concepto':'Aporte estimado de poda por año','M.O. equivalente (kg/ha/año)':round(aporte_poda_anual,1),'Incremento teórico (puntos %/año)':round(100*aporte_poda_anual/masa_suelo_ha,4)},
                            {'Concepto':'TOTAL anual (compost + poda)','M.O. equivalente (kg/ha/año)':round(aporte_total_anual,1),'Incremento teórico (puntos %/año)':round(incremento_anual,4)},
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
            st.info('El compost no se suma automáticamente al balance mineral NPK; ello no significa que carezca de nutrientes.')

            st.subheader('7. Balance NPK · simulación técnica preliminar')
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
                st.dataframe(pd.DataFrame([{'Nutriente':nut, 'Demanda kg/ha':round(demanda[nut],2), 'Oferta estimada kg/ha':round(oferta[nut],2), 'Eficiencia fertilizante %':int(eficiencia[nut]*100), 'Necesidad mineral kg/ha':round(dosis[nut],2)} for nut in demanda]), hide_index=True, use_container_width=True)
                st.caption('La estimación de oferta del suelo no es una medición de absorción anual. El modelo de demanda escala linealmente con rendimiento y no incorpora aún una calibración independiente por edad ni cáscaras.')

                st.subheader('7A. Esquema DEVIDA: primer y segundo abonamiento')
                st.caption('Cantidades de referencia por hectárea, no deducidas del análisis de suelo. No son prescripción universal; revisar necesidad de B, Cu, Zn, Mg y Mn antes de aplicar.')
                micro_ref = [('Sulfato de cobre (0-0-0; CuSO4·5H2O)', 2., 0., 0.),
                             ('Sulfato de zinc (0-0-0; Zn)', 3., 0., 0.),
                             ('Sulfato de magnesio (0-0-0 + 9.6% Mg + 13% S)', 5., 0., 0.),
                             ('Sulfato de manganeso (0-0-0; Mn)', 1., 0., 0.),
                             ('Ulexita (0-0-0; 10–13% B)', 30., 20., 0.)]
                st.dataframe(pd.DataFrame([{'Producto':x,'1.º kg/ha':a,'2.º kg/ha':b,'3.º kg/ha':c,'Total kg/ha':a+b+c} for x,a,b,c in micro_ref]),hide_index=True,use_container_width=True)
                st.warning('El esquema DEVIDA se presenta como referencia separada del optimizador NPK. Especial precaución con cobre y boro: confirmar diagnóstico y concentración del producto antes de recomendar su aplicación.')
                st.subheader('8. Fertilización comercial y tres abonamientos')
                st.caption('Los objetivos NPK ya están ajustados por eficiencia (N 60 %, P₂O₅ 25 %, K₂O 70 %). No se vuelve a aplicar ese factor al convertir nutrientes a productos.')
                area_real = float(fila_parcela['area_ha']) if fila_parcela is not None and pd.notna(fila_parcela['area_ha']) and fila_parcela['area_ha'] > 0 else 1.0
                plantas = int(fila_parcela['plantas_ha']) if fila_parcela is not None and pd.notna(fila_parcela['plantas_ha']) and fila_parcela['plantas_ha'] > 0 else 1100
                total_plantas = area_real * plantas
                st.caption(f'Parcela: {area_real:g} ha · {plantas:,} plantas/ha · {total_plantas:,.0f} plantas estimadas.')
                catalogo = catalogo_v6()
                st.caption('Biblioteca depurada: 20 productos; 8 químicos y 12 orgánicos/minerales naturales (incluidos micronutrientes). Las enmiendas se evalúan por separado.')
                with st.expander('📚 Consultar biblioteca de 20 productos', expanded=False):
                    st.dataframe(pd.DataFrame([{'Producto':nombre,'Origen':clasificar_origen_producto(nombre, v['tipo']), 'N %':round(v['N']*100,2),
                        'P₂O₅ %':round(v['P₂O₅']*100,2),'K₂O %':round(v['K₂O']*100,2),
                        'Ca % (referencial)':v['Ca_reportado'],'Mg % (referencial)':v['Mg_reportado'],
                        'S % (referencial)':v['S_reportado']} for nombre,v in catalogo.items()]),
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
                modo = st.radio('Modalidad de fertilización',
                    ['Selección automática de fertilizantes', 'El agricultor elige sus fertilizantes'],
                    horizontal=True, key='modo_fertilizacion')
                # Admitir orgánicos con NPK declarado; excluir enmiendas y productos sin análisis.
                minerales = {x:v for x,v in catalogo.items()
                    if v['tipo'] not in ('Enm','Otro','Ca','Mg','Micro')
                    and any(v[k] > 0 for k in ('N','P₂O₅','K₂O'))}
                organicos = [x for x,v in minerales.items() if v['tipo'] == 'Org']
                st.caption('Los orgánicos con NPK declarado pueden seleccionarse. Sus nutrientes no son necesariamente disponibles de inmediato.')
                with st.expander('🌿 Disponibilidad anual estimada de nutrientes orgánicos (editar)', expanded=False):
                    st.warning('Porcentajes de simulación, NO validados para los productos locales. Verifique análisis del lote y mineralización. No confundir contenido total con aporte disponible.')
                    co_n, co_p, co_k = st.columns(3)
                    org_n = co_n.number_input('N orgánico disponible en el año (%)', min_value=0, max_value=100, value=30, step=5, key='org_dispon_n') / 100
                    org_p = co_p.number_input('P₂O₅ orgánico disponible en el año (%)', min_value=0, max_value=100, value=30, step=5, key='org_dispon_p') / 100
                    org_k = co_k.number_input('K₂O orgánico disponible en el año (%)', min_value=0, max_value=100, value=70, step=5, key='org_dispon_k') / 100
                # Para el balance anual usar fracciones estimadas; conservar catálogo original
                # para mostrar composición declarada y evitar afirmar disponibilidad total.
                minerales_efectivos = {x:dict(v) for x,v in minerales.items()}
                for x in organicos:
                    for nutriente, factor in [('N',org_n), ('P₂O₅',org_p), ('K₂O',org_k)]:
                        minerales_efectivos[x][nutriente] *= factor
                objetivo = {k:dosis[k]*area_real for k in ('N','P₂O₅','K₂O')}
                if modo.startswith('Selección automática'):
                    predefinidos = ['Fosfato monoamónico (11-52-0)','Urea (46-0-0)','Cloruro de potasio (0-0-60)']
                    fuentes = [x for x in predefinidos if x in minerales]
                    st.info('Modo automático: SIFERT selecciona MAP, urea y KCl como fuentes de referencia. Puede cambiar al modo agricultor para escoger otros productos.')
                else:
                    st.markdown('**Marque ✓ los fertilizantes que desea utilizar.** El resultado se actualiza automáticamente al marcar o desmarcar, sin pulsar Calcular.')
                    fuentes = []
                    cols = st.columns(2)
                    for col, titulo, tipos in [(cols[0], 'QUÍMICOS', ('N','P','K')), (cols[1], 'ORGÁNICOS / MINERALES NATURALES', ('Org','Natural'))]:
                        with col:
                            st.markdown('**' + titulo + '**')
                            for producto, comp in minerales.items():
                                if comp['tipo'] in tipos:
                                    if st.checkbox(producto, value=False, key=f'check_fuente_v62_{producto}'):
                                        fuentes.append(producto)
                    st.caption(f'✓ {len(fuentes)} producto(s) marcado(s). El balance NPK se recalcula automáticamente.')
                    st.caption('Puede marcar productos simples o compuestos. La participación de todos depende de la modalidad elegida abajo. Los orgánicos se calculan con disponibilidad anual provisional editable; las enmiendas y los productos sin NPK declarado no entran en este balance.')
                estrategia_manual = 'Permitir que SIFERT descarte los innecesarios'
                minimo_kg_planta = 0.01
                if modo.startswith('El agricultor') and fuentes:
                    estrategia_manual = st.radio(
                        '¿Cómo desea utilizar los fertilizantes seleccionados?',
                        ['Utilizar todos los fertilizantes seleccionados', 'Permitir que SIFERT descarte los innecesarios'],
                        key='estrategia_manual_v61', horizontal=False)
                    if estrategia_manual.startswith('Utilizar todos'):
                        st.caption('SIFERT asigna un mínimo técnico provisional de 10 g/planta/año por producto para simular su participación. No es dosis validada; revise excedentes.')
                if not fuentes:
                    st.warning('Seleccione al menos un fertilizante para calcular las cantidades.')
                else:
                    if modo.startswith('El agricultor') and estrategia_manual.startswith('Utilizar todos'):
                        minimo = minimo_kg_planta * total_plantas
                        base = {x: minimo for x in fuentes}
                        objetivo_pendiente = {k: max(0.0, objetivo[k] - sum(base[x]*minerales_efectivos[x][k] for x in fuentes)) for k in objetivo}
                        complemento, alerta = optimizar_fuentes(fuentes, minerales_efectivos, objetivo_pendiente)
                        plan = {x: base[x] + complemento[x] for x in fuentes}
                    else:
                        plan, alerta = optimizar_fuentes(fuentes, minerales_efectivos, objetivo)
                    if alerta:
                        st.error('No se pudo generar una mezcla NPK equilibrada: ' + alerta)
                        st.info('Marque una fuente que aporte los nutrientes faltantes; el cálculo acepta excedentes y los mostrará en la auditoría.')
                    else:
                        usados = [x for x in fuentes if plan[x] > 1e-7]
                        no_usados = [x for x in fuentes if plan[x] <= 1e-7]
                        if no_usados:
                            st.caption('Productos seleccionados que no se necesitan para la combinación de menor masa: ' + ', '.join(no_usados))
                        if modo.startswith('El agricultor') and estrategia_manual.startswith('Utilizar todos'):
                            st.info('Se asignó una cantidad mínima a cada fertilizante marcado. La mezcla puede presentar excedentes de NPK; el mínimo no constituye una recomendación de campo.')
                        else:
                            st.caption('El cálculo cubre los objetivos NPK con los productos marcados, minimizando primero los excedentes relativos y luego la masa. No optimiza costo, compatibilidad ni respuesta agronómica.')
                        st.markdown('**Productos seleccionados y cantidad calculada automáticamente**')
                        filas_comerciales = [{'Producto':x,
                            'Necesario kg/ha':round(plan[x]/area_real,2),
                            'Necesario kg/parcela':round(plan[x],2),
                            'Dosis g/planta/año':round(plan[x]*1000/total_plantas,1)} for x in usados]
                        st.dataframe(pd.DataFrame(filas_comerciales), hide_index=True, use_container_width=True)
                        st.caption('No se solicita inventario: el programa calcula directamente las cantidades a partir de las fuentes seleccionadas.')
                        aporte_plan = {k:sum(plan[x]*minerales_efectivos[x][k] for x in usados) for k in objetivo}
                        if any(x in organicos for x in usados):
                            st.warning('El aporte disponible de los fertilizantes orgánicos es hipotético y puede diferir del real. Si también se aplica compost en el módulo 6, evite contar dos veces el mismo producto.')
                            st.dataframe(pd.DataFrame([
                                {'Producto orgánico': x, 'Cantidad (kg)':round(plan[x],2),
                                 'N total declarado (kg)':round(plan[x]*minerales[x]['N'],2),
                                 'N disponible supuesto (kg)':round(plan[x]*minerales_efectivos[x]['N'],2),
                                 'P₂O₅ total declarado (kg)':round(plan[x]*minerales[x]['P₂O₅'],2),
                                 'P₂O₅ disponible supuesto (kg)':round(plan[x]*minerales_efectivos[x]['P₂O₅'],2),
                                 'K₂O total declarado (kg)':round(plan[x]*minerales[x]['K₂O'],2),
                                 'K₂O disponible supuesto (kg)':round(plan[x]*minerales_efectivos[x]['K₂O'],2)}
                                for x in usados if x in organicos]), hide_index=True, use_container_width=True)
                        st.markdown('**Auditoría NPK para la parcela**')
                        st.dataframe(pd.DataFrame([{'Nutriente':k,
                            'Objetivo kg':round(objetivo[k],3),
                            'Aporte calculado kg':round(aporte_plan[k],3),
                            'Diferencia kg':round(aporte_plan[k]-objetivo[k],4)}
                            for k in objetivo]), hide_index=True, use_container_width=True)
                        st.markdown('**Tres abonamientos: dosis TOTAL por planta**')
                        filas_aplicacion, etapas = distribuir_abonamientos(
                            {x:plan[x] for x in usados}, minerales_efectivos, objetivo, total_plantas)
                        st.dataframe(pd.DataFrame(filas_aplicacion), hide_index=True, use_container_width=True)
                        st.caption('Los fertilizantes con P₂O₅ se asignan al primer abonamiento; las demás fuentes se distribuyen en tercios. Esto conserva el total anual, pero no garantiza tercios exactos de N y K. Ajustar según fenología y compatibilidad de mezclas.')
                        n_primero = sum(kg*minerales_efectivos[x]['N'] for x,kg in etapas[0].items())
                        if n_primero > objetivo['N']/3 + 0.01:
                            st.warning('El primer abonamiento supera un tercio del N anual por los fertilizantes compuestos. Revisar la distribución antes de aplicar.')
                        if any(aporte_plan[k] > objetivo[k] * 1.20 + 0.01 for k in objetivo if objetivo[k] > 0):
                            st.error('Atención: al menos un nutriente supera en más del 20 % su objetivo. Esta simulación NO debe interpretarse como dosis de aplicación; ajuste el mínimo o cambie la combinación.')
                        if all(abs(aporte_plan[k]-objetivo[k]) < 0.01 for k in objetivo):
                            st.success('Auditoría matemática NPK: objetivos cubiertos sin excedentes relevantes.')
                        else:
                            excesos = [f'{k}: +{aporte_plan[k]-objetivo[k]:.2f} kg' for k in objetivo if aporte_plan[k] > objetivo[k]+0.01]
                            if excesos:
                                st.warning('La combinación cubre los objetivos, pero presenta excedentes: ' + '; '.join(excesos) + '. Revisar antes de aplicar.')
                        st.download_button('📥 Descargar ficha de fertilización (CSV)',
                            pd.DataFrame(filas_aplicacion).to_csv(index=False).encode('utf-8-sig'),
                            file_name='sifert_tres_abonamientos.csv', mime='text/csv',
                            key='descarga_abonamientos')
                        st.warning('Simulación técnica preliminar: no aplicar dosis sin validar los análisis, etiquetas, calibración local y compatibilidad física de productos.')
            st.caption('Encalado: la dosis permanece pendiente de validar el método INIA para aplicación localizada. CaO y MgO de las enmiendas se incorporarán solo con fichas técnicas verificadas.')
        except ValueError as e:
            st.session_state.pop('evaluacion_pendiente', None)
            st.error(str(e))

    # El botón permanece disponible tras el recálculo de Streamlit.
    # Se guarda exactamente el último análisis evaluado, no campos sin validar.
    pendiente = st.session_state.get('evaluacion_pendiente')
    if pendiente is not None:
        st.divider()
        st.subheader('💾 Guardar análisis de suelo')
        if pid_guardar is None:
            st.info('Para guardar este análisis, registre un participante en la pestaña Inicio y selecciónelo arriba. Puede evaluar sin guardar.')
        else:
            st.caption('Se guardarán los resultados de la última evaluación para el participante seleccionado y la fecha indicada. Compruebe ambos antes de continuar.')
            if st.button('💾 Guardar análisis de suelo', type='primary', key='guardar_evaluacion', use_container_width=True):
                try:
                    valores = pendiente['datos']
                    columnas = ['participante_id', 'fecha'] + FIELD_KEYS + ['textura', 'observaciones']
                    textura = textura_usda(valores['arena'], valores['limo'], valores['arcilla'])
                    params = [pid_guardar, fecha_guardar.isoformat()] + [valores[k] for k in FIELD_KEYS] + [textura, f"Producción esperada al evaluar: {pendiente['rendimiento']:g} kg/ha/año"]
                    execute(f"INSERT INTO analisis({','.join(columnas)}) VALUES ({','.join('?' for _ in columnas)})", params)
                    st.session_state.pop('evaluacion_pendiente', None)
                    st.success('Análisis de suelo guardado correctamente. Consúltelo en «Análisis guardados».')
                except Exception as e:
                    st.error(f'No se pudo guardar el análisis: {e}')

    with st.expander('Información técnica y fuentes de referencia'):
        st.markdown('''**Criterios internos, no editables desde la interfaz.** Las referencias y rangos proceden de la versión V4.2 suministrada. Los coeficientes son heterogéneos y necesitan validación antes de usarse como base de prescripción.\n\n- CaO y MgO: cuadro IFA (2008) para grano, datos de Camerún.\n- S: Malavolta et al. (1984), 0.9 g/kg de grano seco.\n- NPK: coeficientes orientativos heredados de V4.2; comprobar las fuentes originales.\n- Las cáscaras de mazorca, aunque se retiren, representan una exportación adicional.\n- No se presupone densidad aparente ni se convierte directamente inventario analítico en dosis.\n\n**Para guardar un análisis, evalúelo y pulse «Guardar análisis de suelo» después de seleccionar un participante. Para persistencia en la nube configure PostgreSQL. No se exige inicio de sesión.**''')


with secciones[2]:
    st.subheader('Consultar, editar y eliminar análisis de suelo')
    dfp=participantes()
    pid=elegir_participante(dfp, 'p_guardados')
    if pid is not None:
        df=execute('SELECT * FROM analisis WHERE participante_id=? ORDER BY fecha DESC,id DESC',(pid,),True)
        if df.empty:
            st.info('No hay análisis guardados para este participante.')
        else:
            st.dataframe(df, hide_index=True, use_container_width=True)
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
    st.subheader('Registro de aplicaciones reales')
    pid=elegir_participante(participantes(),'p_aplicaciones')
    if pid is not None:
        with st.form('aplicacion'):
            c1,c2,c3=st.columns(3)
            fecha=c1.date_input('Fecha de aplicación',value=date.today())
            tipo=c2.selectbox('Tipo',['Compost','Mineral','Enmienda','Otro'])
            producto=c3.text_input('Producto')
            numero=c1.number_input('N.º aplicación',min_value=1,value=1)
            unidad=c2.selectbox('Unidad',['g/planta','kg/planta','kg/ha'])
            dosis_real=c3.number_input('Dosis aplicada',min_value=0.0,value=0.0)
            area=c1.number_input('Área tratada (ha)',min_value=0.0,value=1.0)
            obs=st.text_area('Observaciones')
            guardar=st.form_submit_button('Guardar aplicación')
        if guardar:
            if not producto.strip():
                st.error('Indique el producto aplicado.')
            else:
                execute('INSERT INTO aplicaciones(participante_id,fecha,producto,tipo,numero,dosis_real,unidad,area_ha,observaciones) VALUES (?,?,?,?,?,?,?,?,?)',
                        (pid,fecha.isoformat(),producto,tipo,numero,dosis_real,unidad,area,obs))
                st.success('Aplicación guardada.')
                st.rerun()
    st.dataframe(execute('SELECT * FROM aplicaciones ORDER BY fecha DESC,id DESC',fetch=True),hide_index=True,use_container_width=True)

with secciones[5]:
    st.subheader('Exportar respaldos')
    for nombre in ['participantes','analisis','aplicaciones']:
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
