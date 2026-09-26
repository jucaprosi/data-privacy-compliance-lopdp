import pandas as pd
from features.niif18.domain.models import CategoriaNIIF18

def auto_classify_niif18_series(df: pd.DataFrame) -> list[str]:
    """Clasifica automáticamente las cuentas según las NIIF 18."""
    categories = []
    for _, row in df.iterrows():
        cta, desc = str(row['Cuenta']).strip(), str(row['Descripcion']).strip().lower()
        if cta.startswith(('1', '2', '3')) or any(w in desc for w in ['activo', 'pasivo', 'patrimonio', 'capital', 'bancos', 'caja', 'proveedor', 'cliente', 'inventario', 'edificio', 'terreno', 'obligacion', 'cuenta por']):
            if not any(w in desc for w in ['ingreso', 'gasto', 'costo']):
                categories.append(CategoriaNIIF18.BALANCE.value)
                continue
        if any(w in desc for w in ['dividendo', 'inversion', 'inversión', 'asociada', 'negocio conjunto', 'participacion']):
            categories.append(CategoriaNIIF18.INVERSION.value)
        elif cta.startswith(('54', '6')) or any(w in desc for w in ['interes', 'interés', 'financier', 'bancari', 'prestamo', 'préstamo', 'deuda', 'arrendamiento financiero']):
            categories.append(CategoriaNIIF18.FINANCIACION.value)
        elif cta.startswith(('55', '59')) or any(w in desc for w in ['impuesto a la renta', 'impuesto a las ganancias', 'gasto por impuesto', 'impuesto diferido']):
            categories.append(CategoriaNIIF18.IMPUESTOS.value)
        elif any(w in desc for w in ['discontinuad', 'interrumpid', 'abandonad']):
            categories.append(CategoriaNIIF18.DISCONTINUADAS.value)
        else:
            categories.append(CategoriaNIIF18.OPERACION.value)
    return categories
