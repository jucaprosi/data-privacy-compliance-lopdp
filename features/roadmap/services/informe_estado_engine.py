"""Informe PDF del estado de una hoja de ruta, generado en el servidor como constancia (RM-20).

Los datos salen de la base de la organización del usuario, nunca del navegador. El alcance depende
del rol: la organización completa para admin_organizacion, coordinador, dpo e implementador; solo
sus áreas para responsable_area. Cada descarga deja en audit_events el SHA-256 del PDF entregado.
"""
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
from uuid import uuid4

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from features.organizacion.organizacion_service import allowed_area_ids
from features.roadmap.services.contexto_tenant import set_session_context

ROLES_ORGANIZACION = {"admin_organizacion", "coordinador", "dpo", "implementador"}

# Dos sentencias fijas y literales (el vigilante test_sin_sql_interpolado no admite SQL armado):
# toda la organización o solo las áreas del responsable.
TAREAS_ORGANIZACION = text("""
    SELECT w.name ola, t.title, t.status, t.priority, a.nombre area, COALESCE(u.nombre, t.owner) owner
    FROM roadmap_tasks t
    JOIN roadmap_waves w ON w.id = t.wave_id
    LEFT JOIN areas a ON a.id = t.area_id AND a.tenant_id = t.tenant_id
    LEFT JOIN users u ON u.id = t.owner
    WHERE w.roadmap_id = :r AND t.tenant_id = :t
    ORDER BY w.sort_order, t.start_date
""")
TAREAS_AREAS = text("""
    SELECT w.name ola, t.title, t.status, t.priority, a.nombre area, COALESCE(u.nombre, t.owner) owner
    FROM roadmap_tasks t
    JOIN roadmap_waves w ON w.id = t.wave_id
    LEFT JOIN areas a ON a.id = t.area_id AND a.tenant_id = t.tenant_id
    LEFT JOIN users u ON u.id = t.owner
    WHERE w.roadmap_id = :r AND t.tenant_id = :t AND t.area_id = ANY(:areas)
    ORDER BY w.sort_order, t.start_date
""")


class _LienzoNumerado(canvas.Canvas):
    """Guarda las páginas para imprimir «Página X de Y» en cada una."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._estados = []

    def showPage(self):
        self._estados.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._estados)
        for numero, estado in enumerate(self._estados, 1):
            self.__dict__.update(estado)
            self.setFont("Helvetica", 8)
            self.drawRightString(A4[0] - 14 * mm, 8 * mm, f"Página {numero} de {total}")
            super().showPage()
        super().save()


def _crear_pdf(constancia: list[tuple[str, str]], tareas: list[dict]) -> bytes:
    salida = BytesIO()
    estilos = getSampleStyleSheet()
    doc = SimpleDocTemplate(salida, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm)
    historia = [Paragraph("Informe del estado de implementación", estilos["Title"])]
    historia += [Paragraph(f"<b>{clave}:</b> {valor}", estilos["BodyText"]) for clave, valor in constancia]
    historia += [Spacer(1, 5 * mm), Paragraph("Tareas", estilos["Heading2"])]
    filas = [["Ola", "Tarea", "Estado", "Prioridad", "Área", "Responsable"]]
    filas += [[t.get(k) or "—" for k in ("ola", "title", "status", "priority", "area", "owner")] for t in tareas]
    tabla = Table(filas, repeatRows=1, colWidths=[22 * mm, 56 * mm, 23 * mm, 21 * mm, 28 * mm, 28 * mm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#26262b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    historia.append(tabla)
    doc.build(historia, canvasmaker=_LienzoNumerado)
    return salida.getvalue()


async def generar_informe_estado(
    session: AsyncSession, tenant_id: str, roadmap_id: str, user_id: str, rol: str,
) -> tuple[bytes, str]:
    await set_session_context(session, tenant_id)
    existe = await session.execute(
        text("SELECT 1 FROM roadmaps WHERE id = :r AND tenant_id = :t"), {"r": roadmap_id, "t": tenant_id}
    )
    if not existe.first():
        raise LookupError("roadmap no encontrado")

    areas = None if rol in ROLES_ORGANIZACION else list(await allowed_area_ids(session, tenant_id, user_id))
    consulta = TAREAS_ORGANIZACION if areas is None else TAREAS_AREAS
    tareas = (await session.execute(
        consulta, {"r": roadmap_id, "t": tenant_id, "areas": areas or []}
    )).mappings().all()

    organizacion = (await session.execute(
        text("SELECT razon_social FROM tenants WHERE id = :t"), {"t": tenant_id}
    )).scalar_one()
    solicitante = (await session.execute(
        text("SELECT nombre FROM users WHERE id = :u"), {"u": user_id}
    )).scalar() or user_id
    if areas is None:
        alcance = "Organización completa"
    else:
        nombres = (await session.execute(
            text("SELECT nombre FROM areas WHERE tenant_id = :t AND id = ANY(:areas) ORDER BY nombre"),
            {"t": tenant_id, "areas": areas},
        )).scalars().all()
        alcance = "Áreas: " + (", ".join(nombres) if nombres else "ninguna asignada")

    informe_id = str(uuid4())
    pdf = _crear_pdf([
        ("Organización", organizacion),
        ("Solicitante", solicitante),
        ("Rol", rol),
        ("Alcance", alcance),
        ("Fecha y hora de corte (UTC)", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")),
        ("Identificador del informe", informe_id),
    ], [dict(t) for t in tareas])
    await registrar_evento(
        session, tenant_id, "roadmap", roadmap_id, "roadmap_report_downloaded", user_id,
        {"rol": rol, "alcance": alcance, "informe_id": informe_id, "sha256": sha256(pdf).hexdigest()},
    )
    await session.commit()
    return pdf, informe_id
