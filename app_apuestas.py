
import streamlit as st
import pandas as pd
import datetime
import os
import json

USERS_FILE = "usuarios.json"
DATA_FILE = "apuestas.csv"

st.set_page_config(page_title="Gestión de Apuestas Simples", layout="wide")

# usuarios
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

if "logueado" not in st.session_state:
    st.session_state.logueado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "bank_inicial" not in st.session_state:
    st.session_state.bank_inicial = 200

# login
if not st.session_state.logueado:
    st.title("📊 App de Gestión de Apuestas Simples")
    st.subheader("🔐 Inicio de sesión")

    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if username and password:
        if username in users:
            if users[username]["password"] == password:
                st.session_state.logueado = True
                st.session_state.usuario = username
                st.session_state.bank_inicial = users[username]["bank"]
                st.success(f"Sesión iniciada como **{username}**")
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
        else:
            st.info("Nuevo usuario. Completa el registro:")
            nuevo_bank = st.number_input("Bank inicial (€)", min_value=10, value=200, step=10)
            if st.button("Registrar"):
                users[username] = {"password": password, "bank": nuevo_bank}
                with open(USERS_FILE, "w") as f:
                    json.dump(users, f)
                st.success("✅ Usuario registrado correctamente. Inicia sesión para continuar.")
else:
    st.title("📊 Gestión de Apuestas Simples")

    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=[
            "Usuario", "Fecha", "Evento", "Competición", "Deporte",
            "Cuota", "Stake (1-10)", "Stake (€)", "Resultado",
            "Ganancia/Pérdida (€)", "Bank (€)"
        ])

    tabs = st.tabs(["📋 Mis Apuestas", "👀 Ver Otras"])

    session_user = st.session_state.usuario
    user_bank_inicial = st.session_state.bank_inicial

    # ----------------------------
    # PESTAÑA 1: MIS APUESTAS
    # ----------------------------
    with tabs[0]:
        st.header("📋 Mis Apuestas")

        with st.form("nueva_apuesta"):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha", datetime.date.today())
                evento = st.text_input("Evento")
                competicion = st.text_input("Competición")
            with col2:
                deporte = st.selectbox("Deporte", ["Fútbol", "Baloncesto", "Tenis", "Otro"])
                cuota = st.number_input("Cuota", min_value=1.01, step=0.01)
                stake = st.slider("Stake (1-10)", 1, 10, 1)

            # bank actual
            user_bets = df[df["Usuario"] == session_user]
            last_bank = user_bets["Bank (€)"].iloc[-1] if not user_bets.empty else user_bank_inicial
            stake_euros = round(stake * last_bank / 100, 2)

            st.markdown(f"💰 <b>Importe a apostar: {stake_euros:.2f} €</b>", unsafe_allow_html=True)

            enviar = st.form_submit_button("Añadir Apuesta")

            if enviar:
                nueva = {
                    "Usuario": session_user,
                    "Fecha": fecha,
                    "Evento": evento,
                    "Competición": competicion,
                    "Deporte": deporte,
                    "Cuota": cuota,
                    "Stake (1-10)": stake,
                    "Stake (€)": stake_euros,
                    "Resultado": "Pendiente",
                    "Ganancia/Pérdida (€)": 0,
                    "Bank (€)": last_bank
                }
                df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success("✅ Apuesta registrada")
                st.rerun()

        # ------------------------
        # gestión resultados
        # ------------------------
        st.subheader("✏️ Gestionar resultados")

        for idx, row in df[df["Usuario"] == session_user].iterrows():
            with st.expander(f"{row['Fecha']} - {row['Evento']}"):
                st.markdown(f"**Cuota:** {row['Cuota']}")
                st.markdown(f"**Stake:** {row['Stake (€)']} €")
                st.markdown(f"**Resultado actual:** {row['Resultado']}")

                if row['Resultado'] == "Pendiente":
                    nuevo_res = st.selectbox(
                        "Resultado",
                        ["Pendiente", "Ganada", "Perdida", "Nula"],
                        key=f"res_{idx}"
                    )

                    if nuevo_res != "Pendiente":
                        if st.button("Actualizar resultado", key=f"btn_{idx}"):
                            stake_euros = row["Stake (€)"]
                            if nuevo_res == "Ganada":
                                ganancia = round(stake_euros * (row["Cuota"] - 1), 2)
                            elif nuevo_res == "Perdida":
                                ganancia = -stake_euros
                            else:
                                ganancia = 0

                            nuevo_bank = row["Bank (€)"] + ganancia
                            df.loc[idx, "Resultado"] = nuevo_res
                            df.loc[idx, "Ganancia/Pérdida (€)"] = ganancia
                            df.loc[idx, "Bank (€)"] = nuevo_bank

                            df.to_csv(DATA_FILE, index=False)
                            st.success(f"✅ Resultado actualizado como {nuevo_res}")
                            st.rerun()

                if st.button("🗑️ Eliminar apuesta", key=f"del_{idx}"):
                    df = df.drop(idx)
                    df.to_csv(DATA_FILE, index=False)
                    st.warning("Apuesta eliminada")
                    st.rerun()

    # ----------------------------
    # PESTAÑA 2: VER OTRAS
    # ----------------------------
    with tabs[1]:
        st.header("👀 Ver apuestas de otros usuarios")
        otros = df["Usuario"].unique().tolist()
        otros = [u for u in otros if u != session_user]

        ver_user = st.selectbox("Elegir usuario", otros) if otros else None

        if ver_user:
            user_df = df[df["Usuario"] == ver_user]
            for idx, row in user_df.iterrows():
                st.markdown(f"**{row['Fecha']} - {row['Evento']}**")
                st.markdown(f"- Cuota: {row['Cuota']}")
                st.markdown(f"- Stake: {row['Stake (€)']} €")
                st.markdown(f"- Resultado: {row['Resultado']}")
                st.markdown("---")
