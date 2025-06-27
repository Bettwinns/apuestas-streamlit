import streamlit as st
import pandas as pd
import datetime
import os
import json

USERS_FILE = "usuarios.json"
DATA_FILE = "apuestas.csv"

st.set_page_config(page_title="Gestión de Apuestas", layout="wide")

# Cargar usuarios
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

# Inicializar sesión
if "logueado" not in st.session_state:
    st.session_state.logueado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""

if not st.session_state.logueado:
    st.title("📊 App de Gestión de Apuestas")
    st.subheader("🔐 Inicio de sesión")

    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if username and password:
        if username in users:
            if users[username] == password:
                st.session_state.logueado = True
                st.session_state.usuario = username
                st.success(f"Sesión iniciada como **{username}**")
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
        else:
            if st.button("Registrar nuevo usuario"):
                users[username] = password
                with open(USERS_FILE, "w") as f:
                    json.dump(users, f)
                st.success("✅ Usuario registrado correctamente. Recarga la página para continuar.")
else:
    st.markdown(
        f"<div style='text-align:right; font-size:0.9em; color:gray;'>👤 Usuario: <b>{st.session_state.usuario}</b></div>",
        unsafe_allow_html=True
    )
    st.title("📊 App de Gestión de Apuestas")

    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=[
            "Usuario", "Fecha", "Evento", "Competición", "Deporte", "Tipo de Apuesta",
            "Pronósticos", "Stake (1-10)", "Stake (€)", "Cuota", "Resultado", "Ganancia/Pérdida (€)", "Bank (€)"
        ])

    tabs = st.tabs(["📋 Mis Apuestas", "👀 Ver Otras", "📈 Comparativa"])
    session_user = st.session_state.usuario

    with tabs[0]:
        st.header("📋 Mis Apuestas")

        with st.form("form_apuesta"):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha", datetime.date.today())
                evento = st.text_input("Evento")
                competicion = st.text_input("Competición")
                apuesta_tipo = st.radio("Tipo de apuesta", ["Simple", "Combinada"])
            with col2:
                deporte = st.selectbox("Deporte", ["Fútbol", "Baloncesto", "Tenis", "Otro"])
                cuota = st.number_input("Cuota total", min_value=1.01, step=0.01, format="%.2f")
                stake = st.slider("Stake (1-10)", 1, 10, 1)

            pronosticos = []
            if apuesta_tipo == "Combinada":
                with st.expander("Añadir pronósticos de la combinada"):
                    num_pronos = st.number_input("¿Cuántos pronósticos?", min_value=2, max_value=10, step=1)
                    for i in range(int(num_pronos)):
                        pron = st.text_input(f"Pronóstico {i+1}", key=f"pron_{i}")
                        pronosticos.append(pron)
            else:
                pronosticos.append(st.text_input("Pronóstico simple"))

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
                "Tipo de Apuesta": apuesta_tipo,
                "Pronósticos": "; ".join(pronosticos),
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

        st.subheader("✏️ Gestionar mis apuestas")
        for idx, row in df[df["Usuario"] == session_user].iterrows():
            with st.expander(f"{row['Fecha']} - {row['Evento']} ({row['Tipo de Apuesta']})"):
                st.markdown(f"Pronósticos: {row['Pronósticos']}")
                st.markdown(f"Cuota: {row['Cuota']}")
                st.markdown(f"Stake: {row['Stake (€)']} €")
                st.markdown(f"Resultado actual: {row['Resultado']}")
                if row['Resultado'] == "Pendiente":
                    col1, col2 = st.columns(2)
                    nuevo_res = col1.selectbox("Actualizar resultado", ["Pendiente", "Ganada", "Perdida", "Nula"], key=idx)
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
                        st.rerun()
                    if col2.button("🗑️ Eliminar", key=f"del_{idx}"):
                        df = df.drop(idx)
                        df.to_csv(DATA_FILE, index=False)
                        st.warning("Apuesta eliminada")
                        st.rerun()

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
