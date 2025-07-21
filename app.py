import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import plotly.express as px
from PIL import Image
import altair as alt

st.set_page_config(
    page_title="Presupuesto EMCALI",
    page_icon="LOGO-EMCALI-vertical-color.png",  # 🟢 Ícono personalizado
    layout="centered"
)

st.sidebar.image("LOGO-EMCALI-vertical-color.png", use_container_width=True)

st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 2px solid #ef5f17;
        padding-top: 1rem;
    }
    h1, h2, h3 {
        color: #ef5f17;
        font-weight: bold;
    }
    .stButton > button {
        background-color: #ef5f17;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5em 1.5em;
        border: none;
        transition: background-color 0.3s;
    }
    .stButton > button:hover {
        background-color: #cc4d12;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def cargar_usuarios(path):
    df_login = pd.read_excel(path, sheet_name="Login")
    credenciales = {
        row["Usuario"]: {
            "password": str(row["Clave"]),
            "centros": [row["Unidad"]]
        }
        for _, row in df_login.iterrows()
    }
    return credenciales

credenciales = cargar_usuarios("presupuesto.xlsx")

if "logueado" not in st.session_state:
    st.session_state["logueado"] = False

def mostrar_login():    
    tangara = Image.open("Pajaro_Tangara_2.png")

    col_logo, col_title = st.columns([1, 6])
   
    with col_title:
        st.title("Inicio de Sesión")
    with col_logo:
        st.image(tangara, width=70)
         
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

if not st.session_state["logueado"]:
    mostrar_login()
    st.stop()
else:
    mostrar_logout()

RELACION_FILE = "presupuesto.xlsx"
BITACORA_FILE = "bitacora_admin.csv"

@st.cache_data
def cargar_relaciones(path):
    hojas = pd.read_excel(path, sheet_name=None)
    return (
        hojas["Grupos_Centros"],
        hojas["Centro_Unidades"],
        hojas["Centro_Conceptos"],
        hojas["Ingresos_Centros"]
    )

grupos_centros_df, centro_unidades_df, centro_conceptos_df, ingresos_centros_df = cargar_relaciones(RELACION_FILE)

if "datos" not in st.session_state:
    st.session_state.datos = pd.DataFrame(columns=[
        "Ítem", "Grupo", "Centro Gestor", "Unidad", "Concepto de Gasto",
        "Descripción del Gasto", "Cantidad", "Valor Unitario", "Total", "Fecha", "Categoría"
    ])

def obtener_ingreso_asignado(centro):
    fila = ingresos_centros_df[ingresos_centros_df["Centro Gestor"] == centro]
    if not fila.empty:
        return float(fila.iloc[0]["Ingreso Asignado"])
    return 0.0

def obtener_centros(grupo):
    return grupos_centros_df[grupos_centros_df["Grupo"] == grupo]["Centro Gestor"].unique().tolist()

def obtener_unidades(centro):
    return centro_unidades_df[centro_unidades_df["Centro Gestor"] == centro]["Unidad"].unique().tolist()

def obtener_conceptos(centro):
    return centro_conceptos_df[centro_conceptos_df["Centro Gestor"] == centro]["Concepto de Gasto"].unique().tolist()

def registrar_bitacora(accion, usuario, item):
    ahora = datetime.now(pytz.timezone("America/Bogota")).strftime("%Y-%m-%d %H:%M:%S")
    fila = pd.DataFrame([[usuario, ahora, accion, item]], columns=["Usuario", "Hora", "Acción", "Ítem"])
    if os.path.exists(BITACORA_FILE):
        existente = pd.read_csv(BITACORA_FILE)
        nueva = pd.concat([existente, fila], ignore_index=True)
    else:
        nueva = fila
    nueva.to_csv(BITACORA_FILE, index=False)

# Menú
opciones_admin = ["Agregar", "Buscar", "Editar", "Eliminar", "Ver Todo", "Historial"]
opciones_usuario = ["Agregar", "Ver Todo"]

menu = st.sidebar.selectbox("Menú", opciones_admin if st.session_state["usuario"] == "admin" else opciones_usuario)
df = st.session_state.datos

# Tarjeta lateral de saldo
with st.sidebar:
    st.markdown("---")
    centro_actual = st.session_state.get("centro_actual", "52000")
    ingreso_asignado = obtener_ingreso_asignado(centro_actual)
    total_gastado = df.query("`Centro Gestor` == @centro_actual")["Total"].sum()
    saldo_disponible = ingreso_asignado - total_gastado
    st.markdown(f"""
    <div style="background-color: #f8f9fa; border: 2px solid #ef5f17; border-radius: 10px;
                padding: 1rem; margin-top: 1rem; font-size: 14px; font-family: Segoe UI, sans-serif;">
        <h4 style="color:#ef5f17; margin:0;">💼 {centro_actual}</h4>
        <p style="margin:0;"><strong>Ingreso:</strong> ${ingreso_asignado:,.2f}</p>
        <p style="margin:0;"><strong>Gastos:</strong> ${total_gastado:,.2f}</p>
        <p style="margin:0;"><strong>Saldo:</strong>
            <span style="color:{'red' if saldo_disponible < 0 else 'green'};">
                ${saldo_disponible:,.2f}
            </span>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
# Tabs organizados
presupuesto_tab, dashboard_tab = st.tabs(["🧾 Presupuesto", "📊 Dashboard"])

with presupuesto_tab:
    col_logo, col_titulo = st.columns([1, 6])  # Ajusta proporciones según el tamaño del logo

    with col_logo:
        st.image("icono-energia.png", width=80)
    
    with col_titulo:
        st.markdown("<h1 style='margin-bottom: 0;'>Gestión Presupuestal UENE 2026</h1>", unsafe_allow_html=True)

    if menu == "Agregar":
        st.subheader("➕ Agregar Registro")
    
        if "contador_item" not in st.session_state:
            st.session_state.contador_item = 1
        
        item = f"G{st.session_state.contador_item:04}"
        st.text_input("Ítem", value=item, disabled=True)

        categoria = st.radio("Seleccione una categoría:", options=["AGOP", "3.1", "Contratos", "Vigencias Futuras"], horizontal=True)
        grupo = st.selectbox("Grupo", grupos_centros_df["Grupo"].unique())
        centros = obtener_centros(grupo)
        centro = st.selectbox("Centro Gestor", centros if centros else ["-"])
        st.session_state["centro_actual"] = centro
        unidades = obtener_unidades(centro)
        unidad = st.selectbox("Unidad", unidades if unidades else ["-"])
        conceptos = obtener_conceptos(centro)
        concepto = st.selectbox("Concepto de Gasto", conceptos if conceptos else ["-"])
        descripcion = st.text_area("Descripción del Gasto")
        cantidad = st.number_input("Cantidad", min_value=1, format="%d")
        valor_unitario = st.number_input("Valor Unitario", min_value=0.0, format="%.2f")
        total = cantidad * valor_unitario
        fecha = st.date_input("Fecha Inicio de Proceso", value=datetime.today())
        st.write(f"💲 **Total Calculado:** {total:,.2f}")
       
        
        total_gastado_ajustado = st.session_state.datos.query("`Centro Gestor` == @centro")["Total"].sum()
        ingreso_disponible = obtener_ingreso_asignado(centro)
        nuevo_total_proyectado = total_gastado_ajustado + total
        
        if nuevo_total_proyectado > ingreso_disponible:
            st.warning(f"⚠️ El valor total proyectado (${nuevo_total_proyectado:,.2f}) supera el Ingreso Asignado (${ingreso_disponible:,.2f}). No se puede guardar.")
            puede_guardar = False
        else:
            puede_guardar = True
        
        if st.button("Guardar", disabled=not puede_guardar):
            nuevo = pd.DataFrame([[item, grupo, centro, unidad, concepto,
                                    descripcion, cantidad, valor_unitario, total, fecha,
                                    categoria]], columns=df.columns)
            st.session_state.datos = pd.concat([df, nuevo], ignore_index=True)
            registrar_bitacora("Agregar", st.session_state["usuario"], item)
            st.session_state.contador_item += 1
            st.success("✅ Registro guardado correctamente")
            st.rerun()  # Esto actualiza todo el layout, incluyendo el resumen de gastos


    if not st.session_state.datos.empty:
        st.subheader("📋 Registros Agregados")
        st.dataframe(st.session_state.datos, use_container_width=True)
        
    if "contador_item" not in st.session_state:
        st.session_state.contador_item = 1
        # Registrar en bitácora (ahora sí, item ya está definido)
        registrar_bitacora("Agregar", st.session_state["usuario"], item)
        st.success("✅ Registro guardado correctamente")
        
    elif menu == "Buscar":
        st.subheader("🔍 Buscar por Ítem")
        buscar_item = st.text_input("Ingrese Ítem")
        if st.button("Buscar"):
            resultado = df[df["Ítem"] == buscar_item]
            if not resultado.empty:
                st.dataframe(resultado)
            else:
                st.warning("No se encontró el ítem")
        
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
                    registrar_bitacora("Editar", st.session_state["usuario"], editar_item)
                    st.success("✅ Registro actualizado")
            else:
                st.warning("Ítem no encontrado")
        
    elif menu == "Eliminar":
        st.subheader("🗑️ Eliminar Registro")
        eliminar_item = st.text_input("Ítem a eliminar")
        if st.button("Eliminar"):
            if eliminar_item in df["Ítem"].values:
                st.session_state.datos = df[df["Ítem"] != eliminar_item]
                registrar_bitacora("Eliminar", st.session_state["usuario"], eliminar_item)
                st.success("✅ Registro eliminado")
            else:
                st.error("Ítem no encontrado")
        
    elif menu == "Ver Todo":
        st.subheader("📋 Todos los Registros")
        st.dataframe(df)
        
    elif menu == "Historial" and st.session_state["usuario"] == "admin":
        st.subheader("🕓 Historial de Actividades")
        if os.path.exists("bitacora_admin.csv"):
            log = pd.read_csv("bitacora_admin.csv")
            st.dataframe(log, use_container_width=True)
            st.download_button("📥 Descargar Historial", data=log.to_csv(index=False), file_name="bitacora_admin.csv", mime="text/csv")
        else:
            st.info("No hay registros de historial aún.")
                

with dashboard_tab:
    st.markdown("## 🧮 Dashboard Financiero")

    # Cálculos clave
    centro_actual = st.session_state.get("centro_actual", "52000")
    ingreso_asignado = obtener_ingreso_asignado(centro_actual)
    datos_centro = st.session_state.datos.query("`Centro Gestor` == @centro_actual")
    total_gastado = datos_centro["Total"].sum()
    saldo_disponible = ingreso_asignado - total_gastado
    num_registros = datos_centro.shape[0]
    color_saldo = "green" if saldo_disponible >= 0 else "red"
    
    # CSS para las tarjetas
    st.markdown("""
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
        }
        .main-title {
            font-size: 2rem;
            font-weight: bold;
            color: #ef5f17;
            padding-bottom: 1rem;
        }
        .card-container {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .card {
            background-color: #f8f9fa;
            border-radius: 12px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
            padding: 1rem;
            width: 220px;
            text-align: center;
            flex-grow: 1;
        }
        .card-title {
            font-size: 1.1rem;
            margin: 0;
        }
        .card-value {
            font-size: 20px;
            font-weight: bold;
            margin: 0.3rem 0;
        }
        .icon {
            width: 28px;
            height: 28px;
            margin-bottom: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # HTML de tarjetas
    st.markdown(f"""
    <div class='card-container'>
        <div class='card'>
            <img class='icon' src='https://img.icons8.com/ios-filled/50/money.png'>
            <h4 class='card-title'>Ingreso</h4>
            <p class='card-value'>${ingreso_asignado:,.2f}</p>
        </div>
        <div class='card'>
            <img class='icon' src='https://img.icons8.com/ios-filled/50/expenses.png'>
            <h4 class='card-title'>Gastos</h4>
            <p class='card-value'>${total_gastado:,.2f}</p>
        </div>
        <div class='card'>
            <img class='icon' src='https://img.icons8.com/ios-filled/50/safe.png'>
            <h4 class='card-title'>Saldo</h4>
            <p class='card-value' style='color:{color_saldo};'>${saldo_disponible:,.2f}</p>
        </div>
        <div class='card'>
            <img class='icon' src='https://img.icons8.com/ios-filled/50/list.png'>
            <h4 class='card-title'>Registros</h4>
            <p class='card-value'>{num_registros}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


    # 🔹 Visualización 1: Barras por concepto
    st.markdown("#### 📌 ¿En qué se está gastando más?")
    gastos_por_concepto = datos_centro.groupby("Concepto de Gasto")["Total"].sum().reset_index()
    chart_conceptos = alt.Chart(gastos_por_concepto).mark_bar().encode(
        x=alt.X('Total:Q', title='Total ($)', axis=alt.Axis(format='$,.0f')),
        y=alt.Y('Concepto de Gasto:N', sort='-x', title=None),
        color=alt.Color('Concepto de Gasto:N', legend=None),
        tooltip=["Concepto de Gasto", "Total"]
    ).properties(width=700, height=400)
    st.altair_chart(chart_conceptos, use_container_width=True)

    # 🔹 Visualización 2: Barras agrupadas por Categoría
    st.markdown("#### 🔍 Comparativa por Categoría y Concepto")
    if "Categoría" in datos_centro.columns:
        gastos_categoria = datos_centro.groupby(["Categoría", "Concepto de Gasto"])["Total"].sum().reset_index()
        chart_categoria = alt.Chart(gastos_categoria).mark_bar().encode(
            x=alt.X("Concepto de Gasto:N", title="Concepto"),
            y=alt.Y("Total:Q", title="Total ($)", axis=alt.Axis(format='$,.0f')),
            color="Categoría:N",
            column=alt.Column("Categoría:N", title=""),
            tooltip=["Categoría", "Concepto de Gasto", "Total"]
        ).properties(height=350).configure_view(stroke=None)
        st.altair_chart(chart_categoria, use_container_width=True)

    # 🔹 Visualización 3: Línea temporal
    st.markdown("#### 🕓 Evolución de los Gastos en el Tiempo")
    if "Fecha" in datos_centro.columns:
        datos_centro["Fecha"] = pd.to_datetime(datos_centro["Fecha"])
        gastos_tiempo = datos_centro.groupby(pd.Grouper(key="Fecha", freq="M"))["Total"].sum().reset_index()
        chart_linea = alt.Chart(gastos_tiempo).mark_line(point=True).encode(
            x=alt.X("Fecha:T", title="Mes"),
            y=alt.Y("Total:Q", title="Total Acumulado", axis=alt.Axis(format='$,.0f')),
            tooltip=["Fecha", "Total"]
        ).properties(width=700, height=300)
        st.altair_chart(chart_linea, use_container_width=True)

    # 🔹 Visualización 4: Donut por unidad
    st.markdown("#### 🧩 Distribución por Unidad")
    if "Unidad" in datos_centro.columns:
        gastos_unidad = datos_centro.groupby("Unidad")["Total"].sum().reset_index()
        donut = alt.Chart(gastos_unidad).mark_arc(innerRadius=50).encode(
            theta="Total:Q",
            color="Unidad:N",
            tooltip=["Unidad", "Total"]
        ).properties(width=400, height=400)
        st.altair_chart(donut, use_container_width=True)
