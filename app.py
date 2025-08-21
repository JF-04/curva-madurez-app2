import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# --- Para PDF con Matplotlib ---
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

st.title("Calibración hormigones ASTMC1074. IoT Provoleta®")

# Título personalizado para informe/hoja
custom_title = st.text_input("📌 Título del informe/archivo", "Informe de calibración")

st.markdown("""
Esta aplicación permite ingresar resultados de ensayos de resistencia a compresión 
y calcular la relación con la madurez (método de Nurse-Saul).
""")

# ========================
# TABLA DE DATOS (editable por el usuario)
# ========================
st.subheader("Cargar datos experimentales (Madurez y Resistencia)")
data = pd.DataFrame({
    "Madurez (°C·h)": [500, 1500, 5000, 15000, 30000],
    "Resistencia (MPa)": [5.0, 12.0, 20.0, 28.0, 35.0]
})
edited_data = st.data_editor(data, num_rows="dynamic")

# ========================
# FUNCIÓN PDF
# ========================
def generar_pdf(edited_df: pd.DataFrame, a: float, b: float, r2: float) -> bytes:
    """Genera un PDF con resultados + tabla + gráfico renderizado."""
    # --- Gráfico Matplotlib ---
    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    ax.scatter(edited_df["Madurez (°C·h)"], edited_df["Resistencia (MPa)"], label="Datos experimentales", color="blue")
    x_fit = np.linspace(float(edited_df["Madurez (°C·h)"].min()), float(edited_df["Madurez (°C·h)"].max()), 200)
    y_fit = a * np.log10(x_fit) + b
    ax.plot(x_fit, y_fit, label="Curva estimada", color="red", linewidth=2)
    ax.set_xlabel("Madurez (°C·h)")
    ax.set_ylabel("Resistencia a compresión (MPa)")
    ax.legend(loc="best")
    img_buf = BytesIO()
    plt.tight_layout()
    plt.savefig(img_buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    img_buf.seek(0)

    # --- Construir PDF ---
    pdf_buf = BytesIO()
    doc = SimpleDocTemplate(pdf_buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Título del informe (desde la app)
    story.append(Paragraph(custom_title, styles["Title"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("📊 Datos experimentales", styles["Heading2"]))
    df_round = edited_df.copy().round(2)
    tabla_datos = [df_round.columns.tolist()] + df_round.values.tolist()
    t = Table(tabla_datos, hAlign="CENTER")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("📌 Resultados de la regresión", styles["Heading2"]))
    res_tab = Table([
        ["Ordenada al origen (b)", f"{b:.2f}"],
        ["Pendiente (a)", f"{a:.2f}"],
        ["R²", f"{r2:.2f}"],
    ], hAlign="CENTER")
    res_tab.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 1), colors.lightgrey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(res_tab)
    story.append(Spacer(1, 12))

    story.append(Paragraph("📈 Gráfico Madurez vs Resistencia", styles["Heading2"]))
    story.append(Image(img_buf, width=430, height=270))

    # Marca IoT Provoleta® abajo a la derecha
    story.append(Spacer(1, 30))
    story.append(Paragraph("<para align='right'>IoT Provoleta®</para>", styles["Normal"]))

    doc.build(story)
    pdf_buf.seek(0)
    return pdf_buf.getvalue()

# ========================
# CÁLCULOS
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
    st.markdown(f"<span style='color:green; font-weight:bold'>Pendiente (a): {a:.2f}</span>", unsafe_allow_html=True)
    st.markdown(f"<span style='color:green; font-weight:bold'>Ordenada al origen (b): {b:.2f}</span>", unsafe_allow_html=True)
    st.markdown(f"**R²:** {r2:.2f}")

    # --- Gráfico interactivo Plotly ---
if not edited_data.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edited_data["Madurez (°C·h)"], y=edited_data["Resistencia (MPa)"],
        mode="markers", name="Datos experimentales",
        marker=dict(size=8, color="blue")
    ))

    x_fit_plot = np.linspace(
        float(edited_data["Madurez (°C·h)"].min()),
        float(edited_data["Madurez (°C·h)"].max()), 200
    )
    y_fit_plot = a * np.log10(x_fit_plot) + b

    fig.add_trace(go.Scatter(
        x=x_fit_plot, y=y_fit_plot, mode="lines", name="Curva estimada",
        line=dict(color="red")
    ))


    fig.update_layout(
        xaxis_title="Madurez (°C·h)",
        yaxis_title="Resistencia a compresión (MPa)",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom", y=-0.3,
            xanchor="center", x=0.5
        )
    )

    st.plotly_chart(fig, use_container_width=True)


    # --- PDF ---
    pdf_bytes = generar_pdf(edited_data.copy(), a, b, r2)
    st.download_button(
        label="📄 Descargar informe en PDF",
        data=pdf_bytes,
        file_name="informe_calibracion.pdf",
        mime="application/pdf"
    )
