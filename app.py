import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sqlite3
from datetime import datetime
from io import BytesIO
from fpdf import FPDF

# ---------- BASE DE DATOS ----------
def init_db():
    conn = sqlite3.connect("resultados.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            titulo TEXT,
            a REAL,
            b REAL,
            r2 REAL
        )
    """)
    conn.commit()
    conn.close()

def guardar_en_db(titulo, a, b, r2, df: pd.DataFrame):
    conn = sqlite3.connect("resultados.db")
    c = conn.cursor()
    c.execute("INSERT INTO resultados (fecha, titulo, a, b, r2) VALUES (?, ?, ?, ?, ?)",
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), titulo, a, b, r2))
    conn.commit()
    conn.close()

# ---------- PDF ----------
def generar_pdf(df: pd.DataFrame, a: float, b: float, r2: float, titulo: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, titulo, ln=True, align="C")

    pdf.set_font("Arial", "", 12)
    pdf.ln(10)
    pdf.cell(0, 10, f"Ecuación ajustada: Resistencia = {a:.3f} * log10(Madurez) + {b:.3f}", ln=True)
    pdf.cell(0, 10, f"Coeficiente de determinación (R²): {r2:.4f}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Datos:", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(0, 8, f"Madurez: {row['Madurez (°C·h)']} - Resistencia: {row['Resistencia (MPa)']}", ln=True)

    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, "IoT Provoleta®", 0, 0, "C")

    pdf_bytes = BytesIO()
    pdf.output(pdf_bytes, "F")
    pdf_bytes.seek(0)
    return pdf_bytes.read()

# ---------- APP ----------
def main():
    st.title("Calibración Norma ASTM C1074")

    titulo = st.text_input("Título del informe", "Ensayo de Calibración ASTM C1074")

    st.markdown("### Ingreso de Datos")
    st.write("Complete la tabla con valores de Madurez (°C·h) y Resistencia (MPa).")

    df = pd.DataFrame({"Madurez (°C·h)": [1000, 5000, 10000],
                       "Resistencia (MPa)": [5, 15, 25]})
    edited_data = st.data_editor(df, num_rows="dynamic")

    if len(edited_data) >= 2:
        x = np.array(edited_data["Madurez (°C·h)"], dtype=float)
        y = np.array(edited_data["Resistencia (MPa)"], dtype=float)

        # Ajuste: y = a * log10(x) + b
        X = np.log10(x).reshape(-1, 1)
        X_b = np.c_[np.ones_like(X), X]  # intercepto + log10(x)
        theta = np.linalg.inv(X_b.T @ X_b) @ (X_b.T @ y)
        b, a = theta  # intercepto, pendiente

        y_pred = a * np.log10(x) + b
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - ss_res / ss_tot

        # Gráfico
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=edited_data["Madurez (°C·h)"], y=edited_data["Resistencia (MPa)"],
            mode="markers", name="Datos experimentales",
            marker=dict(size=8, color="blue")
        ))
        x_fit_plot = np.linspace(float(x.min()), float(x.max()), 200)
        y_fit_plot = a * np.log10(x_fit_plot) + b
        fig.add_trace(go.Scatter(
            x=x_fit_plot, y=y_fit_plot, mode="lines", name="Curva estimada",
            line=dict(color="red")
        ))
        fig.update_layout(
            xaxis_title="Madurez (°C·h)",
            yaxis_title="Resistencia a compresión (MPa)",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Botón para generar PDF + guardar en DB
        if st.button("Generar PDF"):
            pdf_bytes = generar_pdf(edited_data.copy(), a, b, r2, titulo)
            st.download_button("Descargar PDF", pdf_bytes, file_name="informe.pdf")

            guardar_en_db(titulo, a, b, r2, edited_data.copy())
            st.success("Informe guardado en la base de datos.")

if __name__ == "__main__":
    init_db()
    main()
