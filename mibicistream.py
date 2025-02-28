import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from geopy.distance import geodesic
import zipfile
from io import BytesIO

# -----------------------------------------
# 🔹 Configuración Inicial de Streamlit
# -----------------------------------------
st.set_page_config(page_title="Análisis Mibici", layout="wide")
st.image("./IMG/Foto de estacion mi bici.jpg", use_container_width=True)

st.title("🚴‍♂️ Análisis de Datos Mibici")
st.markdown("""
EEste dashboard explora el uso de Mibici a lo largo de los últimos 10 años mediante gráficos y estadísticas detalladas.
Los datos provienen de la plataforma de Mibici - Datos Abiertos y permiten analizar tendencias, patrones de uso y mucho más.

📊 ¿Qué puedes descubrir?
✔️ Uso mensual y anual de las bicicletas.
✔️ Estaciones más utilizadas.
✔️ Comparación de viajes por hora y día de la semana.
✔️ Distancia recorrida, duración promedio y costos estimados.

📂 Para comenzar:
Sube un archivo ZIP con los datos y explora la información de manera visual e interactiva. 🚀
""")

# -----------------------------------------
# 🔹 Sidebar: Configuración y Carga de Datos
# -----------------------------------------
st.sidebar.title("./IMG/Mibici_logo.jpg")
st.sidebar.title("⚙️ Configuración")
uploaded_file = st.sidebar.file_uploader("📁 Sube el ZIP con los datos", type="zip")

# -----------------------------------------
# 🔹 Cargar nomenclatura de estaciones
# -----------------------------------------
@st.cache_data
def cargar_nomenclatura():
    try:
        return pd.read_csv("./datos/Nomenclatura_de_estaciones/nomenclatura_2025_01.csv", encoding='latin-1')
    except Exception as e:
        st.sidebar.error(f"⚠️ Error al cargar la nomenclatura: {e}")
        return None

nomenclatura = cargar_nomenclatura()

# -----------------------------------------
# 🔹 Función para Cargar y Procesar Datos ZIP
# -----------------------------------------
@st.cache_data
def cargar_datos_zip(zip_file):
    """Carga y procesa los archivos CSV dentro del ZIP."""
    dfs_por_año = {}
    
    try:
        with zipfile.ZipFile(zip_file, "r") as z:
            archivos_csv = [f for f in z.namelist() if f.endswith(".csv")]

            for archivo in archivos_csv:
                with z.open(archivo) as f:
                    df = pd.read_csv(f, encoding='latin-1')

                    # Renombrar columnas
                    df.rename(columns={
                        'Usuario_Id': 'Usuario Id',
                        'Año_de_nacimiento': 'Año de nacimiento',
                        'Inicio_del_viaje': 'Inicio del viaje',
                        'Fin_del_viaje': 'Fin del viaje',
                        'Origen_Id': 'Origen Id',
                        'Destino_Id': 'Destino Id',
                        'Viaje_Id': 'Viaje Id'
                    }, inplace=True)

                    # Convertir fechas y extraer Año y Mes
                    df["Inicio del viaje"] = pd.to_datetime(df["Inicio del viaje"], errors="coerce")
                    df["Fin del viaje"] = pd.to_datetime(df["Fin del viaje"], errors="coerce")
                    df["Año"] = df["Inicio del viaje"].dt.year
                    df["Mes"] = df["Inicio del viaje"].dt.month

                    # Extraer el año desde el nombre del archivo
                    año = archivo.split("_")[1][:4]
                    dfs_por_año[año] = df

        global_df = pd.concat(dfs_por_año.values(), ignore_index=True)
        return dfs_por_año, global_df

    except Exception as e:
        st.error(f"⚠️ Error al procesar el archivo ZIP: {e}")
        return None, None

# -----------------------------------------
# 🔹 Cargar Datos desde ZIP
# -----------------------------------------
if uploaded_file:
    dfs_por_año, global_df = cargar_datos_zip(uploaded_file)
    if global_df is not None:
        st.sidebar.success("✅ Datos cargados correctamente.")
    else:
        st.sidebar.error("⚠️ No se pudieron cargar los datos.")
        st.stop()
else:
    st.sidebar.warning("⚠️ Carga un archivo ZIP para continuar.")
    st.stop()

# -----------------------------------------
# 🔹 Sidebar: Selección de Año
# -----------------------------------------
opciones_año = ["Global"] + sorted(dfs_por_año.keys())
seleccion_año = st.sidebar.selectbox("📆 Selecciona un Año", opciones_año)

df_seleccionado = global_df if seleccion_año == "Global" else dfs_por_año[seleccion_año]

# -----------------------------------------
# 📊 Número de Viajes por Mes y Año
# -----------------------------------------
st.subheader("📊 Número de Viajes por Mes y Año")

viajes_mensuales = df_seleccionado.groupby(["Año", "Mes"]).size().reset_index(name="Total de Viajes")

fig, ax = plt.subplots(figsize=(14, 6))
sns.lineplot(data=viajes_mensuales, x="Mes", y="Total de Viajes", hue="Año", palette="tab10", marker="o", ax=ax)
ax.set_xlabel("Mes")
ax.set_ylabel("Total de Viajes")
ax.set_xticks(range(1, 13))
ax.set_xticklabels(["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"])
st.pyplot(fig)
st.text("📌 Este gráfico muestra la evolución mensual del número de viajes en Mibici, agrupados por año. "
        "Cada línea representa un año distinto, permitiendo identificar patrones estacionales y tendencias de uso a lo largo del tiempo. "
        "Se pueden observar meses con mayor o menor demanda, lo que ayuda a comprender cómo varía el uso del sistema de bicicletas compartidas.")


# -----------------------------------------
# 📊 Uso de Estaciones (Top 10)
# -----------------------------------------
st.subheader("🚴‍♂️ Top 10 Estaciones con Más Viajes")

viajes_origen = df_seleccionado["Origen Id"].value_counts().head(10).reset_index()
viajes_origen.columns = ["Estación", "Viajes"]

fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(data=viajes_origen, x="Estación", y="Viajes", palette="viridis", ax=ax)
ax.set_xlabel("Estación")
ax.set_ylabel("Número de Viajes")
ax.set_title("Top 10 Estaciones con Más Viajes")
st.pyplot(fig)
st.text("📌 Este gráfico muestra las 10 estaciones con mayor cantidad de viajes registrados como punto de origen. "
        "Se analiza la frecuencia con la que cada estación es utilizada para iniciar un viaje, permitiendo identificar "
        "las ubicaciones más concurridas dentro del sistema Mibici. Esto puede ayudar en la planificación de infraestructura "
        "y optimización del servicio.")


# -----------------------------------------
# 🔹 Función para Calcular Promedio de Viajes
# -----------------------------------------
def calcular_promedio_viajes(df, group_col, value_name="Total de Viajes"):
    """Agrupa los datos por una columna y calcula el total y promedio de viajes."""
    if group_col not in df.columns:
        st.error(f"⚠️ ERROR: La columna '{group_col}' no está en los datos.")
        return None, None
    
    # Agrupar por la columna dada y contar el número de viajes
    viajes = df.groupby(group_col).size().reset_index(name=value_name)
    
    # Calcular el promedio
    promedio = viajes[value_name].mean()
    
    return viajes, promedio

# -----------------------------------------
# 📊 Promedio de Viajes por Estación
# -----------------------------------------
st.subheader("📌 Promedio de Viajes por Estación")

viajes_por_estacion, promedio_viajes_estacion = calcular_promedio_viajes(global_df, "Origen Id")

if viajes_por_estacion is not None:
    st.write(f"📊 **Promedio de viajes por estación:** {promedio_viajes_estacion:.2f} viajes")

    # 🔹 Mostrar Top 10 Estaciones con más viajes
    top_10_estaciones = viajes_por_estacion.sort_values(by="Total de Viajes", ascending=False).head(10)

    st.subheader("🚲 **Top 10 Estaciones con Más Viajes**")
    st.dataframe(top_10_estaciones)

    # 🔹 Gráfica de los 10 primeros promedios de viajes por estación
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(x=top_10_estaciones['Origen Id'], y=top_10_estaciones['Total de Viajes'], palette="viridis", ax=ax)
    ax.set_xlabel('Estación')
    ax.set_ylabel('Total de Viajes')
    ax.set_title('Top 10 Estaciones con Más Viajes')
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
    st.text("📌 En esta sección, se calcula el promedio de viajes realizados desde cada estación. "
        "Además, se identifican las 10 estaciones con mayor número de viajes, mostrando tanto una tabla "
        "como una gráfica de barras que ilustra las estaciones más utilizadas en el sistema Mibici.")


# -----------------------------------------
# 📆 Promedio de Viajes por Año
# -----------------------------------------
st.subheader("📆 Promedio de Viajes por Año")

viajes_por_año, promedio_viajes_año = calcular_promedio_viajes(global_df, "Año")

if viajes_por_año is not None:
    st.write(f"📊 **Promedio de viajes por año:** {promedio_viajes_año:.2f} viajes")

    # 🔹 Gráfica de la evolución de viajes por año
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(data=viajes_por_año, x="Año", y="Total de Viajes", marker="o", color="b", ax=ax)
    ax.set_xlabel("Año")
    ax.set_ylabel("Número de Viajes")
    ax.set_title("📈 Evolución de Viajes por Año")
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
    st.text("📆 En esta sección, se analiza el promedio de viajes realizados por año. "
        "Se presenta un cálculo del total de viajes por año junto con un promedio general, "
        "además de una gráfica de línea que muestra la evolución del uso del sistema Mibici a lo largo del tiempo.")


# -----------------------------------------
# 📍 Función para Calcular Distancia Recorrida
# -----------------------------------------
def calcular_distancia(row):
    """Calcula la distancia entre estaciones o la aproxima con velocidad promedio."""
    try:
        origen = (row['lat_origin'], row['lon_origin'])
        destino = (row['lat_destination'], row['lon_destination'])

        if pd.isna(origen[0]) or pd.isna(destino[0]):
            return np.nan  # Si hay valores nulos, devuelve NaN

        if origen == destino:
            return (row['Duración (min)'] / 60) * 15  # Aproximación por velocidad 15 km/h
        else:
            return geodesic(origen, destino).km  # Distancia geodésica real
    except:
        return np.nan  # Si hay un error, devuelve NaN
    
# -----------------------------------------
# 🚴 Cálculo de Distancia Recorrida
# -----------------------------------------

st.subheader("📏 **Aproximación de Distancia Recorrida**")

df_distancia = global_df.copy()

# 🔹 **Validar y Calcular Duración si no existe**
if "Duración (min)" not in df_distancia.columns:
    df_distancia["Inicio del viaje"] = pd.to_datetime(df_distancia["Inicio del viaje"], errors="coerce")
    df_distancia["Fin del viaje"] = pd.to_datetime(df_distancia["Fin del viaje"], errors="coerce")
    df_distancia["Duración (min)"] = (df_distancia["Fin del viaje"] - df_distancia["Inicio del viaje"]).dt.total_seconds() / 60

# 🔹 **Cargar y unir coordenadas de la nomenclatura**
nomenclatura = pd.read_csv("./datos/Nomenclatura de las estaciones/nomenclatura_2025_01.csv", encoding='latin-1')
nomenclatura = nomenclatura.rename(columns={"id": "Estación", "latitude": "lat", "longitude": "lon"})

df_distancia = df_distancia.merge(nomenclatura[['Estación', 'lat', 'lon']], left_on="Origen Id", right_on="Estación", how="left")
df_distancia = df_distancia.rename(columns={"lat": "lat_origin", "lon": "lon_origin"}).drop(columns=["Estación"])

df_distancia = df_distancia.merge(nomenclatura[['Estación', 'lat', 'lon']], left_on="Destino Id", right_on="Estación", how="left")
df_distancia = df_distancia.rename(columns={"lat": "lat_destination", "lon": "lon_destination"}).drop(columns=["Estación"])

# 🔹 **Aplicar función de cálculo de distancia**
df_distancia["Distancia (km)"] = df_distancia.apply(calcular_distancia, axis=1)

# 🔹 **Mostrar datos de ejemplo**
st.write("📌 **Ejemplo de Distancias Calculadas (Primeros 10 registros)**")
st.dataframe(df_distancia[["Origen Id", "Destino Id", "Duración (min)", "Distancia (km)"]].head(10))

# 🔹 **Gráfico de Distribución de Distancias**
fig, ax = plt.subplots(figsize=(12, 6))
sns.histplot(df_distancia["Distancia (km)"], bins=30, kde=True, color="blue", ax=ax)
ax.set_xlabel("Distancia Recorrida (km)")
ax.set_ylabel("Frecuencia")
ax.set_title("Distribución de Distancias Recorridas")
st.pyplot(fig)
st.text("📏 Esta sección muestra una estimación de la distancia recorrida en cada viaje. "
        "La distancia se calcula de dos formas: si hay coordenadas de origen y destino, "
        "se utiliza la distancia geodésica real; si no, se estima con una velocidad promedio "
        "de 15 km/h basada en la duración del viaje. Este análisis ayuda a entender los "
        "patrones de movilidad de los usuarios en el sistema Mibici. 🚲📍")


# -----------------------------------------
# 🔥 Comparación de Tiempo de Viaje por Ruta y Género
# -----------------------------------------
st.subheader("⏳ **Comparación de Tiempo de Viaje por Ruta y Género**")

# 🔹 **Filtrar datos y generar rutas**
df_genero_ruta = df_distancia[["Origen Id", "Destino Id", "Duración (min)", "Genero"]].dropna()
df_genero_ruta["Ruta"] = df_genero_ruta["Origen Id"].astype(str) + " → " + df_genero_ruta["Destino Id"].astype(str)

# 🔹 **Gráfico de Distribución de Tiempo de Viaje por Género**
fig1, ax1 = plt.subplots(figsize=(12, 6))
sns.boxplot(data=df_genero_ruta, x="Genero", y="Duración (min)", palette="pastel", ax=ax1)
ax1.set_xlabel("Género")
ax1.set_ylabel("Duración del Viaje (min)")
ax1.set_title("Distribución del Tiempo de Viaje por Género")
st.pyplot(fig1)

# 🔹 **Calcular Promedio de Duración por Ruta y Género**
promedio_por_ruta = df_genero_ruta.groupby(["Ruta", "Genero"])["Duración (min)"].mean().reset_index()

# 🔹 **Seleccionar las 10 rutas más frecuentes**
top_rutas = df_genero_ruta["Ruta"].value_counts().head(10).index
df_top_rutas = promedio_por_ruta[promedio_por_ruta["Ruta"].isin(top_rutas)]

# 🔹 **Gráfico de Comparación del Tiempo de Viaje por Ruta y Género**
fig2, ax2 = plt.subplots(figsize=(14, 6))
sns.barplot(data=df_top_rutas, x="Ruta", y="Duración (min)", hue="Genero", palette="muted", ax=ax2)
ax2.set_xlabel("Ruta")
ax2.set_ylabel("Duración Promedio (min)")
ax2.set_title("Comparación del Tiempo de Viaje por Ruta y Género")
ax2.tick_params(axis='x', rotation=45)
st.pyplot(fig2)
st.text("⏳ Esta sección analiza la duración de los viajes en función del género del usuario y la ruta tomada. "
        "Se presentan dos visualizaciones: un diagrama de cajas que muestra la distribución del tiempo de viaje "
        "según el género y un gráfico de barras que compara la duración promedio de las 10 rutas más populares "
        "para cada género. Este análisis ayuda a identificar diferencias en los patrones de viaje y posibles "
        "factores que influyen en la duración de los trayectos. 🚴‍♂️🚴‍♀️📊")

# -----------------------------------------
# 📊 Función para calcular los viajes por día de la semana
# -----------------------------------------
def calcular_viajes_por_dia(df):
    """Convierte fechas, obtiene días de la semana y cuenta viajes."""
    df["Inicio del viaje"] = pd.to_datetime(df["Inicio del viaje"], errors="coerce")
    df["Día de la Semana"] = df["Inicio del viaje"].dt.dayofweek
    dias_semana = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 
                   4: "Viernes", 5: "Sábado", 6: "Domingo"}
    df["Día de la Semana"] = df["Día de la Semana"].map(dias_semana)
    
    # Contar viajes por día de la semana
    viajes_por_dia = df["Día de la Semana"].value_counts().reindex(dias_semana.values()).reset_index()
    viajes_por_dia.columns = ["Día de la Semana", "Número de Viajes"]
    
    return viajes_por_dia

# -----------------------------------------
# 📊 Análisis de Uso por Día de la Semana
# -----------------------------------------
st.subheader("📅 **Uso de Mibici por Día de la Semana**")

viajes_por_dia = calcular_viajes_por_dia(global_df)

# 🔹 **Gráfico de Barras: Número de Viajes por Día**
fig1, ax1 = plt.subplots(figsize=(10, 5))
sns.barplot(data=viajes_por_dia, x="Día de la Semana", y="Número de Viajes", palette="pastel", ax=ax1)
ax1.set_xlabel("Día de la Semana", fontsize=12)
ax1.set_ylabel("Número de Viajes", fontsize=12)
ax1.set_title("Número Total de Viajes por Día de la Semana", fontsize=14)
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig1)

# 🔹 **Gráfico de Línea: Tendencia de Uso por Día**
fig2, ax2 = plt.subplots(figsize=(10, 5))
sns.lineplot(data=viajes_por_dia, x="Día de la Semana", y="Número de Viajes", marker="o", color="b", ax=ax2)
ax2.set_xlabel("Día de la Semana", fontsize=12)
ax2.set_ylabel("Número de Viajes", fontsize=12)
ax2.set_title("Tendencia de Uso por Día de la Semana", fontsize=14)
plt.xticks(rotation=45)
plt.tight_layout()
st.pyplot(fig2)
st.text("📅 Este análisis examina el uso de Mibici según el día de la semana. Se presentan dos visualizaciones: "
        "un gráfico de barras que muestra el número total de viajes para cada día y un gráfico de líneas que "
        "representa la tendencia de uso a lo largo de la semana. Este estudio permite identificar patrones "
        "de demanda, como días con mayor actividad o posibles variaciones en el uso del sistema. 🚴‍♂️📊")


# -----------------------------------------
# 💰 Función para Calcular el Costo de los Viajes
# -----------------------------------------
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

# -----------------------------------------
# 💰 Cálculo del Total de Dinero Gastado
# -----------------------------------------
st.subheader("💰 **Total de Dinero Gastado (Aproximado)**")

# 🔹 **Verificar si la columna "Duración (min)" existe**
if "Duración (min)" not in global_df.columns:
    
    # Convertir a datetime
    global_df["Inicio del viaje"] = pd.to_datetime(global_df["Inicio del viaje"], errors="coerce")
    global_df["Fin del viaje"] = pd.to_datetime(global_df["Fin del viaje"], errors="coerce")
    
    # Calcular la duración en minutos
    global_df["Duración (min)"] = (global_df["Fin del viaje"] - global_df["Inicio del viaje"]).dt.total_seconds() / 60
    
    # Eliminar valores negativos o nulos
    global_df = global_df[global_df["Duración (min)"] > 0]

# 🔹 **Aplicar la función de costos**
df_costos = global_df.copy()
df_costos["Costo (MXN)"] = df_costos["Duración (min)"].apply(calcular_costo)

# 🔹 **Mostrar los primeros 10 registros**
st.write("📊 **Ejemplo de costos calculados (Primeros 10 registros):**")
st.dataframe(df_costos[["Viaje Id", "Duración (min)", "Costo (MXN)"]].head(10))

# 🔹 **Calcular el gasto total**
total_gasto = df_costos["Costo (MXN)"].sum()
st.write(f"💰 **Gasto Total Aproximado:** ${total_gasto:,.2f} MXN")

# 🔹 **Agrupar por rangos de duración del viaje**
bins = [0, 30, 60, 90, 120, 150, 180, 210, 240, 300, np.inf]
labels = ["0-30 min", "31-60 min", "61-90 min", "91-120 min", "121-150 min",
          "151-180 min", "181-210 min", "211-240 min", "241-300 min", "300+ min"]
df_costos["Rango de Tiempo"] = pd.cut(df_costos["Duración (min)"], bins=bins, labels=labels, right=False)
st.text("💰 Este análisis estima el gasto total generado por los usuarios de Mibici en función del tiempo de uso. "
        "Se calcula el costo de cada viaje con base en la duración en minutos y se presenta un ejemplo de los primeros "
        "10 registros. Además, se muestra el gasto total aproximado y se categorizan los viajes en rangos de tiempo "
        "para analizar cómo varían los costos según la duración. 📊🚴‍♂️")



# -------------------------------------
# 📊 **Análisis de Uso de Estaciones**
# -------------------------------------

st.subheader("📊 Uso de Estaciones (Mes - Año - Inicio - Fin)")

# 🔹 **Verificar si la columna 'Inicio del viaje' existe y convertirla a datetime si es necesario**
if "Inicio del viaje" not in global_df.columns:
    st.error("⚠️ ERROR: La columna 'Inicio del viaje' no existe. Se procederá a calcularla nuevamente.")
    global_df["Inicio del viaje"] = pd.to_datetime(global_df["Inicio del viaje"], errors="coerce")

# 🔹 **Crear columnas adicionales para análisis**
global_df["Mes"] = global_df["Inicio del viaje"].dt.month
global_df["Año"] = global_df["Inicio del viaje"].dt.year

# 🔹 **Definir opciones de análisis en el Sidebar**
st.sidebar.markdown("---")
tipo_grafico = st.sidebar.selectbox(
    "📊 Selecciona el Tipo de Análisis:", 
    ["Uso por Mes", "Uso por Año", "Comparación Inicio vs Fin"]
)

# 🔹 **Diccionario de opciones para gráficos**
graficos = {
    "Uso por Mes": {
        "col": "Mes",
        "titulo": "Uso de Mibici por Mes",
        "xlabel": "Mes",
        "xticks": ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"],
        "paleta": "coolwarm",
        "tipo": "bar"
    },
    "Uso por Año": {
        "col": "Año",
        "titulo": "Evolución del Uso de Mibici por Año",
        "xlabel": "Año",
        "xticks": None,
        "paleta": "Blues",
        "tipo": "line"
    }
}

# 🔹 **Si el usuario selecciona una de las opciones del diccionario**
if tipo_grafico in graficos:
    config = graficos[tipo_grafico]

    st.subheader(f"📅 {config['titulo']}")

    # 🔹 **Conteo de viajes por la columna seleccionada**
    df_agrupado = global_df[config["col"]].value_counts().sort_index().reset_index()
    df_agrupado.columns = [config["col"], "Total de Viajes"]

    # 🔹 **Generar el gráfico según el tipo**
    fig, ax = plt.subplots(figsize=(10, 5))
    
    if config["tipo"] == "bar":
        sns.barplot(x=config["col"], y="Total de Viajes", data=df_agrupado, palette=config["paleta"], ax=ax)
    elif config["tipo"] == "line":
        sns.lineplot(x=config["col"], y="Total de Viajes", data=df_agrupado, marker="o", color="b", ax=ax)

    ax.set_xlabel(config["xlabel"], fontsize=12)
    ax.set_ylabel("Número de Viajes", fontsize=12)
    ax.set_title(config["titulo"], fontsize=14)
    
    if config["xticks"]:
        plt.xticks(range(len(config["xticks"])), config["xticks"], rotation=45)
    
    plt.tight_layout()
    st.pyplot(fig)

# 🔹 **Comparación de Estaciones de Inicio vs Fin**
elif tipo_grafico == "Comparación Inicio vs Fin":
    st.subheader("🚴 Comparación de Uso: Estaciones de Inicio vs Fin")

    # 🔹 **Obtener conteos de viajes desde y hacia estaciones**
    viajes_inicio = global_df["Origen Id"].value_counts().reset_index()
    viajes_inicio.columns = ["Estación", "Viajes Inicio"]

    viajes_fin = global_df["Destino Id"].value_counts().reset_index()
    viajes_fin.columns = ["Estación", "Viajes Fin"]

    # 🔹 **Unir ambos DataFrames**
    uso_estaciones = viajes_inicio.merge(viajes_fin, on="Estación", how="outer").fillna(0)

    # 🔹 **Seleccionar las 10 estaciones más utilizadas**
    top_estaciones = uso_estaciones.sort_values(by=["Viajes Inicio", "Viajes Fin"], ascending=False).head(10)

    # 🔹 **Gráfico de comparación de viajes de inicio vs fin**
    fig, ax = plt.subplots(figsize=(12, 6))
    
    sns.barplot(x="Estación", y="Viajes Inicio", data=top_estaciones, color="blue", label="Inicio", ax=ax)
    sns.barplot(x="Estación", y="Viajes Fin", data=top_estaciones, color="red", alpha=0.6, label="Fin", ax=ax)

    ax.set_xlabel("Estación", fontsize=12)
    ax.set_ylabel("Número de Viajes", fontsize=12)
    ax.set_title("Comparación de Uso: Inicio vs Fin de Viajes", fontsize=14)
    ax.legend()
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
    st.text("📊 Este análisis muestra el uso de las estaciones de Mibici en función del mes y el año. "
        "Se presentan gráficos que permiten visualizar la evolución del uso de bicicletas a lo largo del tiempo, "
        "ayudando a identificar tendencias de uso estacional. También se compara el número de viajes iniciados y finalizados "
        "en las estaciones más utilizadas para analizar los patrones de movilidad urbana. 🚴‍♂️📈")

# -----------------------------------------
# 🔹 Análisis de Correlación Día de la Semana - Tiempo de Viaje
# -----------------------------------------
st.subheader("📊 **Correlación entre Día de la Semana y Tiempo de Viaje**")

# 🔹 **Verificar si las columnas necesarias existen**
if "Inicio del viaje" in global_df.columns and "Duración (min)" in global_df.columns:
    
    # 🔹 **Convertir a datetime si es necesario**
    global_df["Inicio del viaje"] = pd.to_datetime(global_df["Inicio del viaje"], errors="coerce")

    # 🔹 **Extraer el día de la semana (0=Lunes, 6=Domingo)**
    df_dia_tiempo = global_df[["Inicio del viaje", "Duración (min)"]].dropna().copy()
    df_dia_tiempo["Día de la Semana"] = df_dia_tiempo["Inicio del viaje"].dt.dayofweek

    # 🔹 **Mapeo de números a nombres de días**
    dias_semana = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
    df_dia_tiempo["Día de la Semana Nombre"] = df_dia_tiempo["Día de la Semana"].map(dias_semana)

    # 🔹 **Cálculo de la correlación**
    correlacion = df_dia_tiempo["Día de la Semana"].corr(df_dia_tiempo["Duración (min)"])

    st.write(f"🔢 **Coeficiente de Correlación Pearson:** {correlacion:.3f}")

    # 🔹 **Gráfico de Boxplot (Distribución del tiempo de viaje por día)**
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=df_dia_tiempo, x="Día de la Semana Nombre", y="Duración (min)", palette="coolwarm", ax=ax)
    
    ax.set_xlabel("Día de la Semana", fontsize=12)
    ax.set_ylabel("Duración del Viaje (min)", fontsize=12)
    ax.set_title("📉 Relación entre Día de la Semana y Tiempo de Viaje", fontsize=14)
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)
    st.text("📊 Este análisis examina la relación entre el día de la semana y la duración de los viajes en Mibici. "
        "Se calcula el coeficiente de correlación de Pearson para evaluar si existe una tendencia en la duración "
        "de los viajes según el día. Además, se presenta un gráfico de caja (boxplot) para visualizar la distribución "
        "de los tiempos de viaje en cada día de la semana, permitiendo identificar patrones o diferencias significativas "
        "en el uso de Mibici a lo largo de la semana. 🚴‍♂️📅")

else:
    st.error("⚠️ No se encontraron las columnas necesarias ('Inicio del viaje' y 'Duración (min)').")
