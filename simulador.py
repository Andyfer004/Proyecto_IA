# simulador.py

from utils import ordenar_por_importancia

def simular_avance(cursos, aprobados_nombres, ciclo_actual, max_cursos, n_ciclos=4):
    # Mapas nombre⇄código
    nombre_a_codigo = {c["nombre"]: c["codigo"] for c in cursos}
    codigo_a_nombre = {c["codigo"]: c["nombre"] for c in cursos}

    historial = set(
        nombre_a_codigo[n]
        for n in aprobados_nombres
        if n in nombre_a_codigo
    )

    plan = []
    ciclo = ciclo_actual

    for _ in range(n_ciclos):
        dispo = [
            c for c in cursos
            if ciclo in c["semestre"]
               and c["codigo"] not in historial
        ]
        elegibles = [
            c for c in dispo
            if all(pr in historial for pr in c["prerequisitos"])
        ]
        codes = [c["codigo"] for c in elegibles]

        seleccion = ordenar_por_importancia(codes, cursos)[:max_cursos]
        plan.append({
            "ciclo": ciclo,
            "cursos": [codigo_a_nombre[code] for code in seleccion]
        })

        historial.update(seleccion)
        ciclo = 2 if ciclo == 1 else 1

    return plan