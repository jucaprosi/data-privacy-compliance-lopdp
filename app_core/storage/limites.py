# ¤evidencias ¤seguridad
"""Reglas de admisión y construcción de claves de objeto para evidencias en Cloud Storage (RET-02).

Centraliza los tipos MIME permitidos, el límite máximo de tamaño (25 MB) y la validación
de claves con prefijo obligatorio de organización (`tenant_id/...`), sin acoplar a ningún
cliente de almacenamiento específico.
"""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app_core.errors import EVIDENCE_TOO_LARGE, EVIDENCE_TYPE_NOT_ALLOWED, CodigoErrorNegocio

TIPOS_PERMITIDOS: dict[str, tuple[str, ...]] = {
    "application/pdf": (".pdf",),
    "image/png": (".png",),
    "image/jpeg": (".jpg", ".jpeg"),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (".docx",),
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": (".xlsx",),
    "text/csv": (".csv",),
    "text/plain": (".txt",),
}
TAMANO_MAXIMO_BYTES = 25 * 1024 * 1024


def construir_clave_objeto(tenant_id: str, task_id: str, filename: str) -> str:
    """Construye una clave en Cloud Storage aislada bajo `<tenant_id>/<task_id>/`."""
    safe = Path(filename or "archivo").name.replace(" ", "_").replace("..", "")
    if not safe:
        safe = "archivo"
    return f"{tenant_id}/{task_id}/{uuid4().hex}_{safe}"


def clave_pertenece_a_tenant(clave: str, tenant_id: str) -> bool:
    """Verifica que `clave` esté confinada al prefijo `<tenant_id>/` sin saltos de ruta."""
    if not tenant_id or not clave:
        return False
    if "\\" in clave or clave.startswith("/"):
        return False
    segmentos = clave.split("/")
    if any(seg in ("", ".", "..") for seg in segmentos):
        return False
    return segmentos[0] == tenant_id and len(segmentos) >= 2


def motivo_de_rechazo(
    filename: str, mime_type: str, file_size: int
) -> tuple[CodigoErrorNegocio, str] | None:
    """Devuelve `(CodigoErrorNegocio, motivo)` si el archivo no es admisible, o `None`.

    El servidor aplica exactamente las mismas reglas que la interfaz (tipo MIME permitido,
    extensión coincidente y tamaño máximo de 25 MB).
    """
    extensiones = TIPOS_PERMITIDOS.get((mime_type or "").strip().lower())
    if extensiones is None:
        return EVIDENCE_TYPE_NOT_ALLOWED, f"El tipo '{mime_type}' no está permitido como evidencia."
    if not (filename or "").lower().endswith(extensiones):
        return EVIDENCE_TYPE_NOT_ALLOWED, "La extensión del archivo no corresponde a su tipo."
    if file_size > TAMANO_MAXIMO_BYTES:
        return EVIDENCE_TOO_LARGE, f"El archivo supera {TAMANO_MAXIMO_BYTES // (1024 * 1024)} MB."
    return None
