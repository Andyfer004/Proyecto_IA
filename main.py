# main.py  (Streamlit)

import json
import streamlit as st
import streamlit.components.v1 as components

from csp_solver import cargar_plan_ideal,cargar_cursos, cursos_validos, validar_manual
from simulador import simular_avance
from utils import (
    construir_grafo, mostrar_grafo_pyvis,
    alertas_riesgo, predecir_graduacion,ruta_optima_vs_plan_ideal
)

st.set_page_config(page_title="Planificador Académico", layout="centered")
st.title("🎓 Planificador Académico Inteligente")

# Carga y listas maestras
cursos = cargar_cursos()
todos_nombres = [c["nombre"] for c in cursos]
todos_codigos = [c["codigo"] for c in cursos]

# Carga de Plan Ideal
plan_ideal = cargar_plan_ideal()

# Inputs del usuario
aprobados = st.multiselect("Selecciona los cursos que ya aprobaste:", todos_nombres)
anio_actual = st.selectbox("¿En qué año académico estás?", [1, 2, 3, 4, 5])
ciclo_actual = st.selectbox("¿Qué ciclo académico viene?", [1, 2])
max_cursos = st.slider("¿Cuántos cursos planeas llevar por ciclo?", 1, 6, 3)


ciclo_absoluto = (anio_actual - 1) * 2 + ciclo_actual  

modo = st.radio("Modo de recomendación", [
    "Solo próximo ciclo",
    "Simular varios ciclos",
    "Asistida",
    "Comparación Con Plan Ideal"
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

    elif modo == "Asistida":  # Asistida
        manual = st.multiselect("Elige cursos (por código):", todos_codigos)
        val = validar_manual(cursos, manual)
        st.subheader("✅ Cursos válidos según prerequisitos:")
        st.write(val or "Ninguno cumple prerequisitos.")

    elif modo == "Comparación Con Plan Ideal":
        nombre_a_codigo = {c["nombre"]: c["codigo"] for c in cursos}
        aprobados_codigos = [nombre_a_codigo[n] for n in aprobados if n in nombre_a_codigo]

        plan, retrasados = ruta_optima_vs_plan_ideal(
            cursos, plan_ideal, aprobados_codigos, ciclo_absoluto, max_cursos
        )
        
        codigo_a_nombre = {c["codigo"]: c["nombre"] for c in cursos}
        st.subheader("📈 Plan óptimo simulado desde tu situación actual:")
        for etapa in plan:
            anio = (etapa['ciclo'] - 1) // 2 + 1
            semestre = 1 if etapa['ciclo'] % 2 == 1 else 2
            detalles = [f"`{c}` {codigo_a_nombre.get(c, 'Nombre desconocido')}" for c in etapa["cursos"]]

            st.markdown(f"### 🗓️ Año {anio} Semestre {semestre} (Ciclo {etapa['ciclo']})")
            if detalles:
                st.markdown("\n".join([f"- {d}" for d in detalles]))
            else:
                st.info("Sin cursos asignados para este ciclo.")

        if retrasados:
            st.subheader("⚠️ Cursos que irían atrasados respecto al plan ideal:")
            for r in retrasados:
                anio_i = (r['ciclo_ideal'] - 1) // 2 + 1
                sem_i = 1 if r['ciclo_ideal'] % 2 == 1 else 2
                anio_r = (r['ciclo_real'] - 1) // 2 + 1
                sem_r = 1 if r['ciclo_real'] % 2 == 1 else 2
                st.markdown(
                    f"- `{r['codigo']}` {r['nombre']}: ideal Año {anio_i} Sem {sem_i} (Ciclo {r['ciclo_ideal']}), "
                    f"real Año {anio_r} Sem {sem_r} (Ciclo {r['ciclo_real']})"
                )
        else:
            st.success("🎉 ¡No hay cursos atrasados! Vas bien con respecto al plan ideal.")

        
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
