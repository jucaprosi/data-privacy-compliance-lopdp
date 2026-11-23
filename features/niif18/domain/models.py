# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
from enum import Enum

class CategoriaNIIF18(str, Enum):
    BALANCE = "0. Balance General (No P&L / Excluir)"
    OPERACION = "1. Operación (Ingresos / Gastos Operativos)"
    INVERSION = "2. Inversión (Ingresos / Gastos por Inversiones)"
    FINANCIACION = "3. Financiación (Costos / Pasivos Financieros)"
    IMPUESTOS = "4. Impuestos a las Ganancias"
    DISCONTINUADAS = "5. Operaciones Discontinuadas"
