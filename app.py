"""SIFERT CACAO DIGITAL V4.7 — interfaz única para agricultor y técnico.
No emite prescripciones de fertilización sin calibración agronómica local.
"""
import streamlit as st
import pandas as pd

st.set_page_config(page_title='SIFERT CACAO DIGITAL', page_icon='🌱', layout='wide')
st.title('🌱 SIFERT CACAO DIGITAL')
st.caption('V4.7 · Evaluación sencilla del análisis de suelo para cacao · Alto Huallaga')
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
            caserio TEXT, area_ha REAL, plantas_ha INTEGER, edad_anios REAL, creado TEXT)''')
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
        st.info('Registre primero un participante en la pestaña Participantes.')
        return None
    opciones = {f"{r['codigo']} · {r['nombre']}": int(r['id']) for _, r in df.iterrows()}
    if permitir_ninguno:
        opciones = {'Solo evaluar (sin guardar)': None, **opciones}
    return opciones[st.selectbox('Participante', list(opciones), key=key)]

secciones = st.tabs(['🌱 Evaluar suelo', '👥 Participantes', '💾 Análisis guardados',
                     '📈 Comparación histórica', '🌿 Aplicaciones', '📥 Exportar / importar'])

with secciones[0]:
    p_guardar = participantes()
    pid_guardar = elegir_participante(p_guardar, "elegir_para_evaluar", permitir_ninguno=True) if not p_guardar.empty else None
    fecha_guardar = st.date_input("Fecha del análisis", value=date.today(), key="fecha_evaluacion")
    st.caption("Seleccione un participante registrado para guardar el análisis; también puede evaluar sin guardar.")
    with st.form('evaluacion'):
        st.subheader('1. ¿Cuánto cacao seco desea producir?')
        rendimiento = st.number_input('Producción esperada (kg de grano seco por hectárea y año)',
                                      min_value=100.0, max_value=10000.0, value=1000.0, step=100.0)
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
            st.subheader('4. Nutrientes extraídos por la cosecha de cacao')
            st.caption('Estimación de nutrientes que salen de la parcela al cosechar y vender el grano seco. No equivale a cuánto fertilizante debe aplicar; tampoco incluye las cáscaras retiradas.')
            extraccion = pd.DataFrame([{'Macronutriente': nutriente,
                                        'Exportación estimada en grano (kg/ha/año)': round(rendimiento*coef/1000, 2)}
                                       for nutriente, coef in EXTRACCION_GRANO_KG_T.items()])
            st.dataframe(extraccion, hide_index=True, use_container_width=True)
            st.caption('Coeficientes bibliográficos orientativos de V4.2 (N 22; P₂O₅ 6.87; K₂O 10.8; CaO 1.3; MgO 5.3; S 0.9 kg/t). No validados localmente. Las cáscaras retiradas exportan nutrientes adicionales que aquí no se cuantifican.')
            st.subheader('5. Balance nutricional preliminar')
            st.caption('Se contrasta la extracción estimada del grano con la información que aún falta para conocer la oferta anual del suelo. No se calcula un déficit numérico sin esa oferta.')
            balance = []
            for nutriente, coef in EXTRACCION_GRANO_KG_T.items():
                balance.append({
                    'Nutriente': nutriente,
                    'Salida por grano (kg/ha/año)': round(rendimiento * coef / 1000, 2),
                    'Aporte anual del suelo (kg/ha/año)': 'No determinado',
                    'Déficit real (kg/ha/año)': 'No calculable',
                })
            st.dataframe(pd.DataFrame(balance), hide_index=True, use_container_width=True)
            st.caption('Los resultados de UNAS permiten describir propiedades y concentraciones del suelo, pero no equivalen directamente al aporte anual absorbible. La exportación por cáscaras y la demanda de crecimiento tampoco están cuantificadas.')

            st.subheader('6. Compost GOVA SAC – DEVIDA: aporte potencial')
            st.caption('Composición de referencia calculada con puntos medios de la etiqueta del producto; no es una dosis recomendada.')
            # Porcentajes de nutrientes totales estimados, expresados en forma de fertilizante.
            # No se conoce la base húmeda/seca ni la fracción liberada el primer año.
            compost_pct = {'N': 0.90, 'P₂O₅': 0.55 * 2.291, 'K₂O': 0.65 * 1.205}
            tabla_compost = []
            for nutriente, porcentaje in compost_pct.items():
                tabla_compost.append({
                    'Nutriente': nutriente,
                    'Contenido de referencia (%)': round(porcentaje, 3),
                    'Cantidad potencial por saco de 50 kg (kg)': round(50 * porcentaje / 100, 3),
                    'Aporte disponible el primer año': 'No determinado',
                })
            st.dataframe(pd.DataFrame(tabla_compost), hide_index=True, use_container_width=True)
            st.warning('Los contenidos son valores medios referenciales, NO nutrientes disponibles en el primer año. La etiqueta no precisa si los porcentajes se expresan en base seca o húmeda; por ello no se calculan dosis ni equivalencias de sustitución con fertilizantes minerales.')
            st.markdown('**¿Qué falta para recomendar una dosis?** Validar la oferta anual de nutrientes del suelo según el método UNAS, los requerimientos completos del cultivo, la recuperación de fertilizantes, la liberación del compost y el aporte o retiro de las cáscaras.')

            st.subheader('7. ¿Cuánto compost y fertilizante debo aplicar?')
            st.info('Todavía no se puede calcular una dosis confiable únicamente con estos resultados. Falta validar la oferta anual del suelo, la recuperación de fertilizantes y la liberación del compost GOVA SAC. SIFERT no inventará una receta.')
            st.caption('El análisis de suelo expresa concentraciones y reservas analíticas, no necesariamente suministro anual para el cacao. Si no se midió azufre, no se diagnostica su suficiencia.')
        except ValueError as e:
            st.error(str(e))

    with st.expander('Información técnica y fuentes de referencia'):
        st.markdown('''**Criterios internos, no editables desde la interfaz.** Las referencias y rangos proceden de la versión V4.2 suministrada. Los coeficientes son heterogéneos y necesitan validación antes de usarse como base de prescripción.\n\n- CaO y MgO: cuadro IFA (2008) para grano, datos de Camerún.\n- S: Malavolta et al. (1984), 0.9 g/kg de grano seco.\n- NPK: coeficientes orientativos heredados de V4.2; comprobar las fuentes originales.\n- Las cáscaras de mazorca, aunque se retiren, representan una exportación adicional.\n- No se presupone densidad aparente ni se convierte directamente inventario analítico en dosis.\n\n**Los análisis se guardan solo si se selecciona un participante. Para persistencia en la nube configure PostgreSQL. No se exige inicio de sesión.**''')

with secciones[1]:
    st.subheader('Registrar participantes')
    with st.form('nuevo_participante'):
        c1,c2,c3=st.columns(3)
        codigo=c1.text_input('Código único (evite DNI)')
        nombre=c2.text_input('Nombre o identificación interna')
        caserio=c3.text_input('Caserío')
        area=c1.number_input('Área (ha)', min_value=0.0, value=1.0)
        plantas=c2.number_input('Plantas por ha', min_value=1, value=1100)
        edad=c3.number_input('Edad del cacao (años)', min_value=0.0, value=5.0)
        crear=st.form_submit_button('Guardar participante')
    if crear:
        try:
            if not codigo.strip() or not nombre.strip():
                raise ValueError('Código y nombre son obligatorios.')
            execute('INSERT INTO participantes(codigo,nombre,caserio,area_ha,plantas_ha,edad_anios,creado) VALUES (?,?,?,?,?,?,?)',
                    (codigo.strip(),nombre.strip(),caserio.strip(),area,plantas,edad,date.today().isoformat()))
            st.success('Participante guardado.')
            st.rerun()
        except Exception as e:
            st.error(str(e))
    st.dataframe(participantes(), hide_index=True, use_container_width=True)

with secciones[2]:
    st.subheader('Consultar, editar y eliminar análisis UNAS')
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
