import streamlit as st
import os
import glob
import re
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
from nltk.util import ngrams
from nltk.tokenize import RegexpTokenizer
from textblob import TextBlob

# Asegurar que NLTK use la carpeta local si se sube a Streamlit Cloud
nltk.data.path.append('./nltk_data')
nltk.download('stopwords', quiet=True)

# --- Descripción e instrucciones ---
st.title("🎶 Análisis de Letras de Canciones")
st.markdown("""
Este proyecto permite analizar letras de canciones organizadas por carpeta (por ejemplo, géneros o décadas musicales).  
Puedes elegir entre analizar canciones individualmente o todas juntas para obtener una visión general del contenido.

**¿Qué puedes hacer aquí?**
- Ver cuántas palabras tiene cada canción
- Identificar palabras comunes y únicas
- Ver un WordCloud con las palabras más frecuentes
- Analizar combinaciones de palabras (N-gramas)
- Buscar patrones con expresiones regulares
- Evaluar el sentimiento (positivo/negativo) en canciones en inglés
""")

st.info("""
📌 **Instrucciones**:
1. Usa el panel lateral para seleccionar el idioma y la carpeta de canciones.
2. Escoge el modo de análisis: por canción o todas las canciones de la carpeta.
3. Selecciona una o más canciones si estás en modo individual.
4. Explora los resultados visuales e interpretativos.
""")


# --- Configuración Inicial ---
st.set_page_config(page_title="Análisis de Letras de Canciones", layout="wide")
DATA_DIR = "Data songs"  # Carpeta principal donde están las subcarpetas "80's", "Rock", etc.

# --- Funciones auxiliares ---
def cargar_archivos(carpeta):
    ruta = os.path.join(DATA_DIR, carpeta, "*.txt")  # Se asegura de que las canciones estén en la subcarpeta
    archivos = glob.glob(ruta)
    nombres = [os.path.basename(archivo) for archivo in archivos]
    return dict(zip(nombres, archivos))

# --- Panel lateral ---
st.sidebar.title("🎛️ Panel de Configuración")

# Selección de idioma
idioma = st.sidebar.selectbox("Idioma del análisis", ["español", "inglés"])
stop_words = set(stopwords.words('spanish' if idioma == "español" else 'english'))

# Selección de carpeta
carpetas = [nombre for nombre in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, nombre))]
carpeta_seleccionada = st.sidebar.selectbox("Carpeta (género/época)", carpetas)

# Modo de análisis
modo = st.sidebar.radio("Modo de análisis", ["Por canción", "Todas las canciones"])

# Mostrar las canciones disponibles
archivos = cargar_archivos(carpeta_seleccionada)
st.sidebar.write("Canciones disponibles:", list(archivos.keys()))  # Verifica que las canciones se cargan


# --- Funciones de Análisis ---
def limpiar_texto(texto):
    texto = texto.lower()
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(texto)
    tokens = [word for word in tokens if word not in stop_words]
    return tokens

def obtener_ngramas(tokens, n):
    return list(ngrams(tokens, n))

def mostrar_wordcloud(tokens):
    texto = ' '.join(tokens)
    wc = WordCloud(width=800, height=400, background_color='white').generate(texto)
    st.image(wc.to_array())

def mostrar_distribucion(tokens):
    frec = Counter(tokens)
    comunes = frec.most_common(20)
    palabras, cantidades = zip(*comunes)
    plt.figure(figsize=(10,5))
    plt.bar(palabras, cantidades)
    plt.xticks(rotation=45)
    st.pyplot(plt)

import re

def mostrar_analisis(titulo, texto, tokens, modo="Por canción"):
    # Calculando las métricas
    frec = Counter(tokens)
    total_palabras = len(tokens)
    num_oraciones = texto.count('.') + texto.count('!') + texto.count('?')
    promedio = total_palabras / max(1, num_oraciones)
    palabras_unicas = set(tokens)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Palabras", total_palabras)
    col2.metric("Promedio por oración", f"{promedio:.2f}")
    col3.metric("Palabras Únicas", len(palabras_unicas))

    # Palabras comunes
    st.subheader("🔝 Palabras más comunes")
    for palabra, freq in frec.most_common(10):
        st.write(f"{palabra}: {freq}")

    # WordCloud
    st.subheader("☁️ WordCloud")
    mostrar_wordcloud(tokens)

    # Distribución
    st.subheader("📊 Distribución de Vocabulario")
    mostrar_distribucion(tokens)

    # N-gramas
    st.subheader("📎 N-Gramas")
    for n in [2, 3, 4]:
        ngramas = obtener_ngramas(tokens, n)
        frec_ng = Counter(ngramas).most_common(5)
        st.markdown(f"**Top {n}-gramas:**")
        for ng, freq in frec_ng:
            st.write(f"{' '.join(ng)}: {freq}")

    # Regex
    st.subheader("🧪 Búsqueda con Expresiones Regulares")
    patron = st.text_input(f"Escribe un patrón regex para buscar en '{titulo}'", key=titulo)
    
    if patron:  # Si hay un patrón de búsqueda ingresado
        try:
            # Si estamos en el modo "Todas las canciones", concatenamos todo el texto
            if modo == "Todas las canciones":
                # Unir todo el texto de las canciones en un solo bloque
                texto_completo = " ".join(texto)  # Texto combinado de todas las canciones
                texto_normalizado = re.sub(r'[^\w\s]', '', texto_completo.lower())  # Eliminar puntuación y pasar a minúsculas
            else:
                texto_normalizado = re.sub(r'[^\w\s]', '', texto.lower())  # Eliminar puntuación y pasar a minúsculas

            # Usamos re.findall para encontrar las coincidencias del patrón en el texto normalizado
            coincidencias = re.findall(patron.lower(), texto_normalizado)  # Aseguramos que el patrón también sea en minúsculas
            
            # Mostramos el número de coincidencias
            st.write(f"Coincidencias encontradas: {len(coincidencias)}")
            
            # Mostramos las primeras 20 coincidencias si existen
            if coincidencias:
                st.write(f"Primeras 20 coincidencias: {', '.join(coincidencias[:20])}")
            else:
                st.write("No se encontraron coincidencias.")
        except re.error as e:
            # Si el patrón no es válido, muestra un error
            st.error(f"Error en el patrón de expresión regular: {e}")

    # --- Análisis de Sentimiento ---
    st.subheader("💬 Análisis de Sentimiento")

    if idioma == "inglés":
        try:
            blob = TextBlob(' '.join(tokens))
            polaridad = blob.sentiment.polarity
            subjetividad = blob.sentiment.subjectivity

            st.write(f"**Polaridad:** {polaridad:.2f}  *(−1: negativo, +1: positivo)*")
            st.write(f"**Subjetividad:** {subjetividad:.2f}  *(0: objetivo, 1: subjetivo)*")
        except Exception as e:
            st.warning("❌ Ocurrió un error al analizar el sentimiento con TextBlob.")
    else:
        st.info("ℹ️ El análisis de sentimiento está disponible solo para canciones en inglés.")


# --- Lógica principal ---
if modo == "Por canción":
    canciones_seleccionadas = st.multiselect("Selecciona una o más canciones", list(archivos.keys()))
else:
    canciones_seleccionadas = list(archivos.keys())  # selecciona todas automáticamente
    st.info(f"Se analizarán todas las canciones en la carpeta **{carpeta_seleccionada}**.")

if canciones_seleccionadas:
    # Variables globales para análisis conjunto
    tokens_todas = []

    for nombre in canciones_seleccionadas:
        st.header(f"📄 {nombre}")
        with open(archivos[nombre], 'r', encoding='utf-8') as f:
            texto = f.read()
        
        tokens = limpiar_texto(texto)
        tokens_todas.extend(tokens)  # acumular para análisis grupal

        if modo == "Por canción":
            # mostrar análisis completo por canción (como ya tienes)
            mostrar_analisis(nombre, texto, tokens)  # refactorizable en función

    if modo == "Todas las canciones":
        st.header(f"🧾 Análisis Combinado de '{carpeta_seleccionada}'")
        texto_completo = " ".join(tokens_todas)  # O puedes concatenar texto real si lo prefieres
        mostrar_analisis("Todas las canciones", texto_completo, tokens_todas, modo="Todas las canciones")

