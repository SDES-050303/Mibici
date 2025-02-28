import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from geopy.distance import geodesic

st.image("./IMG/Foto de estacion mi bici.jpg", use_column_width=True)


st.title("Análisis Mibici")
st.header("Introducción")
st.subheader("Análisis de datos de Mibici")
st.markdown("""En este repertorio podemos notar una analizis de datos de como las bicicletas **Mibici** Fueron utilizadas atravez de los 10 años,
 que han estado activas vamos a descubrir datos que nunca esperariamos conocer si no fuera por el analisis profundo que se registro y se compartio en
**https://www.mibici.net/es/datos-abiertos/** Por favor de utilizar los datos de manera correcta""")
# ------------------- Configuración del Sidebar -------------------
st.sidebar.title("Panel de Control")
st.sidebar.markdown("### Opciones de Filtrado")
st.sidebar.image("./IMG/Mibici_logo.jpg", use_column_width=True)

# ------------------- Cargar archivos limpios por año -------------------
# Todas las lecturas se hacen con encoding='latin-1'
datos2014 = pd.read_csv("./datos/2014/Mibici_2014_limpios.csv", encoding='latin-1')


# Crear un diccionario con los DataFrames por año
dfs_por_año = {
    "2014": datos2014,
}

# Asegurarse de que cada DataFrame tenga las columnas "Año" y "Mes"
# y renombrar las columnas según lo requerido
for year, df in dfs_por_año.items():
    # Renombrar columnas para homogeneizar los nombres
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

# Crear la variable global uniendo todos los DataFrames
global_df = pd.concat(list(dfs_por_año.values()), ignore_index=True)

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

# Gráfica Global: Número de Viajes por Mes y Año --------------------------------------------------------------------------------------
st.subheader("Gráfica Global: Número de Viajes por Mes y Año")
df_mes = global_df.copy()
# Las columnas "Año" y "Mes" ya se crearon anteriormente
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

#-----------------------------------------------Promedios de tiempo de viaje-----------------------------------------

# ------------------- Cálculo de la Duración de los Viajes (Global) -------------------
# Convertir a formato datetime (si no se ha hecho previamente)
global_df["Inicio del viaje"] = pd.to_datetime(global_df["Inicio del viaje"], errors="coerce")
global_df["Fin del viaje"] = pd.to_datetime(global_df["Fin del viaje"], errors="coerce")
# Calcular la duración en minutos
global_df["Duración (min)"] = (global_df["Fin del viaje"] - global_df["Inicio del viaje"]).dt.total_seconds() / 60

# ------------------- Promedio de Tiempo de Viaje por Estación -------------------
# Agrupar por "Origen Id" y calcular el promedio de duración
promedio_por_estacion = global_df.groupby("Origen Id")["Duración (min)"].mean().reset_index()
promedio_por_estacion.columns = ["Estación", "Promedio de duración (min)"]

# Ordenar de mayor a menor (puedes invertir el orden si lo deseas)
promedio_por_estacion = promedio_por_estacion.sort_values(by="Promedio de duración (min)", ascending=False)

# Seleccionar los 10 primeros
top10_promedios = promedio_por_estacion.head(10)

st.subheader("Top 10 Promedios de Tiempo de Viaje por Estación")
st.dataframe(top10_promedios.reset_index(drop=True))

# ------------------- Gráfica de los Top 10 Promedios de Tiempo de Viaje -------------------
fig3, ax3 = plt.subplots(figsize=(12, 6))
sns.barplot(data=top10_promedios, x="Estación", y="Promedio de duración (min)", palette="rocket", ax=ax3)
ax3.set_xlabel("Estación", fontsize=12)
ax3.set_ylabel("Promedio de Duración (min)", fontsize=12)
ax3.set_title("Top 10 Promedios de Tiempo de Viaje por Estación", fontsize=14)
ax3.tick_params(axis='x', rotation=45)
plt.tight_layout()
st.pyplot(fig3)
