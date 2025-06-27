import streamlit as st
import pandas as pd
import datetime
import os
import json
import ast

USERS_FILE = "usuarios.json"
DATA_FILE = "apuestas.csv"

st.set_page_config(page_title="Gestión de Apuestas", layout="wide")

# Cargar usuarios
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

# Inicializar variables de sesión
if "logueado" not in st.session_state:
    st.session_state.logueado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "bank_inicial" not in st.session_state:
    st.session_state.bank_inicial = 200
if "tipo_apuesta" not in st.session_state:
    st.session_state.tipo_apuesta = "Simple"

# Login
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

    # Cargar datos
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=[
            "Usuario", "Fecha", "Evento", "Competición", "Deporte", "Tipo de Apuesta",
            "Pronósticos", "Cuotas Individuales", "Cuota Total",
            "Stake (1-10)", "Stake (€)", "Resultado", "Ganancia/Pérdida (€)", "Bank (€)"
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

            # Bank actual
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
                    "Bank (€)": last_bank
                }
                df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success("✅ Apuesta registrada correctamente")
                st.rerun()

        st.subheader("✏️ Gestionar resultados")
        for idx, row in df[df["Usuario"] == session_user].iterrows():
            with st.expander(f"{row['Fecha']} - {row['Evento']} ({row['Tipo de Apuesta']})"):
                pronos = ast.literal_eval(row["Pronósticos"])
                cuotas = ast.literal_eval(row["Cuotas Individuales"])
                st.markdown(f"**Pronósticos:**")
                for i, (p, c) in enumerate(zip(pronos, cuotas)):
                    st.markdown(f"{i+1}. {p} (cuota {c})")
                st.markdown(f"**Cuota total:** {round(row['Cuota Total'],2)}")
                st.markdown(f"**Stake:** {row['Stake (€)']} €")
                st.markdown(f"**Resultado actual:** {row['Resultado']}")

                if row['Resultado'] == "Pendiente":
                    if row['Tipo de Apuesta'] == "Combinada":
                        resultados_pronos = []
                        for i, p in enumerate(pronos):
                            res = st.selectbox(
                                f"Resultado de pronóstico {i+1} ({p})",
                                ["Pendiente", "Ganado", "Perdido", "Nulo"],
                                key=f"res_{idx}_{i}"
                            )
                            resultados_pronos.append(res)
                        if st.button("Actualizar combinada", key=f"upd_{idx}"):
                            if "Perdido" in resultados_pronos:
                                final = "Perdida"
                                ganancia = -row["Stake (€)"]
                            else:
                                ganados = [c for c, r in zip(cuotas, resultados_pronos) if r=="Ganado"]
                                if not ganados:
                                    final = "Nula"
                                    ganancia = 0
                                else:
                                    nueva_cuota = 1
                                    for c in ganados:
                                        nueva_cuota *= c
                                    final = "Ganada"
                                    ganancia = round(row["Stake (€)"] * (nueva_cuota - 1), 2)
                            nuevo_bank = row["Bank (€)"] + ganancia
                            df.at[idx, "Resultado"] = final
                            df.at[idx, "Ganancia/Pérdida (€)"] = ganancia
                            df.at[idx, "Bank (€)"] = nuevo_bank
                            df.to_csv(DATA_FILE, index=False)
                            st.success("✅ Combinada actualizada")
                            st.rerun()
                    else:
                        nuevo_res = st.selectbox("Resultado", ["Pendiente", "Ganada", "Perdida", "Nula"], key=f"simp_{idx}")
                        if nuevo_res != "Pendiente" and st.button("Actualizar simple", key=f"btn_{idx}"):
                            stake_euros = row["Stake (€)"]
                            if nuevo_res == "Ganada":
                                ganancia = round(stake_euros * (row["Cuota Total"] - 1), 2)
                            elif nuevo_res == "Perdida":
                                ganancia = -stake_euros
                            else:
                                ganancia = 0
                            nuevo_bank = row["Bank (€)"] + ganancia
                            df.at[idx, "Resultado"] = nuevo_res
                            df.at[idx, "Ganancia/Pérdida (€)"] = ganancia
                            df.at[idx, "Bank (€)"] = nuevo_bank
                            df.to_csv(DATA_FILE, index=False)
                            st.success("✅ Resultado actualizado")
                            st.rerun()
                    if st.button("🗑️ Eliminar apuesta", key=f"del_{idx}"):
                        df = df.drop(idx)
                        df.to_csv(DATA_FILE, index=False)
                        st.warning("Apuesta eliminada")
                        st.rerun()

    with tabs[1]:
        st.header("👀 Ver apuestas de otros usuarios")
        otros = df["Usuario"].unique().tolist()
        ver_user = st.selectbox("Elegir usuario", otros)
        user_df = df[df["Usuario"] == ver_user]
        for idx, row in user_df.iterrows():
            pronos = ast.literal_eval(row["Pronósticos"])
            cuotas = ast.literal_eval(row["Cuotas Individuales"])
            st.markdown(f"**{row['Fecha']} - {row['Evento']} ({row['Tipo de Apuesta']})**")
            for i, (p, c) in enumerate(zip(pronos, cuotas)):
                st.markdown(f"- {p} (cuota {c})")
            st.markdown(f"Cuota total: {round(row['Cuota Total'],2)} | Stake: {row['Stake (€)']} € | Resultado: {row['Resultado']}")
            st.divider()

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
            resumen["% Éxito"] = (resumen["Apuestas Ganadas"] / resumen["Total Apuestas"])*100
            st.dataframe(resumen, use_container_width=True)
            st.line_chart(df[df["Resultado"] != "Pendiente"].groupby("Usuario")["Ganancia/Pérdida (€)"].sum())
