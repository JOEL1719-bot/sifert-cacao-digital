# SIFERT CACAO DIGITAL — versión 1

## Funciones
- Registro de participantes manual y mediante Excel.
- Análisis de suelo UNAS manuales y mediante Excel.
- Comparación de dos análisis de un participante.
- Registro de aplicaciones reales de compost y fertilizantes.
- Exportación de tablas CSV.
- Motor de fertilización todavía no habilitado (requiere validación agronómica).

## Ejecutar localmente
```
pip install -r requirements.txt
streamlit run app.py
```

## Publicar en Streamlit Community Cloud
1. Subir `app.py` y `requirements.txt` a un repositorio GitHub.
2. Crear app en Streamlit Community Cloud apuntando a `app.py`.
3. Para datos persistentes, crear una base PostgreSQL externa (por ejemplo Neon o Supabase PostgreSQL).
4. En los secretos de la aplicación configurar:
```
DATABASE_URL = "postgresql://USUARIO:CLAVE@HOST:5432/BASE?sslmode=require"
```
5. No publicar el valor de `DATABASE_URL` en GitHub.

**Atención:** sin DATABASE_URL, la aplicación usa SQLite local, que NO es almacenamiento permanente en Streamlit Community Cloud. El acceso libre permite a cualquier visitante ver e introducir información: usar códigos internos y no DNI. Se recomienda autenticación antes de utilizar datos reales de productores.

## Formato Excel
Descargar las plantillas desde las pestañas correspondientes del aplicativo. Los nombres de columnas deben conservarse.

## Alcance
No se generan dosis ni recomendaciones técnicas definitivas. Antes de implementar el motor de cálculo se deben validar las ecuaciones y las fuentes de fertilizantes, densidad aparente y composición del compost.
