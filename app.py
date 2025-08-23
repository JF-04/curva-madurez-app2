import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime

# ========================
# CONFIG DB SQLITE LOCAL
# ========================
DB_NAME = "calibraciones.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabla principal: resultados
    c.execute("""
        CREATE TABLE IF NOT EXISTS calibraciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP,
            titulo TEXT,
            a REAL,
            b REAL,
            r2 REAL
        )
    """)
    # Tabla secundaria: datos experimentales
    c.execute("""
        CREATE TABLE IF NOT EXISTS datos_experimentales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            calibracion_id INTEGER,
            madurez REAL,
            resistencia REAL,
            FOREIGN KEY(calibracion_id) REFERENCES calibraciones(id)
        )
    """)
    conn.commit()
    conn.close()

def guardar_resultados(titulo, a, b, r2, df):
    """Guarda resultados y datos experimentales en SQLite local"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Insertar en tabla principal
    c.execute("""
        INSERT INTO calibraciones (fecha, titulo, a, b, r2)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (fecha, titulo, a, b, r2))
    calibracion_id = c.lastrowid

    # Insertar datos experimentales
    for _, row in df.iterrows():
        c.execute("""
            INSERT INTO datos_experimentales (calibracion_id, madurez, resistencia)
            VALUES (?, ?, ?)
        """, (calibracion_id, float(row["Madurez (°C·h)"]), float(row["Resistencia (MPa)"])))

    conn.commit()
    conn.close()
    return calibracion_id

# Inicializar DB
init_db()

# ========================
# APP STREAMLIT
# ========================
st.title("Calibración hormigones ASTMC1074. IoT Provoleta®")

custom_title = st.text_input("📌 Título del informe/archivo", "Informe de calibración")

st.markdown("""
Esta aplicación permite ingresar resultados de ensayos de resistencia a compresión 
y calcular la relación con la madurez (método de Nurse-Saul).
""")

# Tabla de datos
st.subheader("Cargar datos experimentales (Madurez y Resistencia)")
data = pd.DataFrame({
    "Madurez (°C·h)": [500, 1500, 5000, 15000, 30000],
    "Resistencia (MPa)": [5.0, 12.0, 20.0, 28.0, 35.0]
})
edited_data = st.data_editor(data, num_rows="dynamic")

# ========================
# FUNCIÓN PDF (igual a la tuya)
# ========================
def generar_pdf(edited_df: pd.DataFrame, a: float, b: float, r2: float) -> bytes:
    ...
    # (copiar exactamente tu función PDF sin cambios)
    ...

# ========================
# CÁLCULOS + GUARDADO EN DB
# ========================
if not edited_data.empty:
    edited_data = edited_data[edited_data["Madurez (°C·h)"] > 0].copy()
    edited_data["Log10(Madurez)"] = np.log10(edited_data["Madurez (°C·h)"])

    if len(edited_data) < 2:
        st.info("Cargá al menos dos puntos válidos para ajustar la regresión.")
        st.stop()

    X = edited_data["Log10(Madurez)"].values
    Y = edited_data["Resistencia (MPa)"].values

    a, b = np.polyfit(X, Y, 1)
    Y_pred = a * X + b
    ss_res = np.sum((Y - Y_pred) ** 2)
    ss_tot = np.sum((Y - np.mean(Y)) ** 2)
    r2 = float(1 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

    st.markdown("### 📌 Resultados")
    st.markdown(f"**Ordenada al origen (b):** {b:.2f}")
    st.markdown(f"**Pendiente (a):** {a:.2f}")
    st.markdown(f"**R²:** {r2:.2f}")

    # Gráfico Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edited_data["Madurez (°C·h)"], y=edited_data["Resistencia (MPa)"],
        mode="markers", name="Datos experimentales", marker=dict(size=8, color="blue")
    ))
    x_fit_plot = np.linspace(float(edited_data["Madurez (°C·h)"].min()), float(edited_data["Madurez (°C·h)"].max()), 200)
    y_fit_plot = a * np.log10(x_fit_plot) + b
    fig.add_trace(go.Scatter(x=x_fit_plot, y=y_fit_plot, mode="lines", name="Curva estimada", line=dict(color="red")))
    st.plotly_chart(fig, use_container_width=True)

    # Botón de PDF + Guardado en DB
    pdf_bytes = generar_pdf(edited_data.copy(), a, b, r2)
    if st.download_button("📄 Descargar informe en PDF", data=pdf_bytes, file_name="informe_calibracion.pdf", mime="application/pdf"):
        calibracion_id = guardar_resultados(custom_title, a, b, r2, edited_data)
        st.success(f"✅ Datos guardados en la base local (ID {calibracion_id})")
