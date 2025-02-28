import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from geopy.distance import geodesic
import zipfile
from io import BytesIO

st.image("./IMG/Foto de estacion mi bici.jpg", use_container_width=True)

st.title("Análisis Mibici")
st.header("Introducción")
st.subheader("Análisis de datos de Mibici")
st.markdown("""En este repertorio podemos notar un análisis de datos sobre cómo las bicicletas **Mibici** fueron utilizadas a través de los 10 años
que han estado activas. Vamos a descubrir datos que nunca esperaríamos conocer si no fuera por el análisis profundo que se registró y se compartió en
[Datos Abiertos Mibici](https://www.mibici.net/es/datos-abiertos/). ¡Por favor, utiliza los datos de manera correcta!""")

st.markdown("**Advertencia** Se necesita subir un zip para los datos")

# ------------------- Configuración del Sidebar -------------------
st.sidebar.title("Panel de Control")
st.sidebar.markdown("### Opciones de Filtrado")
st.sidebar.image("./IMG/Mibici_logo.jpg", use_container_width=True)
st.sidebar.title("Subir archivo ZIP")
uploaded_file = st.sidebar.file_uploader("Sube el ZIP con los datos", type="zip")

# ------------------- Cargar archivos limpios por año -------------------
# Cargar nomenclatura de estaciones
nomenclatura = pd.read_csv("./datos/Nomenclatura de las estaciones/nomenclatura_2025_01.csv", encoding='latin-1')

# Diccionario para almacenar los DataFrames de cada año
dfs_por_año = {}

if uploaded_file is not None:
    with zipfile.ZipFile(uploaded_file, "r") as z:
        archivos_csv = [f for f in z.namelist() if f.endswith(".csv")]  # Obtener todos los CSV

        st.write(f"Archivos encontrados en el ZIP: {archivos_csv}")

        # Leer cada archivo CSV en un diccionario
        for archivo in archivos_csv:
            with z.open(archivo) as f:
                df = pd.read_csv(f, encoding='latin-1')
                
                # Renombrar columnas para homogeneizar
                df.rename(columns={
                    'Usuario_Id': 'Usuario Id',
                    'Año_de_nacimiento': 'Año de nacimiento',
                    'Inicio_del_viaje': 'Inicio del viaje',
                    'Fin_del_viaje': 'Fin del viaje',
                    'Origen_Id': 'Origen Id',
                    'Destino_Id': 'Destino Id',
                    'Viaje_Id': 'Viaje Id',
                    'AÃ±o_de_nacimiento': 'Año de nacimiento',
                    'A}äe_nacimiento': 'Año de nacimiento',
                    'Aï¿½o_de_nacimiento': 'Año de nacimiento'
                }, inplace=True)

                # Convertir fechas y extraer Año y Mes
                df["Inicio del viaje"] = pd.to_datetime(df["Inicio del viaje"], errors="coerce")
                df["Año"] = df["Inicio del viaje"].dt.year
                df["Mes"] = df["Inicio del viaje"].dt.month

                # Extraer el año desde el nombre del archivo
                año = archivo.split("_")[1][:4]  # Ajusta según el nombre de tus archivos
                dfs_por_año[año] = df  # Guardar en el diccionario

        # Unir todos los DataFrames en uno solo (global)
        global_df = pd.concat(list(dfs_por_año.values()), ignore_index=True)

        st.success("Archivos cargados y datos procesados correctamente 🎉")

# ------------------- Sección de Visualizaciones -------------------
# Definir las opciones para el sidebar: "Global" y los años disponibles
opciones_año = ["Global"] + sorted(list(dfs_por_año.keys()))

# Sidebar para Top 10 estaciones
st.sidebar.markdown("---")
st.sidebar.text("Top 10 estaciones con más viajes")
seleccion_top = st.sidebar.selectbox("Selecciona el año", opciones_año, index=0, key="select_top")

if seleccion_top != "Global":
    df_top = dfs_por_año[seleccion_top]
else:
    df_top = global_df

# Agrupación por estaciones para Top 10
viajes_por_origen = df_top["Origen Id"].value_counts().reset_index()
viajes_por_origen.columns = ["Estación", "Viajes desde"]
viajes_por_destino = df_top["Destino Id"].value_counts().reset_index()
viajes_por_destino.columns = ["Estación", "Viajes hacia"]

uso_estaciones = viajes_por_origen.merge(viajes_por_destino, on="Estación", how="outer").fillna(0)
uso_estaciones["Total de viajes"] = uso_estaciones["Viajes desde"] + uso_estaciones["Viajes hacia"]
uso_estaciones = uso_estaciones.sort_values(by="Total de viajes", ascending=False)

st.subheader(f"Top 10 Estaciones con Más Viajes para: {seleccion_top}")
top_estaciones = uso_estaciones.head(10)
st.dataframe(top_estaciones.reset_index(drop=True))

# Gráfica
st.subheader(f"Grafica Top 10 Estaciones con Más Viajes para: {seleccion_top}")
fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(x=top_estaciones["Estación"], y=top_estaciones["Total de viajes"], palette="viridis", ax=ax)
ax.set_xlabel("Estación", fontsize=12)
ax.set_ylabel("Total de Viajes", fontsize=12)
ax.set_title(f"Top 10 Estaciones con Más Viajes para: {seleccion_top}", fontsize=14)
ax.tick_params(axis='x', rotation=45)
plt.tight_layout()
st.pyplot(fig)

# ------------------- Gráfica Global: Número de Viajes por Mes y Año -------------------
st.subheader("Gráfica Número de Viajes por Mes y Año")
df_mes = global_df.copy()

# Verificación de columnas antes de agrupar
if "Año" not in df_mes.columns or "Mes" not in df_mes.columns:
    st.error("Las columnas 'Año' y 'Mes' no existen en df_mes. Verifica que los datos están bien cargados.")
    st.write("Columnas disponibles en df_mes:", df_mes.columns)
else:
    # Agrupar por Año y Mes
    viajes_mensuales = df_mes.groupby(["Año", "Mes"]).size().reset_index(name="Total de viajes")

    fig2, ax2 = plt.subplots(figsize=(14, 6))
    sns.lineplot(
        data=viajes_mensuales,
        x="Mes",
        y="Total de viajes",
        hue="Año",
        palette="tab10",
        marker="o",
        ax=ax2
    )
    ax2.set_xlabel("Mes", fontsize=12)
    ax2.set_ylabel("Total de Viajes", fontsize=12)
    ax2.set_title("Número de Viajes por Mes y Año (Global)", fontsize=14)
    ax2.set_xticks(range(1, 13))
    ax2.set_xticklabels(["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"])
    plt.tight_layout()
    st.pyplot(fig2)

#------------------------------------------------------------------Promedio en viajes---------------------------------------------

# Calcular el número de viajes por estación (origen y destino)
viajes_por_estacion = global_df.groupby('Origen Id').size().reset_index(name="Total de Viajes")

# Calcular el promedio de viajes por estación
promedio_viajes = viajes_por_estacion["Total de Viajes"].mean()

# Mostrar el promedio
st.write(f"Promedio de viajes por estación: {promedio_viajes:.2f} viajes")
#-------------------------------------------------------------------------------------------
# Agrupar por "Año" y contar el número de viajes
viajes_por_año = global_df.groupby("Año").size().reset_index(name="Total de Viajes")

# Calcular el promedio de viajes por año
promedio_viajes_por_año = viajes_por_año["Total de Viajes"].mean()

# Mostrar el promedio de viajes por año
st.write(f"Promedio de viajes por año: {promedio_viajes_por_año:.2f} viajes")

#-------------------------------------------------------------------------------------------------
# Agrupar por estación (origen) y contar el total de viajes
viajes_por_estacion = global_df.groupby('Origen Id').size().reset_index(name="Total de Viajes")

# Calcular el promedio de viajes por estación
promedio_por_estacion = viajes_por_estacion.groupby('Origen Id')['Total de Viajes'].mean().reset_index()

# Ordenar de mayor a menor para ver las estaciones más populares
promedio_por_estacion = promedio_por_estacion.sort_values(by='Total de Viajes', ascending=False)

# Seleccionar el Top 10
top_10_promedio = promedio_por_estacion.head(10)

# Mostrar los resultados
st.subheader("Top 10 Estaciones con Más Viajes")
st.dataframe(top_10_promedio)

#-------------------------------------------------------------------------------------------------------
# Gráfica de los 10 primeros promedios de viajes por estación
fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(x=top_10_promedio['Origen Id'], y=top_10_promedio['Total de Viajes'], palette="viridis", ax=ax)
ax.set_xlabel('Estación', fontsize=12)
ax.set_ylabel('Total de Viajes', fontsize=12)
ax.set_title('Top 10 Estaciones con Más Viajes', fontsize=14)
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig)

#------------------------------------------------------------Aproximación de Distancia Recorrida------------------------

st.subheader("Aproximación de Distancia Recorrida")

# 🔹 **Copiar el DataFrame original para cálculos**
df_distancia = global_df.copy()

# 🔹 **Verificar si "Duración (min)" existe y calcularla si falta**
if "Duración (min)" not in df_distancia.columns:
    df_distancia["Inicio del viaje"] = pd.to_datetime(df_distancia["Inicio del viaje"], errors="coerce")
    df_distancia["Fin del viaje"] = pd.to_datetime(df_distancia["Fin del viaje"], errors="coerce")
    df_distancia["Duración (min)"] = (df_distancia["Fin del viaje"] - df_distancia["Inicio del viaje"]).dt.total_seconds() / 60

# 🔹 **Cargar las coordenadas de la nomenclatura**
nomenclatura = pd.read_csv("./datos/Nomenclatura de las estaciones/nomenclatura_2025_01.csv", encoding='latin-1')

# 🔹 **Renombrar columnas de nomenclatura para hacer merge más fácil**
nomenclatura.rename(columns={
    "id": "Origen Id",
    "latitude": "lat_origin",
    "longitude": "lon_origin"
}, inplace=True)

# 🔹 **Unir coordenadas de origen**
df_distancia = df_distancia.merge(nomenclatura[['Origen Id', 'lat_origin', 'lon_origin']], on="Origen Id", how="left")

# 🔹 **Renombrar "id" en nomenclatura a "Destino Id" para hacer el merge**
nomenclatura.rename(columns={
    "Origen Id": "Destino Id",
    "lat_origin": "lat_destination",
    "lon_origin": "lon_destination"
}, inplace=True)

# 🔹 **Unir coordenadas de destino**
df_distancia = df_distancia.merge(nomenclatura[['Destino Id', 'lat_destination', 'lon_destination']], on="Destino Id", how="left")

# 🔹 **Mostrar datos después del merge**
st.write("Ejemplo de datos con coordenadas después del merge:")
st.dataframe(df_distancia[["Origen Id", "Destino Id", "Duración (min)", "lat_origin", "lon_origin", "lat_destination", "lon_destination"]].head(10))

# 🔹 **Función para calcular la distancia**
def calcular_distancia(row):
    try:
        origen = (row['lat_origin'], row['lon_origin'])
        destino = (row['lat_destination'], row['lon_destination'])

        # Si alguna coordenada es NaN, devolver NaN
        if pd.isna(origen[0]) or pd.isna(destino[0]):
            return np.nan  

        if origen == destino:
            # Asumimos velocidad promedio 15 km/h
            return (row['Duración (min)'] / 60) * 15  # Distancia en km
        else:
            return geodesic(origen, destino).km  # Distancia geodésica en km
    except Exception as e:
        return np.nan  # Si hay algún error, devolver NaN

# 🔹 **Aplicar la función y calcular la distancia**
df_distancia['Distancia (km)'] = df_distancia.apply(calcular_distancia, axis=1)

# 🔹 **Mostrar los primeros 10 viajes con su distancia**
st.subheader("Ejemplo de Distancia Calculada (Primeros 10 registros)")
st.dataframe(df_distancia[["Origen Id", "Destino Id", "Duración (min)", "Distancia (km)"]])

#-------------------------------------------------- Grafico de comparacion Tiempo y Ruta / Genero ----------------------

# -------------------------------------
# 🔹 Comparación de Tiempo de Viaje por Ruta y Género
# -------------------------------------

st.subheader("Comparación de Tiempo de Viaje por Ruta y Género")

# 🔹 Seleccionar las columnas necesarias
df_genero_ruta = df_distancia[["Origen Id", "Destino Id", "Duración (min)", "Genero"]].copy()

# 🔹 Crear una nueva columna para identificar cada ruta
df_genero_ruta["Ruta"] = df_genero_ruta["Origen Id"].astype(str) + " → " + df_genero_ruta["Destino Id"].astype(str)

# 🔹 Eliminar valores nulos en "Duración (min)" y "Genero"
df_genero_ruta = df_genero_ruta.dropna(subset=["Duración (min)", "Genero"])

# 🔹 Gráfico 1: Distribución de tiempo de viaje por género (Boxplot)
fig1, ax1 = plt.subplots(figsize=(12, 6))
sns.boxplot(data=df_genero_ruta, x="Genero", y="Duración (min)", palette="pastel", ax=ax1)
ax1.set_xlabel("Género", fontsize=12)
ax1.set_ylabel("Duración del Viaje (min)", fontsize=12)
ax1.set_title("Distribución del Tiempo de Viaje por Género", fontsize=14)
plt.tight_layout()
st.pyplot(fig1)

# 🔹 Agrupar por ruta y género para obtener la duración promedio
promedio_por_ruta = df_genero_ruta.groupby(["Ruta", "Genero"])["Duración (min)"].mean().reset_index()

# 🔹 Seleccionar solo las 10 rutas más frecuentes
top_rutas = df_genero_ruta["Ruta"].value_counts().head(10).index
df_top_rutas = promedio_por_ruta[promedio_por_ruta["Ruta"].isin(top_rutas)]

# 🔹 Gráfico 2: Comparación del Tiempo de Viaje Promedio por Ruta y Género (Barras)
fig2, ax2 = plt.subplots(figsize=(14, 6))
sns.barplot(data=df_top_rutas, x="Ruta", y="Duración (min)", hue="Genero", palette="muted", ax=ax2)
ax2.set_xlabel("Ruta", fontsize=12)
ax2.set_ylabel("Duración Promedio (min)", fontsize=12)
ax2.set_title("Comparación del Tiempo de Viaje por Ruta y Género", fontsize=14)
ax2.tick_params(axis='x', rotation=45)
plt.tight_layout()
st.pyplot(fig2)

# -------------------------------------
# 🔹 Análisis del uso de Mibici por días de la semana
# -------------------------------------

st.subheader("Uso de Mibici por Día de la Semana")

# 🔹 Asegurar que las fechas estén en formato datetime
df_dias = global_df.copy()
df_dias["Inicio del viaje"] = pd.to_datetime(df_dias["Inicio del viaje"], errors="coerce")

# 🔹 Obtener el día de la semana (0=Lunes, 6=Domingo)
df_dias["Día de la Semana"] = df_dias["Inicio del viaje"].dt.dayofweek

# 🔹 Mapeo de números a nombres de días
dias_semana = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
df_dias["Día de la Semana"] = df_dias["Día de la Semana"].map(dias_semana)

# 🔹 Contar los viajes por día de la semana
viajes_por_dia = df_dias["Día de la Semana"].value_counts().reindex(dias_semana.values()).reset_index()
viajes_por_dia.columns = ["Día de la Semana", "Número de Viajes"]

# 🔹 Gráfico 1: Barras del número total de viajes por día de la semana
fig1, ax1 = plt.subplots(figsize=(10, 5))
sns.barplot(data=viajes_por_dia, x="Día de la Semana", y="Número de Viajes", palette="pastel", ax=ax1)
ax1.set_xlabel("Día de la Semana", fontsize=12)
ax1.set_ylabel("Número de Viajes", fontsize=12)
ax1.set_title("Número Total de Viajes por Día de la Semana", fontsize=14)
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig1)

# 🔹 Gráfico 2: Línea de la evolución del uso por día de la semana
fig2, ax2 = plt.subplots(figsize=(10, 5))
sns.lineplot(data=viajes_por_dia, x="Día de la Semana", y="Número de Viajes", marker="o", color="b", ax=ax2)
ax2.set_xlabel("Día de la Semana", fontsize=12)
ax2.set_ylabel("Número de Viajes", fontsize=12)
ax2.set_title("Tendencia de Uso por Día de la Semana", fontsize=14)
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig2)

# -------------------------------------
# 🔹 Cálculo del Total de Dinero Gastado (Aproximado)
# -------------------------------------

st.subheader("Total de Dinero Gastado (Aproximado)")

# 🔹 Función para calcular el costo según la duración del viaje
def calcular_costo(duracion):
    """
    Calcula el costo adicional del viaje según su duración en minutos.
    - 0 a 30 min: incluido (0 MXN)
    - 30:01 a 60 min: 29.00 MXN
    - >60 min: 29.00 MXN + 40.00 MXN por cada media hora adicional (o fracción)
    """
    if duracion <= 30:
        return 0.0
    elif duracion <= 60:
        return 29.0
    else:
        periodos_adicionales = np.ceil((duracion - 60) / 30)  # Cada 30 min adicionales
        return 29.0 + (periodos_adicionales * 40.0)

# 🔹 Aplicar la función a los datos
df_costos = global_df.copy()
df_costos["Costo (MXN)"] = df_costos["Duración (min)"].apply(calcular_costo)

# 🔹 Mostrar los primeros 10 registros
st.write("Ejemplo de costos calculados (Primeros 10 registros):")
st.dataframe(df_costos[["Viaje Id", "Duración (min)", "Costo (MXN)"]].head(10))

# 🔹 Calcular el gasto total
total_gasto = df_costos["Costo (MXN)"].sum()
st.write(f"**Gasto Total Aproximado:** ${total_gasto:,.2f} MXN")

# 🔹 Agrupar por rangos de tiempo para visualización
bins = [0, 30, 60, 90, 120, 150, 180, 210, 240, 300, np.inf]
labels = ["0-30 min", "31-60 min", "61-90 min", "91-120 min", "121-150 min",
          "151-180 min", "181-210 min", "211-240 min", "241-300 min", "300+ min"]
df_costos["Rango de Tiempo"] = pd.cut(df_costos["Duración (min)"], bins=bins, labels=labels, right=False)

# 🔹 Calcular total de costos por rango
costos_por_rango = df_costos.groupby("Rango de Tiempo")["Costo (MXN)"].sum().reset_index()

# 🔹 Gráfico de barras del total gastado por rango de duración
fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(data=costos_por_rango, x="Rango de Tiempo", y="Costo (MXN)", palette="coolwarm", ax=ax)
ax.set_xlabel("Duración del Viaje", fontsize=12)
ax.set_ylabel("Costo Total (MXN)", fontsize=12)
ax.set_title("Gasto Total por Duración del Viaje", fontsize=14)
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig)

