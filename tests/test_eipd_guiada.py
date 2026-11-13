# ¤riesgos-eipd ¤mtge-granescala ¤hallazgos ¤arbitro
# ¤¤qa-engineer
"""Árbitro MTGE-03: EIPD guiada de ocho pasos (governance/especificaciones/MTGE-03.md §5).

Corre como `lopdp_app` contra PostgreSQL 16 local (ARNES_BASE=postgresql_local), en una transacción que se
revierte, con datos sintéticos. La sesión autenticada se simula sustituyendo `get_context`.

Mutaciones documentadas (cada una hace fallar la prueba indicada):
- M1 (spec §5): en `cerrar_eipd` se quita la comprobación de residual alto sin decisión → falla
  `test_eipd_residual_alto_decision` (responde 200 en vez de 409 EIPD_SIN_DECISION).
- M2 (R1): en el paso 1 se acepta `obligatoria = false` aunque MTGE la exija → falla
  `test_eipd_obligatoria_por_mtge`.
- M3 (R1, marca del RAT): `obligatoriedad_legal` deja de mirar `requiere_eipd` → falla
  `test_eipd_obligatoriedad_manual_solo_sube` (la marcada por el RAT nace no obligatoria y admite bajar).
- M4 (R2): `_registrar_puntos` deja de llamar al puerto → falla `test_eipd_incumplimientos_hallazgos`.
- M5 (cerrada no se edita): se quita `AND cerrada_en IS NULL` del UPDATE y la comprobación previa → el
  paso se guarda tras el cierre, la huella deja de coincidir y falla `test_eipd_cerrada_no_se_edita`.
- M6 (RLS): se quita ENABLE ROW LEVEL SECURITY de `eipd` → falla `test_rls_eipd`.
- M8 (custodia falla cerrado): `CustodiaNoDisponible.custodiar` deja de lanzar → falla
  `test_eipd_cierre_falla_cerrado_sin_custodia` (la EIPD quedaría cerrada sin custodia).
- M7 (R2 real): `HallazgosHojaDeRuta` devuelve None sin llamar al pasillo → falla
  `test_eipd_puntos_crean_hallazgos_reales`.
"""
import hashlib
import os
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from api.rbac import get_context
from app_core.db.session import get_session
from app_core.errors import ErrorNegocio
from features.riesgos_mtge import riesgos_mtge_service as sala
from api.routers.eipd_guiada import puerto_custodia
from main import app

PRODUCCION = "ep-late-hall"


# ¤arbitro
def _url() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "")
    if PRODUCCION in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    if not url or os.environ.get("ARNES_BASE") != "postgresql_local":
        pytest.skip("Persistencia MTGE-03 no acreditada: falta PostgreSQL local (ARNES_BASE=postgresql_local)")
    return url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url


_RAT_COLUMNAS = (
    "id, tenant_id, codigo, nombre, area_responsable, finalidad, base_legal, medio_soporte, pais_transferencia, "
    "plazo_conservacion, nivel_riesgo, observaciones_dpo, origen, categorias_titulares, categorias_datos, "
    "encargados, destinatarios, medidas_seguridad, datos_sensibles, transferencia_internacional, requiere_eipd, "
    "es_gran_escala, decisiones_automatizadas, volumen_titulares_estimado, volumen_titulares_12_meses, version"
)


async def _actividad(conexion, tenant: str, gran_escala: bool, requiere: bool) -> str:
    aid = str(uuid4())
    await conexion.execute(text(
        f"INSERT INTO rat_actividades ({_RAT_COLUMNAS}) VALUES (:id, :t, :c, 'Tratamiento sintético', 'Área', 'Fin', "
        "'CONSENTIMIENTO', 'Digital', '', '1 año', 'medio', '', 'manual', '[]', '[]', '[]', '[]', '[]', false, false, :r, :g, "
        "false, 10, 10, 1)"), {"id": aid, "t": tenant, "c": f"RAT-{aid[:6]}", "r": requiere, "g": gran_escala})
    return aid


# ¤arbitro
@pytest_asyncio.fixture
async def mundo():
    engine = create_async_engine(_url(), echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            sufijo = uuid4().hex[:8]
            usuario = f"mtge03-u-{sufijo}"
            t1, t2 = f"mtge03-t1-{sufijo}", f"mtge03-t2-{sufijo}"
            await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:e,'Sintético')"),
                                   {"id": usuario, "e": f"{usuario}@correo.invalid"})
            await conexion.execute(text("INSERT INTO tenants(id,nombre_comercial,razon_social,ruc_identificacion) "
                                        "VALUES (:id,'Org','Org SA',:ruc)"),
                                   [{"id": v, "ruc": f"179{uuid4().int % 10**10:010d}"} for v in (t1, t2)])
            act = {
                "mtge": await _actividad(conexion, t1, True, False),
                "rat": await _actividad(conexion, t1, False, True),
                "libre": await _actividad(conexion, t1, False, False),
                "otra": await _actividad(conexion, t2, True, False),
            }
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as sesion:
                yield conexion, sesion, usuario, t1, t2, act
        finally:
            await transaccion.rollback()
    await engine.dispose()


class _Api:
    def __init__(self, sesion, usuario, tenant, rol="implementador"):
        self.sesion, self.usuario, self.tenant, self.rol = sesion, usuario, tenant, rol
        self.custodia = _CustodiaDoble()

    async def __call__(self, metodo: str, ruta: str, json=None) -> httpx.Response:
        async def sesion_de_prueba():
            yield self.sesion
        app.dependency_overrides[get_session] = sesion_de_prueba
        app.dependency_overrides[puerto_custodia] = lambda: self.custodia
        app.dependency_overrides[get_context] = lambda: {
            "user_id": self.usuario, "tenant_id": self.tenant, "role": self.rol}
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://prueba") as api:
                return await api.request(metodo, f"/api/v1{ruta}", json=json)
        finally:
            app.dependency_overrides.pop(get_session, None)
            app.dependency_overrides.pop(get_context, None)
            app.dependency_overrides.pop(puerto_custodia, None)


class _CustodiaDoble:
    def __init__(self):
        self.custodiados: list[tuple[str, str]] = []

    async def custodiar(self, session, tenant_id, user_id, eipd_id, contenido, sha256):
        assert hashlib.sha256(contenido).hexdigest() == sha256
        self.custodiados.append((eipd_id, sha256))


class _HallazgosDoble:
    def __init__(self):
        self.registrados: list[tuple[str, str]] = []

    async def registrar(self, session, tenant_id, user_id, origen_ref, titulo):
        self.registrados.append((origen_ref, titulo))
        return f"hallazgo-{len(self.registrados)}"


_PASOS_1_A_6 = [
    (1, {"obligatoria": True}),
    (2, {"consulta_titulares": "Encuesta a una muestra de titulares"}),
    (3, {"fases": ["recogida", "uso"], "amenazas": ["acceso_no_autorizado"]}),
    (4, {"necesidad": "El tratamiento es necesario y proporcional"}),
    (5, {"puntos": []}),
    (6, {"riesgo_inherente": "alto", "riesgo_residual": "alto"}),
]


async def _hasta_paso_6(api: _Api, tratamiento_id: str) -> str:
    r = await api("POST", "/eipd", {"tratamiento_id": tratamiento_id})
    assert r.status_code == 201, r.text
    eipd_id = r.json()["id"]
    for n, cuerpo in _PASOS_1_A_6:
        r = await api("PUT", f"/eipd/{eipd_id}/paso/{n}", cuerpo)
        assert r.status_code == 200, r.text
    return eipd_id


@pytest.mark.asyncio
async def test_eipd_obligatoria_por_mtge(mundo):
    _, sesion, usuario, t1, _, act = mundo
    api = _Api(sesion, usuario, t1)
    r = await api("POST", "/eipd", {"tratamiento_id": act["mtge"]})
    assert r.status_code == 201, r.text
    assert r.json()["obligatoria"] is True and r.json()["obligatoria_por_ley"] is True
    r = await api("PUT", f"/eipd/{r.json()['id']}/paso/1", {"obligatoria": False})
    assert r.status_code == 409 and r.json()["code"] == "EIPD_OBLIGATORIA"


@pytest.mark.asyncio
async def test_eipd_obligatoriedad_manual_solo_sube(mundo):
    _, sesion, usuario, t1, _, act = mundo
    api = _Api(sesion, usuario, t1)
    marcada = (await api("POST", "/eipd", {"tratamiento_id": act["rat"]})).json()
    assert marcada["obligatoria"] is True
    assert (await api("PUT", f"/eipd/{marcada['id']}/paso/1", {"obligatoria": False})).status_code == 409
    libre = (await api("POST", "/eipd", {"tratamiento_id": act["libre"]})).json()
    assert libre["obligatoria"] is False
    subida = await api("PUT", f"/eipd/{libre['id']}/paso/1", {"obligatoria": True})
    assert subida.status_code == 200 and subida.json()["obligatoria"] is True


@pytest.mark.asyncio
async def test_eipd_residual_alto_decision(mundo):
    _, sesion, usuario, t1, _, act = mundo
    api = _Api(sesion, usuario, t1)
    eipd_id = await _hasta_paso_6(api, act["mtge"])
    r = await api("POST", f"/eipd/{eipd_id}/cerrar")
    assert r.status_code == 409 and r.json()["code"] == "EIPD_PASO_INCOMPLETO"
    assert (await api("PUT", f"/eipd/{eipd_id}/paso/7", {"decision": None})).status_code == 200
    r = await api("POST", f"/eipd/{eipd_id}/cerrar")
    assert r.status_code == 409 and r.json()["code"] == "EIPD_SIN_DECISION"
    r = await api("PUT", f"/eipd/{eipd_id}/paso/7", {"decision": "medidas", "decision_texto": "Cifrado en reposo"})
    assert r.status_code == 200
    r = await api("POST", f"/eipd/{eipd_id}/cerrar")
    assert r.status_code == 200 and len(r.json()["informe_sha256"]) == 64


@pytest.mark.asyncio
async def test_eipd_decision_exige_justificacion(mundo):
    _, sesion, usuario, t1, _, act = mundo
    api = _Api(sesion, usuario, t1)
    eipd_id = await _hasta_paso_6(api, act["mtge"])
    r = await api("PUT", f"/eipd/{eipd_id}/paso/7", {"decision": "aceptar", "decision_texto": "  "})
    assert r.status_code == 422 and r.json()["code"] == "EIPD_PASO_INVALIDO"


@pytest.mark.asyncio
async def test_eipd_incumplimientos_hallazgos(mundo):
    _, sesion, usuario, t1, _, act = mundo
    eipd = await sala.crear_eipd(sesion, t1, usuario, act["mtge"])
    doble = _HallazgosDoble()
    puntos = {"puntos": ["Sin plazo de conservación definido", "Sin cláusula con el encargado"]}
    resultado = await sala.guardar_paso(sesion, t1, usuario, eipd.id, 5, puntos, hallazgos=doble)
    assert [ref for ref, _ in doble.registrados] == [f"{eipd.id}:1", f"{eipd.id}:2"]
    assert sorted(p.hallazgo_id for p in resultado.puntos) == ["hallazgo-1", "hallazgo-2"]
    # Reenviar la misma lista no duplica puntos ni hallazgos.
    resultado = await sala.guardar_paso(sesion, t1, usuario, eipd.id, 5, puntos, hallazgos=doble)
    assert len(doble.registrados) == 2 and len(resultado.puntos) == 2


@pytest.mark.asyncio
async def test_eipd_cerrada_no_se_edita(mundo):
    _, sesion, usuario, t1, _, act = mundo
    api = _Api(sesion, usuario, t1)
    eipd_id = await _hasta_paso_6(api, act["mtge"])
    await api("PUT", f"/eipd/{eipd_id}/paso/7", {"decision": "aceptar", "decision_texto": "Riesgo asumido"})
    huella = (await api("POST", f"/eipd/{eipd_id}/cerrar")).json()["informe_sha256"]
    r = await api("PUT", f"/eipd/{eipd_id}/paso/4", {"necesidad": "Texto cambiado tras el cierre"})
    assert r.status_code == 409 and r.json()["code"] == "EIPD_CERRADA"
    informe = (await api("GET", f"/eipd/{eipd_id}/informe")).json()
    assert informe["integro"] is True and informe["informe_sha256"] == huella


@pytest.mark.asyncio
async def test_eipd_roles(mundo):
    _, sesion, usuario, t1, _, act = mundo
    assert (await _Api(sesion, usuario, t1, "dpo")("POST", "/eipd", {"tratamiento_id": act["mtge"]})).status_code == 403
    eipd_id = (await _Api(sesion, usuario, t1, "coordinador")("POST", "/eipd", {"tratamiento_id": act["mtge"]})).json()["id"]
    assert (await _Api(sesion, usuario, t1, "dpo")("GET", f"/eipd?tratamiento_id={act['mtge']}")).status_code == 200
    assert (await _Api(sesion, usuario, t1, "coordinador")("POST", f"/eipd/{eipd_id}/cerrar")).status_code == 403


@pytest.mark.asyncio
async def test_rls_eipd(mundo):
    conexion, sesion, usuario, t1, t2, act = mundo
    eipd = await sala.crear_eipd(sesion, t1, usuario, act["mtge"])
    await sala.guardar_paso(sesion, t1, usuario, eipd.id, 5, {"puntos": ["Punto A"]}, hallazgos=_HallazgosDoble())
    await conexion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": t2})
    assert (await conexion.execute(text("SELECT count(*) FROM eipd"))).scalar() == 0
    assert (await conexion.execute(text("SELECT count(*) FROM eipd_incumplimientos"))).scalar() == 0
    with pytest.raises(ErrorNegocio):
        await sala.obtener_eipd(sesion, t2, usuario, eipd.id)
    assert await sala.listar_eipd(sesion, t2, usuario) == []


@pytest.mark.asyncio
async def test_eipd_puntos_crean_hallazgos_reales(mundo):
    conexion, sesion, usuario, t1, _, act = mundo
    api = _Api(sesion, usuario, t1)
    eipd_id = (await api("POST", "/eipd", {"tratamiento_id": act["mtge"]})).json()["id"]
    r = await api("PUT", f"/eipd/{eipd_id}/paso/5", {"puntos": ["Punto uno", "Punto dos"]})
    assert r.status_code == 200, r.text
    assert all(p["hallazgo_id"] for p in r.json()["puntos"])
    await conexion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": t1})
    filas = (await conexion.execute(text(
        "SELECT origen, severidad FROM hallazgos WHERE origen_ref LIKE :r"), {"r": f"{eipd_id}:%"})).all()
    assert sorted(filas) == [("eipd", "alta"), ("eipd", "alta")]


@pytest.mark.asyncio
async def test_eipd_cierre_falla_cerrado_sin_custodia(mundo):
    _, sesion, usuario, t1, _, act = mundo
    api = _Api(sesion, usuario, t1)
    eipd_id = await _hasta_paso_6(api, act["mtge"])
    await api("PUT", f"/eipd/{eipd_id}/paso/7", {"decision": "aceptar", "decision_texto": "Riesgo asumido"})
    api.custodia = sala.CustodiaNoDisponible()
    r = await api("POST", f"/eipd/{eipd_id}/cerrar")
    assert r.status_code == 503 and r.json()["code"] == "EIPD_CUSTODIA_NO_DISPONIBLE"
    assert (await api("GET", f"/eipd/{eipd_id}")).json()["cerrada_en"] is None
    api.custodia = _CustodiaDoble()
    r = await api("POST", f"/eipd/{eipd_id}/cerrar")
    assert r.status_code == 200 and api.custodia.custodiados == [(eipd_id, r.json()["informe_sha256"])]
