"""DER-06b · Activar los tipos nuevos de solicitud: TIPOS_ACTIVOS y textos de la interfaz.

`¤regulation-code` `¤arbitro`

Contra la PostgreSQL 16 de pruebas migrada (TEST_DATABASE_URL). Valores simulados.
Cada prueba lleva su mutación.
"""
import re
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text

from features.derechos_arco import derechos_arco_service as compuerta
from features.derechos_arco.domain import plazos
from features.derechos_arco.domain.models import TipoSolicitud

RAIZ = Path(__file__).resolve().parents[1]
NUEVOS = ("SUSPENSION", "DECISIONES_AUTOMATIZADAS", "QUEJA")
DATOS = {"cedula_solicitante": "1700000001", "nombre_solicitante": "Titular Simulado"}
MODULO = RAIZ / "frontend/src/components/modules/ArcoModule.tsx"
TIPOS_TS = RAIZ / "frontend/src/types/arco.ts"


async def _tenant(session) -> str:
    tid = f"t-der06b-{uuid.uuid4().hex[:10]}"
    await session.execute(
        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :ruc)"),
        {"t": tid, "ruc": f"RUC{uuid.uuid4().hex[:12]}"},
    )
    return tid


def test_los_ocho_tipos_estan_activos_con_plazo():
    assert plazos.TIPOS_ACTIVOS == frozenset(TipoSolicitud)
    assert len(plazos.TIPOS_ACTIVOS) == 8
    for nombre in NUEVOS:
        assert plazos.plazo_dias(TipoSolicitud(nombre)) == 10


@pytest.mark.parametrize("nombre", NUEVOS)
@pytest.mark.asyncio
async def test_crear_cada_tipo_nuevo_da_fila_y_plazo_de_diez_dias(db_session, nombre):
    tenant = await _tenant(db_session)
    creada = await compuerta.crear_solicitud_arco(db_session, {**DATOS, "tipo_solicitud": nombre}, tenant_id=tenant)
    assert creada.tipo_solicitud == TipoSolicitud(nombre)
    dias = (creada.fecha_vencimiento - creada.fecha_recepcion).days
    assert dias == 10
    total = (await db_session.execute(
        text("SELECT count(*) FROM derechos_arco_solicitudes WHERE tenant_id_texto = :t"), {"t": tenant}
    )).scalar()
    assert total == 1
    await db_session.rollback()


@pytest.mark.parametrize("nombre", NUEVOS)
@pytest.mark.asyncio
async def test_mutacion_tipo_fuera_de_tipos_activos_se_rechaza(db_session, monkeypatch, nombre):
    """Mutación: dejar un tipo fuera de TIPOS_ACTIVOS rompe la creación."""
    tenant = await _tenant(db_session)
    monkeypatch.setattr(compuerta, "TIPOS_ACTIVOS", plazos.TIPOS_ACTIVOS - {TipoSolicitud(nombre)})
    with pytest.raises(compuerta.TipoNoDisponible):
        await compuerta.crear_solicitud_arco(db_session, {**DATOS, "tipo_solicitud": nombre}, tenant_id=tenant)
    await db_session.rollback()


def _lista_ts() -> set[str]:
    bloque = re.search(r"TIPOS_SOLICITUD_API = \[(.*?)\] as const", TIPOS_TS.read_text(encoding="utf-8"), re.S)
    assert bloque
    return set(re.findall(r'"([A-Z_]+)"', bloque.group(1)))


def test_la_lista_de_tipos_del_frontend_coincide_con_el_enum():
    assert _lista_ts() == {t.value for t in TipoSolicitud}
    # Mutación: una lista a la que le falta un tipo no coincide.
    assert _lista_ts() - {"QUEJA"} != {t.value for t in TipoSolicitud}


def test_el_modulo_deriva_el_tipo_local_del_de_types_y_etiqueta_los_nuevos():
    fuente = MODULO.read_text(encoding="utf-8")
    assert 'from "@/types/arco"' in fuente and "type TipoSolicitud = TipoSolicitudApi" in fuente
    for etiqueta in ("Suspensión del tratamiento", "Decisiones automatizadas", "Queja al responsable"):
        assert etiqueta in fuente
    assert "LOPDP, art. 19" in fuente and "LOPDP, art. 20" in fuente
    assert not re.search(r"[\u00a4\u00a6]", fuente)  # marcas de gobernanza, por escape


def _aviso_autoridad(fuente: str) -> str:
    m = re.search(r'AVISO_AUTORIDAD =\s*"([^"]+)"', fuente)
    assert m
    return m.group(1)


def _viola_aviso(texto: str) -> bool:
    return bool(re.search(r"\d|\bdías?\b|\bart(?:ículo|\.)", texto, re.I))


def test_la_interfaz_no_cita_plazo_ni_articulo_para_la_autoridad():
    aviso = _aviso_autoridad(MODULO.read_text(encoding="utf-8"))
    assert "Autoridad de Protección de Datos Personales" in aviso
    assert not _viola_aviso(aviso)
    # Mutación: añadir un plazo al aviso lo hace fallar.
    assert _viola_aviso(aviso + " Tiene 15 días para reclamar.")
    assert _viola_aviso(aviso + " (LOPDP, art. 64)")
