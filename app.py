# -*- coding: utf-8 -*-
"""
Editor de Spyder

Este es un archivo temporal.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="EMCALI Presupuesto", layout="centered")

# === Credenciales internas ===
credenciales = {
    "admin": {"password": "1234", "centros": ["52000", "52010", "52011", "52012", "52100", "52200","52300"]},
    "usuario": {"password": "abcd", "centros": ["52000"]},
    "jtandrade": {"password": "5678", "centros": ["52012"]}
}

# === Login ===
def mostrar_login():
    st.title("\U0001F512 Inicio de Sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if username in credenciales and credenciales[username]["password"] == password:
            st.session_state["logueado"] = True
            st.session_state["usuario"] = username
            st.session_state["centros_autorizados"] = credenciales[username]["centros"]
            st.success(f"Bienvenido, {username}!")
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos")

def mostrar_logout():
    with st.sidebar:
        st.markdown(f"👤 Usuario: `{st.session_state['usuario']}`")
        if st.button("Cerrar sesión"):
            st.session_state["logueado"] = False
            st.session_state["usuario"] = None
            st.session_state["centros_autorizados"] = []
            st.rerun()

if "logueado" not in st.session_state:
    st.session_state["logueado"] = False

if not st.session_state["logueado"]:
    mostrar_login()
    st.stop()
else:
    mostrar_logout()
    
# === OCULTAR ELEMENTOS STREAMLIT PARA NO ADMIN ===
if st.session_state.get("usuario") != "admin":
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    div[data-testid="stDecoration"] {display:none;}
    div[data-testid="stSidebarNav"] {display:none;}
    button[title="View app in Streamlit Community Cloud"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

# === Ruta de historial de cambios ===
LOG_PATH = "historial_cambios.csv"

def registrar_accion(accion, fila):
    now = datetime.now()
    log = pd.DataFrame([{
        "Usuario": st.session_state["usuario"],
        "Fecha": now.strftime("%Y-%m-%d"),
        "Hora": now.strftime("%H:%M:%S"),
        "Acción": accion,
        **fila
    }])
    if os.path.exists(LOG_PATH):
        log.to_csv(LOG_PATH, mode="a", header=False, index=False)
    else:
        log.to_csv(LOG_PATH, index=False)

# === Cargar relaciones ===
st.title("📊 Gestión Presupuestal UENE")
RELACION_FILE = "presupuesto.xlsx"
@st.cache_data
def cargar_relaciones(path):
    hojas = pd.read_excel(path, sheet_name=None)
    gc = hojas["Grupos_Centros"]
    cu = hojas["Centro_Unidades"]
    cc = hojas["Centro_Conceptos"]
    gc["Centro Gestor"] = gc["Centro Gestor"].astype(str).str[:5]
    cu["Centro Gestor"] = cu["Centro Gestor"].astype(str).str[:5]
    cc["Centro Gestor"] = cc["Centro Gestor"].astype(str).str[:5]
    return gc, cu, cc

grupo_centros, centros_unidades, centros_conceptos = cargar_relaciones(RELACION_FILE)

if "datos" not in st.session_state:
    st.session_state.datos = pd.DataFrame(columns=[
        "Ítem", "Grupo", "Centro Gestor", "Unidad", "Concepto de Gasto",
        "Descripción del Gasto", "Cantidad", "Valor Unitario", "Total", "Fecha"
    ])

df = st.session_state.datos
menu = st.sidebar.selectbox("Menú", ["Agregar", "Buscar", "Editar", "Eliminar", "Ver Todo", "Historial"] if st.session_state["usuario"] == "admin" else ["Agregar", "Buscar", "Editar", "Eliminar", "Ver Todo"])

def obtener_centros(grupo):
    todos = grupo_centros[grupo_centros["Grupo"] == grupo]["Centro Gestor"].unique().tolist()
    return [c for c in todos if c in st.session_state["centros_autorizados"]]

def obtener_unidades(centro):
    return centros_unidades[centros_unidades["Centro Gestor"] == centro]["Unidad"].unique().tolist()

def obtener_conceptos(centro):
    return centros_conceptos[centros_conceptos["Centro Gestor"] == centro]["Concepto de Gasto"].unique().tolist()

# === AGREGAR ===
if menu == "Agregar":
    st.subheader("➕ Agregar Registro")
    item = st.text_input("Ítem")
    grupo = st.selectbox("Grupo", grupo_centros["Grupo"].unique())
    centros = obtener_centros(grupo)
    centro = st.selectbox("Centro Gestor", centros if centros else ["-"])
    unidades = obtener_unidades(centro)
    unidad = st.selectbox("Unidad", unidades if unidades else ["-"])
    conceptos = obtener_conceptos(centro)
    concepto = st.selectbox("Concepto de Gasto", conceptos if conceptos else ["-"])
    descripcion = st.text_area("Descripción del Gasto")
    cantidad = st.number_input("Cantidad", min_value=1, format="%d")
    valor_unitario = st.number_input("Valor Unitario", min_value=0.0, format="%.2f")
    total = cantidad * valor_unitario
    fecha = st.date_input("Fecha", value=datetime.today())
    st.write(f"💲 **Total Calculado:** {total:,.2f}")
    if st.button("Guardar"):
        nuevo = pd.DataFrame([[item, grupo, centro, unidad, concepto,
                               descripcion, cantidad, valor_unitario, total, fecha]],
                             columns=df.columns)
        st.session_state.datos = pd.concat([df, nuevo], ignore_index=True)
        fila = nuevo.iloc[0].to_dict()
        fila["Fecha"] = fecha.strftime("%Y-%m-%d")
        registrar_accion("Agregar", fila)
        st.success("✅ Registro guardado correctamente")

# === BUSCAR ===
elif menu == "Buscar":
    st.subheader("🔍 Buscar por Ítem")
    buscar_item = st.text_input("Ingrese Ítem")
    if st.button("Buscar"):
        resultado = df[df["Ítem"] == buscar_item]
        if not resultado.empty:
            st.dataframe(resultado)
        else:
            st.warning("No se encontró el ítem")

# === EDITAR ===
elif menu == "Editar":
    st.subheader("✏️ Editar Registro")
    editar_item = st.text_input("Ítem a editar")
    if st.button("Cargar"):
        resultado = df[df["Ítem"] == editar_item]
        if not resultado.empty:
            index = resultado.index[0]
            registro = resultado.iloc[0]
            grupo = st.selectbox("Grupo", grupo_centros["Grupo"].unique(), index=list(grupo_centros["Grupo"].unique()).index(registro["Grupo"]))
            centros = obtener_centros(grupo)
            centro = st.selectbox("Centro Gestor", centros, index=centros.index(registro["Centro Gestor"]))
            unidades = obtener_unidades(centro)
            unidad = st.selectbox("Unidad", unidades, index=unidades.index(registro["Unidad"]))
            conceptos = obtener_conceptos(centro)
            concepto = st.selectbox("Concepto de Gasto", conceptos, index=conceptos.index(registro["Concepto de Gasto"]))
            descripcion = st.text_area("Descripción del Gasto", value=registro["Descripción del Gasto"])
            cantidad = st.number_input("Cantidad", min_value=1, value=int(registro["Cantidad"]), format="%d")
            valor_unitario = st.number_input("Valor Unitario", min_value=0.0, value=float(registro["Valor Unitario"]), format="%.2f")
            total = cantidad * valor_unitario
            fecha = st.date_input("Fecha", value=pd.to_datetime(registro["Fecha"]))
            st.write(f"💲 **Total Calculado:** {total:,.2f}")
            if st.button("Actualizar"):
                fila_dict = {
                    "Ítem": editar_item,
                    "Grupo": grupo,
                    "Centro Gestor": centro,
                    "Unidad": unidad,
                    "Concepto de Gasto": concepto,
                    "Descripción del Gasto": descripcion,
                    "Cantidad": cantidad,
                    "Valor Unitario": valor_unitario,
                    "Total": total,
                    "Fecha": fecha.strftime("%Y-%m-%d")
                }
                for campo, valor in fila_dict.items():
                    st.session_state.datos.at[index, campo] = valor
                registrar_accion("Editar", fila_dict)
                st.success("✅ Registro actualizado")
        else:
            st.warning("Ítem no encontrado")

# === ELIMINAR ===
elif menu == "Eliminar":
    st.subheader("🗑️ Eliminar Registro")
    eliminar_item = st.text_input("Ítem a eliminar")
    if st.button("Eliminar"):
        if eliminar_item in df["Ítem"].values:
            fila = df[df["Ítem"] == eliminar_item].iloc[0].to_dict()
            fila["Fecha"] = str(fila["Fecha"])
            registrar_accion("Eliminar", fila)
            st.session_state.datos = df[df["Ítem"] != eliminar_item]
            st.success("✅ Registro eliminado")
        else:
            st.error("Ítem no encontrado")

# === VER TODO ===
elif menu == "Ver Todo":
    st.subheader("📋 Todos los Registros")
    st.dataframe(df)

# === HISTORIAL ===
elif menu == "Historial":
    st.subheader("🕒 Historial de Cambios")
    if os.path.exists(LOG_PATH):
        historial = pd.read_csv(LOG_PATH)
        st.dataframe(historial)
        st.download_button("📥 Descargar historial CSV", data=historial.to_csv(index=False), file_name="historial_cambios.csv")
    else:
        st.info("No hay historial registrado aún.")