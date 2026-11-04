"""SIFERT CACAO DIGITAL V4.3 — interfaz única para agricultor y técnico.
No emite prescripciones de fertilización sin calibración agronómica local.
"""
import streamlit as st
import pandas as pd

st.set_page_config(page_title='SIFERT CACAO DIGITAL', page_icon='🌱', layout='wide')
st.title('🌱 SIFERT CACAO DIGITAL')
st.caption('V4.3 · Evaluación sencilla del análisis de suelo para cacao · Alto Huallaga')
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

def clasificar(k, v):
    if v is None:
        return 'No determinado'
    if k == 'ph':
        if not 0 < v <= 14: return 'Revisar resultado'
        if v < 4.5: return 'Extremadamente ácido'
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
        for clave, nombre, unidad in CAMPOS:
            tabla.append({'Indicador':nombre, 'Resultado': datos[clave] if datos[clave] is not None else 'No medido',
                          'Unidad':unidad, 'Interpretación orientativa':clasificar(clave, datos[clave])})
        st.dataframe(pd.DataFrame(tabla), hide_index=True, use_container_width=True)
        st.caption('Los umbrales son provisionales y requieren contrastarse con el método analítico del laboratorio y la calibración para cacao local.')
        ph, al, mg = datos['ph'], datos['sat_al'], datos['mg']
        if ph is not None and (ph < 5.5 or (al is not None and al >= 20)):
            st.warning('Suelo ácido o con señal de aluminio: conviene evaluar una corrección de acidez con asistencia técnica. No se calcula dosis de cal o dolomita sin datos adicionales.')
        elif al is not None and al >= 20:
            st.warning('Saturación de aluminio elevada: solicite evaluación técnica de acidez.')
        if mg is not None and 0 < mg < 0.5:
            st.info('Magnesio intercambiable bajo según criterio provisional. Verificar antes de seleccionar una enmienda.')
        st.subheader('4. Nutrientes que saldrían en el grano seco')
        st.caption('Cálculo automático a partir de la producción esperada; NO indica cuánto fertilizante aplicar.')
        extraccion = pd.DataFrame([{'Macronutriente': nutriente,
                                    'Exportación estimada en grano (kg/ha/año)': round(rendimiento*coef/1000, 2)}
                                   for nutriente, coef in EXTRACCION_GRANO_KG_T.items()])
        st.dataframe(extraccion, hide_index=True, use_container_width=True)
        st.caption('Coeficientes bibliográficos orientativos de V4.2 (N 22; P₂O₅ 6.87; K₂O 10.8; CaO 1.3; MgO 5.3; S 0.9 kg/t). No validados localmente. Las cáscaras retiradas exportan nutrientes adicionales que aquí no se cuantifican.')
        st.subheader('5. ¿Cuánto compost y fertilizante debo aplicar?')
        st.info('Todavía no se puede calcular una dosis confiable únicamente con estos resultados. Falta validar la oferta anual del suelo, la recuperación de fertilizantes y la liberación del compost GOVA SAC. SIFERT no inventará una receta.')
        st.caption('El análisis de suelo expresa concentraciones y reservas analíticas, no necesariamente suministro anual para el cacao. Si no se midió azufre, no se diagnostica su suficiencia.')
    except ValueError as e:
        st.error(str(e))

with st.expander('Información técnica y fuentes de referencia'):
    st.markdown('''**Criterios internos, no editables desde la interfaz.** Las referencias y rangos proceden de la versión V4.2 suministrada. Los coeficientes son heterogéneos y necesitan validación antes de usarse como base de prescripción.\n\n- CaO y MgO: cuadro IFA (2008) para grano, datos de Camerún.\n- S: Malavolta et al. (1984), 0.9 g/kg de grano seco.\n- NPK: coeficientes orientativos heredados de V4.2; comprobar las fuentes originales.\n- Las cáscaras de mazorca, aunque se retiren, representan una exportación adicional.\n- No se presupone densidad aparente ni se convierte directamente inventario analítico en dosis.\n\n**Esta versión no guarda datos personales ni exige registro.**''')
