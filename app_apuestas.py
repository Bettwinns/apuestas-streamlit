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

# Inicializar sesión
if "logueado" not in st.session_state:
    st.session_state.logueado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "tipo_apuesta" not in st.session_state:
    st.session_state.tipo_apuesta = "Simple"

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

    with tabs[0]:
        st.header("📋 Mis Apuestas")

        with st.form("form_apuesta"):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha", datetime.date.today())
                evento = st.text_input("Evento")
                competicion = st.text_input("Competición")
                apuesta_tipo = st.radio(
                    "Tipo de apuesta", ["Simple", "Combinada"],
                    index=0 if st.session_state.tipo_apuesta == "Simple" else 1,
                    on_change=lambda: st.session_state.update({"tipo_apuesta": "Simple" if st.session_state.tipo_apuesta=="Combinada" else "Combinada"}) or st.rerun()
                )
            with col2:
                deporte = st.selectbox("Deporte", ["Fútbol", "Baloncesto", "Tenis", "Otro"])
                stake = st.slider("Stake (1-10)", 1, 10, 1)

            pronosticos = []
            cuotas_individuales = []
            cuota_total = 1.0

            if apuesta_tipo == "Combinada":
                with st.expander("Añadir pronósticos de la combinada"):
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

            bank_anterior = df[df["Usuario"] == session_user]["Bank (€)"].iloc[-1] if not df[df["Usuario"] == session_user].empty else 200
            stake_estimado = round(stake * bank_anterior / 100, 2)
            st.markdown(f"💰 <b>Importe a apostar: {stake_estimado} €</b>", unsafe_allow_html=True)
            st.markdown(f"🎯 <b>Cuota total: {round(cuota_total, 2)}</b>", unsafe_allow_html=True)

            enviar = st.form_submit_button("Añadir Apuesta")

        if enviar:
            nueva = {
                "Usuario": session_user,
                "Fecha": fecha,
                "Evento": evento,
                "Competición": competicion,
                "Deporte": deporte,
                "Tipo de Apuesta": apuesta_tipo,
                "Pronósticos": str(pronosticos),
                "Cuotas Individuales": str(cuotas_individuales),
                "Cuota Total": cuota_total,
                "Stake (1-10)": stake,
                "Stake (€)": stake_estimado,
                "Resultado": "Pendiente",
                "Ganancia/Pérdida (€)": 0,
                "Bank (€)": bank_anterior
            }
            df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success("✅ Apuesta registrada correctamente")
            st.rerun()

        st.subheader("✏️ Gestionar mis apuestas")
        for idx, row in df[df["Usuario"] == session_user].iterrows():
            with st.expander(f"{row['Fecha']} - {row['Evento']} ({row['Tipo de Apuesta']})"):
                pronos = ast.literal_eval(row["Pronósticos"])
                cuotas = ast.literal_eval(row["Cuotas Individuales"])
                resultado = row["Resultado"]
                st.markdown("**Pronósticos:**")
                for i, (p, c) in enumerate(zip(pronos, cuotas)):
                    st.markdown(f"{i+1}. {p} (cuota {c})")
                st.markdown(f"**Cuota total:** {round(row['Cuota Total'],2)}")
                st.markdown(f"**Stake:** {row['Stake (€)']} €")
                st.markdown(f"**Resultado actual:** {resultado}")

                if resultado == "Pendiente":
                    if row['Tipo de Apuesta'] == "Combinada":
                        resultados_pronos = []
                        for i, p in enumerate(pronos):
                            res = st.selectbox(
                                f"Resultado de pronóstico {i+1} ({p})",
                                ["Pendiente", "Ganado", "Perdido", "Nulo"],
                                key=f"res_{idx}_{i}"
                            )
                            resultados_pronos.append(res)
                        if st.button("Actualizar combinada", key=f"update_{idx}"):
                            if "Perdido" in resultados_pronos:
                                final = "Perdida"
                                ganancia = -row["Stake (€)"]
                            else:
                                pronos_validos = [p for p,r in zip(pronos, resultados_pronos) if r=="Ganado"]
                                cuotas_validas = [c for c,r in zip(cuotas, resultados_pronos) if r=="Ganado"]
                                if not pronos_validos:
                                    final = "Nula"
                                    ganancia = 0
                                else:
                                    nueva_cuota_total = 1
                                    for c in cuotas_validas:
                                        nueva_cuota_total *= c
                                    final = "Ganada"
                                    ganancia = round(row["Stake (€)"] * (nueva_cuota_total - 1),2)
                            bank_actual = row["Bank (€)"] + ganancia
                            df.at[idx, "Resultado"] = final
                            df.at[idx, "Ganancia/Pérdida (€)"] = ganancia
                            df.at[idx, "Bank (€)"] = bank_actual
                            df.to_csv(DATA_FILE, index=False)
                            st.success(f"✅ Resultado combinada actualizado como {final}")
                            st.rerun()
                    else:
                        nuevo_res = st.selectbox("Resultado", ["Pendiente", "Ganada", "Perdida", "Nula"], key=f"simp_{idx}")
                        if nuevo_res != "Pendiente" and st.button("Actualizar resultado", key=f"btn_{idx}"):
                            stake_euros = row["Stake (€)"]
                            if nuevo_res == "Ganada":
                                ganancia = round(stake_euros * (row["Cuota Total"] - 1), 2)
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
                    if st.button("🗑️ Eliminar apuesta", key=f"del_{idx}"):
                        df = df.drop(idx)
                        df.to_csv(DATA_FILE, index=False)
                        st.warning("Apuesta eliminada")
                        st.rerun()

    with tabs[1]:
        st.header("👀 Ver apuestas de otros usuarios")
        opciones = df["Usuario"].unique().tolist()
        elegido = st.selectbox("Selecciona un usuario", opciones)
        user_df = df[df["Usuario"] == elegido]
        if not user_df.empty:
            for idx, row in user_df.iterrows():
                pronos = ast.literal_eval(row["Pronósticos"])
                cuotas = ast.literal_eval(row["Cuotas Individuales"])
                st.markdown(f"**{row['Fecha']} - {row['Evento']} ({row['Tipo de Apuesta']})**")
                for i, (p, c) in enumerate(zip(pronos, cuotas)):
                    st.markdown(f"- {p} (cuota {c})")
                st.markdown(f"Cuota total: {round(row['Cuota Total'],2)} | Stake: {row['Stake (€)']} € | Resultado: {row['Resultado']}")
                st.divider()
        else:
            st.info("Este usuario aún no tiene apuestas registradas.")

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
