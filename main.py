# main.py (versión reorganizada)

import json
import time
import streamlit as st
import pandas as pd
from utils import cargar_cursos, cursos_validos, validar_manual

from utils import construir_grafo, mostrar_grafo_pyvis, alertas_riesgo, predecir_graduacion
import datetime
from csp_solver import (
    planificar_toda_la_carrera,
    contador_backtracks,
    contador_nodos
)
from simulador import simular_avance, simular_avance_csp


# Configuración de la página
st.set_page_config(
    page_title="Planificador Académico Inteligente",
    layout="wide",
    page_icon="🎓",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados (igual que antes)
st.markdown("""
    <style>
        :root {
            --primary: #2E86AB;
            --secondary: #F18F01;
            --success: #4CAF50;
            --warning: #FFC107;
            --danger: #F44336;
        }
        .main {
            max-width: 1400px;
            padding: 2rem;
        }
        .header {
            color: var(--primary);
            border-bottom: 2px solid var(--secondary);
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .subheader {
            color: var(--primary);
            margin-top: 1.5rem;
        }
        .card {
            background-color: #FFFFFF;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        .stButton>button {
            background-color: var(--primary);
            color: white;
            border-radius: 5px;
            padding: 8px 16px;
            margin: 5px 0;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: var(--secondary);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        .stSelectbox, .stSlider, .stMultiselect {
            margin-bottom: 1rem;
        }
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
        .progress-container {
            width: 100%;
            background-color: #e0e0e0;
            border-radius: 5px;
            margin: 10px 0;
        }
        .progress-bar {
            height: 20px;
            border-radius: 5px;
            background-color: var(--primary);
            text-align: center;
            line-height: 20px;
            color: white;
        }
        .course-card {
            border-left: 4px solid var(--primary);
            padding: 10px;
            margin: 5px 0;
            background-color: #f5f5f5;
            border-radius: 0 5px 5px 0;
        }
        .course-card.approved {
            border-left-color: var(--success);
            background-color: #e8f5e9;
        }
        .course-card.pending {
            border-left-color: var(--warning);
            background-color: #fff8e1;
        }
        .tab-content {
            padding: 15px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
        /* Contenedor del multiselect: fondo gris claro y borde para destacarlo */
        .stMultiSelect > div[data-baseweb="select"] {
            background-color: #f0f4f8 !important;
            border: 1px solid #cdd5e0 !important;
            border-radius: 8px !important;
            padding: 0.4rem !important;
        }

        /* Tarjetas de curso: fondo más tenue y texto oscuro */
        .course-card {
            background-color: #E8F4F8 !important;
            color: #1f1f1f !important;
            border-left: 4px solid var(--secondary) !important;
        }

        /* Tabla de progreso: celdas con fondo suave */
        .stDataFrame table, .stDataFrame th, .stDataFrame td {
            background-color: #fafafa !important;
            color: #1f1f1f !important;
        }
    </style>
""", unsafe_allow_html=True)


# Cargar datos
@st.cache_data
def load_data():
    cursos = cargar_cursos()
    nombres_por_codigo = {c["codigo"]: c["nombre"] for c in cursos}
    
    return cursos, nombres_por_codigo

cursos, nombres_por_codigo = load_data()

# Agrupar cursos por año y por ciclo UI (entero)
cursos_por_anio_ciclo = {}
for c in cursos:
    anio = c["anio"]
    # Asegurarnos de que ciclo sea entero: si por error es lista, tomamos el primero
    ciclo_ui = c["ciclo"][0] if isinstance(c["ciclo"], list) else c["ciclo"]
    cursos_por_anio_ciclo.setdefault(anio, {}).setdefault(ciclo_ui, []).append(c)



# Páginas principales
pagina = st.sidebar.radio("Navegación", ["📋 Mi Progreso y Planificación"])

if pagina == "📋 Mi Progreso y Planificación":
    # === PÁGINA DE PROGRESO Y PLANIFICACIÓN ===
    st.markdown('<div class="header"><h1>🎓 Mi Progreso y Planificación</h1></div>', unsafe_allow_html=True)
    
    # === SELECCIÓN DE CURSOS APROBADOS ===
    st.markdown('<div class="subheader"><h2>✅ Selección de Cursos Aprobados</h2></div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ Instrucciones", expanded=False):
        st.info("""
        Selecciona los cursos que ya has aprobado organizados por año y ciclo académico.
        - Usa los botones **Seleccionar todos** para marcar todos los cursos de un ciclo
        - Puedes buscar cursos específicos usando el filtro de búsqueda
        """)
    
    aprobados_codigos = []
    
    if "seleccion_por_ciclo" not in st.session_state:
        st.session_state["seleccion_por_ciclo"] = {}
    
    for anio in sorted(cursos_por_anio_ciclo):
        with st.expander(f"📅 Año {anio}", expanded=True):
            cols = st.columns(2)
            for i, ciclo in enumerate(sorted(cursos_por_anio_ciclo[anio])):
                with cols[i % 2]:
                    lista = cursos_por_anio_ciclo[anio][ciclo]
                    nombres = [c["nombre"] for c in lista]
                    
                    key_select_all = f"select_all_{anio}_{ciclo}"
                    key_multi = f"aprobado_{anio}_{ciclo}"
                    
                    # Inicializar almacenamiento en sesión
                    if key_select_all not in st.session_state["seleccion_por_ciclo"]:
                        st.session_state["seleccion_por_ciclo"][key_select_all] = False
                    
                    # Botón para seleccionar todos
                    if st.button(f"📌 Seleccionar todos - Año {anio} Ciclo {ciclo}", key=f"btn_{anio}_{ciclo}"):
                        st.session_state["seleccion_por_ciclo"][key_select_all] = not st.session_state["seleccion_por_ciclo"][key_select_all]
                    
                    # Definir valor por defecto en el multiselect
                    default_val = nombres if st.session_state["seleccion_por_ciclo"][key_select_all] else []
                    seleccionados = st.multiselect(
                        f"**Ciclo {ciclo} - Año {anio}**",
                        nombres,
                        default=default_val,
                        key=key_multi,
                        help=f"Selecciona los cursos aprobados del ciclo {ciclo} del año {anio}"
                    )
                    
                    # Resetear selección si el usuario borra manualmente
                    if len(seleccionados) == 0:
                        st.session_state["seleccion_por_ciclo"][key_select_all] = False
                    
                    for nombre in seleccionados:
                        for c in lista:
                            if c["nombre"] == nombre:
                                aprobados_codigos.append(c["codigo"])

    # === FILTROS ===
    st.markdown('<div class="subheader"><h2>🔍 Filtros</h2></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        mostrar_aprobados = st.checkbox("Mostrar solo cursos aprobados", False)
    with col2:
        mostrar_pendientes = st.checkbox("Mostrar solo cursos pendientes", False)
    
    # === RESUMEN DE PROGRESO ===
    st.markdown('<div class="subheader"><h2>📊 Resumen de Progreso Académico</h2></div>', unsafe_allow_html=True)
    
    if aprobados_codigos:
        # Calcular estadísticas generales
        total_cursos = len(cursos)
        cursos_aprobados = len(aprobados_codigos)
        porcentaje_avance = (cursos_aprobados / total_cursos) * 100
        
        # Mostrar barra de progreso
        st.markdown(f"""
        <div class="progress-container">
            <div class="progress-bar" style="width: {porcentaje_avance}%">
                {porcentaje_avance:.1f}% completado
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total cursos aprobados", cursos_aprobados)
        with col2:
            st.metric("Total cursos pendientes", total_cursos - cursos_aprobados)
        with col3:
            st.metric("Porcentaje completado", f"{porcentaje_avance:.1f}%")
        
        # Mostrar tabla detallada
        datos_aprobados = []
        for c in cursos:
            if c["codigo"] in aprobados_codigos:
                datos_aprobados.append({
                    "Año": c["anio"],
                    "Ciclo": c["ciclo"],
                    "Código": c["codigo"],
                    "Nombre": c["nombre"],
                    "Créditos": c.get("creditos", 0),
                    "Estado": "✅ Aprobado"
                })
            else:
                datos_aprobados.append({
                    "Año": c["anio"],
                    "Ciclo": c["ciclo"],
                    "Código": c["codigo"],
                    "Nombre": c["nombre"],
                    "Créditos": c.get("creditos", 0),
                    "Estado": "⌛ Pendiente"
                })
        
        df_progreso = pd.DataFrame(datos_aprobados)
        
        # Aplicar filtros
        if mostrar_aprobados:
            df_progreso = df_progreso[df_progreso["Estado"] == "✅ Aprobado"]
        if mostrar_pendientes:
            df_progreso = df_progreso[df_progreso["Estado"] == "⌛ Pendiente"]
        df_progreso["Ciclo"] = df_progreso["Ciclo"].apply(
        lambda x: x[0] if isinstance(x, list) else x
    )
        
        st.dataframe(
            df_progreso.sort_values(by=["Año", "Ciclo", "Nombre"]),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Estado": st.column_config.SelectboxColumn(
                    "Estado",
                    options=["✅ Aprobado", "⌛ Pendiente"]
                )
            }
        )
    else:
        st.warning("No has seleccionado ningún curso aprobado aún.")
    
    # === CONFIGURACIÓN ===
    st.markdown('<div class="subheader"><h2>⚙️ Configuración</h2></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        ciclo_actual = st.selectbox(
            "Ciclo académico próximo", 
            [1, 2], 
            help="Selecciona el ciclo que vas a cursar"
        )
    with col2:
        max_cursos = st.slider(
            "Cursos por ciclo", 
            min_value=1,
            max_value=8,
            value=3,
            step=1,
            help="Número máximo de cursos que planeas llevar por ciclo"
        )
    
    
    st.markdown('<div class="subheader"><h2>📅 </h2></div>', unsafe_allow_html=True)
    
    codigos_aprobados = set(aprobados_codigos)
    nombres_pendientes = [c["nombre"] for c in cursos if c["codigo"] not in codigos_aprobados]
    
    # === RECOMENDACIÓN INTELIGENTE ===
    st.markdown('<div class="subheader"><h2>🤖 Recomendación Inteligente</h2></div>', unsafe_allow_html=True)
    
    modo_recomendacion = st.radio(
    "Modo de recomendación:",
    ["Solo próximo ciclo", "🧠 Greedy completo","🧠 Recomendación por IA (CSP)"],
    horizontal=True
)

    
    if st.button("🎯 Generar Recomendación", use_container_width=True, key="btn_recomendar"):
            aprobados_nombres = [nombres_por_codigo[c] for c in aprobados_codigos]
            start_year = datetime.datetime.now().year

            # 1) Solo próximo ciclo
            if modo_recomendacion == "Solo próximo ciclo":
                recomendados = cursos_validos(cursos, aprobados_nombres, ciclo_actual, max_cursos)
                if recomendados:
                    st.success("📋 Cursos para el próximo ciclo:")
                    st.dataframe(
                        pd.DataFrame(recomendados, columns=["Curso"]),
                        use_container_width=True
                    )
                else:
                    st.warning("😕 No hay cursos válidos para el próximo ciclo.")
                plan_sim, back_sim, nodes_sim = None, 0, 0

            elif modo_recomendacion == "🧠 Recomendación por IA (CSP)":
                from csp_solver import planificar_ciclo_unico, planificar_toda_la_carrera
                st.info("Aplicando recomendación basada en IA (CSP)...")
                cursos_ciclo = planificar_ciclo_unico(cursos, aprobados_codigos, ciclo_actual, max_cursos)
                if cursos_ciclo:
                    df = pd.DataFrame([{
                    "Código": c["codigo"],
                    "Nombre": c["nombre"],
                    "Año": c["anio"],
                    "Ciclo": c["ciclo"],
                    "Créditos": c.get("creditos", 0)
                    } for c in cursos_ciclo])
                    st.success("📋 Cursos recomendados para el próximo ciclo (CSP):")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.warning("No hay cursos válidos según CSP para el próximo ciclo.")

            # 2) Greedy completo
            elif modo_recomendacion == "🧠 Greedy completo":
                t0 = time.time()
                plan_sim, iter_greedy, nodos_greedy = simular_avance(
                    cursos, aprobados_nombres, ciclo_actual, max_cursos, start_year
                )
                elapsed_greedy = time.time() - t0

                st.subheader("📊 Métricas Greedy")
                st.metric("⏱️ Tiempo (s)",      f"{elapsed_greedy:.3f}")
                st.metric("🔄 Iteraciones",      iter_greedy)
                st.metric("🔎 Nodos explorados", nodos_greedy)

                # — Mostrar plan SEMESTRE A SEMESTRE — 
            if modo_recomendacion == "🧠 Greedy completo" and plan_sim:
                st.subheader("🗓️ Plan semestre a semestre")
                for etapa in plan_sim:
                    with st.expander(f"Ciclo {etapa['ciclo']} — Año {etapa['año']}", expanded=False):
                        df = pd.DataFrame([{"Curso": n} for n in etapa["cursos"]])
                        st.dataframe(df, hide_index=True, use_container_width=True)



    # ——————————————————————————————————————
# 🔗 Grafo de prerequisitos (en la misma página)
if st.button("🖇️ Ver grafo de prerequisitos", use_container_width=True):
    with st.spinner("Generando grafo..."):
        G = construir_grafo(cursos)
        html_file = mostrar_grafo_pyvis(G, aprobados=aprobados_codigos)
        # lo mostramos embebido
        st.components.v1.html(
            open(html_file, 'r', encoding='utf-8').read(),
            height=600,
            scrolling=True
        )
        st.markdown("**🔹 Azul = aprobado • 🟠 Naranja = pendiente**")
# ——————————————————————————————————————
