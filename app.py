# -*- coding: utf-8 -*-
"""
Editor de Spyder

Este es un archivo temporal.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os

from datetime import datetime
import pytz



st.set_page_config(page_title="CRUD Presupuesto", layout="centered")

# === Credenciales internas (sin .env) ===
credenciales = {
    "admin": {"password": "1234", "centros": ["52000", "52010", "52012", "51000", "51010"]},
    "usuario": {"password": "abcd", "centros": ["52000"]},
    "jtandrade": {"password": "5678", "centros": ["52012"]}
}

zona_colombia = pytz.timezone("America/Bogota")
ahora = datetime.now(zona_colombia)

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

if st.session_state.get("usuario") != "admin":
    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    div[data-testid="stDecoration"] {display:none;}
    div[data-testid="stSidebarNav"] {display:none;}
    div[data-testid="stSidebarUserContent"] {display:none;}
    button[title="View app in Streamlit Community Cloud"] {display: none;}
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# === CONFIGURACIÓN GENERAL ===
st.title("📊 Gestión Presupuestal Dinámica")

RELACION_FILE = "presupuesto.xlsx"

@st.cache_data
def cargar_relaciones(path):
    hojas = pd.read_excel(path, sheet_name=None)
    return hojas["Grupos_Centros"], hojas["Centro_Unidades"], hojas["Centro_Conceptos"]

grupos_centros_df, centro_unidades_df, centro_conceptos_df = cargar_relaciones(RELACION_FILE)

if "datos" not in st.session_state:
    st.session_state.datos = pd.DataFrame(columns=[
        "Ítem", "Grupo", "Centro Gestor", "Unidad", "Concepto de Gasto",
        "Descripción del Gasto", "Cantidad", "Valor Unitario", "Total", "Fecha"
    ])

if "auditoria" not in st.session_state:
    st.session_state.auditoria = pd.DataFrame(columns=[
        "Usuario", "Acción", "Ítem", "FechaHora", "Grupo", "Centro Gestor",
        "Unidad", "Concepto de Gasto", "Descripción", "Cantidad", "Valor Unitario", "Total"
    ])

df = st.session_state.datos
menu = st.sidebar.selectbox("Menú", ["Agregar", "Buscar", "Editar", "Eliminar"])

def obtener_centros(grupo):
    return grupos_centros_df[grupos_centros_df["Grupo"] == grupo]["Centro Gestor"].unique().tolist()

def obtener_unidades(centro):
    return centro_unidades_df[centro_unidades_df["Centro Gestor"] == centro]["Unidad"].unique().tolist()

def obtener_conceptos(centro):
    return centro_conceptos_df[centro_conceptos_df["Centro Gestor"] == centro]["Concepto de Gasto"].unique().tolist()

# === AGREGAR ===
if menu == "Agregar":
    st.subheader("➕ Agregar Registro")
    item = st.text_input("Ítem")
    grupo = st.selectbox("Grupo", grupos_centros_df["Grupo"].unique())
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

        st.session_state.auditoria = pd.concat([st.session_state.auditoria, pd.DataFrame([{
            "Usuario": st.session_state["usuario"],
            "Acción": "Agregar",
            "Ítem": item,
            "FechaHora": datetime.now(pytz.timezone("America/Bogota")).strftime("%Y-%m-%d %H:%M:%S"),
            "Grupo": grupo,
            "Centro Gestor": centro,
            "Unidad": unidad,
            "Concepto de Gasto": concepto,
            "Descripción": descripcion,
            "Cantidad": cantidad,
            "Valor Unitario": valor_unitario,
            "Total": total
        }])], ignore_index=True)

        st.success("✅ Registro guardado correctamente")

    # Mostrar tabla de registros agregados justo debajo
    if not st.session_state.datos.empty:
        st.subheader("📋 Registros Agregados")
        st.dataframe(st.session_state.datos, use_container_width=True)

    if st.session_state["usuario"] == "admin" and not st.session_state.auditoria.empty:
        st.subheader("🛡️ Registro de Auditoría")
        st.dataframe(st.session_state.auditoria, use_container_width=True)

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
            grupo = st.selectbox("Grupo", grupos_centros_df["Grupo"].unique(), index=list(grupos_centros_df["Grupo"].unique()).index(registro["Grupo"]))
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
                st.session_state.auditoria = pd.concat([st.session_state.auditoria, pd.DataFrame([{
                    "Usuario": st.session_state["usuario"],
                    "Acción": "Editar",
                    "Ítem": editar_item,
                    "FechaHora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Grupo": grupo,
                    "Centro Gestor": centro,
                    "Unidad": unidad,
                    "Concepto de Gasto": concepto,
                    "Descripción": descripcion,
                    "Cantidad": cantidad,
                    "Valor Unitario": valor_unitario,
                    "Total": total
                }])], ignore_index=True)
                st.success("✅ Registro actualizado")
        else:
            st.warning("Ítem no encontrado")

# === ELIMINAR ===
elif menu == "Eliminar":
    st.subheader("🗑️ Eliminar Registro")
    eliminar_item = st.text_input("Ítem a eliminar")
    if st.button("Eliminar"):
        if eliminar_item in df["Ítem"].values:
            eliminado = df[df["Ítem"] == eliminar_item].iloc[0]
            st.session_state.auditoria = pd.concat([st.session_state.auditoria, pd.DataFrame([{
                "Usuario": st.session_state["usuario"],
                "Acción": "Eliminar",
                "Ítem": eliminar_item,
                "FechaHora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Grupo": eliminado["Grupo"],
                "Centro Gestor": eliminado["Centro Gestor"],
                "Unidad": eliminado["Unidad"],
                "Concepto de Gasto": eliminado["Concepto de Gasto"],
                "Descripción": eliminado["Descripción del Gasto"],
                "Cantidad": eliminado["Cantidad"],
                "Valor Unitario": eliminado["Valor Unitario"],
                "Total": eliminado["Total"]
            }])], ignore_index=True)

            st.session_state.datos = df[df["Ítem"] != eliminar_item]
            st.success("✅ Registro eliminado")
        else:
            st.error("Ítem no encontrado")
