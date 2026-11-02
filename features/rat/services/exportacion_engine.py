# ¤rat ¤rbac-tenant
"""Exportación del RAT a XLSX y PDF (RAT-06). Contrato: governance/especificaciones/RAT-06.md.

El XLSX es el documento de referencia: su SHA-256 es la huella, y el PDF se genera leyendo esos mismos bytes,
de modo que ambos dicen lo mismo. Sin tablas nuevas. Una columna entra aquí solo si describe el tratamiento:
categorías, nunca registros de titulares (R3). Por eso quedan fuera `observaciones_dpo`, texto libre, y los
identificadores de usuario de las versiones.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from io import BytesIO
from xml.sax.saxutils import escape

from openpyxl import Workbook, load_workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.errores import ErrorNegocio
from features.rat.domain.models import rat_actividades
from features.rat.services.versiones_engine import rat_versiones

MEDIA_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MEDIA_PDF = "application/pdf"
TITULO = "Registro de Actividades de Tratamiento"
SIN_VERSION = "Sin versión"
# Ecuador continental no tiene horario de verano; zoneinfo exige tzdata en Windows.
GUAYAQUIL = timezone(timedelta(hours=-5))

# Columnas fijas (R1), en el orden del RAT: (campo, encabezado).
COLUMNAS: tuple[tuple[str, str], ...] = (
    ("codigo", "Código"),
    ("nombre", "Actividad de tratamiento"),
    ("area_responsable", "Área responsable"),
    ("finalidad", "Finalidad"),
    ("base_legal", "Base de legitimación"),
    ("condicion_habilitante", "Condición habilitante"),
    ("categorias_titulares", "Categorías de titulares"),
    ("categorias_datos", "Categorías de datos"),
    ("datos_sensibles", "Datos sensibles"),
    ("volumen_titulares_estimado", "Titulares estimados"),
    ("volumen_titulares_12_meses", "Titulares en 12 meses"),
    ("medio_soporte", "Medio o soporte"),
    ("encargados", "Encargados"),
    ("destinatarios", "Destinatarios"),
    ("transferencia_internacional", "Transferencia internacional"),
    ("pais_transferencia", "País de transferencia"),
    ("plazo_conservacion", "Plazo de conservación"),
    ("medidas_seguridad", "Medidas de seguridad"),
    ("nivel_riesgo", "Nivel de riesgo"),
    ("decisiones_automatizadas", "Decisiones automatizadas"),
    ("requiere_eipd", "Requiere evaluación de impacto"),
    ("es_gran_escala", "Gran escala"),
    ("version_numero", "Versión"),
    ("version_fecha", "Fecha de la versión"),
)


@dataclass(frozen=True)
class Exportacion:
    contenido: bytes
    media_type: str
    nombre_archivo: str
    huella: str


def celda_segura(valor: str) -> str:
    """Un texto no se ejecuta como fórmula al abrirlo y no lleva caracteres que el XLSX no admite."""
    limpio = ILLEGAL_CHARACTERS_RE.sub("", valor)
    return f"'{limpio}" if limpio.lstrip()[:1] in ("=", "+", "-", "@") else limpio


def nombre_archivo(tenant_id: str, fecha: str, extension: str) -> str:
    """Solo caracteres seguros en una cabecera: el identificador no puede romper Content-Disposition."""
    tenant = re.sub(r"[^A-Za-z0-9_-]+", "-", tenant_id).strip("-")[:60] or "organizacion"
    return f"rat-{tenant}-{fecha}.{extension}"


def _texto(campo: str, valor: object) -> object:
    if campo == "version_numero":
        return SIN_VERSION if valor is None else valor
    if campo == "version_fecha":
        return "" if valor is None else valor.astimezone(GUAYAQUIL).strftime("%Y-%m-%d")
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if isinstance(valor, list):
        return celda_segura("; ".join(str(v) for v in valor))
    if isinstance(valor, int):
        return valor
    return celda_segura("" if valor is None else str(valor))


async def fichas_vigentes(session: AsyncSession, tenant_id: str) -> list[dict]:
    """Fichas sin baja con el número y la fecha de su última versión (RAT-05)."""
    a, v = rat_actividades, rat_versiones
    ultima = (
        select(v.c.tratamiento_id, func.max(v.c.numero).label("numero"))
        .where(v.c.tenant_id == tenant_id)
        .group_by(v.c.tratamiento_id)
        .subquery()
    )
    consulta = (
        select(a, ultima.c.numero.label("version_numero"), v.c.creado_en.label("version_fecha"))
        .select_from(
            a.outerjoin(ultima, ultima.c.tratamiento_id == a.c.id).outerjoin(
                v,
                and_(v.c.tenant_id == a.c.tenant_id, v.c.tratamiento_id == a.c.id, v.c.numero == ultima.c.numero),
            )
        )
        .where(a.c.tenant_id == tenant_id, a.c.deleted_at.is_(None))
        .order_by(a.c.codigo, a.c.id)
    )
    return [dict(f) for f in (await session.execute(consulta)).mappings().all()]


def generar_xlsx(fichas: list[dict]) -> bytes:
    libro = Workbook()
    hoja = libro.active
    hoja.title = "RAT"
    hoja.append([titulo for _, titulo in COLUMNAS])
    for ficha in fichas:
        hoja.append([_texto(campo, ficha[campo]) for campo, _ in COLUMNAS])
    hoja.freeze_panes = "A2"
    salida = BytesIO()
    libro.save(salida)
    return salida.getvalue()


def generar_pdf(xlsx: bytes, huella: str) -> bytes:
    """Una tabla por ficha, porque las columnas no caben a lo ancho. Lee el XLSX, no la base."""
    filas = list(load_workbook(BytesIO(xlsx), read_only=True).active.iter_rows(values_only=True))
    encabezados, fichas = filas[0], filas[1:]
    estilos = getSampleStyleSheet()
    normal = estilos["BodyText"]
    normal.fontSize, normal.leading = 8, 10
    pie = f"Huella SHA-256 del XLSX: {huella}"

    def dibujar_pie(lienzo, documento) -> None:
        lienzo.saveState()
        lienzo.setFont("Helvetica", 7)
        lienzo.drawString(15 * mm, 8 * mm, pie)
        lienzo.drawRightString(A4[0] - 15 * mm, 8 * mm, f"Página {documento.page}")
        lienzo.restoreState()

    contenido = [Paragraph(TITULO, estilos["Title"])]
    for ficha in fichas:
        tabla = Table(
            [
                [Paragraph(escape(str(titulo)), normal), Paragraph(escape("" if valor is None else str(valor)), normal)]
                for titulo, valor in zip(encabezados, ficha)
            ],
            colWidths=[50 * mm, 130 * mm],
        )
        tabla.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.25, "#cccccc")]))
        contenido += [tabla, Spacer(1, 6 * mm)]

    salida = BytesIO()
    SimpleDocTemplate(
        salida, pagesize=A4, title=TITULO, subject=pie, keywords=huella, author="Plataforma LOPDP 360",
        leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm, bottomMargin=15 * mm,
    ).build(contenido, onFirstPage=dibujar_pie, onLaterPages=dibujar_pie)
    return salida.getvalue()


async def exportar_rat(session: AsyncSession, tenant_id: str, formato: str) -> Exportacion:
    fichas = await fichas_vigentes(session, tenant_id)
    if not fichas:
        raise ErrorNegocio("RAT_VACIO")
    xlsx = generar_xlsx(fichas)
    huella = hashlib.sha256(xlsx).hexdigest()
    fecha = datetime.now(GUAYAQUIL).strftime("%Y-%m-%d")
    if formato == "pdf":
        return Exportacion(generar_pdf(xlsx, huella), MEDIA_PDF, nombre_archivo(tenant_id, fecha, "pdf"), huella)
    return Exportacion(xlsx, MEDIA_XLSX, nombre_archivo(tenant_id, fecha, "xlsx"), huella)
