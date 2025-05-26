from collections import defaultdict
from csp_solver import planificar_toda_la_carrera

def contar_dependencias(curso_codigo, cursos):
    return sum(1 for c in cursos if curso_codigo in c["requisitos"])

def prioridad_compuesta(curso, cursos, historial):
    años_pendientes = [c["anio"] for c in cursos if c["codigo"] not in historial]
    min_anio = min(años_pendientes) if años_pendientes else curso["anio"]
    penalizacion = (curso["anio"] - min_anio) * 10
    sem_val = curso["semestre"][0] if isinstance(curso.get("semestre"), list) else curso.get("semestre")
    return (penalizacion, sem_val, -contar_dependencias(curso["codigo"], cursos))

def ordenar_por_prioridad(candidatos, cursos, historial):
    # candidatos: lista de objetos curso
    return sorted(candidatos, key=lambda c: prioridad_compuesta(c, cursos, historial))

def simular_avance(cursos, aprobados_nombres, ciclo_actual, max_cursos, start_year, por_aprobar=None):
    """
    Simula avance semestre a semestre hasta agotar todos los cursos.
    """
    nombre_a_codigo = {c["nombre"]: c["codigo"] for c in cursos}
    historial = {nombre_a_codigo[n] for n in aprobados_nombres if n in nombre_a_codigo}
    if por_aprobar:
        historial.update(nombre_a_codigo[n] for n in por_aprobar if n in nombre_a_codigo)

    plan = []
    # Año y ciclo actuales para rastrear cambios de año
    current_year = start_year
    current_cycle = ciclo_actual
    restantes = [c for c in cursos if c["codigo"] not in historial]

    while restantes:
        # Filtrar candidatos válidos en este ciclo
        cursos_ciclo = [
            c for c in cursos
            if current_cycle in c["semestre"]
            and c["codigo"] not in historial
            and all(pr in historial for pr in c["requisitos"])
        ]
        if not cursos_ciclo:
            break
        # Completar con alternativos si hay cupo
        if len(cursos_ciclo) < max_cursos:
            alternativos = [
                c for c in cursos
                if current_cycle in c["semestre"]
                and c["codigo"] not in historial
                and all(pr in historial for pr in c["requisitos"])
                and c not in cursos_ciclo
            ]
            alternativos = ordenar_por_prioridad(alternativos, cursos, historial)
            cursos_ciclo.extend(alternativos[: max_cursos - len(cursos_ciclo)])

        # Seleccionar y anotar año actual
        seleccion = ordenar_por_prioridad(cursos_ciclo, cursos, historial)[:max_cursos]
        plan.append({
            "ciclo": current_cycle,
            "año": current_year,
            "cursos": [c["nombre"] for c in seleccion],
            "detalles": seleccion,
            "creditos": sum(c.get("creditos", 0) for c in seleccion)
        })

        # Actualizar historial y alternar ciclo
        historial.update(c["codigo"] for c in seleccion)
                # Alternar ciclo
        current_cycle = 2 if current_cycle == 1 else 1
        # Incrementar año si cambiamos al otro ciclo (p.ej. ciclo 2→1 o 1→2)
        if current_cycle != ciclo_actual:
            current_year += 1

        restantes = [c for c in cursos if c["codigo"] not in historial]

    return plan

def simular_avance_csp(cursos, aprobados_nombres, ciclo_inicial, max_cursos, start_year):
    # 1) Convierte nombres aprobados a códigos
    nombre_a_codigo   = { c["nombre"]: c["codigo"] for c in cursos }
    aprobados_codigos = {
        nombre_a_codigo[n]
        for n in aprobados_nombres
        if n in nombre_a_codigo
    }

    # 2) Llama al solver CSP que ya devuelve (plan, backtracks, nodos)
    plan_csp, backtracks, nodos = planificar_toda_la_carrera(
        cursos, aprobados_codigos, ciclo_inicial, max_cursos
    )

    # 3) Reconstruye el formato con años y ciclos
    plan = []
    year  = start_year
    cycle = ciclo_inicial
    for etapa in plan_csp:
        detalles = etapa["cursos"]
        plan.append({
            "ciclo":    etapa["ciclo"],
            "año":      year,
            "cursos":   [c["nombre"] for c in detalles],
            "detalles": detalles,
            "creditos": sum(c.get("creditos",0) for c in detalles)
        })
        cycle = 2 if cycle == 1 else 1
        if cycle == ciclo_inicial:
            year += 1

    # 4) Devuelve siempre tres valores
    return plan, backtracks, nodos
