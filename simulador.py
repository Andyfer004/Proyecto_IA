
def contar_dependencias(curso_codigo, cursos):
    return sum(1 for c in cursos if curso_codigo in c["requisitos"])

def prioridad_compuesta(curso, cursos, historial):
    min_anio_pendiente = min([c["anio"] for c in cursos if c["codigo"] not in historial], default=curso["anio"])
    penalizacion = (curso["anio"] - min_anio_pendiente) * 10
    return (penalizacion, curso["ciclo"], -contar_dependencias(curso["codigo"], cursos))

def ordenar_por_prioridad(candidatos, cursos, historial):
    return sorted(candidatos, key=lambda x: prioridad_compuesta(x, cursos, historial))

def simular_avance(cursos, aprobados_nombres, ciclo_actual, max_cursos, n_ciclos=6, por_aprobar=None):
    nombre_a_codigo = {c["nombre"]: c["codigo"] for c in cursos}
    codigo_a_nombre = {c["codigo"]: c["nombre"] for c in cursos}

    historial = set(nombre_a_codigo[n] for n in aprobados_nombres if n in nombre_a_codigo)
    if por_aprobar:
        historial.update(nombre_a_codigo[n] for n in por_aprobar if n in nombre_a_codigo)

    plan = []
    ciclo = ciclo_actual

    for _ in range(n_ciclos):
        cursos_ciclo = [
            c for c in cursos
            if c["ciclo"] == ciclo
            and c["codigo"] not in historial
            and all(pr in historial for pr in c["requisitos"])
        ]

        if len(cursos_ciclo) < max_cursos:
            cursos_alternativos = [
                c for c in cursos
                if c["codigo"] not in historial
                and all(pr in historial for pr in c["requisitos"])
                and c not in cursos_ciclo
            ]
            cursos_alternativos = ordenar_por_prioridad(cursos_alternativos, cursos, historial)
            cursos_ciclo.extend(cursos_alternativos[:max_cursos - len(cursos_ciclo)])

        seleccion = ordenar_por_prioridad(cursos_ciclo, cursos, historial)[:max_cursos]
        plan.append({
            "ciclo": ciclo,
            "cursos": [c["nombre"] for c in seleccion],
            "detalles": seleccion,
            "creditos": sum(c.get("creditos", 0) for c in seleccion)
        })

        historial.update(c["codigo"] for c in seleccion)
        ciclo = 2 if ciclo == 1 else 1

    return plan
