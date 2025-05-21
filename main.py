# main.py  (Streamlit)

import json
import streamlit as st
import streamlit.components.v1 as components

from csp_solver import cargar_cursos, cursos_validos, validar_manual
from simulador import simular_avance
from utils import (
    construir_grafo, mostrar_grafo_pyvis,
    alertas_riesgo, predecir_graduacion
)

st.set_page_config(page_title="Planificador Académico", layout="centered")
st.title("🎓 Planificador Académico Inteligente")

# Carga y listas maestras
cursos = cargar_cursos()
todos_nombres = [c["nombre"] for c in cursos]
todos_codigos = [c["codigo"] for c in cursos]

# Inputs del usuario
aprobados = st.multiselect("Selecciona los cursos que ya aprobaste:", todos_nombres)
ciclo_actual = st.selectbox("¿Qué ciclo académico viene?", [1, 2])
max_cursos = st.slider("¿Cuántos cursos planeas llevar por ciclo?", 1, 6, 3)

modo = st.radio("Modo de recomendación", [
    "Solo próximo ciclo",
    "Simular varios ciclos",
    "Asistida"
])

# Botón principal
if st.button("🎯 Recomendar cursos"):
    if modo == "Solo próximo ciclo":
        recomendados = cursos_validos(cursos, aprobados, ciclo_actual, max_cursos)
        st.subheader("📋 Cursos recomendados:")
        st.write(recomendados or "😕 No hay cursos válidos disponibles.")

    elif modo == "Simular varios ciclos":
        plan = simular_avance(cursos, aprobados, ciclo_actual, max_cursos, n_ciclos=4)
        st.subheader("🧭 Plan de avance sugerido:")
        for e in plan:
            txt = ', '.join(e["cursos"]) or "Sin cursos disponibles"
            st.markdown(f"**Ciclo {e['ciclo']}:** {txt}")
        avisos = alertas_riesgo(plan, max_cursos)
        if avisos:
            st.warning("\n".join(avisos))

    else:  # Asistida
        manual = st.multiselect("Elige cursos (por código):", todos_codigos)
        val = validar_manual(cursos, manual)
        st.subheader("✅ Cursos válidos según prerequisitos:")
        st.write(val or "Ninguno cumple prerequisitos.")

# Grafo de prerequisitos
if st.button("📊 Ver grafo de prerequisitos"):
    G = construir_grafo(cursos)
    html_file = mostrar_grafo_pyvis(G)
    with open(html_file, 'r') as f:
        components.html(f.read(), height=620)

# Predicción de graduación
if st.button("⏳ Predecir semestre de graduación"):
    sem = predecir_graduacion(cursos, aprobados, ciclo_actual, max_cursos)
    if sem:
        st.success(f"Semestre esperado de graduación: {sem}")
    else:
        st.error("No se completa con este plan.")

# Guardar / cargar plan
if 'plan' in locals():
    st.download_button(
        "💾 Descargar plan JSON",
        data=json.dumps(plan, ensure_ascii=False),
        file_name="plan.json"
    )

upl = st.file_uploader("📂 Cargar plan guardado", type="json")
if upl:
    carg = json.load(upl)
    st.write("Plan cargado:", carg)
