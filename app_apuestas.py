import streamlit as st
import pandas as pd
import datetime
import os
import json
import ast

USERS_FILE = "usuarios.json"
DATA_FILE = "apuestas.csv"

st.set_page_config(page_title="Gestión de Apuestas", layout="wide")

# cargar usuarios
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

# sesión
if "logueado" not in st.session_state:
    st.session_state.logueado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "bank_inicial" not in st.session_state:
    st.session_state.bank_inicial = 200
if "tipo_apuesta" not in st.session_state:
    st.session_state.tipo_apuesta = "Simple"

# login
if not st.session_state.logueado:
    st.title("📊 App de Gestión de Apuestas")
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
    st.markdown(
        f"<div style='text-align:right; font-size:0.9em; color:gray;'>👤 {st.session_state.usuario} | Bank inicial: {st.session_state.bank_inicial} €</div>",
        unsafe_allow_html=True
    )
    st.title("📊 App de Gestión de Apuestas")

    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if "Resultados Pronósticos" not in df.columns:
            df["Resultados Pronósticos"] = ""
    else:
        df = pd.DataFrame(columns=[
            "Usuario", "Fecha", "Evento", "Competición", "Deporte", "Tipo de Apuesta",
            "Pronósticos", "Cuotas Individuales", "Cuota Total",
            "Stake (1-10)", "Stake (€)", "Resultado", "Ganancia/Pérdida (€)", "Bank (€)",
            "Resultados Pronósticos"
        ])

    tabs = st.tabs(["📋 Mis Apuestas", "👀 Ver Otras", "📈 Comparativa"])

    session_user = st.session_state.usuario
    user_bank_inicial = st.session_state.bank_inicial

    with tabs[0]:
        st.header("📋 Mis Apuestas")

        st.subheader("➕ Nueva Apuesta")
        apuesta_tipo = st.radio(
            "Tipo de apuesta",
            ["Simple", "Combinada"],
            index=0 if st.session_state.get("tipo_apuesta", "Simple") == "Simple" else 1
        )
        st.session_state["tipo_apuesta"] = apuesta_tipo

        with st.form("form_apuesta"):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha", datetime.date.today())
                evento = st.text_input("Evento")
                competicion = st.text_input("Competición")
            with col2:
                deporte = st.selectbox("Deporte", ["Fútbol", "Baloncesto", "Tenis", "Otro"])
                stake = st.slider("Stake (1-10)", 1, 10, 1)

            pronosticos = []
            cuotas_individuales = []
            cuota_total = 1.0

            if st.session_state["tipo_apuesta"] == "Combinada":
                with st.expander("Pronósticos de la combinada"):
                    num_pronos = st.number_input("¿Cuántos pronósticos?", min_value=2, max_value=10, step=1)
                    for i in range(int(num_pronos)):
                        pron = st.text_input(f"Pronóstico {i+1}", key=f"pron_{i}")
                        cuota = st.number_input(f"Cuota pronóstico {i+1}", min_value=1.01, step=0.01, key=f"cuota_{i}")
                        pronosticos.append(pron)
                        cuotas_individuales.append(cuota)
                    for c in cuotas_individuales:
                        cuota_total *= c
            else:
                pron = st.text_input("Pronóstico simple")
                cuota_total = st.number_input("Cuota", min_value=1.01, step=0.01)
                pronosticos.append(pron)
                cuotas_individuales.append(cuota_total)

            user_bets = df[df["Usuario"] == session_user]
            last_bank = user_bets["Bank (€)"].iloc[-1] if not user_bets.empty else user_bank_inicial
            stake_euros = round(stake * last_bank / 100, 2)

            st.markdown(f"💰 <b>Importe a apostar: {stake_euros:.2f} €</b>", unsafe_allow_html=True)
            st.markdown(f"🎯 <b>Cuota total: {round(cuota_total, 2)}</b>", unsafe_allow_html=True)

            enviar = st.form_submit_button("Añadir Apuesta")

            if enviar:
                nueva = {
                    "Usuario": session_user,
                    "Fecha": fecha,
                    "Evento": evento,
                    "Competición": competicion,
                    "Deporte": deporte,
                    "Tipo de Apuesta": st.session_state["tipo_apuesta"],
                    "Pronósticos": str(pronosticos),
                    "Cuotas Individuales": str(cuotas_individuales),
                    "Cuota Total": cuota_total,
                    "Stake (1-10)": stake,
                    "Stake (€)": stake_euros,
                    "Resultado": "Pendiente",
                    "Ganancia/Pérdida (€)": 0,
                    "Bank (€)": last_bank,
                    "Resultados Pronósticos": str(["Pendiente"] * len(pronosticos))
                }
                df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success("✅ Apuesta registrada correctamente")
                st.rerun()

        # -------------------------------------------------------
        # GESTIONAR RESULTADOS VISUAL CON TABLA Y COLORES
        # -------------------------------------------------------
        st.subheader("✏️ Gestionar resultados")

        for idx, row in df[df["Usuario"] == session_user].iterrows():
            pronos = ast.literal_eval(row["Pronósticos"])
            cuotas = ast.literal_eval(row["Cuotas Individuales"])
            resultados_previos = ast.literal_eval(row["Resultados Pronósticos"]) if row["Resultados Pronósticos"] else ["Pendiente"]*len(pronos)

            st.markdown(f"**{row['Fecha']} - {row['Evento']} ({row['Tipo de Apuesta']})**")

            # TABLA
            table_md = """
            <table style="width:100%; border-collapse:collapse;">
              <tr style="background-color:#333; color:white;">
                <th style="padding:4px;">Pronóstico</th>
                <th style="padding:4px;">Cuota</th>
                <th style="padding:4px;">Estado</th>
              </tr>
            """
            for i, (p, c, r) in enumerate(zip(pronos, cuotas, resultados_previos)):
                color = {
                    "Ganado": "#4CAF50", "Perdido": "#f44336", "Nulo": "#ff9800", "Pendiente": "#9e9e9e"
                }[r]
                table_md += f"""
                <tr style="background-color:#222;">
                    <td style="padding:4px;">{p}</td>
                    <td style="padding:4px;">{c}</td>
                    <td style="padding:4px; color:{color}; font-weight:bold;">{r}</td>
                </tr>
                """
            table_md += "</table>"
            st.markdown(table_md, unsafe_allow_html=True)

            # PANEL EDICIÓN
            if row['Resultado'] == "Pendiente":
                with st.expander("Editar resultados de esta combinada"):
                    resultados_pronos = []
                    for i, p in enumerate(pronos):
                        res = st.selectbox(
                            f"Resultado pronóstico {i+1} ({p})",
                            ["Pendiente", "Ganado", "Perdido", "Nulo"],
                            index=["Pendiente", "Ganado", "Perdido", "Nulo"].index(resultados_previos[i]),
                            key=f"res_{idx}_{i}"
                        )
                        resultados_pronos.append(res)

                    if st.button("💾 Guardar cambios", key=f"save_{idx}"):
                        df.at[idx, "Resultados Pronósticos"] = str(resultados_pronos)

                        if "Perdido" in resultados_pronos:
                            final = "Perdida"
                            ganancia = -row["Stake (€)"]
                        else:
                            ganados = [c for c, r in zip(cuotas, resultados_pronos) if r == "Ganado"]
                            nulos = [r for r in resultados_pronos if r == "Nulo"]
                            if not ganados and nulos:
                                final = "Nula"
                                ganancia = 0
                            elif ganados:
                                nueva_cuota = 1
                                for c, r in zip(cuotas, resultados_pronos):
                                    if r == "Ganado":
                                        nueva_cuota *= c
                                final = "Ganada"
                                ganancia = round(row["Stake (€)"] * (nueva_cuota - 1), 2)
                            else:
                                final = "Nula"
                                ganancia = 0

                        nuevo_bank = row["Bank (€)"] + ganancia
                        df.at[idx, "Resultado"] = final
                        df.at[idx, "Ganancia/Pérdida (€)"] = ganancia
                        df.at[idx, "Bank (€)"] = nuevo_bank

                        df.to_csv(DATA_FILE, index=False)
                        st.success(f"✅ Combinada actualizada como {final}")
                        st.rerun()
