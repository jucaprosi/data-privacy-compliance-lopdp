"""
Compuerta ADPA pública para NIIF 18.
[¤niif18-backend] Integra parser, clasificador, P&L, diagnóstico, recomendaciones, MPM y reportes.
"""
import io
from typing import Any, Dict, List

import pandas as pd

from features.niif18.engines.parser_engine import (
    clean_numeric_series,
    infer_columns_by_mathematical_weights,
    read_excel_smart_header,
)
from features.niif18.engines.classifier_engine import auto_classify_niif18_series
from features.niif18.engines._service import (
    calcular_indicadores,
    calculate_niif18_subtotals,
    calculate_pl_contribution,
    conciliar_mpm,
    diagnosticar_balance,
    estructurar_estado_resultados,
    generar_excel_estado_resultados,
    generar_informe_markdown,
    generar_informe_pdf,
    generar_recomendaciones,
)

# El frontend envía claves en minúscula; los motores trabajan con estas columnas.
_ALIAS_COLUMNAS = {
    "Cuenta": ("cuenta", "Cuenta"),
    "Descripcion": ("descripcion", "Descripcion"),
    "Saldo": ("saldo_original", "saldo", "Saldo"),
    "Categoria_NIIF18": ("categoria", "Categoria_NIIF18"),
}


def _a_dataframe(cuentas: List[Dict[str, Any]]) -> pd.DataFrame:
    """Normaliza las cuentas recibidas (formato API o formato interno) al formato de los motores."""
    filas = []
    for c in cuentas:
        fila = {}
        for destino, alias in _ALIAS_COLUMNAS.items():
            fila[destino] = next((c[a] for a in alias if a in c and c[a] is not None), None)
        if fila["Cuenta"] is None or fila["Saldo"] is None or fila["Categoria_NIIF18"] is None:
            raise ValueError("Cada cuenta requiere cuenta, saldo y categoría.")
        fila["Descripcion"] = fila["Descripcion"] or ""
        filas.append(fila)
    if not filas:
        raise ValueError("No hay cuentas para procesar.")
    df = pd.DataFrame(filas)
    df["Saldo"] = pd.to_numeric(df["Saldo"])
    return df


def _cuentas_api(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Cuentas en el formato que consume el frontend."""
    return [
        {
            "cuenta": str(r["Cuenta"]),
            "descripcion": str(r["Descripcion"]),
            "saldo_original": float(r["Saldo"]),
            "categoria": str(r["Categoria_NIIF18"]),
            "pl_neto": float(r["PL_Neto"]),
        }
        for _, r in df.iterrows()
    ]


def _subtotales_api(df: pd.DataFrame) -> Dict[str, float]:
    s = calculate_niif18_subtotals(df)
    return {
        "1_resultado_operativo": s["sub_1_resultado_operativo"],
        "2_resultado_antes_fin_imp": s["sub_2_antes_fin_impuestos"],
        "3_resultado_periodo": s["sub_3_resultado_periodo"],
    }


def _analisis(df: pd.DataFrame) -> Dict[str, Any]:
    """Diagnóstico, indicadores y recomendaciones de una balanza ya clasificada."""
    diagnostico = diagnosticar_balance(df)
    indicadores = calcular_indicadores(df)
    return {"diagnostico": diagnostico, "indicadores": indicadores}


def procesar_balance_prueba(file_bytes: bytes, filename: str) -> dict:
    """Ingesta inicial: parseo, inferencia heurística, pre-clasificación y diagnóstico."""
    file_io = io.BytesIO(file_bytes)
    if filename.lower().endswith('.csv'):
        df = pd.read_csv(file_io)
    else:
        df = read_excel_smart_header(file_io, sheet_name=0)

    col_cta, col_desc, col_saldo, confid = infer_columns_by_mathematical_weights(df)

    df = pd.DataFrame({
        'Cuenta': df[col_cta].astype(str),
        'Descripcion': df[col_desc].astype(str),
        'Saldo': clean_numeric_series(df[col_saldo]),
    })
    df = df[df['Cuenta'].str.strip().str.lower() != 'nan'].reset_index(drop=True)

    df['Categoria_NIIF18'] = auto_classify_niif18_series(df)
    df['PL_Neto'] = df.apply(calculate_pl_contribution, axis=1)

    return {
        "inferencia_columnas": {
            "cuenta": col_cta,
            "descripcion": col_desc,
            "saldo": col_saldo,
            "confianza_porcentaje": confid,
        },
        "subtotales": _subtotales_api(df),
        "cuentas": _cuentas_api(df),
        **_analisis(df),
    }


def recalcular_estado_niif18(cuentas_dict_list: List[Dict[str, Any]]) -> dict:
    """Recalcula aportes, subtotales y diagnóstico tras la reclasificación hecha en el frontend."""
    df = _a_dataframe(cuentas_dict_list)
    df['PL_Neto'] = df.apply(calculate_pl_contribution, axis=1)
    return {
        "subtotales": _subtotales_api(df),
        "cuentas": _cuentas_api(df),
        **_analisis(df),
    }


def validar_mpm(nombre: str, subtotal_base: str, valor_base: float, ajuste: float, justificacion: str) -> dict:
    """Registra y valida una MPM calculando su efecto impositivo."""
    return conciliar_mpm(nombre, subtotal_base, valor_base, ajuste, justificacion)


def generar_informe_niif18(cuentas: List[Dict[str, Any]], mpm: List[Dict[str, Any]] | None = None) -> dict:
    """Diagnóstico completo: estado de resultados, indicadores, hallazgos y recomendaciones."""
    df = _a_dataframe(cuentas)
    df['PL_Neto'] = df.apply(calculate_pl_contribution, axis=1)
    analisis = _analisis(df)
    return {
        "subtotales": _subtotales_api(df),
        "estado_resultados": estructurar_estado_resultados(df),
        **analisis,
        "recomendaciones": generar_recomendaciones(
            analisis["diagnostico"], analisis["indicadores"], len(mpm or [])),
        "mpm": mpm or [],
    }


def exportar_excel_niif18(cuentas_dict_list: List[Dict[str, Any]], mpm: List[Dict[str, Any]] | None = None) -> bytes:
    """Paquete Excel de cierre: estado de resultados, trazabilidad, MPM, diagnóstico y hoja de ruta."""
    informe = generar_informe_niif18(cuentas_dict_list, mpm)
    df = _a_dataframe(cuentas_dict_list)
    df['PL_Neto'] = df.apply(calculate_pl_contribution, axis=1)
    return generar_excel_estado_resultados(df, mpm, informe["diagnostico"], informe["recomendaciones"])


def exportar_informe_markdown(cuentas: List[Dict[str, Any]], mpm: List[Dict[str, Any]] | None = None,
                              empresa: str = "") -> str:
    """Informe de implementación NIIF 18 en Markdown."""
    informe = generar_informe_niif18(cuentas, mpm)
    return generar_informe_markdown(
        informe["estado_resultados"], informe["diagnostico"], informe["recomendaciones"],
        informe["indicadores"], mpm, empresa)


def exportar_informe_pdf(cuentas: List[Dict[str, Any]], mpm: List[Dict[str, Any]] | None = None,
                         empresa: str = "") -> bytes:
    """Informe de implementación NIIF 18 en PDF."""
    informe = generar_informe_niif18(cuentas, mpm)
    return generar_informe_pdf(
        informe["estado_resultados"], informe["diagnostico"], informe["recomendaciones"],
        informe["indicadores"], mpm, empresa)
