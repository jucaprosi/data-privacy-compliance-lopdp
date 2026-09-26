from enum import Enum
from pydantic import BaseModel

class CategoriaNIIF18(str, Enum):
    BALANCE = "0. Balance General (No P&L / Excluir)"
    OPERACION = "1. Operación (Ingresos / Gastos Operativos)"
    INVERSION = "2. Inversión (Ingresos / Gastos por Inversiones)"
    FINANCIACION = "3. Financiación (Costos / Pasivos Financieros)"
    IMPUESTOS = "4. Impuestos a las Ganancias"
    DISCONTINUADAS = "5. Operaciones Discontinuadas"

class CuentaContableDTO(BaseModel):
    cuenta: str
    descripcion: str
    saldo: float
    categoria_niif18: str | None = None
