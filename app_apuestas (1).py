
import streamlit as st
import pandas as pd
import datetime
import os

# Inicialización del archivo
FILE_PATH = "apuestas.csv"

# Cargar o crear DataFrame
if os.path.exists(FILE_PATH):
    df = pd.read_csv(FILE_PATH)
else:
    df = pd.DataFrame(columns=[
        "Fecha", "Evento", "Competición", "Deporte", "Tipo de Apuesta",
        "Stake (1-10)", "Stake (€)", "Cuota", "Resultado",
        "Ganancia/Pérdida (€)", "Bank (€)"
    ])

# Función para calcular stake, ganancia y bank
def calcular_fila(row, bank_anterior):
    stake_euros = row["Stake (1-10)"] * bank_anterior / 100
    if row["Resultado"] == "Ganada":
        ganancia = stake_euros * (row["Cuota"] - 1)
    elif row["Resultado"] == "Perdida":
        ganancia = -stake_euros
    else:
        ganancia = 0
    bank_actual = bank_anterior + ganancia
    return round(stake_euros, 2), round(ganancia, 2), round(bank_actual, 2)

# Interfaz de la app
st.title("📊 App de Gestión de Apuestas")

st.sidebar.header("➕ Nueva Apuesta")

# Formulario de entrada
with st.sidebar.form("form_apuesta"):
    fecha = st.date_input("Fecha", datetime.date.today())
    evento = st.text_input("Evento")
    competicion = st.text_input("Competición")
    deporte = st.selectbox("Deporte", ["Fútbol", "Baloncesto", "Tenis", "Otro"])
    tipo = st.text_input("Tipo de Apuesta")
    stake = st.slider("Stake (1-10)", 1, 10, 1)
    cuota = st.number_input("Cuota", min_value=1.01, step=0.01)
    resultado = st.selectbox("Resultado", ["Ganada", "Perdida", "Nula"])
    submit = st.form_submit_button("Añadir Apuesta")

if submit:
    bank_anterior = df["Bank (€)"].iloc[-1] if not df.empty else 200
    stake_euros, ganancia, bank = calcular_fila({
        "Stake (1-10)": stake,
        "Cuota": cuota,
        "Resultado": resultado
    }, bank_anterior)

    nueva_apuesta = {
        "Fecha": fecha,
        "Evento": evento,
        "Competición": competicion,
        "Deporte": deporte,
        "Tipo de Apuesta": tipo,
        "Stake (1-10)": stake,
        "Stake (€)": stake_euros,
        "Cuota": cuota,
        "Resultado": resultado,
        "Ganancia/Pérdida (€)": ganancia,
        "Bank (€)": bank
    }

    df = pd.concat([df, pd.DataFrame([nueva_apuesta])], ignore_index=True)
    df.to_csv(FILE_PATH, index=False)
    st.success("✅ Apuesta añadida correctamente")

# Mostrar historial
st.subheader("📋 Historial de Apuestas")
st.dataframe(df.style.format({"Stake (€)": "{:.2f}", "Ganancia/Pérdida (€)": "{:.2f}", "Bank (€)": "{:.2f}"}), use_container_width=True)

# Estadísticas
st.subheader("📈 Estadísticas")
total = len(df)
ganadas = len(df[df["Resultado"] == "Ganada"])
perdidas = len(df[df["Resultado"] == "Perdida"])
nulas = len(df[df["Resultado"] == "Nula"])
beneficio = df["Ganancia/Pérdida (€)"].sum()
yield_total = (beneficio / df["Stake (€)"].sum() * 100) if df["Stake (€)"].sum() > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total apuestas", total)
col2.metric("Beneficio total (€)", f"{beneficio:.2f}")
col3.metric("Yield (%)", f"{yield_total:.2f}")

# Gráfico evolución bank
st.subheader("📊 Evolución del Bank")
if not df.empty:
    st.line_chart(df["Bank (€)"])
