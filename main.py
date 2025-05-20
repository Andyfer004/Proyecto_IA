import streamlit as st
from csp_solver import cargar_cursos, cursos_validos

st.set_page_config(page_title="Planificador Académico", layout="centered")

st.title("📚 Planificador Académico Inteligente")

cursos = cargar_cursos()
todos = [c["nombre"] for c in cursos]

aprobados = st.multiselect("Selecciona los cursos que ya aprobaste:", todos)
semestre = st.selectbox("¿Qué semestre viene?", [1, 2])
max_cursos = st.slider("¿Cuántos cursos planeas llevar?", 1, 6, 3)

if st.button("🎯 Recomendar cursos"):
    recomendados = cursos_validos(cursos, aprobados, semestre, max_cursos)
    st.subheader("📋 Cursos recomendados:")
    st.write(recomendados if recomendados else "😕 No hay cursos válidos disponibles.")