
from collections import defaultdict

contador_backtracks = 0
contador_nodos = 0

def heuristica_completa(codigo, cursos, historial):
    curso = next(c for c in cursos if c["codigo"] == codigo)
    dependencias = sum(1 for c in cursos if codigo in c["requisitos"])
    # Penalizar cursos de años mayores si hay pendientes de años menores
    años_pendientes = [c["anio"] for c in cursos if c["codigo"] not in historial]
    min_anio_pendiente = min(años_pendientes) if años_pendientes else curso["anio"]
    penalizacion = (curso["anio"] - min_anio_pendiente) * 10
    sem_val = curso["semestre"][0] if isinstance(curso.get("semestre"), list) else curso.get("semestre")
    return (penalizacion, sem_val, -dependencias)

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
    global contador_backtracks, contador_nodos
    contador_nodos += 1   
    if len(asignaciones) == len(pendientes):
        return asignaciones

    sin_asignar = [c for c in pendientes if c not in asignaciones]
    variable = min(sin_asignar, key=lambda v: len(dominio[v]))

    for ciclo in dominio[variable]:
        if sum(1 for v in asignaciones.values() if v == ciclo) >= max_cursos:
            continue

        curso = next(c for c in cursos if c["codigo"] == variable)
        if requisitos_cumplidos(curso, asignaciones, ciclo):
            contador_backtracks += 1
            asignaciones[variable] = ciclo            
            if forward_checking(variable, cursos, asignaciones, ciclo, max_cursos, total_ciclos):
                resultado = backtracking(asignaciones, cursos, pendientes, dominio, ciclo_actual, max_cursos, total_ciclos)
                if resultado:
                    return resultado
            del asignaciones[variable]
    return None

def planificar_ciclo_unico(cursos, aprobados_codigos, ciclo_actual, max_cursos):
    """
    Planifica el próximo ciclo usando heurística de dependencias y semestres.
    """
    historial = set(aprobados_codigos)
    # Filtrar candidatos válidos para el semestre actual
    candidatos = [
        c for c in cursos
        if c["codigo"] not in historial
        and ciclo_actual in c["semestre"]
        and all(pr in historial for pr in c["requisitos"])
    ]

    # Ordenar por relevancia usando heuristica_completa a través de ordenar_por_prioridad
    codes_sorted = ordenar_por_prioridad(
        [c["codigo"] for c in candidatos], cursos, historial
    )

    # Mapear códigos ordenados a objetos y devolver los primeros max_cursos
    seleccion = [
        next(course for course in cursos if course["codigo"] == code)
        for code in codes_sorted[:max_cursos]
    ]

    return seleccion

def planificar_toda_la_carrera(cursos, aprobados_codigos, ciclo_actual, max_cursos, total_ciclos=12):
    global contador_backtracks, contador_nodos
    contador_backtracks = 0
    contador_nodos      = 0

    pendientes = [c for c in cursos if c["codigo"] not in aprobados_codigos]
    cod_pend   = [c["codigo"] for c in pendientes]
    dominio    = { c["codigo"]: c["semestre"] for c in pendientes }

    asign = backtracking({}, cursos, cod_pend, dominio, ciclo_actual, max_cursos, total_ciclos)
    # SI FALLA, asign será None, devolvemos métricas igualmente
    if not asign:
        return [], contador_backtracks, contador_nodos

    # Si funciona, construimos el plan como lista de dicts
    from collections import defaultdict
    ciclos = defaultdict(list)
    for cod, ciclo in asign.items():
        curso = next(c for c in cursos if c["codigo"] == cod)
        ciclos[ciclo].append(curso)

    resultado = []
    for ciclo in sorted(ciclos):
        resultado.append({
            "ciclo": ciclo,
            "cursos": sorted(ciclos[ciclo], key=lambda c: (c["anio"], c["ciclo"], c["nombre"]))
        })

    return resultado, contador_backtracks, contador_nodos
