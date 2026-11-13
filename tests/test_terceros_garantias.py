# ¤hallazgos ¤evidencias ¤arbitro
# ¤¤qa-engineer
"""Árbitro TER-01: hallazgos automáticos de terceros (especificación TER-01 §5).

Reglas puras siempre. La persistencia (hallazgos reales, RLS con lopdp_app) corre contra la base local del
arnés (127.0.0.1 o ARNES_BASE=postgresql_local); una URL remota no la habilita y producción se rechaza.
Datos sintéticos dentro de una transacción que se revierte.

Mutaciones documentadas (cada una hace fallar al menos una prueba):
- M1 · `falta_garantia` devuelve siempre False (se omite R2) ⇒ falla `test_transferencia_sin_garantia`
  y `test_mutacion_omitir_r2_se_detecta` lo comprueba en cada corrida.
- M2 · `decidir` no consulta `existentes` (se pierde R4) ⇒ falla `test_terceros_idempotente`.
- M3 · se quita el cierre (R3) ⇒ falla `test_encargado_sin_contrato`.
- M4 · `transferencias_service` deja de filtrar por tenant y la RLS se desactiva ⇒ falla `test_rls_terceros_garantias`.
"""
import os
import uuid
from datetime import date, timedelta
from urllib.parse import urlparse

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app_core.errors import ErrorNegocio
from features.terceros import terceros_service
from features.terceros.services import garantias_engine as motor

HOY = date(2026, 11, 13)
H_CONTRATO = "a" * 64
H_GARANTIA = "b" * 64


def _t(**kw) -> motor.TerceroGarantias:
    base = dict(id="t1", nombre="Proveedor", rol="ENCARGADO", pais="EC", contrato_sha256=None,
                contrato_vigente_hasta=None, garantia_tipo=None, garantia_sha256=None, criticidad=None,
                proxima_revision=None)
    base.update(kw)
    return motor.TerceroGarantias(**base)


# ------------------------------------------------------------------ dobles de los puertos
class TercerosDoble:
    def __init__(self, *terceros):
        self.filas = {t.id: t for t in terceros}

    async def listar(self):
        return list(self.filas.values())

    async def obtener(self, tercero_id):
        return self.filas.get(tercero_id)

    async def actualizar(self, tercero_id, campos):
        if tercero_id not in self.filas:
            return None
        self.filas[tercero_id] = motor.TerceroGarantias(**(vars(self.filas[tercero_id]) | campos))
        return self.filas[tercero_id]


class HallazgosDoble:
    def __init__(self):
        self.filas: dict[str, motor.HallazgoExistente] = {}
        self.severidad: dict[str, str] = {}

    async def listar(self):
        return list(self.filas.values())

    async def abrir(self, origen_ref, severidad, titulo):
        hid = "h-" + origen_ref
        self.filas[origen_ref] = motor.HallazgoExistente(hid, origen_ref, "abierto")
        self.severidad[origen_ref] = severidad
        return hid

    def _cambiar(self, hid, estado):
        for ref, h in self.filas.items():
            if h.id == hid:
                self.filas[ref] = motor.HallazgoExistente(hid, ref, estado)

    async def reabrir(self, hid):
        self._cambiar(hid, "abierto")

    async def cerrar(self, hid):
        self._cambiar(hid, "cerrado")


class EvidenciasDoble:
    def __init__(self, *huellas):
        self.huellas = set(huellas)

    def existe(self, sha):
        return sha if sha in self.huellas else None


def _abiertos(h: HallazgosDoble) -> dict[str, str]:
    return {ref: h.severidad[ref] for ref, x in h.filas.items() if x.estado != "cerrado"}


# ------------------------------------------------------------------ reglas puras
def test_r1_solo_encargados_y_vencimiento():
    assert motor.falta_contrato(_t(), HOY)
    assert motor.falta_contrato(_t(rol="SUBENCARGADO"), HOY)
    assert not motor.falta_contrato(_t(rol="DESTINATARIO"), HOY)
    assert not motor.falta_contrato(_t(contrato_sha256=H_CONTRATO, contrato_vigente_hasta=HOY), HOY)
    assert motor.falta_contrato(_t(contrato_sha256=H_CONTRATO, contrato_vigente_hasta=HOY - timedelta(days=1)), HOY)


def test_r2_por_pais_y_sin_pais_no_hay_hallazgo_falso():
    assert motor.falta_garantia(_t(pais="US"))
    assert not motor.falta_garantia(_t(pais="US", garantia_sha256=H_GARANTIA))
    assert not motor.falta_garantia(_t(pais="EC"))
    assert not motor.falta_garantia(_t(pais=None))


def test_titulo_no_afirma_incumplimiento():
    titulos = [c.titulo for c, _ in motor.condiciones(_t(pais="US"), HOY)]
    assert any("garantía no registrada" in t for t in titulos)
    assert not any("incumpl" in t.lower() or "ilegal" in t.lower() for t in titulos)


@pytest.mark.asyncio
async def test_encargado_sin_contrato_doble():
    terceros, hallazgos = TercerosDoble(_t()), HallazgosDoble()
    assert await terceros_service.evaluar_terceros(terceros, hallazgos, HOY) == {"hallazgos_creados": 1, "cerrados": 0}
    assert _abiertos(hallazgos) == {"t1:contrato": "alta"}
    entrada = terceros_service.GarantiasEntrada(contrato_sha256=H_CONTRATO, contrato_vigente_hasta=HOY)
    vista = await terceros_service.actualizar_garantias("t1", entrada, terceros, hallazgos,
                                                        EvidenciasDoble(H_CONTRATO), HOY)
    assert vista["hallazgos"] == [] and _abiertos(hallazgos) == {}


@pytest.mark.asyncio
async def test_transferencia_sin_garantia_doble():
    hallazgos = HallazgosDoble()
    await terceros_service.evaluar_terceros(TercerosDoble(_t(rol="DESTINATARIO", pais="US")), hallazgos, HOY)
    assert _abiertos(hallazgos) == {"t1:garantia": "critica"}


@pytest.mark.asyncio
async def test_idempotente_y_reapertura_doble():
    terceros, hallazgos = TercerosDoble(_t(pais="US")), HallazgosDoble()
    assert (await terceros_service.evaluar_terceros(terceros, hallazgos, HOY))["hallazgos_creados"] == 2
    assert await terceros_service.evaluar_terceros(terceros, hallazgos, HOY) == {"hallazgos_creados": 0, "cerrados": 0}
    await terceros.actualizar("t1", {"pais": "EC"})
    assert await terceros_service.evaluar_terceros(terceros, hallazgos, HOY) == {"hallazgos_creados": 0, "cerrados": 1}
    await terceros.actualizar("t1", {"pais": "US"})
    assert await terceros_service.evaluar_terceros(terceros, hallazgos, HOY) == {"hallazgos_creados": 1, "cerrados": 0}
    assert len(hallazgos.filas) == 2  # se reabre el mismo, no se duplica


@pytest.mark.asyncio
async def test_huella_inexistente_es_422():
    entrada = terceros_service.GarantiasEntrada(garantia_sha256=H_GARANTIA)
    with pytest.raises(ErrorNegocio) as exc:
        await terceros_service.actualizar_garantias("t1", entrada, TercerosDoble(_t()), HallazgosDoble(),
                                                    EvidenciasDoble(), HOY)
    assert exc.value.status_code == 422 and "EVIDENCIA_NO_ENCONTRADA" in repr(vars(exc.value))


def test_entrada_rechaza_organizacion_en_el_cuerpo():
    with pytest.raises(Exception):
        terceros_service.GarantiasEntrada(tenant_id="otra")
    with pytest.raises(Exception):
        terceros_service.GarantiasEntrada(pais="ecuador")


@pytest.mark.asyncio
async def test_mutacion_omitir_r2_se_detecta(monkeypatch):
    """M1: sin R2 la transferencia sin garantía no abre hallazgo; la aserción de la prueba lo detecta."""
    monkeypatch.setattr(motor, "falta_garantia", lambda t: False)
    hallazgos = HallazgosDoble()
    await terceros_service.evaluar_terceros(TercerosDoble(_t(rol="DESTINATARIO", pais="US")), hallazgos, HOY)
    assert _abiertos(hallazgos) != {"t1:garantia": "critica"}


# ------------------------------------------------------------------ persistencia (PostgreSQL 16 local)
@pytest_asyncio.fixture
async def db_ter():
    url = os.environ.get("TEST_DATABASE_URL", "")
    if "ep-late-hall" in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    local = (os.environ.get("ARNES_BASE") == "postgresql_local"
             or (urlparse(url).hostname or "") in ("127.0.0.1", "localhost", "::1"))
    if not url or not local:
        pytest.skip("Persistencia pendiente: falta la base local del arnés (PostgreSQL 16 en 127.0.0.1)")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            if not (await conexion.execute(text(
                    "SELECT 1 FROM information_schema.columns WHERE table_name='transferencias_terceros' "
                    "AND column_name='garantia_sha256'"))).scalar():
                pytest.fail("Aplicar la migración de TER-01 solo en la base propia antes de este árbitro", pytrace=False)
            usuario = "ter01-" + uuid.uuid4().hex
            await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:e,'TER-01')"),
                                   {"id": usuario, "e": usuario + "@example.test"})
            orgs = ["ter01-org-" + uuid.uuid4().hex for _ in range(2)]
            for tid in orgs:
                await conexion.execute(text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                    "VALUES (:id, 'Org sintética', 'Org sintética S.A.', :ruc)"), {"id": tid, "ruc": str(uuid.uuid4().int)[:13]})
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as sesion:
                yield sesion, usuario, orgs
        except DBAPIError:
            pytest.fail("Fallo DB TER-01 (detalles de conexión omitidos); comprobar migración y permisos", pytrace=False)
        finally:
            await transaccion.rollback()
    await engine.dispose()


async def _crear(sesion, tenant, usuario, nombre, rol, pais):
    await sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})
    return (await sesion.execute(text(
        "INSERT INTO transferencias_terceros (tenant_id,nombre,rol,pais_destino,nivel_proteccion,clausulas_firmadas,pais) "
        "VALUES (:t,:n,:r,'texto libre','ESTANDAR',false,:p) RETURNING id::text"),
        {"t": tenant, "n": nombre, "r": rol, "p": pais})).scalar()


def _puertos(sesion, tenant, usuario):
    from api.routers import terceros_garantias as r
    return r._Terceros(sesion, tenant, usuario), r._Hallazgos(sesion, tenant, usuario)


async def _abiertos_db(hallazgos) -> dict[str, str]:
    return {h.origen_ref: h.estado for h in await hallazgos.listar() if h.estado != "cerrado"}


@pytest.mark.asyncio
async def test_encargado_sin_contrato(db_ter):
    sesion, usuario, (org, _) = db_ter
    tid = await _crear(sesion, org, usuario, "Nube S.A.", "ENCARGADO", "EC")
    terceros, hallazgos = _puertos(sesion, org, usuario)
    await terceros_service.evaluar_terceros(terceros, hallazgos, HOY)
    from features.roadmap import roadmap_service
    filas = await roadmap_service.listar_hallazgos(sesion, org, usuario, origen="tercero")
    severidades = {h.origen_ref: h.severidad for h in filas}
    assert severidades == {f"{tid}:contrato": "alta"}
    entrada = terceros_service.GarantiasEntrada(contrato_sha256=H_CONTRATO, contrato_vigente_hasta=HOY)
    vista = await terceros_service.actualizar_garantias(tid, entrada, terceros, hallazgos, EvidenciasDoble(H_CONTRATO), HOY)
    assert vista["hallazgos"] == [] and await _abiertos_db(hallazgos) == {}
    assert vista["contrato_vigente_hasta"] == HOY.isoformat()


@pytest.mark.asyncio
async def test_transferencia_sin_garantia(db_ter):
    sesion, usuario, (org, _) = db_ter
    tid = await _crear(sesion, org, usuario, "Datos Globales LLC", "DESTINATARIO", "US")
    terceros, hallazgos = _puertos(sesion, org, usuario)
    await terceros_service.evaluar_terceros(terceros, hallazgos, HOY)
    from features.roadmap import roadmap_service
    filas = await roadmap_service.listar_hallazgos(sesion, org, usuario, origen="tercero")
    assert [(h.origen_ref, h.severidad, h.estado) for h in filas] == [(f"{tid}:garantia", "critica", "abierto")]


@pytest.mark.asyncio
async def test_terceros_idempotente(db_ter):
    sesion, usuario, (org, _) = db_ter
    await _crear(sesion, org, usuario, "Doble S.A.", "ENCARGADO", "US")
    terceros, hallazgos = _puertos(sesion, org, usuario)
    assert (await terceros_service.evaluar_terceros(terceros, hallazgos, HOY))["hallazgos_creados"] == 2
    assert await terceros_service.evaluar_terceros(terceros, hallazgos, HOY) == {"hallazgos_creados": 0, "cerrados": 0}
    assert len(await hallazgos.listar()) == 2


@pytest.mark.asyncio
async def test_rls_terceros_garantias(db_ter):
    sesion, usuario, (org_a, org_b) = db_ter
    await _crear(sesion, org_a, usuario, "Solo de A", "ENCARGADO", "US")
    terceros_a, hallazgos_a = _puertos(sesion, org_a, usuario)
    await terceros_service.evaluar_terceros(terceros_a, hallazgos_a, HOY)
    terceros_b, hallazgos_b = _puertos(sesion, org_b, usuario)
    assert await terceros_b.listar() == [] and await hallazgos_b.listar() == []
    await sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": org_b})
    assert (await sesion.execute(text("SELECT count(*) FROM transferencias_terceros"))).scalar() == 0
    with pytest.raises(DBAPIError):  # WITH CHECK: B no escribe filas de A
        async with sesion.begin_nested():
            await sesion.execute(text(
                "INSERT INTO transferencias_terceros (tenant_id,nombre,rol,pais_destino,nivel_proteccion) "
                "VALUES (:a,'x','ENCARGADO','x','ESTANDAR')"), {"a": org_a})


@pytest.mark.asyncio
async def test_check_de_columnas(db_ter):
    sesion, usuario, (org, _) = db_ter
    tid = await _crear(sesion, org, usuario, "Check S.A.", "ENCARGADO", "EC")
    for sentencia, valor in (
        ("UPDATE transferencias_terceros SET pais = :v WHERE id::text = :i", "ecu"),
        ("UPDATE transferencias_terceros SET garantia_tipo = :v WHERE id::text = :i", "otro"),
        ("UPDATE transferencias_terceros SET criticidad = :v WHERE id::text = :i", "maxima"),
        ("UPDATE transferencias_terceros SET contrato_sha256 = :v WHERE id::text = :i", "x"),
    ):
        with pytest.raises(DBAPIError):
            async with sesion.begin_nested():
                await sesion.execute(text(sentencia), {"v": valor, "i": tid})
