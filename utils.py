
import json
import networkx as nx
from pyvis.network import Network

def cargar_cursos(path="cursos.json"):
    with open(path, "r") as f:
        cursos = json.load(f)
        for c in cursos:
            c["semestre"] = [(c["anio"]-1)*2 + c["ciclo"]]
        return cursos

def cursos_validos(cursos, aprobados_nombres, ciclo_actual, max_cursos, por_aprobar=None):
    nombre_a_codigo = {c["nombre"]: c["codigo"] for c in cursos}
    codigo_a_nombre = {c["codigo"]: c["nombre"] for c in cursos}

    aprobados = [nombre_a_codigo[n] for n in aprobados_nombres if n in nombre_a_codigo]
    if por_aprobar:
        por_aprobar_codes = [nombre_a_codigo[n] for n in por_aprobar if n in nombre_a_codigo]
        aprobados += por_aprobar_codes

    prox_ciclo = 2 if ciclo_actual == 1 else 1

    cursos_prox_ciclo = [
        c for c in cursos 
        if c["ciclo"] == prox_ciclo 
        and c["codigo"] not in aprobados
        and all(pr in aprobados for pr in c["requisitos"])
    ]

    if len(cursos_prox_ciclo) < max_cursos:
        cursos_alternativos = [
            c for c in cursos
            if c["codigo"] not in aprobados
            and c["ciclo"] != prox_ciclo
            and all(pr in aprobados for pr in c["requisitos"])
            and c not in cursos_prox_ciclo
        ]
        cursos_alternativos = ordenar_por_importancia(
            [c["codigo"] for c in cursos_alternativos], cursos)
        cursos_alternativos = [next(c for c in cursos if c["codigo"] == cod) 
                             for cod in cursos_alternativos]

        cursos_prox_ciclo.extend(cursos_alternativos[:max_cursos - len(cursos_prox_ciclo)])

    cursos_ordenados = ordenar_por_importancia(
        [c["codigo"] for c in cursos_prox_ciclo], cursos)
    return [codigo_a_nombre[c] for c in cursos_ordenados[:max_cursos]]

def validar_manual(cursos, seleccion_manual):
    validos = []
    for code in seleccion_manual:
        curso = next(c for c in cursos if c["codigo"] == code)
        if all(pr in seleccion_manual for pr in curso["requisitos"]):
            validos.append(curso["nombre"])
    return validos

def ordenar_por_importancia(codigos, cursos):
    def contar_dependencias(curso_codigo):
        return sum(1 for c in cursos if curso_codigo in c["requisitos"])
    return sorted(codigos, key=contar_dependencias, reverse=True)

def construir_grafo(cursos):
    G = nx.DiGraph()
    for curso in cursos:
        G.add_node(curso["codigo"], label=curso["nombre"])
        for prereq in curso["requisitos"]:
            G.add_edge(prereq, curso["codigo"])
    return G

def mostrar_grafo_pyvis(G, aprobados=[]):
    net = Network(height="750px", width="100%", directed=True)
    for node in G.nodes(data=True):
        color = "#2E86AB" if node[0] in aprobados else "#F18F01"
        net.add_node(node[0], label=node[1]['label'], color=color)

    for source, target in G.edges():
        net.add_edge(source, target)

    net.set_options("""
    var options = {
      "nodes": {
        "font": {
          "size": 16
        }
      },
      "edges": {
        "arrows": {
          "to": {
            "enabled": true
          }
        }
      },
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -12000,
          "centralGravity": 0.3,
          "springLength": 95
        }
      }
    }
    """)
    path = "grafo.html"
    net.save_graph(path)
    return path

def alertas_riesgo(plan, max_cursos):
    alertas = []
    for etapa in plan:
        if len(etapa["cursos"]) > max_cursos:
            alertas.append(f"El ciclo {etapa['ciclo']} excede el máximo de {max_cursos} cursos.")
    return alertas

def predecir_graduacion(cursos, aprobados_nombres, ciclo_actual, max_cursos):
    restantes = [c for c in cursos if c["nombre"] not in aprobados_nombres]
    if not restantes:
        return "Graduado"

    historial = set(c["nombre"] for c in cursos if c["nombre"] in aprobados_nombres)
    ciclo = ciclo_actual
    ciclos_usados = 0

    while restantes and ciclos_usados < 12:
        posibles = [c for c in restantes if all(pr in [cur["codigo"] for cur in cursos if cur["nombre"] in historial] for pr in c["requisitos"]) and c["ciclo"] == ciclo]
        seleccion = ordenar_por_importancia([c["codigo"] for c in posibles], cursos)[:max_cursos]
        if not seleccion:
            ciclo = 2 if ciclo == 1 else 1
            ciclos_usados += 1
            continue
        historial.update(c["nombre"] for c in cursos if c["codigo"] in seleccion)
        restantes = [c for c in restantes if c["nombre"] not in historial]
        ciclo = 2 if ciclo == 1 else 1
        ciclos_usados += 1

    if restantes:
        return None
    return f"Semestre {2023 + (ciclos_usados // 2)}-{(ciclos_usados % 2) + 1}"
