"""DER-05 · Plazo por tipo de solicitud: tabla única, unidad estimada y campos en la respuesta.

`¤regulation-code` `¤arbitro`

Sin base de datos: sesión simulada. Valores simulados.
"""
import asyncio
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from api.routers.arco_router import SolicitudARCOSchema
from features.derechos_arco import derechos_arco_service as compuerta
from features.derechos_arco.domain import plazos
from features.derechos_arco.domain.models import TipoSolicitud

RAIZ = Path(__file__).resolve().parents[1]
ESPERADO = {
    "ACCESO": 15,
    "RECTIFICACION": 15,
    "CANCELACION": 15,
    "OPOSICION": 15,
    "PORTABILIDAD": 10,
}


class _SesionSimulada:
    def __init__(self):
        self.agregadas = []

    def add(self, obj):
        self.agregadas.append(obj)

    async def flush(self):
        return None

    async def refresh(self, obj):
        return None


def _crear(tipo: str):
    sesion = _SesionSimulada()
    datos = {"tipo_solicitud": tipo, "cedula_solicitante": "1700000001", "nombre_solicitante": "Titular Simulado"}
    creada = asyncio.run(compuerta.crear_solicitud_arco(sesion, datos, tenant_id="t-der05"))
    return creada


@pytest.mark.parametrize("tipo,dias", sorted(ESPERADO.items()))
def test_a_plazo_y_vencimiento_por_tipo(tipo, dias):
    assert plazos.plazo_dias(TipoSolicitud(tipo)) == dias
    creada = _crear(tipo)
    assert creada.fecha_vencimiento - creada.fecha_recepcion == timedelta(days=dias)


def test_a_la_tabla_cubre_todos_los_tipos_del_enum():
    assert {t.value for t in plazos.PLAZO_POR_TIPO} == {t.value for t in TipoSolicitud}
    assert plazos.UNIDAD == "corridos" and plazos.ESTIMADO is True


def test_b_el_literal_15_solo_vive_en_plazos():
    servicio = (RAIZ / "features/derechos_arco/derechos_arco_service.py").read_text(encoding="utf-8")
    assert not re.search(r"\b15\b", servicio)
    assert "PLAZO_DIAS" not in servicio
    assert re.search(r"\b15\b", (RAIZ / "features/derechos_arco/domain/plazos.py").read_text(encoding="utf-8"))


@pytest.mark.parametrize("tipo,dias", sorted(ESPERADO.items()))
def test_c_la_respuesta_lleva_los_tres_campos(tipo, dias):
    ahora = datetime.now(timezone.utc)
    esquema = SolicitudARCOSchema(
        id=uuid.uuid4(), tenant_id="t-der05", tipo_solicitud=tipo, estado="RECIBIDA",
        cedula_solicitante="1700000001", nombre_solicitante="Titular Simulado",
        fecha_recepcion=ahora, fecha_vencimiento=ahora + timedelta(days=dias),
    )
    cuerpo = esquema.model_dump(mode="json")
    assert cuerpo["plazo_dias"] == dias
    assert cuerpo["plazo_unidad"] == "corridos"
    assert cuerpo["plazo_estimado"] is True


def test_c2_plazo_dias_sale_de_la_fila_no_del_tipo():
    """Una portabilidad creada antes con 15 días muestra 15, no los 10 del tipo."""
    ahora = datetime.now(timezone.utc)
    esquema = SolicitudARCOSchema(
        id=uuid.uuid4(), tenant_id="t-der05", tipo_solicitud="PORTABILIDAD", estado="RECIBIDA",
        cedula_solicitante="1700000001", nombre_solicitante="Titular Simulado",
        fecha_recepcion=ahora, fecha_vencimiento=ahora + timedelta(days=15),
    )
    assert esquema.model_dump(mode="json")["plazo_dias"] == 15
