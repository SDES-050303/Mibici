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
