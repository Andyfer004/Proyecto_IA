
# csp_utils.py

import json

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
