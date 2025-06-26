
import streamlit as st
import pandas as pd
import datetime
import os
import json

USERS_FILE = "usuarios.json"
DATA_FILE = "apuestas.csv"

# Cargar usuarios
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

# Login
st.set_page_config(page_title="Gestión de Apuestas", layout="centered")
st.title("📊 App de Gestión de Apuestas")
st.subheader("🔐 Inicio de sesión")

username = st.text_input("Usuario")
password = st.text_input("Contraseña", type="password")

if username and password:
    if username in users:
        if users[username] == password:
            st.success(f"Sesión iniciada como **{username}**")
            session_user = username
        else:
            st.error("❌ Contraseña incorrecta")
            st.stop()
    else:
        if st.button("Registrar nuevo usuario"):
            users[username] = password
            with open(USERS_FILE, "w") as f:
                json.dump(users, f)
            st.success("✅ Usuario registrado correctamente. Recarga la página para continuar.")
            st.stop()
else:
    st.info("Introduce usuario y contraseña.")
    st.stop()

# Cargar apuestas
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Usuario", "Fecha", "Evento", "Competición", "Deporte", "Tipo de Apuesta",
        "Stake (1-10)", "Stake (€)", "Cuota", "Resultado", "Ganancia/Pérdida (€)", "Bank (€)"
    ])

# Tabs
tabs = st.tabs(["📋 Mis Apuestas", "👀 Ver Otras", "📈 Comparativa"])

with tabs[0]:
    st.header("📋 Historial y Registro de Apuestas")

    with st.form("form_apuesta"):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", datetime.date.today())
            evento = st.text_input("Evento")
            competicion = st.text_input("Competición")
        with col2:
            deporte = st.selectbox("Deporte", ["Fútbol", "Baloncesto", "Tenis", "Otro"])
            tipo = st.text_input("Tipo de Apuesta")
            stake = st.slider("Stake (1-10)", 1, 10, 1)
        cuota = st.number_input("Cuota", min_value=1.01, step=0.01, format="%.2f")

        bank_anterior = df[df["Usuario"] == session_user]["Bank (€)"].iloc[-1] if not df[df["Usuario"] == session_user].empty else 200
        stake_estimado = round(stake * bank_anterior / 100, 2)
        st.markdown(f"💰 <b>Importe a apostar: {stake_estimado} €</b>", unsafe_allow_html=True)

        enviar = st.form_submit_button("Añadir Apuesta")

    if enviar:
        nueva = {
            "Usuario": session_user,
            "Fecha": fecha,
            "Evento": evento,
            "Competición": competicion,
            "Deporte": deporte,
            "Tipo de Apuesta": tipo,
            "Stake (1-10)": stake,
            "Stake (€)": stake_estimado,
            "Cuota": cuota,
            "Resultado": "Pendiente",
            "Ganancia/Pérdida (€)": 0,
            "Bank (€)": bank_anterior
        }
        df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("✅ Apuesta registrada")

    # Actualizar resultados
    st.subheader("✏️ Actualizar Resultados")
    pendientes = df[(df["Usuario"] == session_user) & (df["Resultado"] == "Pendiente")]
    if pendientes.empty:
        st.info("No tienes apuestas pendientes.")
    else:
        for idx, row in pendientes.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"📅 {row['Fecha']} - {row['Evento']} ({row['Cuota']})")
            with col2:
                nuevo_res = st.selectbox("Resultado", ["Pendiente", "Ganada", "Perdida", "Nula"], key=idx)
                if nuevo_res != "Pendiente":
                    stake_euros = row["Stake (€)"]
                    if nuevo_res == "Ganada":
                        ganancia = round(stake_euros * (row["Cuota"] - 1), 2)
                    elif nuevo_res == "Perdida":
                        ganancia = -stake_euros
                    else:
                        ganancia = 0
                    bank_actual = row["Bank (€)"] + ganancia
                    df.at[idx, "Resultado"] = nuevo_res
                    df.at[idx, "Ganancia/Pérdida (€)"] = ganancia
                    df.at[idx, "Bank (€)"] = bank_actual
                    df.to_csv(DATA_FILE, index=False)
                    st.success("✅ Resultado actualizado")

    st.subheader("📄 Historial de Apuestas")
    st.dataframe(df[df["Usuario"] == session_user], use_container_width=True)

with tabs[1]:
    st.header("👀 Ver apuestas de otros usuarios")
    opciones = df["Usuario"].unique().tolist()
    elegido = st.selectbox("Selecciona un usuario", opciones)
    st.dataframe(df[df["Usuario"] == elegido], use_container_width=True)

with tabs[2]:
    st.header("📈 Comparativa entre usuarios")
    if df.empty:
        st.info("Aún no hay datos suficientes.")
    else:
        resumen = df.groupby("Usuario").agg({
            "Ganancia/Pérdida (€)": "sum",
            "Stake (€)": "sum",
            "Resultado": lambda x: (x == "Ganada").sum(),
            "Evento": "count"
        }).rename(columns={
            "Ganancia/Pérdida (€)": "Beneficio (€)",
            "Stake (€)": "Total Stake (€)",
            "Resultado": "Apuestas Ganadas",
            "Evento": "Total Apuestas"
        })
        resumen["Yield (%)"] = (resumen["Beneficio (€)"] / resumen["Total Stake (€)"]) * 100
        resumen["% Éxito"] = (resumen["Apuestas Ganadas"] / resumen["Total Apuestas"]) * 100
        st.dataframe(resumen[["Beneficio (€)", "Yield (%)", "% Éxito", "Total Apuestas"]], use_container_width=True)
        st.line_chart(df[df["Resultado"] != "Pendiente"].groupby("Usuario")["Ganancia/Pérdida (€)"].sum())
