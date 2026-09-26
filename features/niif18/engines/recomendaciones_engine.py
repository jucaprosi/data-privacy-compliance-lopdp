"""
Recomendaciones para implementar la NIIF 18 a partir del diagnóstico.
[¤niif18-recomendaciones]
"""

# Acción correctiva por código de hallazgo.
_ACCION_POR_HALLAZGO = {
    "D01": ("Corregir", "Conciliar la balanza con el ERP hasta que sume cero antes de clasificar; investigar asientos descuadrados y cuentas omitidas en la exportación."),
    "D02": ("Corregir", "Revisar el mapeo de columnas y la clasificación: la exportación debe incluir las cuentas de ingresos, costos y gastos."),
    "D03": ("Corregir", "Verificar la naturaleza de las cuentas de ingresos y su signo en la exportación del ERP."),
    "D05": ("Corregir", "Reclasificar a las categorías 1 a 5 las cuentas de resultados que quedaron en Balance."),
    "D04": ("Revisar", "Aplicar juicio profesional: mover a Inversión o Financiación las partidas que corresponda; Operación solo debe conservar lo residual."),
    "D12": ("Revisar", "Depurar o consolidar los códigos duplicados para no duplicar saldos."),
    "D14": ("Revisar", "Confirmar devoluciones, reversiones o errores de signo con contabilidad y documentar la decisión."),
    "D08": ("Revisar", "Confirmar el registro del gasto por impuesto a las ganancias, corriente y diferido."),
    "D09": ("Revisar", "Analizar por qué el resultado operativo es negativo y validar la ubicación de costos y gastos."),
    "D06": ("Confirmar", "Documentar que no existen partidas de financiación en el periodo."),
    "D07": ("Confirmar", "Documentar que no existen partidas de inversión en el periodo."),
    "D10": ("Depurar", "Retirar del mapeo las cuentas sin saldo para simplificar el catálogo."),
    "D13": ("Preparar", "Crear cuentas o etiquetas para aislar depreciación y amortización si la gerencia comunica EBITDA."),
}
_PRIORIDAD_POR_SEVERIDAD = {"ALTA": "P1", "MEDIA": "P2", "BAJA": "P3", "INFO": "P3"}

# Hoja de ruta estándar de implementación.
_HOJA_DE_RUTA = [
    ("Fase 1 · Brecha y gobierno", "Comparar la presentación actual (NIC 1) con la NIIF 18, designar responsables y definir el calendario de adopción.", "Volumen 1: marco general y alcance"),
    ("Fase 2 · Catálogo y mapeo", "Asignar cada cuenta de resultados a una de las cinco categorías y documentar el criterio de las partidas de juicio.", "Volumen 7: guía de reclasificación y mapeo"),
    ("Fase 3 · Estado de resultados", "Presentar Resultado operativo, Resultado antes de financiación e impuestos y Resultado del periodo como subtotales obligatorios.", "Volumen 3: subtotales mandatorios"),
    ("Fase 4 · Agregación y desagregación", "Revisar el nivel de detalle de las partidas y la información por naturaleza o función del gasto.", "Volumen 5: agregación y desagregación"),
    ("Fase 5 · MPM", "Inventariar métricas comunicadas al mercado (EBITDA, utilidad ajustada), conciliarlas con el subtotal NIIF 18 comparable, con efecto impositivo y justificación, en una nota única.", "Volumen 4: medidas definidas por la gerencia"),
    ("Fase 6 · Transición y comparativos", "Reexpresar el periodo comparativo con la nueva estructura y preparar la información de transición.", "Volumen 6: transición y comparativos"),
]


def generar_recomendaciones(diagnostico: dict, indicadores: dict, mpm_registrados: int = 0) -> dict:
    """Devuelve acciones priorizadas (P1..P3) y la hoja de ruta de implementación."""
    acciones = []
    for h in diagnostico["hallazgos"]:
        tipo, accion = _ACCION_POR_HALLAZGO.get(h["codigo"], ("Revisar", h["detalle"]))
        acciones.append({
            "prioridad": _PRIORIDAD_POR_SEVERIDAD[h["severidad"]],
            "tipo": tipo, "accion": accion,
            "fundamento": h["referencia"], "hallazgo": h["codigo"], "cuentas": h["cuentas"],
        })

    margen = indicadores.get("margen_operativo")
    if margen is not None and margen < 0.05:
        acciones.append({
            "prioridad": "P2", "tipo": "Analizar",
            "accion": f"El margen operativo es {margen:.1%}; documentar en la nota de desempeño los factores que lo explican.",
            "fundamento": "Volumen 3: resultado operativo", "hallazgo": None, "cuentas": [],
        })
    cobertura = indicadores.get("cobertura_intereses")
    if cobertura is not None and cobertura < 2:
        acciones.append({
            "prioridad": "P2", "tipo": "Analizar",
            "accion": f"La cobertura de intereses es {cobertura:.1f}x; considerar la revelación del efecto de la financiación en el resultado.",
            "fundamento": "Volumen 2: categoría de financiación", "hallazgo": None, "cuentas": [],
        })
    if mpm_registrados == 0:
        acciones.append({
            "prioridad": "P3", "tipo": "Preparar",
            "accion": "No hay MPM registradas: si la gerencia comunica métricas ajustadas fuera de los estados financieros, concíliarlas en el módulo MPM.",
            "fundamento": "Volumen 4: medidas definidas por la gerencia", "hallazgo": None, "cuentas": [],
        })

    acciones.sort(key=lambda a: a["prioridad"])
    return {
        "acciones": acciones,
        "hoja_de_ruta": [{"fase": f, "descripcion": d, "referencia": r} for f, d, r in _HOJA_DE_RUTA],
    }
