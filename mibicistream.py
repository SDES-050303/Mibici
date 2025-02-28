import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from geopy.distance import geodesic

# -------------------------------------
# Encabezado e introducción
# -------------------------------------
st.image("./IMG/Foto de estacion mi bici.jpg", use_container_width=True)
st.title("Análisis Mibici")
st.header("Introducción")
st.subheader("Análisis de datos de Mibici")
st.markdown("""En este repertorio podemos notar un análisis de datos de cómo las bicicletas **Mibici** fueron utilizadas a través de los 10 años
que han estado activas. Vamos a descubrir datos que nunca esperábamos conocer si no fuera por el análisis profundo registrado y compartido en
[https://www.mibici.net/es/datos-abiertos/](https://www.mibici.net/es/datos-abiertos/). Por favor, utiliza los datos de manera responsable.""")

# -------------------------------------
# Configuración del Sidebar
# -------------------------------------
st.sidebar.title("Panel de Control")
st.sidebar.markdown("### Opciones de Filtrado")
st.sidebar.image("./IMG/Mibici_logo.jpg", use_container_width=True)

# -------------------------------------
# Cargar archivos limpios por año
# -------------------------------------
datos2014 = pd.read_csv("./datos/2014/Mibici_2014_limpios.csv", encoding='latin-1')

nomenclatura = pd.read_csv("./datos/Nomenclatura de las estaciones/nomenclatura_2025_01.csv", encoding='latin-1')

# Crear un diccionario con los DataFrames por año
dfs_por_año = {
    "2014": datos2014,
}

# -------------------------------------
# Renombrar columnas y crear "Año" y "Mes"
# -------------------------------------
for year, df in dfs_por_año.items():
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
    
    df["Inicio del viaje"] = pd.to_datetime(df["Inicio del viaje"], errors="coerce")
    df["Año"] = df["Inicio del viaje"].dt.year
    df["Mes"] = df["Inicio del viaje"].dt.month
    dfs_por_año[year] = df

# -------------------------------------
# Unir los DataFrames en uno global
# -------------------------------------
global_df = pd.concat(list(dfs_por_año.values()), ignore_index=True)

# -------------------------------------
# Visualizaciones
# -------------------------------------
opciones_año = ["Global"] + sorted(list(dfs_por_año.keys()))

st.sidebar.markdown("---")
st.sidebar.text("Top 10 estaciones con más viajes")
seleccion_top = st.sidebar.selectbox("Selecciona el año", opciones_año, index=0, key="select_top")

if seleccion_top != "Global":
    df_top = dfs_por_año[seleccion_top]
else:
    df_top = global_df

# Top 10 estaciones
viajes_por_origen = df_top["Origen Id"].value_counts().reset_index()
viajes_por_origen.columns = ["Estación", "Viajes desde"]
viajes_por_destino = df_top["Destino Id"].value_counts().reset_index()
viajes_por_destino.columns = ["Estación", "Viajes hacia"]

uso_estaciones = viajes_por_origen.merge(viajes_por_destino, on="Estación", how="outer").fillna(0)
uso_estaciones["Total de viajes"] = uso_estaciones["Viajes desde"] + uso_estaciones["Viajes hacia"]
uso_estaciones = uso_estaciones.sort_values(by="Total de viajes", ascending=False)

st.subheader("Top 10 Estaciones con Más Viajes para: " + seleccion_top)
top_estaciones = uso_estaciones.head(10)
st.dataframe(top_estaciones.reset_index(drop=True))

st.subheader("Gráfica de las 10 Estaciones con Más Viajes")
fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(x=top_estaciones["Estación"], y=top_estaciones["Total de viajes"], palette="viridis", ax=ax)
ax.set_xlabel("Estación", fontsize=12)
ax.set_ylabel("Total de Viajes", fontsize=12)
ax.set_title("Top 10 Estaciones con Más Viajes para: " + seleccion_top, fontsize=14)
ax.tick_params(axis='x', rotation=45)
plt.tight_layout()
st.pyplot(fig)

# -------------------------------------
# Gráfica Global: Número de Viajes por Mes y Año
# -------------------------------------
st.subheader("Gráfica Global: Número de Viajes por Mes y Año")
df_mes = global_df.copy()
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

# -------------------------------------
# Promedios de tiempo de viaje
# -------------------------------------
st.subheader("Top 10 Promedios de Tiempo de Viaje por Estación")

# Asegurarnos de tener las columnas de fecha en datetime y calcular Duración (min)
global_df["Inicio del viaje"] = pd.to_datetime(global_df["Inicio del viaje"], errors="coerce")
global_df["Fin del viaje"] = pd.to_datetime(global_df["Fin del viaje"], errors="coerce")
global_df["Duración (min)"] = (global_df["Fin del viaje"] - global_df["Inicio del viaje"]).dt.total_seconds() / 60

# Agrupar por "Origen Id" y calcular el promedio
promedio_por_estacion = global_df.groupby("Origen Id")["Duración (min)"].mean().reset_index()
promedio_por_estacion.columns = ["Estación", "Promedio de duración (min)"]
promedio_por_estacion = promedio_por_estacion.sort_values(by="Promedio de duración (min)", ascending=False)

# Seleccionar los 10 primeros
top10_promedios = promedio_por_estacion.head(10)
st.dataframe(top10_promedios.reset_index(drop=True))

st.subheader("Top 10 Promedios de Tiempo de Viaje por Estación: Gráfica")
fig3, ax3 = plt.subplots(figsize=(12, 6))
sns.barplot(data=top10_promedios, x="Estación", y="Promedio de duración (min)", palette="rocket", ax=ax3)
ax3.set_xlabel("Estación", fontsize=12)
ax3.set_ylabel("Promedio de Duración (min)", fontsize=12)
ax3.set_title("Top 10 Promedios de Tiempo de Viaje por Estación", fontsize=14)
ax3.tick_params(axis='x', rotation=45)
plt.tight_layout()
st.pyplot(fig3)

# -------------------------------------
# Aproximación de distancia recorrida
# -------------------------------------
st.subheader("Aproximación de Distancia Recorrida")

# 1. Ajusta el DataFrame para que tenga el tiempo de viaje en minutos y columnas "Origen Id", "Destino Id".
#    Supongamos que en global_df ya tienes "Duración (min)" calculada.
#    Si no, asegúrate de crearla antes.

# 2. Unir coordenadas de origen y destino con nomenclatura
df_distancia = global_df.copy()

# Asegúrate de tener la columna "Origen Id" y "Destino Id" con nombres idénticos a 'id' en nomenclatura.
# Merge con coordenadas de origen
df_distancia = df_distancia.merge(
    nomenclatura[['id', 'latitude', 'longitude']],
    left_on='Origen Id',
    right_on='id',
    how='left'
)
df_distancia.rename(columns={
    'latitude': 'lat_origin',
    'longitude': 'lon_origin'
}, inplace=True)
df_distancia.drop(columns=['id'], inplace=True)

# Merge con coordenadas de destino
df_distancia = df_distancia.merge(
    nomenclatura[['id', 'latitude', 'longitude']],
    left_on='Destino Id',
    right_on='id',
    how='left'
)
df_distancia.rename(columns={
    'latitude': 'lat_destination',
    'longitude': 'lon_destination'
}, inplace=True)
df_distancia.drop(columns=['id'], inplace=True)

# Función para calcular la distancia
def calcular_distancia(row):
    origen = (row['lat_origin'], row['lon_origin'])
    destino = (row['lat_destination'], row['lon_destination'])
    if pd.isna(origen[0]) or pd.isna(destino[0]):
        # Si no tenemos coordenadas, devolvemos NaN
        return np.nan
    if origen == destino:
        # Asumimos velocidad promedio 15 km/h
        return (row['Duración (min)'] / 60) * 15
    else:
        return geodesic(origen, destino).km

df_distancia['distance_km'] = df_distancia.apply(calcular_distancia, axis=1)

# Mostrar los primeros 10 viajes con su distancia
st.write("Ejemplo de Distancia Calculada (Primeros 10 registros):")
st.dataframe(df_distancia[["Origen Id", "Destino Id", "Duración (min)", "distance_km"]].head(10))
