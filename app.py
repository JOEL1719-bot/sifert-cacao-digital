"""SIFERT CACAO DIGITAL V5.0 · AVANCE — interfaz única para agricultor y técnico.
No emite prescripciones de fertilización sin calibración agronómica local.
"""
import streamlit as st
import pandas as pd

st.set_page_config(page_title='SIFERT CACAO DIGITAL', page_icon='🌱', layout='wide')
st.title('🌱 SIFERT CACAO DIGITAL')
st.caption('V5.0 · RESPALDO DE AVANCE · Análisis de suelo y manejo nutricional del cacao')
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

    if calcular:
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
            st.subheader('4. Evaluación preliminar de cal agrícola o dolomita')
            st.caption('Selección orientativa basada en el esquema Ca/Mg proporcionado por el usuario. Sus rangos no están aún validados como criterio universal para cacao; la necesidad de encalar se evalúa aparte con el enfoque del INIA.')
            ca_val, mg_val = datos.get('ca'), datos.get('mg')
            relacion = ca_val / mg_val if ca_val is not None and mg_val is not None and mg_val > 0 else None
            if relacion is None:
                st.info('Para evaluar la relación Ca/Mg ingrese Ca y Mg intercambiables en las mismas unidades; Mg debe ser mayor que cero.')
            else:
                st.metric('Relación Ca/Mg', f'{relacion:.2f}:1')
                if 3 <= relacion < 4:
                    enmienda = 'Cal agrícola (orientativa)'
                elif 4 <= relacion <= 7:
                    enmienda = 'Dolomita (orientativa)'
                elif 7 < relacion <= 12:
                    enmienda = 'Dolomita; revisar aporte adicional de Mg (orientativo)'
                else:
                    enmienda = 'Fuera de los rangos de la lámina; requiere revisión técnica'
                st.info(f'**Selección preliminar según la lámina:** {enmienda}. La relación Ca/Mg sola no determina la necesidad ni la dosis de encalado.')
            st.caption('Referencia de encalado: manual técnico INIA 2025 para café y cacao, capítulo 9. Objetivo de saturación de Al del ejemplo: 20 %. El método y sus factores para aplicación localizada deben contrastarse con el manual antes de prescribir dosis.')
            c_cal, c_dolo = st.columns(2)
            prnt_cal = c_cal.number_input('PRNT cal agrícola (%)', min_value=1.0, max_value=250.0, value=135.0, step=1.0, key='prnt_cal')
            prnt_dolo = c_dolo.number_input('PRNT dolomita (%) — referencial', min_value=1.0, max_value=250.0, value=94.0, step=1.0, key='prnt_dolo')
            plantas_encalado = int(fila_parcela['plantas_ha']) if fila_parcela is not None and pd.notna(fila_parcela['plantas_ha']) and fila_parcela['plantas_ha'] > 0 else 1100
            area_planta = 3.141592653589793 * 0.5**2
            area_tratada = area_planta * plantas_encalado
            st.caption(f'Aplicación superficial, radio fijo 0.50 m: {area_planta:.4f} m²/planta · {area_tratada:.2f} m²/ha · {area_tratada / 100:.2f} % de hectárea. Profundidad de referencia del análisis: 0–20 cm.')
            if datos.get('al') is not None and datos.get('cice') is not None and datos['cice'] > 0:
                exceso_al = max(0.0, datos['al'] - 0.20 * datos['cice'])
                st.caption(f'Exceso de Al sobre la meta teórica del 20 %: {exceso_al:.3f} cmol(+)/kg. No se traduce automáticamente en dosis comercial.')
            st.warning('Dosis de enmienda en kg/ha, g/planta y sacos: PENDIENTE de verificar la ecuación completa del INIA y su aplicabilidad a la aplicación superficial localizada. No aplicar una dosis basada solo en este cálculo preliminar.')
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

            st.subheader('6. Compost: aporte nutricional y recomendación de aplicación')
            st.caption('Composición referencial editable. Verifique los porcentajes y la base seca o húmeda del análisis de su compost; no constituye una dosis recomendada.')
            # Porcentajes de nutrientes totales estimados, expresados en forma de fertilizante.
            # No se conoce la base húmeda/seca ni la fracción liberada el primer año.
            col_n, col_p, col_k, col_saco = st.columns(4)
            compost_pct = {
                'N': col_n.number_input('N del compost (%)', min_value=0.0, max_value=100.0, value=0.90, step=0.05, key='compost_n'),
                'P₂O₅': col_p.number_input('P₂O₅ del compost (%)', min_value=0.0, max_value=100.0, value=1.26, step=0.05, key='compost_p'),
                'K₂O': col_k.number_input('K₂O del compost (%)', min_value=0.0, max_value=100.0, value=0.78, step=0.05, key='compost_k'),
            }
            peso_saco = col_saco.number_input('Peso del saco (kg)', min_value=1.0, value=50.0, step=1.0, key='compost_saco')
            cantidad_compost = st.number_input('Cantidad de compost para simulación (kg/ha)', min_value=0.0, value=1000.0, step=100.0, key='compost_cantidad')
            plantas_compost = int(fila_parcela['plantas_ha']) if fila_parcela is not None and pd.notna(fila_parcela['plantas_ha']) and fila_parcela['plantas_ha'] > 0 else 1100
            st.caption(f'Equivalencias: {cantidad_compost / plantas_compost:.2f} kg/planta · {cantidad_compost / peso_saco:.2f} sacos/ha. Es una simulación de cantidad ingresada, NO una dosis calculada por el sistema.')
            tabla_compost = []
            for nutriente, porcentaje in compost_pct.items():
                tabla_compost.append({
                    'Nutriente': nutriente,
                    'Contenido de referencia (%)': round(porcentaje, 3),
                    'Cantidad potencial por saco (kg)': round(peso_saco * porcentaje / 100, 3),
                    'Aporte total en simulación (kg/ha)': round(cantidad_compost * porcentaje / 100, 3),
                    'Aporte disponible el primer año': 'No determinado',
                })
            st.dataframe(pd.DataFrame(tabla_compost), hide_index=True, use_container_width=True)
            st.warning('Los aportes son contenidos totales teóricos, NO nutrientes disponibles en el primer año. Confirme la composición y si está expresada en base seca o húmeda; no se calcula una dosis agronómica.')
            st.markdown('**¿Qué falta para recomendar una dosis?** Validar la oferta anual de nutrientes del suelo según el método de suelo, los requerimientos completos del cultivo, la recuperación de fertilizantes, la liberación del compost y el aporte o retiro de las cáscaras.')

            st.subheader('7. ¿Cuánto compost y fertilizante debo aplicar?')
            st.info('Todavía no se puede calcular una dosis confiable únicamente con estos resultados. Falta validar la oferta anual del suelo, la recuperación de fertilizantes y la liberación del compost. SIFERT no inventará una receta.')
            st.caption('El análisis de suelo expresa concentraciones y reservas analíticas, no necesariamente suministro anual para el cacao. Si no se midió azufre, no se diagnostica su suficiencia.')
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
