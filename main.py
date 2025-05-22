# main.py (versión reorganizada)

import json
import streamlit as st
import pandas as pd
from utils import cargar_cursos, cursos_validos, validar_manual
from simulador import simular_avance
from utils import construir_grafo, mostrar_grafo_pyvis, alertas_riesgo, predecir_graduacion

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

# Cargar datos
@st.cache_data
def load_data():
    cursos = cargar_cursos()
    nombres_por_codigo = {c["codigo"]: c["nombre"] for c in cursos}
    
    # Agregar semestre basado en ciclo (1 o 2)
    for c in cursos:
        c["semestre"] = [c["ciclo"]]
    
    return cursos, nombres_por_codigo

cursos, nombres_por_codigo = load_data()

# Agrupar cursos por año y ciclo
cursos_por_anio_ciclo = {}
for c in cursos:
    anio, ciclo = c["anio"], c["ciclo"]
    cursos_por_anio_ciclo.setdefault(anio, {}).setdefault(ciclo, []).append(c)

# Páginas principales
pagina = st.sidebar.radio("Navegación", ["📋 Mi Progreso y Planificación", "📊 Visualizaciones"])

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
            1, 6, 3,
            help="Número máximo de cursos que planeas llevar por ciclo"
        )
    
    
    st.markdown('<div class="subheader"><h2>📅 </h2></div>', unsafe_allow_html=True)
    
    codigos_aprobados = set(aprobados_codigos)
    nombres_pendientes = [c["nombre"] for c in cursos if c["codigo"] not in codigos_aprobados]
    
    # === RECOMENDACIÓN INTELIGENTE ===
    st.markdown('<div class="subheader"><h2>🤖 Recomendación Inteligente</h2></div>', unsafe_allow_html=True)
    
    modo_recomendacion = st.radio(
        "**Modo de recomendación:**",
        ["Solo próximo ciclo", "Simular varios ciclos", "Validación manual", "🧠 Recomendación por IA (CSP)"],
        horizontal=True,
        help="Elige cómo deseas que el sistema te ayude a planificar"
    )
    
    if st.button("🎯 Generar Recomendación", use_container_width=True, key="btn_recomendar"):
        aprobados_nombres = [nombres_por_codigo[c] for c in aprobados_codigos if c in nombres_por_codigo]
        
        if modo_recomendacion == "Solo próximo ciclo":
            recomendados = cursos_validos(cursos, aprobados_nombres, ciclo_actual, max_cursos)
            
            if recomendados:
                st.success("### 📋 Cursos recomendados para el próximo ciclo:")
                
                # Mostrar como tarjetas
                cols = st.columns(2)
                for i, curso in enumerate(recomendados):
                    with cols[i % 2]:
                        curso_info = next(c for c in cursos if c["nombre"] == curso)
                        st.markdown(f"""
                        <div class="course-card">
                            <strong>{curso_info['codigo']}</strong><br>
                            {curso}<br>
                            <small>Año: {curso_info['anio']} | Ciclo: {curso_info['ciclo']} | Créditos: {curso_info.get('creditos', 0)}</small>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Mostrar también como tabla
                df_recomendados = pd.DataFrame([{
                    "Código": c["codigo"],
                    "Nombre": c["nombre"],
                    "Año": c["anio"],
                    "Ciclo": c["ciclo"],
                    "Créditos": c.get("creditos", 0)
                } for c in cursos if c["nombre"] in recomendados])
                
                st.dataframe(df_recomendados, use_container_width=True, hide_index=True)
            else:
                st.warning("😕 No hay cursos válidos disponibles para el próximo ciclo con los requisitos actuales.")
        
        elif modo_recomendacion == "Simular varios ciclos":
            pass
        elif modo_recomendacion == "🧠 Recomendación por IA (CSP)":
            from csp_solver import planificar_ciclo_unico, planificar_toda_la_carrera
            st.info("Aplicando recomendación basada en IA (CSP)...")

            if st.checkbox("📘 Simular toda la carrera con CSP"):
                plan = planificar_toda_la_carrera(cursos, aprobados_codigos, ciclo_actual, max_cursos)
                if plan:
                    for etapa in plan:
                        with st.expander(f"Ciclo {etapa['ciclo']}", expanded=False):
                            df = pd.DataFrame([{
                                "Código": c["codigo"],
                                "Nombre": c["nombre"],
                                "Año": c["anio"],
                                "Ciclo": c["ciclo"],
                                "Créditos": c.get("creditos", 0)
                            } for c in etapa["cursos"]])
                            st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.error("No se pudo encontrar una planificación válida con CSP.")
            else:
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

            with st.spinner("Simulando plan de estudios..."):
                plan = simular_avance(cursos, aprobados_nombres, ciclo_actual, max_cursos, n_ciclos=6)
            
            if plan:
                st.success("### 🧭 Plan de avance sugerido (6 ciclos):")
                
                for i, etapa in enumerate(plan):
                    with st.expander(f"📌 Ciclo {etapa['ciclo']} - Año {1 + (etapa['ciclo']-1)//2}", expanded=i<2):
                        if etapa["cursos"]:
                            # Mostrar métricas rápidas
                            cols = st.columns(3)
                            with cols[0]:
                                st.metric("Cursos", len(etapa["cursos"]))
                            with cols[1]:
                                creditos = sum(c.get("creditos", 0) for c in cursos if c["nombre"] in etapa["cursos"])
                                st.metric("Total créditos", creditos)
                            with cols[2]:
                                dificultad = sum(len(c["requisitos"]) for c in cursos if c["nombre"] in etapa["cursos"])
                                st.metric("Dificultad relativa", dificultad)
                            
                            # Mostrar cursos como tarjetas
                            for curso in etapa["cursos"]:
                                curso_info = next(c for c in cursos if c["nombre"] == curso)
                                st.markdown(f"""
                                <div class="course-card">
                                    <strong>{curso_info['codigo']}</strong><br>
                                    {curso}<br>
                                    <small>Año: {curso_info['anio']} | Créditos: {curso_info.get('creditos', 0)}</small>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.info("No hay cursos disponibles para este ciclo según los requisitos.")
                
                # Mostrar alertas
                avisos = alertas_riesgo(plan, max_cursos)
                if avisos:
                    st.warning("### ⚠️ Alertas importantes:")
                    for aviso in avisos:
                        st.markdown(f"- {aviso}")
            else:
                st.error("No se pudo generar un plan de avance con los parámetros actuales.")
# === PÁGINA DE VISUALIZACIONES ===
    st.markdown('<div class="header"><h1>📊 Visualizaciones del Avance Académico</h1></div>', unsafe_allow_html=True)
    
    # Verificar si hay cursos aprobados seleccionados
    if "seleccion_por_ciclo" not in st.session_state or not any(st.session_state["seleccion_por_ciclo"].values()):
        st.warning("Por favor selecciona tus cursos aprobados en la página de 'Mi Progreso' primero para habilitar las visualizaciones.")
        st.stop()
    
    # Obtener códigos de cursos aprobados
    aprobados_codigos = []
    for key in st.session_state["seleccion_por_ciclo"]:
        if key.startswith("aprobado_"):
            anio_ciclo = key.replace("aprobado_", "").split("_")
            if len(anio_ciclo) == 2:
                anio = int(anio_ciclo[0])
                ciclo = int(anio_ciclo[1])
                for c in cursos_por_anio_ciclo.get(anio, {}).get(ciclo, []):
                    if c["nombre"] in st.session_state["seleccion_por_ciclo"][key]:
                        aprobados_codigos.append(c["codigo"])
    
    if not aprobados_codigos:
        st.warning("No hay cursos aprobados seleccionados. Por favor selecciona al menos un curso aprobado.")
        st.stop()
    
    # Gráficos de progreso
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Progreso por año")
        
        datos_progreso = []
        for anio in sorted(cursos_por_anio_ciclo):
            total_anio = sum(1 for c in cursos if c["anio"] == anio)
            aprobados_anio = sum(1 for c in cursos if c["anio"] == anio and c["codigo"] in aprobados_codigos)
            datos_progreso.append({
                "Año": f"Año {anio}",
                "Total": total_anio,
                "Aprobados": aprobados_anio,
                "Pendientes": total_anio - aprobados_anio
            })
        
        df_progreso = pd.DataFrame(datos_progreso).set_index("Año")
        st.bar_chart(df_progreso[["Aprobados", "Pendientes"]], color=["#2E86AB", "#F18F01"])
    
    with col2:
        st.markdown("### ⏳ Predicción de graduación")
        
        # Obtener configuración
        ciclo_actual = st.selectbox(
            "Ciclo académico próximo", 
            [1, 2], 
            help="Selecciona el ciclo que vas a cursar",
            key="pred_ciclo"
        )
        max_cursos = st.slider(
            "Cursos por ciclo", 
            1, 6, 3,
            help="Número máximo de cursos que planeas llevar por ciclo",
            key="pred_max"
        )
        
        if st.button("Calcular fecha estimada", key="btn_prediccion"):
            with st.spinner("Calculando..."):
                aprobados_nombres = [nombres_por_codigo[c] for c in aprobados_codigos if c in nombres_por_codigo]
                sem = predecir_graduacion(cursos, aprobados_nombres, ciclo_actual, max_cursos)
                
                if sem:
                    año_graduacion = 2023 + (int(sem.split("-")[1]) // 2)
                    st.success(f"""
                    <div style="text-align: center; padding: 20px; background-color: #E8F4F8; border-radius: 10px;">
                        <h3>Semestre esperado de graduación:</h3>
                        <h1 style="color: var(--primary);">{sem}</h1>
                        <p>Aproximadamente en {año_graduacion}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Calcular tiempo estimado
                    ciclos_restantes = int(sem.split("-")[1]) - ciclo_actual
                    años_restantes = ciclos_restantes // 2
                    meses_restantes = años_restantes * 6  # 6 meses por ciclo
                    
                    st.metric("Tiempo estimado", f"{años_restantes} año(s) y {ciclos_restantes % 2} ciclo(s)")
                else:
                    st.error("No se puede completar el plan de estudios con la configuración actual.")
    
    # Grafo de prerequisitos
    st.markdown("---")
    st.markdown('<div class="subheader"><h3>📚 Grafo de Prerequisitos</h3></div>', unsafe_allow_html=True)
    
    if st.button("🖇️ Generar grafo interactivo", use_container_width=True):
        with st.spinner("Generando visualización..."):
            G = construir_grafo(cursos)
            html_file = mostrar_grafo_pyvis(G, aprobados=aprobados_codigos)
            
            # Mostrar el grafo en un contenedor más grande
            st.components.v1.html(open(html_file).read(), height=800, scrolling=True)
            
            st.info("""
            💡 **Leyenda del grafo:**
            - 🔵 Nodos azules: Cursos aprobados
            - 🟠 Nodos naranja: Cursos pendientes
            - ➡️ Flechas: Relaciones de prerequisitos
            """)
    
    # Exportar datos
    st.markdown("---")
    st.markdown('<div class="subheader"><h3>📤 Exportar datos</h3></div>', unsafe_allow_html=True)
    
    if st.button("💾 Exportar mi progreso a JSON"):
        progreso = {
            "aprobados": aprobados_codigos,
            "configuracion": {
                "ciclo_actual": ciclo_actual,
                "max_cursos": max_cursos
            }
        }
        st.download_button(
            label="Descargar archivo JSON",
            data=json.dumps(progreso, indent=2),
            file_name="progreso_academico.json",
            mime="application/json"
        )