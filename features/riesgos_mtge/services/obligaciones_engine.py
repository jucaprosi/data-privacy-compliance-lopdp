# ¤mtge-granescala
# ¤rbac-tenant
"""Motor de cálculo y persistencia de obligaciones de tratamiento a gran escala (MTGE-02).

Fuente legal:
- Res. SPDP-SPD-2026-0005-R (Arts. 15-18 y Disposición Transitoria).
- Entrada F11 de governance/artefactos/FUENTES_Y_BIBLIOGRAFIA.md.

Reglas vinculantes:
- Art. 16: Privacidad desde el diseño y por defecto (recordatorio informativo mientras SPDP emite norma técnica).
- Art. 17: Auditoría interna o externa al menos cada 12 meses (365 días). Se conserva 5 años. Exime certificación equivalente vigente.
- Art. 18: Informe anual de cumplimiento conservado 5 años; política de privacidad que identifica tratamientos gran escala.
- Disposición Transitoria: 90 días desde la fecha de vigencia que registre el administrador para designar y registrar al DPO.
- Conservación (5 años): Borrar auditorías o informes anuales antes de 5 años desde su fecha genera 409 Conflict citando los arts. 17 o 18.
- Si la organización no tiene tratamientos calificados como gran escala, todas las obligaciones aplican como 'NO_APLICA'.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field, model_validator

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from features.organizacion import organizacion_service
from features.rat import rat_service


def _mas_un_anio(fecha: date) -> date:
    """Vencimiento de la auditoría: el mismo día del año siguiente (29 de febrero → 28 de febrero, el plazo más corto)."""
    try:
        return fecha.replace(year=fecha.year + 1)
    except ValueError:
        return fecha.replace(year=fecha.year + 1, day=28)


def _fin_conservacion(fecha: date, anios: int = 5) -> date:
    """Fin del plazo de conservación en años calendario (29 de febrero → 1 de marzo, el plazo más largo)."""
    try:
        return fecha.replace(year=fecha.year + anios)
    except ValueError:
        return date(fecha.year + anios, 3, 1)


class EstadoObligacion(str, Enum):
    AL_DIA = "AL_DIA"
    POR_VENCER = "POR_VENCER"  # En 30 días o menos
    VENCIDA = "VENCIDA"
    NO_APLICA = "NO_APLICA"
    FALTA_FECHA_VIGENCIA = "FALTA_FECHA_VIGENCIA"
    RECORDATORIO = "RECORDATORIO"  # Art. 16: sin normativa específica de la SPDP todavía


class ResumenObligacion(BaseModel):
    obligacion: str
    articulo_fuente: str
    estado: EstadoObligacion
    dias_restantes: Optional[int] = None
    fecha_limite: Optional[date] = None
    descripcion: str
    accion_siguiente: str


class EstadoObligacionesResponse(BaseModel):
    tiene_gran_escala: bool
    cantidad_tratamientos_gran_escala: int
    fecha_vigencia_norma: Optional[date] = None
    obligaciones: List[ResumenObligacion]


class ConfiguracionVigenciaCreate(BaseModel):
    fecha_vigencia_norma: date


class AuditoriaGranEscalaCreate(BaseModel):
    fecha_auditoria: date
    tipo: str = Field(..., pattern=r"^(interna|externa)$")
    alcance: str
    auditor: str
    archivo_informe: Optional[str] = None
    es_certificacion_equivalente: bool = False
    certificacion_nombre: Optional[str] = None
    certificacion_vigente_hasta: Optional[date] = None

    @model_validator(mode="after")
    def _certificacion_con_vigencia(self):
        # Art. 17: solo exime una certificación vigente; sin fecha de vigencia no se puede comprobar.
        if self.es_certificacion_equivalente and self.certificacion_vigente_hasta is None:
            raise ValueError("La certificación equivalente requiere su fecha de vigencia (certificacion_vigente_hasta).")
        return self


class InformeAnualCreate(BaseModel):
    anio: int = Field(..., ge=2020, le=2100)
    fecha_aprobacion: date
    archivo_informe: Optional[str] = None
    observaciones: Optional[str] = None


class PoliticaPrivacidadCreate(BaseModel):
    version: str
    fecha_emision: date
    enlace_o_archivo: str
    identifica_gran_escala: bool = True


# ============================================================================
# CONSULTA DE TRATAMIENTOS GRAN ESCALA (RAT SERVICE)
# ============================================================================

async def organizacion_tiene_gran_escala(session: AsyncSession, tenant_id: str) -> tuple[bool, int]:
    """Determina si la organización tiene al menos una actividad calificada a gran escala."""
    actividades = await rat_service.listar_actividades_rat(session, tenant_id)
    # Una actividad es gran escala si tiene la bandera es_gran_escala en True
    gran_escala = [a for a in actividades if getattr(a, "es_gran_escala", False)]
    return len(gran_escala) > 0, len(gran_escala)


# ============================================================================
# CONFIGURACIÓN DE FECHA DE VIGENCIA DE LA NORMA (DISPOSICIÓN TRANSITORIA)
# ============================================================================

async def obtener_fecha_vigencia(session: AsyncSession, tenant_id: str) -> Optional[date]:
    res = await session.execute(
        text("SELECT fecha_vigencia_norma FROM mtge_configuracion_vigencia WHERE tenant_id = :t"),
        {"t": tenant_id},
    )
    fila = res.first()
    return fila[0] if fila else None


async def registrar_fecha_vigencia(
    session: AsyncSession, tenant_id: str, user_id: str, payload: ConfiguracionVigenciaCreate,
) -> date:
    ahora = datetime.now(timezone.utc)
    res = await session.execute(
        text("SELECT tenant_id FROM mtge_configuracion_vigencia WHERE tenant_id = :t"),
        {"t": tenant_id},
    )
    if res.first():
        await session.execute(
            text(
                """
                UPDATE mtge_configuracion_vigencia
                SET fecha_vigencia_norma = :fv, registrado_por = :u, actualizado_en = :ahora
                WHERE tenant_id = :t
                """
            ),
            {"t": tenant_id, "fv": payload.fecha_vigencia_norma, "u": user_id, "ahora": ahora},
        )
    else:
        await session.execute(
            text(
                """
                INSERT INTO mtge_configuracion_vigencia (
                    tenant_id, fecha_vigencia_norma, registrado_por, creado_en, actualizado_en
                ) VALUES (:t, :fv, :u, :ahora, :ahora)
                """
            ),
            {"t": tenant_id, "fv": payload.fecha_vigencia_norma, "u": user_id, "ahora": ahora},
        )

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="mtge_configuracion_vigencia",
        entity_id=tenant_id,
        action="registrar_fecha_vigencia_mtge",
        user_id=user_id,
        payload={"fecha_vigencia_norma": str(payload.fecha_vigencia_norma)},
    )
    return payload.fecha_vigencia_norma


# ============================================================================
# GESTIÓN DE AUDITORÍAS (ART. 17)
# ============================================================================

async def registrar_auditoria(
    session: AsyncSession, tenant_id: str, user_id: str, payload: AuditoriaGranEscalaCreate,
) -> dict:
    """Registra una auditoría anual o certificación equivalente (Art. 17)."""
    aid = f"mtge-aud-{uuid.uuid4().hex[:12]}"
    ahora = datetime.now(timezone.utc)

    # Art. 17: al menos cada 12 meses desde la fecha de la auditoría.
    # Con certificación equivalente vigente, el vencimiento es el de la certificación.
    if payload.es_certificacion_equivalente:
        fecha_vencimiento = payload.certificacion_vigente_hasta
    else:
        fecha_vencimiento = _mas_un_anio(payload.fecha_auditoria)

    await session.execute(
        text(
            """
            INSERT INTO mtge_auditorias (
                id, tenant_id, fecha_auditoria, tipo, alcance, auditor, archivo_informe,
                es_certificacion_equivalente, certificacion_nombre, certificacion_vigente_hasta,
                fecha_vencimiento, creado_por, creado_en
            ) VALUES (
                :id, :t, :fa, :tipo, :alcance, :auditor, :archivo,
                :es_cert, :cert_nom, :cert_hasta, :fv, :u, :ahora
            )
            """
        ),
        {
            "id": aid,
            "t": tenant_id,
            "fa": payload.fecha_auditoria,
            "tipo": payload.tipo,
            "alcance": payload.alcance,
            "auditor": payload.auditor,
            "archivo": payload.archivo_informe,
            "es_cert": payload.es_certificacion_equivalente,
            "cert_nom": payload.certificacion_nombre,
            "cert_hasta": payload.certificacion_vigente_hasta,
            "fv": fecha_vencimiento,
            "u": user_id,
            "ahora": ahora,
        },
    )

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="mtge_auditoria",
        entity_id=aid,
        action="registrar_auditoria_gran_escala",
        user_id=user_id,
        payload={
            "tipo": payload.tipo,
            "fecha_auditoria": str(payload.fecha_auditoria),
            "fecha_vencimiento": str(fecha_vencimiento),
            "es_certificacion_equivalente": payload.es_certificacion_equivalente,
        },
    )

    return {
        "id": aid,
        "tenant_id": tenant_id,
        "fecha_auditoria": payload.fecha_auditoria,
        "fecha_vencimiento": fecha_vencimiento,
        "tipo": payload.tipo,
        "auditor": payload.auditor,
    }


async def listar_auditorias(session: AsyncSession, tenant_id: str) -> list[dict]:
    res = await session.execute(
        text(
            """
            SELECT id, tenant_id, fecha_auditoria, tipo, alcance, auditor, archivo_informe,
                   es_certificacion_equivalente, certificacion_nombre, certificacion_vigente_hasta,
                   fecha_vencimiento, creado_por, creado_en
            FROM mtge_auditorias
            WHERE tenant_id = :t
            ORDER BY fecha_auditoria DESC
            """
        ),
        {"t": tenant_id},
    )
    return [dict(r) for r in res.mappings().all()]


async def eliminar_auditoria(session: AsyncSession, tenant_id: str, auditoria_id: str, user_id: str) -> None:
    """Elimina una auditoría si han pasado al menos 5 años (Art. 17)."""
    res = await session.execute(
        text("SELECT fecha_auditoria FROM mtge_auditorias WHERE id = :id AND tenant_id = :t"),
        {"id": auditoria_id, "t": tenant_id},
    )
    fila = res.first()
    if not fila:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auditoría no encontrada")

    fecha_auditoria = fila[0]
    # Art. 17: el informe de auditoría se conserva 5 años calendario
    limite_5_anios = _fin_conservacion(fecha_auditoria)
    hoy = date.today()

    if hoy < limite_5_anios:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Prohibido eliminar el informe de auditoría antes de cumplirse el plazo de conservación "
                f"obligatorio de 5 años conforme al Art. 17 de la Res. SPDP-SPD-2026-0005-R. "
                f"Conservación obligatoria hasta: {limite_5_anios}."
            ),
        )

    await session.execute(
        text("DELETE FROM mtge_auditorias WHERE id = :id AND tenant_id = :t"),
        {"id": auditoria_id, "t": tenant_id},
    )
    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="mtge_auditoria",
        entity_id=auditoria_id,
        action="eliminar_auditoria_gran_escala",
        user_id=user_id,
        payload={"fecha_auditoria": str(fecha_auditoria)},
    )


# ============================================================================
# GESTIÓN DE INFORMES ANUALES (ART. 18)
# ============================================================================

async def registrar_informe_anual(
    session: AsyncSession, tenant_id: str, user_id: str, payload: InformeAnualCreate,
) -> dict:
    inf_id = f"mtge-inf-{uuid.uuid4().hex[:12]}"
    ahora = datetime.now(timezone.utc)

    await session.execute(
        text(
            """
            INSERT INTO mtge_informes_anuales (
                id, tenant_id, anio, fecha_aprobacion, archivo_informe, observaciones, creado_por, creado_en
            ) VALUES (
                :id, :t, :anio, :fa, :archivo, :obs, :u, :ahora
            )
            """
        ),
        {
            "id": inf_id,
            "t": tenant_id,
            "anio": payload.anio,
            "fa": payload.fecha_aprobacion,
            "archivo": payload.archivo_informe,
            "obs": payload.observaciones,
            "u": user_id,
            "ahora": ahora,
        },
    )

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="mtge_informe_anual",
        entity_id=inf_id,
        action="registrar_informe_anual_cumplimiento",
        user_id=user_id,
        payload={"anio": payload.anio, "fecha_aprobacion": str(payload.fecha_aprobacion)},
    )

    return {
        "id": inf_id,
        "tenant_id": tenant_id,
        "anio": payload.anio,
        "fecha_aprobacion": payload.fecha_aprobacion,
    }


async def listar_informes_anuales(session: AsyncSession, tenant_id: str) -> list[dict]:
    res = await session.execute(
        text(
            """
            SELECT id, tenant_id, anio, fecha_aprobacion, archivo_informe, observaciones, creado_por, creado_en
            FROM mtge_informes_anuales
            WHERE tenant_id = :t
            ORDER BY anio DESC
            """
        ),
        {"t": tenant_id},
    )
    return [dict(r) for r in res.mappings().all()]


async def eliminar_informe_anual(session: AsyncSession, tenant_id: str, informe_id: str, user_id: str) -> None:
    """Elimina un informe anual si han pasado al menos 5 años desde su aprobación (Art. 18)."""
    res = await session.execute(
        text("SELECT fecha_aprobacion, anio FROM mtge_informes_anuales WHERE id = :id AND tenant_id = :t"),
        {"id": informe_id, "t": tenant_id},
    )
    fila = res.first()
    if not fila:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Informe anual no encontrado")

    fecha_aprobacion, anio = fila[0], fila[1]
    # Art. 18: el informe anual de cumplimiento se conserva 5 años calendario
    limite_5_anios = _fin_conservacion(fecha_aprobacion)
    hoy = date.today()

    if hoy < limite_5_anios:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Prohibido eliminar el informe anual de cumplimiento antes de cumplirse el plazo de conservación "
                f"obligatorio de 5 años conforme al Art. 18 de la Res. SPDP-SPD-2026-0005-R. "
                f"Conservación obligatoria hasta: {limite_5_anios}."
            ),
        )

    await session.execute(
        text("DELETE FROM mtge_informes_anuales WHERE id = :id AND tenant_id = :t"),
        {"id": informe_id, "t": tenant_id},
    )
    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="mtge_informe_anual",
        entity_id=informe_id,
        action="eliminar_informe_anual_cumplimiento",
        user_id=user_id,
        payload={"anio": anio, "fecha_aprobacion": str(fecha_aprobacion)},
    )


# ============================================================================
# POLÍTICA DE PRIVACIDAD (ART. 18)
# ============================================================================

async def registrar_politica_privacidad(
    session: AsyncSession, tenant_id: str, user_id: str, payload: PoliticaPrivacidadCreate,
) -> dict:
    pid = f"mtge-pol-{uuid.uuid4().hex[:12]}"
    ahora = datetime.now(timezone.utc)

    await session.execute(
        text(
            """
            INSERT INTO mtge_politica_privacidad (
                id, tenant_id, version, fecha_emision, enlace_o_archivo, identifica_gran_escala, creado_por, creado_en
            ) VALUES (
                :id, :t, :ver, :fe, :link, :id_mtge, :u, :ahora
            )
            """
        ),
        {
            "id": pid,
            "t": tenant_id,
            "ver": payload.version,
            "fe": payload.fecha_emision,
            "link": payload.enlace_o_archivo,
            "id_mtge": payload.identifica_gran_escala,
            "u": user_id,
            "ahora": ahora,
        },
    )

    await registrar_evento(
        session=session,
        tenant_id=tenant_id,
        entity_type="mtge_politica_privacidad",
        entity_id=pid,
        action="registrar_politica_privacidad_mtge",
        user_id=user_id,
        payload={"version": payload.version, "fecha_emision": str(payload.fecha_emision)},
    )

    return {
        "id": pid,
        "tenant_id": tenant_id,
        "version": payload.version,
        "fecha_emision": payload.fecha_emision,
    }


async def listar_politicas_privacidad(session: AsyncSession, tenant_id: str) -> list[dict]:
    res = await session.execute(
        text(
            """
            SELECT id, tenant_id, version, fecha_emision, enlace_o_archivo, identifica_gran_escala, creado_por, creado_en
            FROM mtge_politica_privacidad
            WHERE tenant_id = :t
            ORDER BY fecha_emision DESC
            """
        ),
        {"t": tenant_id},
    )
    return [dict(r) for r in res.mappings().all()]


# ============================================================================
# MOTOR DE VENCIMIENTOS Y ESTADO DE OBLIGACIONES
# ============================================================================

async def calcular_estado_obligaciones(
    session: AsyncSession, tenant_id: str, hoy: Optional[date] = None,
) -> EstadoObligacionesResponse:
    """Calcula el estado consolidado de las obligaciones del tratamiento a gran escala."""
    if hoy is None:
        hoy = date.today()

    tiene_gran_escala, cantidad = await organizacion_tiene_gran_escala(session, tenant_id)
    fecha_vigencia = await obtener_fecha_vigencia(session, tenant_id)

    if not tiene_gran_escala:
        # Si no hay tratamientos a gran escala, todas las obligaciones aplican como NO_APLICA
        return EstadoObligacionesResponse(
            tiene_gran_escala=False,
            cantidad_tratamientos_gran_escala=0,
            fecha_vigencia_norma=fecha_vigencia,
            obligaciones=[
                ResumenObligacion(
                    obligacion="Auditoría periódica (al menos cada 12 meses)",
                    articulo_fuente="Art. 17 Res. SPDP-SPD-2026-0005-R",
                    estado=EstadoObligacion.NO_APLICA,
                    descripcion="No requerida: la organización no opera tratamientos calificados a gran escala.",
                    accion_siguiente="Ninguna requerida.",
                ),
                ResumenObligacion(
                    obligacion="Informe anual de cumplimiento",
                    articulo_fuente="Art. 18 Res. SPDP-SPD-2026-0005-R",
                    estado=EstadoObligacion.NO_APLICA,
                    descripcion="No requerido: la organización no opera tratamientos calificados a gran escala.",
                    accion_siguiente="Ninguna requerida.",
                ),
                ResumenObligacion(
                    obligacion="Identificación de gran escala en Política de Privacidad",
                    articulo_fuente="Art. 18 Res. SPDP-SPD-2026-0005-R",
                    estado=EstadoObligacion.NO_APLICA,
                    descripcion="No requerida: la organización no opera tratamientos calificados a gran escala.",
                    accion_siguiente="Ninguna requerida.",
                ),
                ResumenObligacion(
                    obligacion="Designación y registro de DPO (plazo 90 días)",
                    articulo_fuente="Disposición Transitoria Res. SPDP-SPD-2026-0005-R",
                    estado=EstadoObligacion.NO_APLICA,
                    descripcion="No exigido por causa de tratamiento a gran escala.",
                    accion_siguiente="Ninguna requerida.",
                ),
                ResumenObligacion(
                    obligacion="Privacidad desde el diseño y por defecto",
                    articulo_fuente="Art. 16 Res. SPDP-SPD-2026-0005-R",
                    estado=EstadoObligacion.NO_APLICA,
                    descripcion="Recordatorio general conforme a normativa que expida la SPDP.",
                    accion_siguiente="Monitorear resoluciones de la autoridad.",
                ),
            ],
        )

    # Si hay tratamientos a gran escala, calculamos cada obligación:
    obligaciones: List[ResumenObligacion] = []

    # 1. Auditoría Anual (Art. 17): al menos cada 12 meses
    auditorias = await listar_auditorias(session, tenant_id)
    if not auditorias:
        obligaciones.append(
            ResumenObligacion(
                obligacion="Auditoría periódica (al menos cada 12 meses)",
                articulo_fuente="Art. 17 Res. SPDP-SPD-2026-0005-R",
                estado=EstadoObligacion.VENCIDA,
                descripcion="Sin registro de auditorías ni certificación equivalente en la organización.",
                accion_siguiente="Ejecutar y registrar auditoría interna o externa de inmediato.",
            )
        )
    else:
        # Cuenta el registro que vence más tarde (una certificación puede cubrir más que la última auditoría)
        aud_reciente = max(auditorias, key=lambda a: a["fecha_vencimiento"])
        fv: date = aud_reciente["fecha_vencimiento"]
        dias_restantes = (fv - hoy).days

        if dias_restantes < 0:
            est = EstadoObligacion.VENCIDA
            accion = "Auditoría vencida. Programar auditoría de inmediato."
        elif dias_restantes <= 30:
            est = EstadoObligacion.POR_VENCER
            accion = f"Auditoría próxima a vencer en {dias_restantes} días. Iniciar proceso de auditoría."
        else:
            est = EstadoObligacion.AL_DIA
            accion = f"Al día. Próxima auditoría antes del {fv}."

        tipo_desc = "Certificación equivalente" if aud_reciente["es_certificacion_equivalente"] else "Auditoría periódica"
        obligaciones.append(
            ResumenObligacion(
                obligacion="Auditoría periódica (al menos cada 12 meses)",
                articulo_fuente="Art. 17 Res. SPDP-SPD-2026-0005-R",
                estado=est,
                dias_restantes=dias_restantes,
                fecha_limite=fv,
                descripcion=f"{tipo_desc} registrada con vencimiento el {fv}.",
                accion_siguiente=accion,
            )
        )

    # 2. Informe Anual de Cumplimiento (Art. 18). La resolución no fija en el texto revisado una fecha
    # de presentación: sin el informe del ejercicio anterior el estado es «por vencer», nunca «vencida».
    informes = await listar_informes_anuales(session, tenant_id)
    anio_anterior = hoy.year - 1
    tiene_informe_vigente = any(inf["anio"] >= anio_anterior for inf in informes)
    if tiene_informe_vigente:
        inf_reciente = informes[0]
        obligaciones.append(
            ResumenObligacion(
                obligacion="Informe anual de cumplimiento",
                articulo_fuente="Art. 18 Res. SPDP-SPD-2026-0005-R",
                estado=EstadoObligacion.AL_DIA,
                fecha_limite=None,
                descripcion=f"Informe anual del ejercicio {inf_reciente['anio']} aprobado el {inf_reciente['fecha_aprobacion']}.",
                accion_siguiente="Conservar informe 5 años. Elaborar el informe del ejercicio actual.",
            )
        )
    else:
        obligaciones.append(
            ResumenObligacion(
                obligacion="Informe anual de cumplimiento",
                articulo_fuente="Art. 18 Res. SPDP-SPD-2026-0005-R",
                estado=EstadoObligacion.POR_VENCER,
                descripcion=(
                    f"No se registra informe anual de cumplimiento para el ejercicio {anio_anterior}. "
                    "La resolución no fija una fecha de presentación."
                ),
                accion_siguiente=f"Elaborar y aprobar el informe anual de cumplimiento del ejercicio {anio_anterior}.",
            )
        )

    # 3. Política de Privacidad (Art. 18)
    # Art. 18 Res. SPDP-SPD-2026-0005-R
    politicas = await listar_politicas_privacidad(session, tenant_id)
    if politicas and politicas[0]["identifica_gran_escala"]:
        pol = politicas[0]
        obligaciones.append(
            ResumenObligacion(
                obligacion="Identificación de gran escala en Política de Privacidad",
                articulo_fuente="Art. 18 Res. SPDP-SPD-2026-0005-R",
                estado=EstadoObligacion.AL_DIA,
                fecha_limite=None,
                descripcion=f"Política versión {pol['version']} (emitida {pol['fecha_emision']}) contempla tratamientos a gran escala.",
                accion_siguiente="Mantener actualizada ante cambios en finalidades o categorías.",
            )
        )
    else:
        obligaciones.append(
            ResumenObligacion(
                obligacion="Identificación de gran escala en Política de Privacidad",
                articulo_fuente="Art. 18 Res. SPDP-SPD-2026-0005-R",
                estado=EstadoObligacion.VENCIDA,
                descripcion="No consta registro de que la política de privacidad identifique los tratamientos a gran escala.",
                accion_siguiente="Actualizar la política de privacidad para incluir tratamientos, finalidades y derechos.",
            )
        )

    # 4. Plazo del DPO (Disposición Transitoria): 90 días desde la vigencia registrada por el administrador.
    # Se cumple con la designación formal activa e inscrita ante la SPDP (ORG-06).
    designaciones = await organizacion_service.obtener_informe_estado_designaciones(session, tenant_id)
    dpd = designaciones["dpd"]
    if dpd["designado"] and dpd["inscrito_spdp"]:
        obligaciones.append(
            ResumenObligacion(
                obligacion="Designación y registro de DPO (plazo 90 días)",
                articulo_fuente="Disposición Transitoria Res. SPDP-SPD-2026-0005-R",
                estado=EstadoObligacion.AL_DIA,
                descripcion="Delegado designado formalmente e inscrito ante la SPDP.",
                accion_siguiente="Mantener la designación vigente.",
            )
        )
    elif fecha_vigencia is None:
        obligaciones.append(
            ResumenObligacion(
                obligacion="Designación y registro de DPO (plazo 90 días)",
                articulo_fuente="Disposición Transitoria Res. SPDP-SPD-2026-0005-R",
                estado=EstadoObligacion.FALTA_FECHA_VIGENCIA,
                descripcion="Falta registrar la fecha de vigencia oficial de la resolución en el Registro Oficial.",
                accion_siguiente="El administrador debe registrar la fecha de vigencia oficial en la configuración.",
            )
        )
    else:
        limite_dpo = fecha_vigencia + timedelta(days=90)
        dias_dpo = (limite_dpo - hoy).days
        if dias_dpo < 0:
            est_dpo = EstadoObligacion.VENCIDA
            accion_dpo = "Plazo transitorio de 90 días vencido. Formalizar e inscribir la designación ante la SPDP de inmediato."
        elif dias_dpo <= 30:
            est_dpo = EstadoObligacion.POR_VENCER
            accion_dpo = f"Quedan {dias_dpo} días para formalizar la designación e inscripción del DPO ante la SPDP."
        else:
            est_dpo = EstadoObligacion.AL_DIA
            accion_dpo = f"Plazo vigente hasta el {limite_dpo} ({dias_dpo} días restantes)."

        obligaciones.append(
            ResumenObligacion(
                obligacion="Designación y registro de DPO (plazo 90 días)",
                articulo_fuente="Disposición Transitoria Res. SPDP-SPD-2026-0005-R",
                estado=est_dpo,
                dias_restantes=dias_dpo,
                fecha_limite=limite_dpo,
                descripcion=f"Plazo legal de 90 días contado desde la vigencia registrada ({fecha_vigencia}).",
                accion_siguiente=accion_dpo,
            )
        )

    # 5. Privacidad desde el diseño y por defecto (Art. 16)
    obligaciones.append(
        ResumenObligacion(
            obligacion="Privacidad desde el diseño y por defecto",
            articulo_fuente="Art. 16 Res. SPDP-SPD-2026-0005-R",
            estado=EstadoObligacion.RECORDATORIO,
            descripcion="Obligación permanente antes y durante los tratamientos; la SPDP aún debe expedir la normativa específica.",
            accion_siguiente="Verificar aplicación de medidas preventivas y monitorear directrices de la SPDP.",
        )
    )

    return EstadoObligacionesResponse(
        tiene_gran_escala=True,
        cantidad_tratamientos_gran_escala=cantidad,
        fecha_vigencia_norma=fecha_vigencia,
        obligaciones=obligaciones,
    )
