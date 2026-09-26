"""Lógica de verificación de integridad (SHA-256) y repositorio de evidencias."""
from __future__ import annotations

import hashlib
import re
import threading
from datetime import datetime, timezone
from typing import Optional

from features.evidencias.domain.models import (
    EvidenciaError,
    EvidenciaNoEncontrada,
    EvidenciaRegistro,
    normalizar_controles,
    normalizar_sha256,
)


class CodigoDuplicado(EvidenciaError):
    """El código solicitado ya está en uso dentro del tenant."""


class InMemoryEvidenciasRepository:
    def __init__(self) -> None:
        self._store: dict[str, EvidenciaRegistro] = {}
        self.lock = threading.RLock()

    def guardar(self, evidencia: EvidenciaRegistro) -> EvidenciaRegistro:
        self._store[evidencia.id] = evidencia
        return evidencia

    def obtener_por_id(self, evidencia_id: str) -> Optional[EvidenciaRegistro]:
        return self._store.get(evidencia_id)

    def obtener_de_tenant(self, tenant_id: str, evidencia_id: str) -> Optional[EvidenciaRegistro]:
        evidencia = self._store.get(evidencia_id)
        if evidencia is None or evidencia.tenant_id != tenant_id:
            return None
        return evidencia

    def listar_por_tenant(self, tenant_id: str) -> list[EvidenciaRegistro]:
        return [e for e in self._store.values() if e.tenant_id == tenant_id]

    def buscar_por_hash(
        self, tenant_id: str, sha256_hash: str, normativa: Optional[str] = None
    ) -> list[EvidenciaRegistro]:
        return [
            e
            for e in self._store.values()
            if e.tenant_id == tenant_id
            and e.sha256_hash == sha256_hash
            and (normativa is None or e.normativa == normativa)
        ]

    def limpiar(self) -> None:
        self._store.clear()


repo_evidencias = InMemoryEvidenciasRepository()


def calcular_hash_sha256(contenido_bytes: bytes) -> str:
    return hashlib.sha256(contenido_bytes).hexdigest()


def _siguiente_codigo(tenant_id: str) -> str:
    """Código correlativo EVD-AAAA-NNNN basado en el máximo existente (no en el conteo)."""
    anio = datetime.now(timezone.utc).year
    patron = re.compile(rf"^EVD-{anio}-(\d+)$")
    maximo = 0
    for e in repo_evidencias.listar_por_tenant(tenant_id):
        coincidencia = patron.match(e.codigo)
        if coincidencia:
            maximo = max(maximo, int(coincidencia.group(1)))
    return f"EVD-{anio}-{maximo + 1:04d}"


def registrar_evidencia(evidencia: EvidenciaRegistro) -> tuple[EvidenciaRegistro, bool]:
    """Registra una evidencia con hash ya resuelto.

    Deduplica por (tenant, sha256, normativa): si ya existe, devuelve la existente
    y ``True`` como indicador de duplicado.
    """
    evidencia.sha256_hash = normalizar_sha256(evidencia.sha256_hash)
    with repo_evidencias.lock:
        existentes = repo_evidencias.buscar_por_hash(
            evidencia.tenant_id, evidencia.sha256_hash, evidencia.normativa
        )
        if existentes:
            # Registrar de nuevo el mismo documento no crea otra evidencia, pero
            # los controles que se pidió vincular se incorporan a la existente.
            existente = existentes[0]
            existente.controles_vinculados = sorted(
                set(existente.controles_vinculados) | set(evidencia.controles_vinculados)
            )
            return existente, True
        if evidencia.codigo:
            en_uso = any(
                e.codigo == evidencia.codigo
                for e in repo_evidencias.listar_por_tenant(evidencia.tenant_id)
            )
            if en_uso:
                raise CodigoDuplicado(f"El código {evidencia.codigo} ya existe en el tenant")
        else:
            evidencia.codigo = _siguiente_codigo(evidencia.tenant_id)
        return repo_evidencias.guardar(evidencia), False


def registrar_nueva_evidencia(
    evidencia: EvidenciaRegistro, contenido_bytes: Optional[bytes] = None
) -> EvidenciaRegistro:
    """Compatibilidad: calcula el hash desde bytes solo si no viene precalculado."""
    if contenido_bytes is not None and not evidencia.sha256_hash:
        evidencia.sha256_hash = calcular_hash_sha256(contenido_bytes)
    guardada, _ = registrar_evidencia(evidencia)
    return guardada


def obtener_evidencias_tenant(
    tenant_id: str, normativa: Optional[str] = None
) -> list[EvidenciaRegistro]:
    evidencias = repo_evidencias.listar_por_tenant(tenant_id)
    if normativa is not None:
        evidencias = [e for e in evidencias if e.normativa == normativa]
    return sorted(evidencias, key=lambda e: e.created_at)


def obtener_evidencia(tenant_id: str, evidencia_id: str) -> EvidenciaRegistro:
    evidencia = repo_evidencias.obtener_de_tenant(tenant_id, evidencia_id)
    if evidencia is None:
        raise EvidenciaNoEncontrada(evidencia_id)
    return evidencia


def actualizar_vinculos(
    tenant_id: str,
    evidencia_id: str,
    agregar: Optional[list[int]] = None,
    quitar: Optional[list[int]] = None,
) -> EvidenciaRegistro:
    """Vincula/desvincula controles del assessment (1..80). Operación atómica."""
    a_agregar = set(normalizar_controles(agregar or []))
    a_quitar = set(normalizar_controles(quitar or []))
    with repo_evidencias.lock:
        evidencia = obtener_evidencia(tenant_id, evidencia_id)
        actuales = set(evidencia.controles_vinculados)
        evidencia.controles_vinculados = sorted((actuales | a_agregar) - a_quitar)
        return evidencia


def buscar_por_hash(
    tenant_id: str, sha256_hash: str, normativa: Optional[str] = None
) -> Optional[EvidenciaRegistro]:
    normalizado = normalizar_sha256(sha256_hash)
    coincidencias = repo_evidencias.buscar_por_hash(tenant_id, normalizado, normativa)
    if not coincidencias:
        return None
    return min(coincidencias, key=lambda e: e.created_at)


def reiniciar_repositorio() -> None:
    """Vacía el repositorio en memoria (uso en pruebas)."""
    with repo_evidencias.lock:
        repo_evidencias.limpiar()
