# ¤rat ¤hallazgos
"""Reglas de validación de una ficha RAT (RAT-05). Funciones puras, sin base de datos.

Contrato: governance/especificaciones/RAT-05.md §3. Viven en código hasta que REG-01 las lleve al
paquete normativo. Correspondencia con la ficha: `marcar_eipd` es `requiere_eipd`, `base_legitimacion`
es `base_legal`, `menores` es la categoría de titulares MENORES_EDAD, `perfilamiento` es
`decisiones_automatizadas` y `biometria` es una categoría de datos que nombra la biometría.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from app_core.errors import CodigoErrorNegocio
from features.rat.domain.models import ActividadRAT, CategoriaTitular

RAT_NO_ENCONTRADO = CodigoErrorNegocio(
    codigo="RAT_NO_ENCONTRADO",
    status_code=404,
    mensaje_defecto="La ficha de tratamiento no existe en la organización.",
)

SEVERIDAD_ALTA = "alta"
SEVERIDAD_MEDIA = "media"

# Control P1-P80 «Registro de Actividades de Tratamiento (RAT)» y su dimensión: permite convertir el hallazgo en tarea.
CONTROL_RAT = "P10"
DIMENSION_RAT = "D02"


@dataclass(frozen=True)
class ResultadoRegla:
    codigo: str
    cumple: bool
    mensaje: str
    severidad: str


def _vacio(valor: object) -> bool:
    return valor is None or (isinstance(valor, str) and not valor.strip())


def _sin_tildes(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def _trata_biometria(ficha: ActividadRAT) -> bool:
    return any("biometr" in _sin_tildes(c) for c in ficha.categorias_datos)


def origen_ref_regla(tratamiento_id: str, codigo: str) -> str:
    """Clave estable del hallazgo de una regla (R2): `<tratamiento_id>:<codigo_regla>`."""
    return f"{tratamiento_id}:{codigo}"


def evaluar_reglas(ficha: ActividadRAT) -> list[ResultadoRegla]:
    """Las cuatro reglas R1, siempre en el mismo orden."""
    exige_eipd = (
        CategoriaTitular.MENORES_EDAD in ficha.categorias_titulares
        or ficha.decisiones_automatizadas
        or _trata_biometria(ficha)
    )
    return [
        ResultadoRegla(
            "RAT-SENS",
            not ficha.datos_sensibles or not _vacio(ficha.condicion_habilitante),
            "Los datos sensibles exigen una condición habilitante del artículo 26 de la LOPDP.",
            SEVERIDAD_ALTA,
        ),
        ResultadoRegla(
            "RAT-EIPD",
            not exige_eipd or ficha.requiere_eipd,
            "Menores, perfilamiento o biometría exigen marcar la evaluación de impacto.",
            SEVERIDAD_ALTA,
        ),
        ResultadoRegla(
            "RAT-BASE",
            not _vacio(ficha.base_legal),
            "Indique la base de legitimación del tratamiento.",
            SEVERIDAD_MEDIA,
        ),
        ResultadoRegla(
            "RAT-PLAZO",
            not _vacio(ficha.plazo_conservacion),
            "Indique el plazo de conservación de los datos.",
            SEVERIDAD_MEDIA,
        ),
    ]
