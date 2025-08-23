import sqlite3
from datetime import datetime

# Inicializa la base de datos
def init_db():
    conn = sqlite3.connect("resultados.db")
    cursor = conn.cursor()

    # tabla con parámetros de la regresión
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resultados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        titulo TEXT,
        a REAL,
        b REAL,
        r2 REAL
    )
    """)

    # tabla con los datos experimentales asociados
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS datos_experimentales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resultado_id INTEGER,
        madurez REAL,
        resistencia REAL,
        FOREIGN KEY(resultado_id) REFERENCES resultados(id)
    )
    """)

    conn.commit()
    conn.close()

# Guarda resultados y datos experimentales
def guardar_en_db(titulo, a, b, r2, datos_df):
    conn = sqlite3.connect("resultados.db")
    cursor = conn.cursor()

    # Insertar encabezado
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO resultados (fecha, titulo, a, b, r2)
        VALUES (?, ?, ?, ?, ?)
    """, (fecha, titulo, a, b, r2))
    resultado_id = cursor.lastrowid

    # Insertar cada fila de datos experimentales
    for _, row in datos_df.iterrows():
        cursor.execute("""
            INSERT INTO datos_experimentales (resultado_id, madurez, resistencia)
            VALUES (?, ?, ?)
        """, (resultado_id, float(row["Madurez (°C·h)"]), float(row["Resistencia (MPa)"])))

    conn.commit()
    conn.close()
    
if st.button("Generar PDF"):
    pdf_bytes = generar_pdf(edited_data.copy(), a, b, r2)
    st.download_button("Descargar PDF", pdf_bytes, file_name="informe.pdf")

    # Guardar en base de datos
    guardar_en_db(titulo, a, b, r2, edited_data.copy())
    st.success("Informe guardado en la base de datos.")
