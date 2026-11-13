"""Compuerta pública de la sala ADPA: Evidencias."""
from __future__ import annotations

from typing import Optional

from features.evidencias.domain.models import (
    CONTROL_ID_MAX,
    CONTROL_ID_MIN,
    NORMATIVA_POR_DEFECTO,
    TIPO_MIME_POR_DEFECTO,
    ControlFueraDeRango,
    EvidenciaError,
    EvidenciaNoEncontrada,
    EvidenciaRegistro,
    HashInvalido,
    NivelCalidadEvidencia,
    es_sha256_valido,
    normalizar_sha256,
)
from features.evidencias.services.evidencias_engine import (
    CodigoDuplicado,
    actualizar_vinculos,
    buscar_por_hash,
    calcular_hash_sha256,
    obtener_evidencia,
    obtener_evidencias_tenant,
    registrar_evidencia,
    registrar_nueva_evidencia,
    reiniciar_repositorio,
)

__all__ = [
    "CONTROL_ID_MAX",
    "CONTROL_ID_MIN",
    "NORMATIVA_POR_DEFECTO",
    "TIPO_MIME_POR_DEFECTO",
    "CodigoDuplicado",
    "ControlFueraDeRango",
    "EvidenciaError",
    "EvidenciaNoEncontrada",
    "EvidenciaRegistro",
    "HashInvalido",
    "NivelCalidadEvidencia",
    "calcular_hash_sha256",
    "es_sha256_valido",
    "normalizar_sha256",
    "registrar_evidencia_documental",
    "registrar_evidencia_deduplicada",
    "listar_evidencias_tenant",
    "obtener_evidencia_tenant",
    "vincular_controles",
    "verificar_hash",
    "reiniciar_repositorio_evidencias",
]


def registrar_evidencia_documental(
    evidencia: EvidenciaRegistro, contenido_bytes: Optional[bytes] = None
) -> EvidenciaRegistro:
    """Registra y asegura la integridad criptográfica de una evidencia (compatibilidad)."""
    return registrar_nueva_evidencia(evidencia, contenido_bytes)


def registrar_evidencia_deduplicada(
    evidencia: EvidenciaRegistro,
) -> tuple[EvidenciaRegistro, bool]:
    """Registra una evidencia con SHA-256 resuelto; devuelve (evidencia, duplicada)."""
    return registrar_evidencia(evidencia)


def listar_evidencias_tenant(
    tenant_id: str, normativa: Optional[str] = None
) -> list[EvidenciaRegistro]:
    """Obtiene el catálogo de evidencias de una organización."""
    return obtener_evidencias_tenant(tenant_id, normativa)


def obtener_evidencia_tenant(tenant_id: str, evidencia_id: str) -> EvidenciaRegistro:
    """Obtiene una evidencia del tenant; lanza EvidenciaNoEncontrada si no le pertenece."""
    return obtener_evidencia(tenant_id, evidencia_id)


def vincular_controles(
    tenant_id: str,
    evidencia_id: str,
    agregar: Optional[list[int]] = None,
    quitar: Optional[list[int]] = None,
) -> EvidenciaRegistro:
    """Agrega y/o quita controles del assessment vinculados a una evidencia."""
    return actualizar_vinculos(tenant_id, evidencia_id, agregar, quitar)


def verificar_hash(
    tenant_id: str, sha256_hash: str, normativa: Optional[str] = None
) -> Optional[EvidenciaRegistro]:
    """Devuelve la evidencia del tenant cuyo SHA-256 coincide, o None."""
    return buscar_por_hash(tenant_id, sha256_hash, normativa)


def reiniciar_repositorio_evidencias() -> None:
    """Vacía el repositorio en memoria (solo pruebas)."""
    reiniciar_repositorio()

# === DEMO-03e ===
from features.evidencias.services.clon_plantilla_engine import (  # noqa: E402
    clonar_desde_plantilla,
    sembrar_en_plantilla,
)

__all__.extend(["clonar_desde_plantilla", "sembrar_en_plantilla"])
# === fin DEMO-03e ===


# === ADPA-05 ===
# ¤adpa Los códigos de error de esta sala viven en features/evidencias/domain/errores.py y se registran al importarlo.
from features.evidencias.domain import errores as _errores_sala  # noqa: E402,F401
# === fin ADPA-05 ===

# === EVI-01 ===
# ¤evidencias Documentos guardados en el almacén y comprobados por el servidor.
from app_core.storage.gcs import FirmaSubida  # noqa: E402,F401
from features.evidencias.domain.models import (  # noqa: E402,F401
    ROLES_CONSULTA_DOCUMENTOS,
    DocumentoEvidencia,
)
from features.evidencias.domain.retencion import retencion_dias  # noqa: E402,F401
from features.evidencias.services.evidencias_engine import (  # noqa: E402,F401
    almacen_de_evidencias,
    confirmar_subida,
    controles_con_documento_registrado,
    desvincular_documento,
    listar_documentos,
    pedir_subida,
    subida_firmada_activa,
    vincular_documento,
)
# === fin EVI-01 ===

# === EVI-02 ===
# ¤evidencias-vigencia Vigencia, visibilidad y paquete para inspección.
from features.evidencias.domain import errores as errores_sala  # noqa: E402,F401
from features.evidencias.domain.vigencia import AtributosDocumento, esta_vigente, puede_ver  # noqa: E402,F401
from features.evidencias.services.paquete_inspeccion_engine import armar_paquete  # noqa: E402,F401
from features.evidencias.services.vigencia_engine import (  # noqa: E402,F401
    atributos_de,
    controles_con_documento_vigente,
    controles_para_sellar,
    documentos_vencidos_de_controles,
    fijar_atributos,
    listar_atributos,
)
# === fin EVI-02 ===
