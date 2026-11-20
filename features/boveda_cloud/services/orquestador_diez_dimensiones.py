# ¤boveda-cloud ¤videovigilancia-cctv ¤dpo-cockpit ¤conservacion ¤adpa
"""Orquestador Comercial de las 10 Dimensiones LOPDP y Telemetría de Bóveda Cloud (BOV-04).

Consolida de forma multidimensional:
- Las 10 dimensiones SGPDP/LOPDP (`D01`..`D10`) desglosadas por separado (`INV_LOPDP_MULTIDIMENSIONAL_METRICS`).
- Telemetría de Bóveda Cloud (almacenamiento y descargas en GB frente a cuota del paquete).
- Cámaras CCTV activas conformes y clips protegidos en *Hold Legal* (WORM).
- Actas criptográficas de purga/destrucción con certificado `SHA-256` verificable por el DPO.
- Escaneos DLP muestreados y estado del caché normativo.

Aislamiento ADPA: esta sala no importa directamente otras salas de `features/`; toda lectura
externa se canaliza vía `app_core/pasillo/`.
"""
from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timezone
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import fijar_contexto_rls
from features.boveda_cloud.domain import errores
from features.boveda_cloud.models import ObjetoCustodiaBoveda

BYTES_POR_GB = 1024**3
_SHA256_HEX = re.compile(r"^[0-9a-fA-F]{64}$")

# Catálogo canónico de las 10 dimensiones LOPDP (alineado con escala_madurez.json).
CATALOGO_DIEZ_DIMENSIONES: tuple[tuple[str, str, str], ...] = (
    ("D01", "Gobierno y responsabilidad proactiva", "Gobernanza y DPO"),
    ("D02", "Inventario, RAT, finalidades y legitimación", "RAT y Descubrimiento"),
    ("D03", "Transparencia e información al titular", "Transparencia"),
    ("D04", "Derechos de titulares", "Derechos ARCOP+"),
    ("D05", "Procesos críticos y ciclo de vida de datos", "Conservación y Videovigilancia"),
    ("D06", "Encargados, proveedores y transferencias", "Terceros y Transferencias"),
    ("D07", "Seguridad de datos personales", "Bóveda Cloud y Seguridad"),
    ("D08", "Incidentes y vulneraciones", "Vulneraciones"),
    ("D09", "Riesgos, EIPD, LIA y privacidad desde el diseño", "Riesgos y EIPD"),
    ("D10", "Capacitación, cultura, auditoría y mejora continua", "Formación y Auditoría"),
)
CODIGOS_DIMENSIONES: tuple[str, ...] = tuple(cod for cod, _, _ in CATALOGO_DIEZ_DIMENSIONES)
_MAPA_CATALOGO = {cod: (nombre, modulo) for cod, nombre, modulo in CATALOGO_DIEZ_DIMENSIONES}

# Claves prohibidas por INV_LOPDP_MULTIDIMENSIONAL_METRICS (R1).
CAMPOS_METRICA_GLOBAL_PROHIBIDOS: frozenset[str] = frozenset({
    "porcentaje_global",
    "porcentaje_unico",
    "puntaje_global",
    "puntaje_unico",
    "cumplimiento_global",
    "metrica_global",
    "promedio_global",
    "indice_global",
    "global_percentage",
})
_CODIGOS_GLOBALES_PROHIBIDOS: frozenset[str] = frozenset({
    "GLOBAL",
    "TOTAL",
    "UNICA",
    "UNICO",
    "CONSOLIDADO_GLOBAL",
})


def validar_sha256_acta(sha256: str) -> str:
    """R2: exige huella SHA-256 hexadecimal de 64 caracteres para toda acta de destrucción."""
    if not isinstance(sha256, str):
        raise errores.error(errores.BOVEDA_ACTA_SHA256_INVALIDA)
    limpio = sha256.strip()
    if not _SHA256_HEX.fullmatch(limpio):
        raise errores.error(errores.BOVEDA_ACTA_SHA256_INVALIDA)
    return limpio.lower()


def exigir_sin_metrica_global(
    datos: dict[str, Any] | None = None,
    *,
    incluir_metrica_global: bool = False,
) -> None:
    """R1 (INV_LOPDP_MULTIDIMENSIONAL_METRICS): bloquea cualquier proyección o cálculo escalar global."""
    if incluir_metrica_global:
        raise errores.error(errores.BOVEDA_METRICA_GLOBAL_PROHIBIDA)
    if isinstance(datos, dict):
        claves_prohibidas = CAMPOS_METRICA_GLOBAL_PROHIBIDOS & set(datos.keys())
        if claves_prohibidas:
            raise errores.error(errores.BOVEDA_METRICA_GLOBAL_PROHIBIDA)


class EstadoDimensionCloud(BaseModel):
    """Estado individual de una dimensión LOPDP (`D01`..`D10`) sin dilución en un promedio único."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    codigo: str
    nombre: str
    nivel_asignado: int = Field(default=1, ge=1, le=5)
    nivel_evidencia: int = Field(default=0, ge=0, le=4)
    controles_conformes: int = Field(default=0, ge=0)
    controles_totales: int = Field(default=0, ge=0)
    evidencias_custodiadas: int = Field(default=0, ge=0)
    estado_operativo: str = "PENDIENTE"
    automatizacion_activa: bool = False
    modulo_asociado: str = ""

    @field_validator("codigo")
    @classmethod
    def _validar_codigo_dimension(cls, valor: str) -> str:
        codigo = valor.strip().upper()
        if codigo in _CODIGOS_GLOBALES_PROHIBIDOS:
            raise errores.error(errores.BOVEDA_METRICA_GLOBAL_PROHIBIDA)
        if codigo not in _MAPA_CATALOGO:
            raise ValueError(f"Código de dimensión LOPDP desconocido: {valor!r}")
        return codigo


class ActaDestruccionCertificada(BaseModel):
    """Acta criptográfica de purga o congelamiento verificable por el DPO mediante su SHA-256."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    acta_id: str = Field(min_length=1, max_length=120)
    origen: str = Field(default="CCTV_QUINCENAL", min_length=1, max_length=80)
    fecha_emision: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sha256: str
    elementos_purgados: int = Field(default=0, ge=0)
    elementos_hold_legal: int = Field(default=0, ge=0)
    verificada_dpo: bool = True

    @field_validator("sha256")
    @classmethod
    def _validar_huella(cls, valor: str) -> str:
        return validar_sha256_acta(valor)


class ResumenOrquestadorDiezDimensiones(BaseModel):
    """Proyección ejecutiva multidimensional de las 10 dimensiones LOPDP y la Bóveda Cloud."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tenant_id: str = Field(min_length=1, max_length=64)
    dimensiones: list[EstadoDimensionCloud]
    uso_boveda_gb: float = Field(default=0.0, ge=0.0)
    uso_egress_gb: float = Field(default=0.0, ge=0.0)
    cuota_boveda_gb: float = Field(default=0.0, ge=0.0)
    cuota_egress_gb: float = Field(default=0.0, ge=0.0)
    camaras_activas: int = Field(default=0, ge=0)
    clips_en_hold_legal: int = Field(default=0, ge=0)
    actas_destruccion_emitidas: int = Field(default=0, ge=0)
    escaneos_dlp_completados: int = Field(default=0, ge=0)
    estado_cache_normativo: str = "ACTIVO"
    actas_sha256: list[ActaDestruccionCertificada] = Field(default_factory=list)
    modo_lectura: bool = False
    paquete_codigo: str = "INICIAL"
    estado_suscripcion: str = "ACTIVA"

    @model_validator(mode="before")
    @classmethod
    def _rechazar_metrica_global(cls, data: Any) -> Any:
        if isinstance(data, dict):
            exigir_sin_metrica_global(data)
        return data

    @model_validator(mode="after")
    def _validar_diez_dimensiones_separadas(self) -> "ResumenOrquestadorDiezDimensiones":
        codigos = [d.codigo for d in self.dimensiones]
        if len(codigos) != len(set(codigos)) or set(codigos) != set(CODIGOS_DIMENSIONES):
            raise ValueError("El orquestador exige exactamente las 10 dimensiones D01..D10 por separado.")
        return self


def construir_dimensiones_base(
    parciales: Iterable[EstadoDimensionCloud | dict[str, Any]] | None = None,
) -> list[EstadoDimensionCloud]:
    """Construye la matriz canónica D01..D10 aplicando overrides parciales sin fusionar dimensiones."""
    por_codigo: dict[str, EstadoDimensionCloud] = {}
    for item in parciales or ():
        if isinstance(item, dict):
            exigir_sin_metrica_global(item)
            dim = EstadoDimensionCloud.model_validate(item)
        else:
            dim = item
        por_codigo[dim.codigo] = dim

    salida: list[EstadoDimensionCloud] = []
    for codigo, nombre, modulo in CATALOGO_DIEZ_DIMENSIONES:
        if codigo in por_codigo:
            actual = por_codigo[codigo]
            if not actual.modulo_asociado:
                actual = actual.model_copy(update={"modulo_asociado": modulo})
            salida.append(actual)
        else:
            salida.append(
                EstadoDimensionCloud(
                    codigo=codigo,
                    nombre=nombre,
                    modulo_asociado=modulo,
                )
            )
    return salida


_CANDADO_REGISTRO = threading.Lock()
_ESTADO_TENANTS: dict[str, ResumenOrquestadorDiezDimensiones] = {}


def limpiar_registro_orquestador(tenant_id: str | None = None) -> None:
    """Limpia el estado en memoria de un tenant o de todos (uso principal en pruebas)."""
    with _CANDADO_REGISTRO:
        if tenant_id is None:
            _ESTADO_TENANTS.clear()
        else:
            _ESTADO_TENANTS.pop(tenant_id, None)


def registrar_estado_orquestador_tenant(
    tenant_id: str,
    datos: ResumenOrquestadorDiezDimensiones | dict[str, Any] | None = None,
    **campos: Any,
) -> ResumenOrquestadorDiezDimensiones:
    """Registra y valida la proyección multidimensional de un tenant en memoria aislada."""
    if not tenant_id or not tenant_id.strip():
        raise ValueError("tenant_id requerido")
    tid = tenant_id.strip()

    bruto: dict[str, Any] = {}
    if isinstance(datos, ResumenOrquestadorDiezDimensiones):
        bruto.update(datos.model_dump())
    elif isinstance(datos, dict):
        exigir_sin_metrica_global(datos)
        bruto.update(datos)
    elif datos is not None:
        raise TypeError("datos debe ser ResumenOrquestadorDiezDimensiones o dict")

    exigir_sin_metrica_global(campos)
    bruto.update(campos)
    bruto["tenant_id"] = tid

    raw_dimensiones = bruto.get("dimensiones")
    bruto["dimensiones"] = construir_dimensiones_base(raw_dimensiones)

    actas_normalizadas: list[ActaDestruccionCertificada] = []
    for acta in bruto.get("actas_sha256") or ():
        if isinstance(acta, ActaDestruccionCertificada):
            validar_sha256_acta(acta.sha256)
            actas_normalizadas.append(acta)
        elif isinstance(acta, dict):
            actas_normalizadas.append(ActaDestruccionCertificada.model_validate(acta))
        else:
            raise TypeError("Cada acta debe ser ActaDestruccionCertificada o dict")
    bruto["actas_sha256"] = actas_normalizadas

    if "actas_destruccion_emitidas" not in bruto:
        bruto["actas_destruccion_emitidas"] = len(actas_normalizadas)

    resumen = ResumenOrquestadorDiezDimensiones.model_validate(bruto)
    with _CANDADO_REGISTRO:
        _ESTADO_TENANTS[tid] = resumen
    return resumen


def _consultar_estado_cache_normativo() -> str:
    """Consulta el estado del caché normativo vía pasillo de regulación sin crear recursos en GCP."""
    try:
        from app_core.pasillo import regulacion_rag as pasillo_reg

        corpus = pasillo_reg.corpus_citable()
        if not corpus:
            return "SIN_CORPUS"
        try:
            descriptor = pasillo_reg.obtener_o_crear_cache_normativo("gemini-2.5-flash")
            if getattr(descriptor, "cache_name", None):
                return "ACTIVO"
        except Exception:
            return "DISPONIBLE_EN_ESPERA"
    except Exception:
        return "NO_DISPONIBLE"
    return "DISPONIBLE_EN_ESPERA"


async def _leer_suscripcion_boveda(session: AsyncSession, tenant_id: str) -> dict[str, Any] | None:
    """Lee la suscripción y consumo de la propia sala `boveda_cloud` respetando RLS."""
    await fijar_contexto_rls(session, tenant_id)
    fila = (
        await session.execute(
            text(
                "SELECT s.paquete_codigo, s.cuota_almacenamiento_bytes, s.uso_almacenamiento_bytes, "
                "s.cuota_egress_mensual_bytes, s.uso_egress_mensual_bytes, s.certificaciones_heredadas, s.estado "
                "FROM boveda_suscripciones_tenant s WHERE s.tenant_id = :t"
            ),
            {"t": tenant_id},
        )
    ).mappings().first()
    if fila is None:
        return None
    datos = dict(fila)
    if isinstance(datos.get("certificaciones_heredadas"), str):
        datos["certificaciones_heredadas"] = json.loads(datos["certificaciones_heredadas"])
    excedida = (
        datos["uso_almacenamiento_bytes"] >= datos["cuota_almacenamiento_bytes"]
        or datos["uso_egress_mensual_bytes"] >= datos["cuota_egress_mensual_bytes"]
    )
    estado = "CUOTA_EXCEDIDA" if datos["estado"] == "ACTIVA" and excedida else datos["estado"]
    return {
        "paquete_codigo": datos["paquete_codigo"],
        "estado_suscripcion": estado,
        "uso_boveda_gb": round(datos["uso_almacenamiento_bytes"] / BYTES_POR_GB, 4),
        "cuota_boveda_gb": round(datos["cuota_almacenamiento_bytes"] / BYTES_POR_GB, 4),
        "uso_egress_gb": round(datos["uso_egress_mensual_bytes"] / BYTES_POR_GB, 4),
        "cuota_egress_gb": round(datos["cuota_egress_mensual_bytes"] / BYTES_POR_GB, 4),
    }


async def _enriquecer_desde_sesion(
    session: AsyncSession,
    tenant_id: str,
    base: ResumenOrquestadorDiezDimensiones,
) -> ResumenOrquestadorDiezDimensiones:
    """Enriquece la proyección con datos reales de PostgreSQL y pasillos ADPA cuando hay AsyncSession."""
    actualizaciones: dict[str, Any] = {}
    dim_actuales = {d.codigo: d for d in base.dimensiones}

    try:
        async with session.begin_nested():
            sus = await _leer_suscripcion_boveda(session, tenant_id)
            if sus is not None:
                actualizaciones.update(sus)
            ev_count = (
                await session.execute(
                    select(func.count()).select_from(ObjetoCustodiaBoveda).where(ObjetoCustodiaBoveda.tenant_id == tenant_id)
                )
            ).scalar() or 0
            if ev_count > 0:
                d07 = dim_actuales["D07"]
                dim_actuales["D07"] = d07.model_copy(
                    update={"evidencias_custodiadas": max(d07.evidencias_custodiadas, int(ev_count)), "automatizacion_activa": True}
                )
    except Exception:
        pass

    try:
        from app_core.pasillo import videovigilancia as pasillo_cctv

        async with session.begin_nested():
            camaras = await pasillo_cctv.listar_camaras(session, tenant_id)
            clips = await pasillo_cctv.listar_clips(session, tenant_id)
            if camaras:
                actualizaciones["camaras_activas"] = max(base.camaras_activas, len(camaras))
            en_hold = sum(1 for c in clips if getattr(c, "hold_legal_activo", False))
            if en_hold:
                actualizaciones["clips_en_hold_legal"] = max(base.clips_en_hold_legal, en_hold)
            if camaras or clips:
                d05 = dim_actuales["D05"]
                dim_actuales["D05"] = d05.model_copy(update={"automatizacion_activa": True})
    except Exception:
        pass

    try:
        from app_core.pasillo import dlp_discovery as pasillo_dlp

        async with session.begin_nested():
            escaneos = await pasillo_dlp.listar_escaneos(session, tenant_id)
            if escaneos:
                actualizaciones["escaneos_dlp_completados"] = max(base.escaneos_dlp_completados, len(escaneos))
                d02 = dim_actuales["D02"]
                dim_actuales["D02"] = d02.model_copy(update={"automatizacion_activa": True})
    except Exception:
        pass

    actualizaciones["dimensiones"] = [dim_actuales[c] for c in CODIGOS_DIMENSIONES]
    return base.model_copy(update=actualizaciones)


async def obtener_resumen_orquestador_10d(
    session: AsyncSession | None,
    tenant_id: str,
    *,
    modo_lectura: bool = False,
    incluir_metrica_global: bool = False,
    politicas_conservacion_vencidas: int | None = None,
) -> ResumenOrquestadorDiezDimensiones:
    """Consolida el resumen multidimensional de las 10 dimensiones LOPDP y Bóveda Cloud por tenant."""
    exigir_sin_metrica_global(incluir_metrica_global=incluir_metrica_global)
    if not tenant_id or not tenant_id.strip():
        raise ValueError("tenant_id requerido")
    tid = tenant_id.strip()

    with _CANDADO_REGISTRO:
        registrado = _ESTADO_TENANTS.get(tid)

    if registrado is None:
        base = ResumenOrquestadorDiezDimensiones(
            tenant_id=tid,
            dimensiones=construir_dimensiones_base(),
            estado_cache_normativo=_consultar_estado_cache_normativo(),
            modo_lectura=modo_lectura,
        )
    else:
        base = registrado

    if isinstance(session, AsyncSession):
        base = await _enriquecer_desde_sesion(session, tid, base)

    if politicas_conservacion_vencidas and politicas_conservacion_vencidas > 0:
        dims = [
            d.model_copy(update={"estado_operativo": "ATENCION_REQUERIDA"}) if d.codigo == "D05" else d
            for d in base.dimensiones
        ]
        base = base.model_copy(update={"dimensiones": dims})

    return base.model_copy(update={"modo_lectura": modo_lectura})


async def consultar_orquestador_boveda_dpo(
    session: AsyncSession | None = None,
    tenant_id: str = "",
    *,
    incluir_metrica_global: bool = False,
    politicas_conservacion_vencidas: int | None = None,
) -> ResumenOrquestadorDiezDimensiones:
    """Expone al DPO las actas SHA-256, clips en Hold Legal y 10 dimensiones en modo solo lectura."""
    return await obtener_resumen_orquestador_10d(
        session,
        tenant_id,
        modo_lectura=True,
        incluir_metrica_global=incluir_metrica_global,
        politicas_conservacion_vencidas=politicas_conservacion_vencidas,
    )
