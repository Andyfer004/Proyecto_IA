def contar_dependencias(curso_nombre, cursos):
    count = 0
    for curso in cursos:
        if curso_nombre in curso["prerequisitos"]:
            count += 1
    return count

def ordenar_por_importancia(candidatos, cursos):
    importancia = {
        c: contar_dependencias(c, cursos) for c in candidatos
    }
    return sorted(candidatos, key=lambda x: importancia[x], reverse=True)

def filtrar_por_semestre(cursos, semestre):
    return [c for c in cursos if semestre in c["semestre"]]

def filtrar_aprobados(cursos, aprobados):
    return [c for c in cursos if c["nombre"] not in aprobados]