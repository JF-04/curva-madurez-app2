import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
from fpdf import FPDF
from sklearn.linear_model import LinearRegression

# -------------------------------
# Función para generar el PDF
# -------------------------------
def generar_pdf(df: pd.DataFrame, a: float, b: float, r2: float, titulo: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    # Encabezado
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "IoT Provoleta®", ln=True, align="R")

    # Título
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Calibración Norma ASTM C1074", ln=True, align="C")
    pdf.ln(10)

    # Subtítulo personalizado
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, titulo, ln=True, align="C")
    pdf.ln(10)

    # Resultados de la regresión
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Ordenada al origen (a): ", ln=False)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"{a:.3f}", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Pendiente (b): ", ln=False)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"{b:.3f}", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Coeficiente de determinación R²: {r2:.3f}", ln=True)

    # Exportar tabla
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Datos utilizados:", ln=True)

    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(0, 8, f"Madurez: {row['Madurez']}  |  Resistencia: {row['Resistencia']}", ln=True)

    return pdf.output(dest="S").encode("latin-1")


# -------------------------------
# Interfaz Streamlit
# -------------------------------
st.set_page_config(page_title="Calibración ASTM C1074", layout="centered")

st.title("Calibración Norma ASTM C1074")

# Subtítulo personalizable
titulo = st.text_input("Ingrese título del informe:", "")

# Subir datos
st.write("Cargue sus datos de madurez (°C·h) y resistencia (MPa):")
file = st.file_uploader("Subir CSV con columnas: Madurez, Resistencia", type=["csv"])

if file:
    df = pd.read_csv(file)

    if "Madurez" not in df.columns or "Resistencia" not in df.columns:
        st.error("El archivo debe contener las columnas: Madurez, Resistencia")
    else:
        # Calcular log10(Madurez)
        df["logMadurez"] = np.log10(df["Madurez"])

        # Ajuste lineal
        X = df[["logMadurez"]].values
        y = df["Resistencia"].values
        model = LinearRegression().fit(X, y)

        a = model.intercept_
        b = model.coef_[0]
        r2 = model.score(X, y)

        # Mostrar resultados
        st.subheader("Resultados de la regresión")
        st.write(f"**Ordenada al origen (a):** {a:.3f}")
        st.write(f"**Pendiente (b):** {b:.3f}")
        st.write(f"Coeficiente de determinación (R²): {r2:.3f}")

        # Gráfico
        fig = px.scatter(
            df,
            x="Madurez",
            y="Resistencia",
            title="Curva de Madurez (ASTM C1074)",
            labels={"Madurez": "Madurez (°C·h)", "Resistencia": "Resistencia (MPa)"}
        )

        # Línea de regresión
        x_vals = np.linspace(df["Madurez"].min(), df["Madurez"].max(), 100)
        y_vals = a + b * np.log10(x_vals)
        fig.add_scatter(x=x_vals, y=y_vals, mode="lines", name="Ajuste")

        st.plotly_chart(fig, use_container_width=True)

        # Exportar PDF
        pdf_bytes = generar_pdf(df, a, b, r2, titulo)
        st.download_button(
            "⬇️ Descargar informe PDF",
            data=pdf_bytes,
            file_name="calibracion_astm.pdf",
            mime="application/pdf",
        )
