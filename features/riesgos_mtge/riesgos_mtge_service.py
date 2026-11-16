"""Compuerta pública de la sala ADPA: Riesgos y MTGE Gran Escala."""
from features.riesgos_mtge.domain.models import (
    AlcanceGeografico,
    CategoriasDatos,
    EntradaCalculoMTGE,
    Frecuencia,
    Permanencia,
    ResultadoMTGE,
    SupuestoDirecto,
)
from features.riesgos_mtge.services.mtge_calculator import UMBRAL_GRAN_ESCALA_PUNTOS, calcular_mtge_actividad


def evaluar_gran_escala_mtge(entrada: EntradaCalculoMTGE) -> ResultadoMTGE:
    """Califica un tratamiento como de gran escala (Res. SPDP-SPD-2026-0005-R, arts. 8-10 y 14)."""
    return calcular_mtge_actividad(entrada)


__all__ = [
    "AlcanceGeografico",
    "CategoriasDatos",
    "EntradaCalculoMTGE",
    "Frecuencia",
    "Permanencia",
    "ResultadoMTGE",
    "SupuestoDirecto",
    "UMBRAL_GRAN_ESCALA_PUNTOS",
    "evaluar_gran_escala_mtge",
]

# === MTGE-02 ===
from features.riesgos_mtge.services.obligaciones_engine import (
    AuditoriaGranEscalaCreate,
    ConfiguracionVigenciaCreate,
    EstadoObligacion,
    EstadoObligacionesResponse,
    InformeAnualCreate,
    PoliticaPrivacidadCreate,
    ResumenObligacion,
    calcular_estado_obligaciones,
    eliminar_auditoria,
    eliminar_informe_anual,
    listar_auditorias,
    listar_informes_anuales,
    listar_politicas_privacidad,
    obtener_fecha_vigencia,
    organizacion_tiene_gran_escala,
    registrar_auditoria,
    registrar_fecha_vigencia,
    registrar_informe_anual,
    registrar_politica_privacidad,
)

__all__ += [
    "AuditoriaGranEscalaCreate",
    "ConfiguracionVigenciaCreate",
    "EstadoObligacion",
    "EstadoObligacionesResponse",
    "InformeAnualCreate",
    "PoliticaPrivacidadCreate",
    "ResumenObligacion",
    "calcular_estado_obligaciones",
    "eliminar_auditoria",
    "eliminar_informe_anual",
    "listar_auditorias",
    "listar_informes_anuales",
    "listar_politicas_privacidad",
    "obtener_fecha_vigencia",
    "organizacion_tiene_gran_escala",
    "registrar_auditoria",
    "registrar_fecha_vigencia",
    "registrar_informe_anual",
    "registrar_politica_privacidad",
]
# === fin MTGE-02 ===


# === ADPA-05 ===
# ¤adpa Los códigos de error de esta sala viven en features/riesgos_mtge/domain/errores.py y se registran al importarlo.
from features.riesgos_mtge.domain import errores as _errores_sala  # noqa: E402,F401
# === fin ADPA-05 ===


# === MTGE-03 ===
# ¤riesgos-eipd EIPD guiada de ocho pasos.
from features.riesgos_mtge.domain.eipd import (  # noqa: E402
    AMENAZAS, FASES_CICLO_VIDA, CierreEipd, CrearEipd, Eipd, InformeEipd,
)
from features.riesgos_mtge.services.eipd_engine import (  # noqa: E402
    CustodiaNoDisponible, HallazgosHojaDeRuta, PuertoCustodia, PuertoHallazgos, cerrar_eipd, crear_eipd, guardar_paso, informe_eipd, listar_eipd,
    obtener_eipd,
)

__all__ += [
    "AMENAZAS", "FASES_CICLO_VIDA", "CierreEipd", "CrearEipd", "Eipd", "InformeEipd", "HallazgosHojaDeRuta", "CustodiaNoDisponible", "PuertoCustodia",
    "PuertoHallazgos", "cerrar_eipd", "crear_eipd", "guardar_paso", "informe_eipd", "listar_eipd", "obtener_eipd",
]
# === fin MTGE-03 ===
