"""Compuerta pública de la sala ADPA: Riesgos y MTGE Gran Escala."""
from features.riesgos_mtge.domain.models import EntradaCalculoMTGE, ResultadoMTGE, AlcanceGeografico
from features.riesgos_mtge.services.mtge_calculator import calcular_mtge_actividad

def evaluar_gran_escala_mtge(entrada: EntradaCalculoMTGE) -> ResultadoMTGE:
    """Evalúa si un tratamiento detona obligaciones reforzadas de Gran Escala (DPO y EIPD obligatorios)."""
    return calcular_mtge_actividad(entrada)