import json
from utils import filtrar_por_semestre, filtrar_aprobados, ordenar_por_importancia

def cargar_cursos(path="cursos.json"):
    with open(path, "r") as f:
        return json.load(f)

def cursos_validos(cursos, aprobados_nombres, ciclo_actual, max_cursos):
    # 1) Mapas nombre⇄código
    nombre_a_codigo = {c["nombre"]: c["codigo"] for c in cursos}
    codigo_a_nombre = {c["codigo"]: c["nombre"] for c in cursos}

    # 2) Convierte los aprobados (nombres) a códigos
    aprobados = [ nombre_a_codigo[n]
                  for n in aprobados_nombres
                  if n in nombre_a_codigo ]

    # 3) Filtrar por semestre y quitar los ya aprobados
    dispo = [
        c for c in cursos
        if ciclo_actual in c["semestre"]
           and c["codigo"] not in aprobados
    ]

    # 4) Chequear prerequisitos (todos en 'aprobados')
    elegibles = [
        c["codigo"]
        for c in dispo
        if all(pr in aprobados for pr in c["prerequisitos"])
    ]

    # 5) Ordenar por importancia (usa tu utils)
    ordenados = ordenar_por_importancia(elegibles, cursos)

    # 6) Devolver nombres para la UI
    return [ codigo_a_nombre[c] for c in ordenados ][:max_cursos]