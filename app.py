# -*- coding: utf-8 -*-
"""
Editor de Spyder

Este es un archivo temporal.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="CRUD Presupuesto", layout="centered")

# === Credenciales internas ===
credenciales = {
    "admin": {"password": "1234", "centros": ["52000", "52010", "52011", "52012", "52100", "52200", "52300"]},
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
menu = st.sidebar.selectbox("Menú", ["Agregar", "Buscar", "Editar", "Eliminar", "Ver Todo"])

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
                st.session_state.datos.at[index, "Grupo"] = grupo
                st.session_state.datos.at[index, "Centro Gestor"] = centro
                st.session_state.datos.at[index, "Unidad"] = unidad
                st.session_state.datos.at[index, "Concepto de Gasto"] = concepto
                st.session_state.datos.at[index, "Descripción del Gasto"] = descripcion
                st.session_state.datos.at[index, "Cantidad"] = cantidad
                st.session_state.datos.at[index, "Valor Unitario"] = valor_unitario
                st.session_state.datos.at[index, "Total"] = total
                st.session_state.datos.at[index, "Fecha"] = fecha
                st.success("✅ Registro actualizado")
        else:
            st.warning("Ítem no encontrado")

# === ELIMINAR ===
elif menu == "Eliminar":
    st.subheader("🗑️ Eliminar Registro")
    eliminar_item = st.text_input("Ítem a eliminar")
    if st.button("Eliminar"):
        if eliminar_item in df["Ítem"].values:
            st.session_state.datos = df[df["Ítem"] != eliminar_item]
            st.success("✅ Registro eliminado")
        else:
            st.error("Ítem no encontrado")

# === VER TODO ===
elif menu == "Ver Todo":
    st.subheader("📋 Todos los Registros")
    st.dataframe(df)
