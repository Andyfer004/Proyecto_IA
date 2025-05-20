import streamlit as st
from csp_solver import cargar_cursos, cursos_validos
from simulador import simular_avance

st.set_page_config(page_title="Planificador Académico", layout="centered")

st.title("🎓 Planificador Académico Inteligente")

cursos = cargar_cursos()
todos = [c["nombre"] for c in cursos]

aprobados = st.multiselect("Selecciona los cursos que ya aprobaste:", todos)
ciclo_actual = st.selectbox("¿Qué ciclo académico viene?", [1, 2])
max_cursos = st.slider("¿Cuántos cursos planeas llevar por ciclo?", 1, 6, 3)

modo = st.radio("Modo de recomendación", ["Solo próximo ciclo", "Simular varios ciclos"])

if st.button("🎯 Recomendar cursos"):
    if modo == "Solo próximo ciclo":
        recomendados = cursos_validos(cursos, aprobados, ciclo_actual, max_cursos)
        st.subheader("📋 Cursos recomendados:")
        st.write(recomendados if recomendados else "😕 No hay cursos válidos disponibles.")
    else:
        plan = simular_avance(cursos, aprobados, ciclo_actual, max_cursos, n_ciclos=10)
        st.subheader("🧭 Plan de avance sugerido:")
        for etapa in plan:
            cursos_texto = ', '.join(etapa["cursos"]) if etapa["cursos"] else "Sin cursos disponibles"
            st.markdown(f"**Ciclo {etapa['ciclo']}:** {cursos_texto}")