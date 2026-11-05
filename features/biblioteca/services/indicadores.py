# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Indicadores verificables de Biblioteca (BIB-305).

Tres indicadores separados, nunca una cifra única ni un porcentaje global (Doctrina 4,
INV_LOPDP_MULTIDIMENSIONAL_METRICS):

- Acciones verificadas: solo cuenta la última verificación «conforme» de BIB-303. Un documento
  aprobado o enlazado a la acción no la verifica por sí solo: la acción queda «pendiente».
- Documentos pendientes de revisión: estado efectivo del documento (aprobado con revisión vencida
  cuenta como «vencido»).
- Decisiones sin información: impactos editoriales de la organización aún sin decisión (BIB-304).

Cada indicador trae fecha de corte, denominador, conteos por categoría, exclusiones y estados sin
mapear, y permite llegar a los registros de origen con las mismas filas que lo calculan. El porcentaje
se denomina «avance de implementación»: no certifica ni garantiza cumplimiento.
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from features.biblioteca.services.documentos_consulta import contexto

ClaveIndicador = Literal["acciones", "documentos", "decisiones"]
ETIQUETA_AVANCE = "Avance de implementación. No es una certificación ni garantía de cumplimiento."
SIN_MAPEAR = "sin_mapear"

CATEGORIAS: dict[str, tuple[str, ...]] = {
    "acciones": ("verificada", "no_conforme", "pendiente", SIN_MAPEAR),
    "documentos": ("pendiente_revision", "borrador", "aprobado", "vencido", SIN_MAPEAR),
    "decisiones": ("sin_informacion", "decidida", SIN_MAPEAR),
}
TITULOS = {"acciones": "Acciones verificadas", "documentos": "Documentos pendientes de revisión",
           "decisiones": "Decisiones sin información"}
FOCO = {"acciones": "verificada", "documentos": "pendiente_revision", "decisiones": "sin_informacion"}
AVANCE = {"acciones": "verificada", "documentos": "aprobado", "decisiones": "decidida"}
ORIGEN = {"acciones": "biblioteca_verificaciones", "documentos": "biblioteca_documentos",
          "decisiones": "biblioteca_impactos_organizacion"}
EXCLUSIONES_FIJAS = {
    "acciones": "Acciones del plan sin evidencia ni enlace documental: no tienen requisito documental y no "
                "entran en el denominador (Biblioteca no las cuenta).",
}


class Exclusion(BaseModel):
    motivo: str
    cantidad: int | None


class Indicador(BaseModel):
    clave: ClaveIndicador
    titulo: str
    fecha_corte: datetime
    categoria_foco: str
    valor_foco: int
    denominador: int
    conteos: dict[str, int]
    sin_mapear: int
    exclusiones: list[Exclusion]
    avance_implementacion: float | None
    etiqueta_avance: str
    origen: str


class Indicadores(BaseModel):
    fecha_corte: datetime
    etiqueta: str
    indicadores: list[Indicador]


class RegistroOrigen(BaseModel):
    id: str
    categoria: str
    estado_origen: str | None
    descripcion: str
    origen: str


class RegistrosIndicador(BaseModel):
    clave: ClaveIndicador
    categoria: str | None
    fecha_corte: datetime
    registros: list[RegistroOrigen]


# ¤adpa
def clasificar_accion(ultimo_resultado: str | None, documento_aprobado: bool) -> str:
    """Solo una verificación conforme verifica la acción; una aprobación documental no cuenta."""
    del documento_aprobado  # dato del registro de origen, no criterio de verificación
    if ultimo_resultado == "conforme":
        return "verificada"
    if ultimo_resultado == "no_conforme":
        return "no_conforme"
    if ultimo_resultado is None:
        return "pendiente"
    return SIN_MAPEAR


# ¤adpa
def clasificar_documento(estado: str | None) -> str:
    return {"en_revision": "pendiente_revision", "borrador": "borrador", "aprobado": "aprobado",
            "vencido": "vencido"}.get(estado or "", SIN_MAPEAR)


# ¤adpa
def clasificar_decision(decision: str | None) -> str:
    if decision == "pendiente":
        return "sin_informacion"
    if decision in ("actualizar", "no_aplica"):
        return "decidida"
    return SIN_MAPEAR


# ¤adpa
def construir_indicador(clave: ClaveIndicador, registros: Iterable[RegistroOrigen], corte: datetime) -> Indicador:
    """Los estados sin mapear se muestran aparte y no entran en el denominador."""
    conteos = {categoria: 0 for categoria in CATEGORIAS[clave]}
    for registro in registros:
        conteos[registro.categoria] = conteos.get(registro.categoria, 0) + 1
    sin_mapear = conteos[SIN_MAPEAR]
    denominador = sum(conteos.values()) - sin_mapear
    exclusiones = [Exclusion(motivo="Registros con estado sin mapear: se muestran aparte.", cantidad=sin_mapear)]
    if clave in EXCLUSIONES_FIJAS:
        exclusiones.append(Exclusion(motivo=EXCLUSIONES_FIJAS[clave], cantidad=None))
    avance = round(100 * conteos[AVANCE[clave]] / denominador, 1) if denominador else None
    return Indicador(clave=clave, titulo=TITULOS[clave], fecha_corte=corte, categoria_foco=FOCO[clave],
                     valor_foco=conteos[FOCO[clave]], denominador=denominador, conteos=conteos,
                     sin_mapear=sin_mapear, exclusiones=exclusiones, avance_implementacion=avance,
                     etiqueta_avance=ETIQUETA_AVANCE, origen=ORIGEN[clave])


async def _acciones(session: AsyncSession, tenant_id: str) -> list[RegistroOrigen]:
    filas = (await session.execute(text(
        "SELECT a.accion_id, (SELECT v.resultado FROM biblioteca_verificaciones v WHERE v.tenant_id=:t "
        "AND v.accion_id=a.accion_id ORDER BY v.creado_en DESC, v.secuencia DESC LIMIT 1) AS ultimo, "
        "EXISTS (SELECT 1 FROM biblioteca_revision_acciones r JOIN biblioteca_documentos d "
        "ON d.id=r.documento_id AND d.tenant_id=r.tenant_id WHERE r.tenant_id=:t AND r.accion_id=a.accion_id "
        "AND d.estado='aprobado') AS aprobado "
        "FROM (SELECT accion_id FROM biblioteca_evidencias WHERE tenant_id=:t UNION "
        "SELECT accion_id FROM biblioteca_revision_acciones WHERE tenant_id=:t) a ORDER BY a.accion_id"
    ), {"t": tenant_id})).mappings().all()
    return [RegistroOrigen(
        id=f["accion_id"], categoria=clasificar_accion(f["ultimo"], bool(f["aprobado"])),
        estado_origen=f["ultimo"],
        descripcion="Documento enlazado aprobado; falta verificación" if f["aprobado"] and f["ultimo"] is None
        else "Acción con requisito documental", origen=ORIGEN["acciones"]) for f in filas]


async def _documentos(session: AsyncSession, tenant_id: str, hoy: date) -> list[RegistroOrigen]:
    filas = (await session.execute(text(
        "SELECT id, nombre, CASE WHEN estado='aprobado' AND proxima_revision < :hoy THEN 'vencido' "
        "ELSE estado END AS estado FROM biblioteca_documentos WHERE tenant_id=:t ORDER BY nombre, id"
    ), {"t": tenant_id, "hoy": hoy})).mappings().all()
    return [RegistroOrigen(id=f["id"], categoria=clasificar_documento(f["estado"]), estado_origen=f["estado"],
                           descripcion=f["nombre"], origen=ORIGEN["documentos"]) for f in filas]


async def _decisiones(session: AsyncSession, tenant_id: str) -> list[RegistroOrigen]:
    filas = (await session.execute(text(
        "SELECT o.id, o.decision, i.codigo FROM biblioteca_impactos_organizacion o "
        "JOIN biblioteca_impactos i ON i.id=o.impacto_id WHERE o.tenant_id=:t ORDER BY o.creado_en, o.id"
    ), {"t": tenant_id})).mappings().all()
    return [RegistroOrigen(id=f["id"], categoria=clasificar_decision(f["decision"]), estado_origen=f["decision"],
                           descripcion=f"Actualización de {f['codigo']}", origen=ORIGEN["decisiones"]) for f in filas]


async def _registros(session: AsyncSession, tenant_id: str, clave: str, hoy: date) -> list[RegistroOrigen]:
    if clave == "acciones":
        return await _acciones(session, tenant_id)
    if clave == "documentos":
        return await _documentos(session, tenant_id, hoy)
    return await _decisiones(session, tenant_id)


async def calcular_indicadores(session: AsyncSession, tenant_id: str, actor: str) -> Indicadores:
    await contexto(session, tenant_id, actor)
    corte = datetime.now(timezone.utc)
    indicadores = [construir_indicador(clave, await _registros(session, tenant_id, clave, corte.date()), corte)
                   for clave in CATEGORIAS]
    return Indicadores(fecha_corte=corte, etiqueta=ETIQUETA_AVANCE, indicadores=indicadores)


async def registros_de_indicador(
    session: AsyncSession, tenant_id: str, actor: str, clave: str, categoria: str | None = None
) -> RegistrosIndicador:
    """Drill-down: las mismas filas que calculan el indicador, filtradas por categoría."""
    if clave not in CATEGORIAS:
        raise ErrorNegocio("BIB_INDICADOR_DESCONOCIDO")
    if categoria is not None and categoria not in CATEGORIAS[clave]:
        raise ErrorNegocio("BIB_INDICADOR_CATEGORIA_INVALIDA")
    await contexto(session, tenant_id, actor)
    corte = datetime.now(timezone.utc)
    registros = await _registros(session, tenant_id, clave, corte.date())
    if categoria is not None:
        registros = [r for r in registros if r.categoria == categoria]
    return RegistrosIndicador(clave=clave, categoria=categoria, fecha_corte=corte, registros=registros)
