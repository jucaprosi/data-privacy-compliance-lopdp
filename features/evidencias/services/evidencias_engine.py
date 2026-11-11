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


# === EVI-01 ===
# ¤evidencias Documentos guardados en el almacén y comprobados por el servidor (rutas detrás de bandera).
import os  # noqa: E402
import re  # noqa: E402
import uuid  # noqa: E402
from datetime import timedelta  # noqa: E402

from sqlalchemy import text  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app_core.audit import registrar_evento  # noqa: E402
from app_core.errors import ErrorNegocio  # noqa: E402
from app_core.storage import gcs  # noqa: E402
from app_core.storage.r2 import TAMANO_MAXIMO_BYTES, motivo_de_rechazo  # noqa: E402
from features.evidencias.domain import errores as _e  # noqa: E402
from features.evidencias.domain.models import (  # noqa: E402
    NORMATIVA_POR_DEFECTO,
    DocumentoEvidencia,
    puede_subir,
    validar_control_id,
)
from features.evidencias.domain.retencion import retencion_dias  # noqa: E402

VARIABLE_BANDERA_SUBIDA_FIRMADA = "EVIDENCIAS_SUBIDA_FIRMADA"
_VALORES_ENCENDIDO = frozenset({"1", "true", "si", "on"})
_PATRON_CLAVE = re.compile(r"^[0-9a-f]{32}$")
_REINTENTOS_CODIGO = 3

# Firma del formato: los primeros bytes que debe llevar el archivo según su tipo declarado.
_FIRMAS_DE_FORMATO: dict[str, tuple[bytes, ...]] = {
    "application/pdf": (b"%PDF-",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (b"PK\x03\x04",),
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": (b"PK\x03\x04",),
}
_TIPOS_DE_TEXTO = frozenset({"text/csv", "text/plain"})


def subida_firmada_activa() -> bool:
    """Bandera `EVIDENCIAS_SUBIDA_FIRMADA`: se lee solo aquí, en el backend; apagada por defecto."""
    return os.environ.get(VARIABLE_BANDERA_SUBIDA_FIRMADA, "").strip().lower() in _VALORES_ENCENDIDO


def firma_de_formato_valida(tipo_mime: str, contenido: bytes) -> bool:
    tipo = (tipo_mime or "").strip().lower()
    if tipo in _TIPOS_DE_TEXTO:
        try:
            contenido.decode("utf-8")
        except UnicodeDecodeError:
            return False
        return b"\x00" not in contenido
    firmas = _FIRMAS_DE_FORMATO.get(tipo)
    return firmas is not None and contenido.startswith(firmas)


def almacen_de_evidencias() -> gcs.Almacen:
    try:
        return gcs.almacen_por_defecto()
    except gcs.AlmacenNoDisponible as exc:
        raise ErrorNegocio(_e.ALMACEN_NO_DISPONIBLE) from exc


def exigir_puede_subir(rol: str, real_sellado: bool) -> None:
    if not puede_subir(rol, real_sellado):
        raise ErrorNegocio(_e.SIN_PERMISO_PARA_SUBIR)


def exigir_puede_vincular(rol: str, real_sellado: bool) -> None:
    """Sellado el real nadie vincula ni desvincula (409); antes, solo el DPO (403)."""
    if real_sellado:
        raise ErrorNegocio(_e.VINCULOS_CERRADOS)
    if rol != "dpo":
        raise ErrorNegocio(_e.SIN_PERMISO_PARA_VINCULAR)


def pedir_subida(
    almacen: gcs.Almacen, tenant_id: str, rol: str, real_sellado: bool, nombre_archivo: str, tipo_mime: str,
    tamano_bytes: int,
) -> gcs.FirmaSubida:
    """Paso 1: valida nombre, tipo y tamaño con las reglas de SEC-05 y firma la URL de subida."""
    exigir_puede_subir(rol, real_sellado)
    rechazo = motivo_de_rechazo(nombre_archivo, tipo_mime, tamano_bytes)
    if rechazo is not None:
        codigo, motivo = rechazo
        raise ErrorNegocio(codigo, detail=motivo)
    clave = f"{tenant_id}/{uuid.uuid4().hex}"
    return almacen.firmar_subida(clave, tipo_mime.strip().lower())


def _a_documento(fila, controles: list[int]) -> DocumentoEvidencia:
    return DocumentoEvidencia(
        id=fila["id"], tenant_id=fila["tenant_id"], codigo=fila["codigo"], nombre_archivo=fila["nombre_archivo"],
        tipo_mime=fila["tipo_mime"], tamano_bytes=fila["tamano_bytes"], sha256=fila["sha256"],
        normativa=fila["normativa"], clave_almacen=fila["clave_almacen"], subido_por=fila["subido_por"],
        subido_en=fila["subido_en"], retencion_dias=fila["retencion_dias"], controles=controles,
    )


async def _fijar_rls(session: AsyncSession, tenant_id: str, user_id: str | None = None) -> None:
    from app_core.db.session import fijar_contexto_rls

    await fijar_contexto_rls(session, tenant_id, user_id)


async def _controles_de(session: AsyncSession, tenant_id: str, documento_ids: list[str]) -> dict[str, list[int]]:
    if not documento_ids:
        return {}
    filas = await session.execute(
        text(
            "SELECT documento_id, control_id FROM evidencias_vinculos "
            "WHERE tenant_id = :t AND documento_id = ANY(:ids) ORDER BY control_id"
        ),
        {"t": tenant_id, "ids": documento_ids},
    )
    por_documento: dict[str, list[int]] = {}
    for documento_id, control_id in filas.all():
        por_documento.setdefault(documento_id, []).append(int(control_id))
    return por_documento


async def _documento_existente(
    session: AsyncSession, tenant_id: str, sha256: str, normativa: str, clave: str
) -> DocumentoEvidencia | None:
    fila = (
        await session.execute(
            text(
                "SELECT id, tenant_id, codigo, nombre_archivo, tipo_mime, tamano_bytes, sha256, normativa, "
                "clave_almacen, subido_por, subido_en, retencion_dias FROM evidencias_documentos "
                "WHERE tenant_id = :t AND ((sha256 = :s AND normativa = :n) OR clave_almacen = :k) "
                "ORDER BY subido_en LIMIT 1"
            ),
            {"t": tenant_id, "s": sha256, "n": normativa, "k": clave},
        )
    ).mappings().first()
    if fila is None:
        return None
    controles = await _controles_de(session, tenant_id, [fila["id"]])
    return _a_documento(fila, controles.get(fila["id"], []))


async def _siguiente_codigo_en_base(session: AsyncSession, tenant_id: str) -> str:
    anio = datetime.now(timezone.utc).year
    maximo = (
        await session.execute(
            text(
                "SELECT COALESCE(MAX(CAST(substring(codigo FROM '[0-9]+$') AS INTEGER)), 0) "
                "FROM evidencias_documentos WHERE tenant_id = :t AND codigo LIKE :patron"
            ),
            {"t": tenant_id, "patron": f"EVD-{anio}-%"},
        )
    ).scalar_one()
    return f"EVD-{anio}-{int(maximo) + 1:04d}"


async def confirmar_subida(
    session: AsyncSession,
    almacen: gcs.Almacen,
    tenant_id: str,
    user_id: str,
    rol: str,
    real_sellado: bool,
    clave: str,
    huella_navegador: str,
    nombre_archivo: str,
    tipo_mime: str,
    normativa: str = NORMATIVA_POR_DEFECTO,
) -> tuple[DocumentoEvidencia, bool]:
    """Paso 3: el servidor descarga el archivo, lo comprueba, calcula su huella y lo registra.

    Devuelve (documento, duplicada). Si la huella del navegador no coincide con la que calcula el
    servidor, o no se logra fijar la retención del objeto, no se registra nada.
    """
    exigir_puede_subir(rol, real_sellado)
    prefijo, _, sufijo = clave.partition("/")
    if prefijo != tenant_id or not _PATRON_CLAVE.fullmatch(sufijo):
        raise ErrorNegocio(_e.CLAVE_NO_ENCONTRADA)
    esperada = normalizar_sha256(huella_navegador)
    try:
        contenido = almacen.descargar(clave, TAMANO_MAXIMO_BYTES)
    except gcs.ObjetoDemasiadoGrande as exc:
        raise ErrorNegocio(_e.ARCHIVO_INVALIDO) from exc
    if contenido is None:
        raise ErrorNegocio(_e.CLAVE_NO_ENCONTRADA)
    rechazo = motivo_de_rechazo(nombre_archivo, tipo_mime, len(contenido))
    if rechazo is not None:
        codigo, motivo = rechazo
        raise ErrorNegocio(codigo, detail=motivo)
    if not firma_de_formato_valida(tipo_mime, contenido):
        raise ErrorNegocio(_e.ARCHIVO_INVALIDO)
    huella = calcular_hash_sha256(contenido)
    if huella != esperada:
        raise ErrorNegocio(_e.HUELLA_NO_COINCIDE)

    normativa = (normativa or "").strip() or NORMATIVA_POR_DEFECTO
    await _fijar_rls(session, tenant_id, user_id)
    previo = await _documento_existente(session, tenant_id, huella, normativa, clave)
    if previo is not None:
        return previo, True

    dias = retencion_dias(tenant_id)
    try:
        almacen.fijar_retencion(clave, datetime.now(timezone.utc) + timedelta(days=dias))
    except Exception as exc:  # falla cerrada: sin retención fijada el documento no se registra
        raise ErrorNegocio(_e.RETENCION_NO_FIJADA) from exc

    documento_id = str(uuid.uuid4())
    for intento in range(_REINTENTOS_CODIGO):
        codigo_evd = await _siguiente_codigo_en_base(session, tenant_id)
        try:
            async with session.begin_nested():
                fila = (
                    await session.execute(
                        text(
                            "INSERT INTO evidencias_documentos (id, tenant_id, codigo, nombre_archivo, tipo_mime, "
                            "tamano_bytes, sha256, normativa, clave_almacen, subido_por, retencion_dias) "
                            "VALUES (:id, :t, :cod, :nom, :mime, :tam, :sha, :norm, :clave, :u, :dias) "
                            "RETURNING id, tenant_id, codigo, nombre_archivo, tipo_mime, tamano_bytes, sha256, "
                            "normativa, clave_almacen, subido_por, subido_en, retencion_dias"
                        ),
                        {
                            "id": documento_id, "t": tenant_id, "cod": codigo_evd, "nom": nombre_archivo.strip(),
                            "mime": tipo_mime.strip().lower(), "tam": len(contenido), "sha": huella,
                            "norm": normativa, "clave": clave, "u": user_id, "dias": dias,
                        },
                    )
                ).mappings().one()
            break
        except IntegrityError:
            carrera = await _documento_existente(session, tenant_id, huella, normativa, clave)
            if carrera is not None:
                return carrera, True
            if intento == _REINTENTOS_CODIGO - 1:
                raise
    await registrar_evento(
        session, tenant_id, "evidencia_documento", documento_id, "registrar", user_id,
        {"codigo": codigo_evd, "sha256": huella},
    )
    return _a_documento(fila, []), False


async def listar_documentos(session: AsyncSession, tenant_id: str, user_id: str) -> list[DocumentoEvidencia]:
    await _fijar_rls(session, tenant_id, user_id)
    filas = (
        await session.execute(
            text(
                "SELECT id, tenant_id, codigo, nombre_archivo, tipo_mime, tamano_bytes, sha256, normativa, "
                "clave_almacen, subido_por, subido_en, retencion_dias FROM evidencias_documentos "
                "WHERE tenant_id = :t ORDER BY subido_en, codigo"
            ),
            {"t": tenant_id},
        )
    ).mappings().all()
    controles = await _controles_de(session, tenant_id, [f["id"] for f in filas])
    return [_a_documento(f, controles.get(f["id"], [])) for f in filas]


async def vincular_documento(
    session: AsyncSession, tenant_id: str, user_id: str, rol: str, real_sellado: bool, documento_id: str,
    control_id: int,
) -> bool:
    """Vincula un control al documento; devuelve False si ya estaba vinculado."""
    exigir_puede_vincular(rol, real_sellado)
    validar_control_id(control_id)
    await _fijar_rls(session, tenant_id, user_id)
    existe = await session.execute(
        text("SELECT 1 FROM evidencias_documentos WHERE id = :d AND tenant_id = :t"),
        {"d": documento_id, "t": tenant_id},
    )
    if existe.first() is None:
        raise ErrorNegocio(_e.DOCUMENTO_NO_ENCONTRADO)
    insertado = await session.execute(
        text(
            "INSERT INTO evidencias_vinculos (id, tenant_id, documento_id, control_id, vinculado_por) "
            "VALUES (:id, :t, :d, :c, :u) ON CONFLICT (documento_id, control_id) DO NOTHING RETURNING id"
        ),
        {"id": str(uuid.uuid4()), "t": tenant_id, "d": documento_id, "c": control_id, "u": user_id},
    )
    if insertado.first() is None:
        return False
    await registrar_evento(
        session, tenant_id, "evidencia_vinculo", documento_id, "vincular", user_id, {"control_id": control_id}
    )
    return True


async def desvincular_documento(
    session: AsyncSession, tenant_id: str, user_id: str, rol: str, real_sellado: bool, documento_id: str,
    control_id: int,
) -> bool:
    """Quita el vínculo; devuelve False si no existía."""
    exigir_puede_vincular(rol, real_sellado)
    validar_control_id(control_id)
    await _fijar_rls(session, tenant_id, user_id)
    borrado = await session.execute(
        text(
            "DELETE FROM evidencias_vinculos WHERE tenant_id = :t AND documento_id = :d AND control_id = :c "
            "RETURNING id"
        ),
        {"t": tenant_id, "d": documento_id, "c": control_id},
    )
    if borrado.first() is None:
        return False
    await registrar_evento(
        session, tenant_id, "evidencia_vinculo", documento_id, "desvincular", user_id, {"control_id": control_id}
    )
    return True


async def controles_con_documento_registrado(session: AsyncSession, tenant_id: str) -> set[int]:
    """Controles con un documento vinculado que el servidor registró (lo usa DIAG-03 al sellar)."""
    await _fijar_rls(session, tenant_id)
    filas = await session.execute(
        text("SELECT DISTINCT control_id FROM evidencias_vinculos WHERE tenant_id = :t"), {"t": tenant_id}
    )
    return {int(c) for (c,) in filas.all()}
# === fin EVI-01 ===
