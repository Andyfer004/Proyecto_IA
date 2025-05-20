import json
from utils import filtrar_por_semestre, filtrar_aprobados, ordenar_por_importancia

def cargar_cursos(path="cursos.json"):
    with open(path, "r") as f:
        return json.load(f)

def cursos_validos(cursos, aprobados, semestre_actual, max_cursos):
    disponibles = filtrar_por_semestre(cursos, semestre_actual)
    no_aprobados = filtrar_aprobados(disponibles, aprobados)

    elegibles = []
    for curso in no_aprobados:
        if all(pr in aprobados for pr in curso["prerequisitos"]):
            elegibles.append(curso["nombre"])

    elegidos = ordenar_por_importancia(elegibles, cursos)
    return elegidos[:max_cursos]