import pandas as pd
from .financials_engine import calculate_pl_contribution

def calculate_mpm(df_clasificado: pd.DataFrame, mpm_name: str, subtotal_base: str, ajuste: float, rationale: str) -> dict:
    """
    Registrar Nueva MPM (Medida de Rendimiento de la Gerencia)
    Ajuste y anclaje según la Fase 4 de NIIF 18.
    """
    val_base = 0.0
    if df_clasificado is not None and not df_clasificado.empty:
        df_calc = df_clasificado.copy()
        if 'PL_Neto' not in df_calc.columns:
            df_calc['PL_Neto'] = df_calc.apply(calculate_pl_contribution, axis=1)
            
        if "1. Resultado Operativo" in subtotal_base:
            val_base = float(df_calc[df_calc['Categoria_NIIF18'].str.startswith('1.')]['PL_Neto'].sum())
        else:
            val_base = float(df_calc['PL_Neto'].sum())
            
    efecto_fiscal = -(ajuste * TASA_IMPOSITIVA_DEFECTO)
    total_mpm = val_base + ajuste
    
    return {
        "Métrica": mpm_name,
        "Anclaje NIIF": subtotal_base,
        "Base NIIF ($)": val_base,
        "Ajuste ($)": ajuste,
        "Efecto Fiscal ($)": efecto_fiscal,
        "Total MPM ($)": total_mpm,
        "Justificación": rationale
    }


TASA_IMPOSITIVA_DEFECTO = 0.25


def conciliar_mpm(nombre: str, subtotal_base: str, valor_base: float, ajuste: float,
                  justificacion: str, tasa_impositiva: float = TASA_IMPOSITIVA_DEFECTO) -> dict:
    """
    Concilia una MPM con su subtotal NIIF 18 comparable. La norma exige nombre,
    anclaje, ajuste, efecto impositivo y justificación en una nota única.
    """
    if not str(nombre).strip():
        raise ValueError("La MPM requiere una denominación.")
    if not str(justificacion).strip():
        raise ValueError("La MPM requiere una justificación para los usuarios de los estados financieros.")
    return {
        "nombre": str(nombre).strip(),
        "subtotal_base": subtotal_base,
        "valor_base": float(valor_base),
        "ajuste": float(ajuste),
        "efecto_fiscal": -(float(ajuste) * tasa_impositiva),
        "total_mpm": float(valor_base) + float(ajuste),
        "justificacion": str(justificacion).strip(),
    }
