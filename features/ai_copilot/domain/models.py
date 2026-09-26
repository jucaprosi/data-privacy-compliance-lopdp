from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class AnalisisDiagnosticoRequest(BaseModel):
    id_diagnostico: str
    normativa: str
    brechas_identificadas: List[str]
    scoring_global: float

class TareaMitigacionIA(BaseModel):
    descripcion: str
    impacto_riesgo: str

class PlanMitigacionResponse(BaseModel):
    analisis_general: str
    tareas_propuestas: List[TareaMitigacionIA]
