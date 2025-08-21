import streamlit as st
import pandas as pd
import plotly.express as px
import statsmodels.api as sm
from fpdf import FPDF
import base64

st.set_page_config(page_title="Calibración ASTM C1074", layout="wide")

st.title("📈 Calibración norma ASTM C1074")
st.caption("IoT Provoleta")

# ===============================
# 1. Carga de datos
# ===============================
st.subheader("Carga de datos de ensayo")
st.markdown("Ingrese la **Madurez (°C·h)** y la **Resistencia (MPa)**:")

# Ejemplo de tabla editable
data = {
    "Madurez (°C·h)": [1000, 2000, 3000, 4000],
    "Resistencia (MPa)": [10, 18, 25, 30]
}
df = pd.DataFrame(data)

edited_df = st.data_editor(df, num_rows="dynamic")

# ===============================
# 2. Ajuste de regresión lineal
# ===============================
if len(edited_df) >= 2:
    X = edited_df["Madurez (°C·h)"]
    y = edited_df["Resistencia (MPa)"]

    X_const = sm.add_constant(X)
    model = sm.OLS(y, X_const).fit()

    a, b = model.params  # a = intercepto, b = pendiente
    r2 = model.rsquared

    st.success(f"📊 Ecuación: **Resistencia = {a:.2f} + {b:.4f} × Madurez**")
    st.write(f"Coeficiente de determinación R² = **{r2:.4f}**")

    # ===============================
    # 3. Gráfico
    # ===============================
    fig = px.scatter(
        edited_df, x="Madurez (°C·h)", y="Resistencia (MPa)",
        trendline="ols", title="Curva de Calibración ASTM C1074"
    )
    st.plotly_chart(fig, use_container_width=True)

    # ===============================
    # 4. Exportar a PDF
    # ===============================
    def generar_pdf(df, a, b, r2):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, "IoT Provoleta", ln=True, align="R")
        pdf.cell(200, 10, "Calibración norma ASTM C1074", ln=True, align="C")

        pdf.set_font("Arial", "", 12)
        pdf.ln(10)
        pdf.multi_cell(0, 10, f"Ecuación de correlación:\n\nResistencia = {a:.2f} + {b:.4f} × Madurez\n\nR² = {r2:.4f}")

        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Datos utilizados:", ln=True)

        pdf.set_font("Arial", "", 11)
        for _, row in df.iterrows():
            pdf.cell(0, 8, f"Madurez: {row['Madurez (°C·h)']}, Resistencia: {row['Resistencia (MPa)']}", ln=True)

        return pdf.output(dest="S").encode("latin1")

    if st.button("📄 Generar PDF"):
        pdf_bytes = generar_pdf(edited_df, a, b, r2)
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="calibracion_astm.pdf">⬇️ Descargar PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

else:
    st.warning("⚠️ Cargue al menos dos puntos de datos para generar la curva.")
