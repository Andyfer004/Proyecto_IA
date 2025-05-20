# simulador.py
from utils import filtrar_aprobados, filtrar_por_semestre, ordenar_por_importancia

def cursos_elegibles(cursos, aprobados, ciclo):
    disponibles = filtrar_por_semestre(cursos, ciclo)
    no_aprobados = filtrar_aprobados(disponibles, aprobados)
    elegibles = []
    for curso in no_aprobados:
        if all(pr in aprobados for pr in curso["prerequisitos"]):
            elegibles.append(curso)
    return elegibles

def simular_avance(cursos, aprobados_nombres, ciclo_actual, max_cursos, n_ciclos=10):
    # Mapas nombre⇄código
    nombre_a_codigo = {c["nombre"]: c["codigo"] for c in cursos}
    codigo_a_nombre = {c["codigo"]: c["nombre"] for c in cursos}

    # Historial en códigos
    historial = set(
        nombre_a_codigo[n]
        for n in aprobados_nombres
        if n in nombre_a_codigo
    )

    plan = []
    ciclo = ciclo_actual

    for _ in range(n_ciclos):
        # cursos disponibles en este ciclo y no aprobados
        dispo = [
            c for c in cursos
            if ciclo in c["semestre"]
               and c["codigo"] not in historial
        ]
        # los que cumplen prerequisitos
        elegibles = [
            c for c in dispo
            if all(pr in historial for pr in c["prerequisitos"])
        ]
        codes = [c["codigo"] for c in elegibles]

        # seleccionar top-importancia
        seleccion = ordenar_por_importancia(codes, cursos)[:max_cursos]

        # añadir al plan, convirtiendo a nombres
        plan.append({
            "ciclo": ciclo,
            "cursos": [codigo_a_nombre[code] for code in seleccion]
        })

        # simular aprobación de esos cursos
        historial.update(seleccion)
        # alternar ciclo
        ciclo = 2 if ciclo == 1 else 1

    return plan
