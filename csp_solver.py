# csp_solver.py

import json
from utils import filtrar_por_semestre, filtrar_aprobados, ordenar_por_importancia

def cargar_cursos(path="cursos.json"):
    with open(path, "r") as f:
        return json.load(f)
    
def cargar_plan_ideal(path="plan_ideal.json"):
    with open(path, "r") as f:
        return json.load(f)

def cursos_validos(cursos, aprobados_nombres, ciclo_actual, max_cursos):
    # 1) Mapeo nombre⇄código
    nombre_a_codigo = {c["nombre"]: c["codigo"] for c in cursos}
    codigo_a_nombre = {c["codigo"]: c["nombre"] for c in cursos}

    # 2) Convierte aprobados (nombres) → códigos
    aprobados = [
        nombre_a_codigo[n]
        for n in aprobados_nombres
        if n in nombre_a_codigo
    ]

    # 3) Filtra por semestre y quita ya aprobados
    dispo = [
        c for c in cursos
        if ciclo_actual in c["semestre"]
           and c["codigo"] not in aprobados
    ]

    # 4) Chequea prerequisitos
    elegibles = [
        c["codigo"]
        for c in dispo
        if all(pr in aprobados for pr in c["prerequisitos"])
    ]

    # 5) Ordena y convierte a nombres
    ordenados = ordenar_por_importancia(elegibles, cursos)
    return [codigo_a_nombre[c] for c in ordenados][:max_cursos]

def validar_manual(cursos, seleccion_manual):
    validos = []
    for code in seleccion_manual:
        curso = next(c for c in cursos if c["codigo"] == code)
        if all(pr in seleccion_manual for pr in curso["prerequisitos"]):
            validos.append(curso["nombre"])
    return validos