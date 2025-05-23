# utils.py

def contar_dependencias(curso_nombre, cursos):
    count = 0
    for curso in cursos:
        if curso_nombre in curso["prerequisitos"]:
            count += 1
    return count

def ordenar_por_importancia(candidatos, cursos):
    importancia = {c: contar_dependencias(c, cursos) for c in candidatos}
    return sorted(candidatos, key=lambda x: importancia[x], reverse=True)

def filtrar_por_semestre(cursos, semestre):
    return [c for c in cursos if semestre in c["semestre"]]

def filtrar_aprobados(cursos, aprobados):
    return [c for c in cursos if c["nombre"] not in aprobados]


# ——— Nuevas funcionalidades ———

import networkx as nx
from pyvis.network import Network

def construir_grafo(cursos):
    G = nx.DiGraph()
    for c in cursos:
        G.add_node(c["codigo"], label=c["nombre"])
        for pr in c["prerequisitos"]:
            G.add_edge(pr, c["codigo"])
    return G

def mostrar_grafo_pyvis(G, output="grafo.html"):
    """
    Genera un archivo HTML con la visualización del grafo PyVis
    sin usar el modo notebook (evita errores de template).
    Devuelve la ruta al archivo generado.
    """
    from pyvis.network import Network

    # Crear red dirigida con tamaño fijo
    net = Network(height="600px", width="100%", directed=True)
    net.from_nx(G)

    # Escribir HTML sin intentar abrir navegador ni modo notebook
    net.write_html(output, open_browser=False, notebook=False)
    return output


def alertas_riesgo(plan, max_cursos):
    avisos = []
    for etapa in plan:
        if len(etapa["cursos"]) < max_cursos:
            avisos.append(
                f"Ciclo {etapa['ciclo']}: riesgo de atraso (solo {len(etapa['cursos'])} cursos)."
            )
    return avisos

def predecir_graduacion(cursos, aprobados_nombres, ciclo_actual, max_cursos):
    from simulador import simular_avance

    plan = simular_avance(cursos, aprobados_nombres, ciclo_actual, max_cursos, n_ciclos=20)
    acumulado = set(aprobados_nombres)
    total = set(c["nombre"] for c in cursos)
    for etapa in plan:
        acumulado.update(etapa["cursos"])
        if total <= acumulado:
            return etapa["ciclo"]
    return None


def ruta_optima_vs_plan_ideal(cursos, plan_ideal, aprobados_codigos, ciclo_absoluto, max_cursos, n_ciclos=20):
    curso_dict = {c["codigo"]: c for c in cursos}
    plan_por_curso = {
        codigo: (bloque["anio"], bloque["semestre"])
        for bloque in plan_ideal
        for codigo in bloque["cursos"]
    }

    historial = set(aprobados_codigos)
    plan = []

    for ciclo_index in range(ciclo_absoluto, ciclo_absoluto + n_ciclos):
        semestre = 1 if ciclo_index % 2 == 1 else 2

        dispo = [
            c for c in cursos
            if semestre in c["semestre"] and c["codigo"] not in historial
        ]
        elegibles = [
            c for c in dispo
            if all(pr in historial for pr in c["prerequisitos"])
        ]

        seleccion = [c["codigo"] for c in elegibles][:max_cursos]
        plan.append({"ciclo": ciclo_index, "cursos": seleccion})
        historial.update(seleccion)

        if len(historial) == len(cursos):
            break

    # Comparar contra plan ideal
    cursos_simulados = {}
    for etapa in plan:
        for c in etapa["cursos"]:
            cursos_simulados[c] = etapa["ciclo"]

    retrasados = []
    for c, (anio, semestre) in plan_por_curso.items():
        ciclo_ideal = (anio - 1) * 2 + semestre
        ciclo_real = cursos_simulados.get(c)
        if ciclo_real is not None and ciclo_real > ciclo_ideal:
            retrasados.append({
                "codigo": c,
                "nombre": curso_dict[c]["nombre"],
                "ciclo_ideal": ciclo_ideal,
                "ciclo_real": ciclo_real
            })

    return plan, retrasados
