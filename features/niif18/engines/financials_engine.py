"""
Motor de resultados NIIF 18: naturaleza de cuentas, aporte al P&L, subtotales
mandatorios y estructura del Estado de Resultados.
[¤niif18-resultados]
"""
import pandas as pd

# Términos que delatan una partida de gasto/costo; prevalecen sobre los de ingreso
# ("Gasto por impuesto a las ganancias", "Costo de ventas", "Pérdida en venta").
_TERMINOS_GASTO = (
    'costo', 'gasto', 'impuesto', 'depreciaci', 'amortizaci', 'comisi',
    'provisi', 'perdida', 'pérdida', 'deterioro',
)
_TERMINOS_INGRESO = ('ingreso', 'venta', 'honorario', 'ganancia', 'rendimiento', 'dividendo', 'utilidad')


def es_cuenta_ingreso(cuenta: str, descripcion: str, saldo: float = 0.0) -> bool:
    """Determina si la cuenta de resultados es de naturaleza ingreso (True) o gasto (False)."""
    cta = str(cuenta).strip()
    desc = str(descripcion).strip().lower()
    if cta.startswith('4'):
        return True
    if any(t in desc for t in _TERMINOS_GASTO):
        return False
    if any(t in desc for t in _TERMINOS_INGRESO):
        return True
    if 'interes' in desc or 'interés' in desc:
        return saldo < 0
    if cta[:1] in ('5', '6', '7', '8', '9'):
        return False
    return saldo < 0


def calculate_pl_contribution(row: pd.Series) -> float:
    """Aporte al resultado del periodo: positivo para ingresos, negativo para gastos."""
    cat = str(row.get('Categoria_NIIF18', ''))
    if cat.startswith('0.'):
        return 0.0
    saldo = float(row.get('Saldo', 0.0))
    ingreso = es_cuenta_ingreso(row.get('Cuenta', ''), row.get('Descripcion', ''), saldo)
    return abs(saldo) if ingreso else -abs(saldo)


def _con_aporte(df: pd.DataFrame) -> pd.DataFrame:
    df_c = df.copy()
    if 'PL_Neto' not in df_c.columns:
        df_c['PL_Neto'] = df_c.apply(calculate_pl_contribution, axis=1)
    return df_c


def _suma_categoria(df_c: pd.DataFrame, prefijo: str) -> float:
    return float(df_c[df_c['Categoria_NIIF18'].astype(str).str.startswith(prefijo)]['PL_Neto'].sum())


def calculate_niif18_subtotals(df: pd.DataFrame) -> dict:
    """Calcula los tres subtotales mandatorios de la NIIF 18."""
    df_c = _con_aporte(df)
    v_op = _suma_categoria(df_c, '1.')
    v_inv = _suma_categoria(df_c, '2.')
    v_fin = _suma_categoria(df_c, '3.')
    v_imp = _suma_categoria(df_c, '4.')
    v_disc = _suma_categoria(df_c, '5.')
    sub_2 = v_op + v_inv
    return {
        "sub_1_resultado_operativo": v_op,
        "sub_2_antes_fin_impuestos": sub_2,
        "sub_3_resultado_periodo": sub_2 + v_fin + v_imp + v_disc,
    }


def estructurar_estado_resultados(df: pd.DataFrame) -> list[dict]:
    """
    Estado de Resultados NIIF 18 en filas {concepto, monto, tipo}, donde tipo es
    'categoria', 'cuenta' o 'subtotal', en el orden de presentación de la norma.
    """
    df_c = _con_aporte(df)
    df_c['_cat'] = df_c['Categoria_NIIF18'].astype(str)
    filas: list[dict] = []

    def cuentas(prefijo: str, ingresos: bool | None = None) -> pd.DataFrame:
        sel = df_c[df_c['_cat'].str.startswith(prefijo)]
        if ingresos is True:
            return sel[sel['PL_Neto'] >= 0]
        if ingresos is False:
            return sel[sel['PL_Neto'] < 0]
        return sel

    def bloque(titulo: str, sel: pd.DataFrame) -> float:
        total = float(sel['PL_Neto'].sum())
        filas.append({"concepto": titulo, "monto": total, "tipo": "categoria"})
        for _, r in sel.iterrows():
            filas.append({"concepto": f"  {r['Cuenta']} · {r['Descripcion']}", "monto": float(r['PL_Neto']), "tipo": "cuenta"})
        return total

    ing = bloque("Ingresos de actividades operativas", cuentas('1.', True))
    gas = bloque("Costos y gastos operativos", cuentas('1.', False))
    sub1 = ing + gas
    filas.append({"concepto": "RESULTADO OPERATIVO", "monto": sub1, "tipo": "subtotal"})
    inv = bloque("Categoría de inversión", cuentas('2.'))
    sub2 = sub1 + inv
    filas.append({"concepto": "RESULTADO ANTES DE FINANCIACIÓN E IMPUESTOS A LAS GANANCIAS", "monto": sub2, "tipo": "subtotal"})
    fin = bloque("Categoría de financiación", cuentas('3.'))
    imp = bloque("Impuestos a las ganancias", cuentas('4.'))
    dis = bloque("Operaciones discontinuadas", cuentas('5.'))
    filas.append({"concepto": "RESULTADO DEL PERIODO", "monto": sub2 + fin + imp + dis, "tipo": "subtotal"})
    return filas
