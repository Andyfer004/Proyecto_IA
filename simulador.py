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

# simulador.py

# Contadores globales
contador_iteraciones = 0
contador_nodos      = 0

def simular_avance(cursos, aprobados_nombres, ciclo_actual, max_cursos, start_year, por_aprobar=None):
    """
    Simula avance semestre a semestre hasta agotar todos los cursos,
    y devuelve:
      - plan: lista de etapas {ciclo, año, cursos, detalles, creditos}
      - contador_iteraciones: cuántas iteraciones del bucle principal
      - contador_nodos:        cuántos "nodos" (cursos candidatos) se exploraron
    """
    global contador_iteraciones, contador_nodos
    contador_iteraciones = 0
    contador_nodos      = 0

    # --- Inicializar historial de aprobados ---
    nombre_a_codigo = {c["nombre"]: c["codigo"] for c in cursos}
    historial = {nombre_a_codigo[n] for n in aprobados_nombres if n in nombre_a_codigo}
    if por_aprobar:
        historial.update(nombre_a_codigo[n] for n in por_aprobar if n in nombre_a_codigo)

    plan = []
    current_year  = start_year
    current_cycle = ciclo_actual
    restantes     = [c for c in cursos if c["codigo"] not in historial]

    # --- Bucle principal semestre a semestre ---
    while restantes:
        contador_iteraciones += 1

        # 1) Filtrar candidatos válidos en este ciclo
        cursos_ciclo = [
            c for c in cursos
            if current_cycle in c.get("semestre", [])
               and c["codigo"] not in historial
               and all(pr in historial for pr in c["requisitos"])
        ]
        # Contar nodos explorados
        contador_nodos += len(cursos_ciclo)

        if not cursos_ciclo:
            break

        # 2) Si caben menos de max_cursos, buscar alternativos en mismo ciclo
        if len(cursos_ciclo) < max_cursos:
            alternativos = [
                c for c in cursos
                if current_cycle in c.get("semestre", [])
                   and c["codigo"] not in historial
                   and all(pr in historial for pr in c["requisitos"])
                   and c not in cursos_ciclo
            ]
            # ordena alternativos según tu heurística de prioridad
            alternativos = ordenar_por_prioridad(alternativos, cursos, historial)
            cursos_ciclo.extend(alternativos[: max_cursos - len(cursos_ciclo)])
            contador_nodos += len(alternativos[: max_cursos - len(cursos_ciclo)])

        # 3) Elegir los top-max_cursos y añadir etapa
        seleccion = ordenar_por_prioridad(cursos_ciclo, cursos, historial)[:max_cursos]
        plan.append({
            "ciclo":    current_cycle,
            "año":      current_year,
            "cursos":   [c["nombre"] for c in seleccion],
            "detalles": seleccion,
            "creditos": sum(c.get("creditos", 0) for c in seleccion)
        })

        # 4) Actualizar historial y alternar ciclo/año
        historial.update(c["codigo"] for c in seleccion)
        current_cycle = 2 if current_cycle == 1 else 1
        if current_cycle == ciclo_actual:
            current_year += 1

        restantes = [c for c in cursos if c["codigo"] not in historial]

    # 5) Devolver siempre los tres valores
    return plan, contador_iteraciones, contador_nodos


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
