"""
Diagnóstico de la balanza de comprobación frente a la NIIF 18.
[¤niif18-diagnostico]
"""
import pandas as pd

from features.niif18.engines.financials_engine import (
    calculate_niif18_subtotals,
    calculate_pl_contribution,
    es_cuenta_ingreso,
)

TOLERANCIA_CUADRE = 0.01
_PENALIZACION = {"ALTA": 20, "MEDIA": 8, "BAJA": 2, "INFO": 0}
_NOMBRE_CATEGORIA = {
    '0.': 'Balance general', '1.': 'Operación', '2.': 'Inversión',
    '3.': 'Financiación', '4.': 'Impuestos a las ganancias', '5.': 'Operaciones discontinuadas',
}
_TERMINOS_PL = ('ingreso', 'gasto', 'costo')
_TERMINOS_FINANCIEROS = ('interes', 'interés', 'prestamo', 'préstamo', 'financier', 'bancari')
_TERMINOS_INVERSION = ('dividendo', 'asociada', 'negocio conjunto')
_TERMINOS_DYA = ('depreciaci', 'amortizaci')


def _hallazgo(codigo: str, severidad: str, titulo: str, detalle: str, referencia: str, cuentas: list[str] | None = None) -> dict:
    return {
        "codigo": codigo, "severidad": severidad, "titulo": titulo,
        "detalle": detalle, "referencia": referencia, "cuentas": cuentas or [],
    }


def _prepara(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d['_cat'] = d['Categoria_NIIF18'].astype(str)
    d['_desc'] = d['Descripcion'].astype(str).str.lower()
    d['PL_Neto'] = d.apply(calculate_pl_contribution, axis=1)
    return d


def calcular_indicadores(df: pd.DataFrame) -> dict:
    """Indicadores de rendimiento derivados de la estructura NIIF 18."""
    d = _prepara(df)
    sub = calculate_niif18_subtotals(d)
    op = d[d['_cat'].str.startswith('1.')]
    ingresos_op = float(op[op['PL_Neto'] > 0]['PL_Neto'].sum())
    fin = float(d[d['_cat'].str.startswith('3.')]['PL_Neto'].sum())
    imp = float(d[d['_cat'].str.startswith('4.')]['PL_Neto'].sum())
    antes_imp = sub["sub_3_resultado_periodo"] - imp
    dya = float(-d[d['_desc'].apply(lambda t: any(k in t for k in _TERMINOS_DYA)) & (d['PL_Neto'] < 0)]['PL_Neto'].sum())

    def razon(num: float, den: float) -> float | None:
        return round(num / den, 4) if abs(den) > 1e-9 else None

    return {
        "ingresos_operativos": ingresos_op,
        "margen_operativo": razon(sub["sub_1_resultado_operativo"], ingresos_op),
        "margen_neto": razon(sub["sub_3_resultado_periodo"], ingresos_op),
        "tasa_efectiva_impuestos": razon(-imp, antes_imp),
        "cobertura_intereses": razon(sub["sub_2_antes_fin_impuestos"], -fin),
        "depreciacion_amortizacion": dya,
        "ebitda_referencial": sub["sub_1_resultado_operativo"] + dya,
    }


def diagnosticar_balance(df: pd.DataFrame) -> dict:
    """
    Audita la balanza clasificada: cuadre contable, cobertura del estado de
    resultados, coherencia de las categorías y preparación para MPM.
    """
    d = _prepara(df)
    hallazgos: list[dict] = []
    pl = d[~d['_cat'].str.startswith('0.')]
    balance = d[d['_cat'].str.startswith('0.')]

    diferencia = float(d['Saldo'].sum())
    if abs(diferencia) > TOLERANCIA_CUADRE:
        hallazgos.append(_hallazgo(
            "D01", "ALTA", "La balanza no cuadra",
            f"La suma algebraica de saldos es {diferencia:,.2f}; una balanza de comprobación debe sumar cero. "
            "Los subtotales calculados sobre datos descuadrados no son confiables.",
            "Integridad de la fuente de datos (Volumen 7)"))

    if pl.empty:
        hallazgos.append(_hallazgo(
            "D02", "ALTA", "Sin cuentas de resultados",
            "Ninguna cuenta fue clasificada en las categorías 1 a 5; no es posible construir el Estado de Resultados.",
            "Volumen 2: categorías del estado de resultados"))
    elif float(pl[pl['PL_Neto'] > 0]['PL_Neto'].sum()) <= 0:
        hallazgos.append(_hallazgo(
            "D03", "ALTA", "No se identifican ingresos",
            "Las cuentas de resultados no aportan ingresos; verifique la naturaleza de las cuentas de ventas y otros ingresos.",
            "Volumen 3: subtotales mandatorios"))

    perdidas = balance[balance['_desc'].apply(lambda t: any(k in t for k in _TERMINOS_PL))]
    if not perdidas.empty:
        hallazgos.append(_hallazgo(
            "D05", "ALTA", "Posibles cuentas de resultados excluidas",
            f"{len(perdidas)} cuenta(s) en la categoría 0 (Balance) parecen ser de ingresos, costos o gastos.",
            "Volumen 2: todo ingreso y gasto debe clasificarse en una categoría",
            perdidas['Cuenta'].astype(str).tolist()))

    op = pl[pl['_cat'].str.startswith('1.')]
    mal_op = op[op['_desc'].apply(lambda t: any(k in t for k in _TERMINOS_FINANCIEROS + _TERMINOS_INVERSION))]
    if not mal_op.empty:
        hallazgos.append(_hallazgo(
            "D04", "MEDIA", "Partidas operativas con rasgos de inversión o financiación",
            "La categoría Operación es residual; estas cuentas mencionan intereses, préstamos o dividendos y podrían pertenecer a otra categoría.",
            "Volumen 2: Operación es la categoría residual",
            mal_op['Cuenta'].astype(str).tolist()))

    duplicadas = d[d['Cuenta'].astype(str).duplicated(keep=False)]
    if not duplicadas.empty:
        hallazgos.append(_hallazgo(
            "D12", "MEDIA", "Códigos de cuenta duplicados",
            "Hay códigos repetidos en la balanza; pueden duplicar saldos en los subtotales.",
            "Integridad de la fuente de datos",
            sorted(set(duplicadas['Cuenta'].astype(str)))))

    invertidas = pl[pl.apply(lambda r: (es_cuenta_ingreso(r['Cuenta'], r['Descripcion'], r['Saldo']) and r['Saldo'] > 0)
                             or (not es_cuenta_ingreso(r['Cuenta'], r['Descripcion'], r['Saldo']) and r['Saldo'] < 0), axis=1)]
    if not invertidas.empty:
        hallazgos.append(_hallazgo(
            "D14", "MEDIA", "Saldos con signo contrario a su naturaleza",
            "Ingresos con saldo deudor o gastos con saldo acreedor (devoluciones, reversiones o errores de signo). "
            "El motor los trata por valor absoluto: confirme que sea lo correcto.",
            "Volumen 7: guía de reclasificación y mapeo",
            invertidas['Cuenta'].astype(str).tolist()))

    sub = calculate_niif18_subtotals(d)
    if not pl.empty and sub["sub_3_resultado_periodo"] > 0 and not d['_cat'].str.startswith('4.').any():
        hallazgos.append(_hallazgo(
            "D08", "MEDIA", "Resultado positivo sin impuestos a las ganancias",
            "Hay utilidad del periodo pero ninguna cuenta en la categoría de impuestos.",
            "Volumen 2: categoría 4, impuestos a las ganancias"))

    if not pl.empty and sub["sub_1_resultado_operativo"] < 0:
        hallazgos.append(_hallazgo(
            "D09", "MEDIA", "Resultado operativo negativo",
            f"El resultado operativo es {sub['sub_1_resultado_operativo']:,.2f}. Revise la clasificación de costos antes de presentar.",
            "Volumen 3: resultado operativo"))

    for prefijo, codigo, nombre in (('2.', 'D07', 'inversión'), ('3.', 'D06', 'financiación')):
        if not pl.empty and not d['_cat'].str.startswith(prefijo).any():
            hallazgos.append(_hallazgo(
                codigo, "INFO", f"Categoría de {nombre} sin cuentas",
                f"Ninguna cuenta se clasificó como {nombre}. Confirme que la entidad realmente no tiene estas partidas.",
                "Volumen 2: categorías del estado de resultados"))

    ceros = pl[pl['Saldo'].abs() < TOLERANCIA_CUADRE]
    if not ceros.empty:
        hallazgos.append(_hallazgo(
            "D10", "BAJA", "Cuentas de resultados con saldo cero",
            "Cuentas sin movimiento que pueden depurarse del mapeo.", "Volumen 7: catálogo de cuentas",
            ceros['Cuenta'].astype(str).tolist()))

    if not pl.empty and not d['_desc'].apply(lambda t: any(k in t for k in _TERMINOS_DYA)).any():
        hallazgos.append(_hallazgo(
            "D13", "INFO", "Depreciación y amortización no identificables",
            "Para conciliar un EBITDA como MPM se necesita aislar la depreciación y amortización dentro de los gastos operativos.",
            "Volumen 4: medidas de rendimiento definidas por la gerencia"))

    puntaje = max(0, 100 - sum(_PENALIZACION[h["severidad"]] for h in hallazgos))
    hay_alta = any(h["severidad"] == "ALTA" for h in hallazgos)
    if hay_alta:
        estado = "REQUIERE_CORRECCION"
    elif any(h["severidad"] in ("MEDIA", "BAJA") for h in hallazgos):
        estado = "CON_OBSERVACIONES"
    else:
        estado = "LISTO_PARA_PRESENTAR"

    por_categoria = [
        {"categoria": nombre, "cuentas": int(d['_cat'].str.startswith(pref).sum()),
         "aporte": float(d[d['_cat'].str.startswith(pref)]['PL_Neto'].sum())}
        for pref, nombre in _NOMBRE_CATEGORIA.items()
    ]
    orden = {"ALTA": 0, "MEDIA": 1, "BAJA": 2, "INFO": 3}
    return {
        "estado": estado,
        "puntaje": puntaje,
        "cuadre": {"diferencia": diferencia, "cuadra": abs(diferencia) <= TOLERANCIA_CUADRE},
        "total_cuentas": int(len(d)),
        "por_categoria": por_categoria,
        "hallazgos": sorted(hallazgos, key=lambda h: (orden[h["severidad"]], h["codigo"])),
    }
