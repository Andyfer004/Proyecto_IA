
from collections import defaultdict

def heuristica_completa(codigo, cursos, historial):
    curso = next(c for c in cursos if c["codigo"] == codigo)
    dependencias = sum(1 for c in cursos if codigo in c["requisitos"])
    # Penalizar cursos de años mayores si hay pendientes de años menores
    años_pendientes = [c["anio"] for c in cursos if c["codigo"] not in historial]
    min_anio_pendiente = min(años_pendientes) if años_pendientes else curso["anio"]
    penalizacion = (curso["anio"] - min_anio_pendiente) * 10
    return (penalizacion, curso["ciclo"], -dependencias)

def ordenar_por_prioridad(codigos, cursos, historial):
    return sorted(codigos, key=lambda x: heuristica_completa(x, cursos, historial))

def requisitos_cumplidos(curso, asignaciones, ciclo):
    return all(pr in asignaciones and asignaciones[pr] < ciclo for pr in curso["requisitos"])

def forward_checking(curso_codigo, cursos, asignaciones, ciclo_actual, max_cursos, total_ciclos):
    for c in cursos:
        if c["codigo"] not in asignaciones:
            if not requisitos_cumplidos(c, {**asignaciones, curso_codigo: ciclo_actual}, ciclo_actual):
                return False
    return True

def backtracking(asignaciones, cursos, pendientes, dominio, ciclo_actual, max_cursos, total_ciclos):
    if len(asignaciones) == len(pendientes):
        return asignaciones

    sin_asignar = [c for c in pendientes if c not in asignaciones]
    variable = min(sin_asignar, key=lambda v: len(dominio[v]))

    for ciclo in dominio[variable]:
        if sum(1 for v in asignaciones.values() if v == ciclo) >= max_cursos:
            continue

        curso = next(c for c in cursos if c["codigo"] == variable)
        if requisitos_cumplidos(curso, asignaciones, ciclo):
            asignaciones[variable] = ciclo
            if forward_checking(variable, cursos, asignaciones, ciclo, max_cursos, total_ciclos):
                resultado = backtracking(asignaciones, cursos, pendientes, dominio, ciclo_actual, max_cursos, total_ciclos)
                if resultado:
                    return resultado
            del asignaciones[variable]
    return None

def planificar_ciclo_unico(cursos, aprobados_codigos, ciclo_actual, max_cursos):
    historial = set(aprobados_codigos)
    pendientes = [c for c in cursos if c["codigo"] not in historial]
    candidatos = [
        c for c in pendientes
        if c["ciclo"] == ciclo_actual and all(pr in historial for pr in c["requisitos"])
    ]
    candidatos = ordenar_por_prioridad([c["codigo"] for c in candidatos], cursos, historial)
    return [c for c in cursos if c["codigo"] in candidatos[:max_cursos]]

def planificar_toda_la_carrera(cursos, aprobados_codigos, ciclo_actual, max_cursos, total_ciclos=12):
    pendientes = [c for c in cursos if c["codigo"] not in aprobados_codigos]
    codigos_pendientes = [c["codigo"] for c in pendientes]
    historial = set(aprobados_codigos)

    dominio = {
        c["codigo"]: list(range(ciclo_actual, ciclo_actual + total_ciclos))
        for c in pendientes
    }

    asignaciones = backtracking({}, cursos, codigos_pendientes, dominio, ciclo_actual, max_cursos, total_ciclos)
    if not asignaciones:
        return []

    ciclos = defaultdict(list)
    for cod, ciclo in asignaciones.items():
        curso = next(c for c in cursos if c["codigo"] == cod)
        ciclos[ciclo].append(curso)

    resultado = []
    for ciclo in sorted(ciclos):
        resultado.append({
            "ciclo": ciclo,
            "cursos": sorted(ciclos[ciclo], key=lambda c: (c["anio"], c["ciclo"], c["nombre"]))
        })

    return resultado
