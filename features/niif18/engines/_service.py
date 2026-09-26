"""
Compuerta _service.py para features/niif18/engines.
[¤vocabulario_precision_agentica]
"""
from .financials_engine import (
    calculate_pl_contribution,
    calculate_niif18_subtotals,
    estructurar_estado_resultados,
)
from .mpm_engine import calculate_mpm, conciliar_mpm
from .diagnostico_engine import diagnosticar_balance, calcular_indicadores
from .recomendaciones_engine import generar_recomendaciones
from .export_engine import generar_excel_estado_resultados, generar_informe_markdown, generar_informe_pdf

__all__ = [
    'calculate_pl_contribution',
    'calculate_niif18_subtotals',
    'estructurar_estado_resultados',
    'calculate_mpm',
    'conciliar_mpm',
    'diagnosticar_balance',
    'calcular_indicadores',
    'generar_recomendaciones',
    'generar_excel_estado_resultados',
    'generar_informe_markdown',
    'generar_informe_pdf',
]
