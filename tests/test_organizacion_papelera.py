# ¤rbac-tenant
# ¤seguridad
# ¤arbitro
"""Árbitro de ORG-20: papelera (archivar y restaurar) y exportación completa de la organización.

Valida (contrato: governance/especificaciones/ORG-20.md):
1. Restaurar devuelve el registro retirado y nada se borra físicamente (`test_papelera_restaura`).
2. `lopdp_app` no gana ningún DELETE sobre las tablas de ORG-20 y el conjunto de tablas con DELETE no crece
   (`test_sin_delete`).
3. La exportación trae el manifiesto, una entrada por entidad con datos y la huella del archivo
   (`test_exportacion_completa`); declara lo que no incluye y no se llama completa.
4. RLS de `exportaciones` con `lopdp_app` (`test_rls_exportaciones`).
5. La exportación completa no saca ningún dato de otra organización, con dos organizaciones sembradas, tanto
   con `lopdp_app` (RLS) como con el dueño de la base (solo el filtro de `tenant_id`).
6. 409 EXPORTACION_EN_CURSO, 410 EXPORTACION_CADUCADA, almacén cerrado y R4.

Las pruebas de integración necesitan TEST_DATABASE_URL (PostgreSQL 16 local, 127.0.0.1, rol dueño) y se omiten
sin ella. Datos ficticios: correos con el dominio reservado .invalid.

Mutaciones documentadas:
- En `papelera_engine.restaurar`/retiro, sustituir el retiro por un DELETE físico: `test_papelera_restaura` falla
  (la fila retirada ya no existe).
- En `exportacion_engine._leer_entidad`, quitar `WHERE tenant_id = :t`: `test_exportacion_sin_datos_de_otra_organizacion`
  falla en la variante del dueño de la base (sin RLS), que es la que prueba el filtro por sí solo.
"""
from __future__ import annotations

import io
import json
import os
import uuid
import zipfile
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.routers import organizacion_papelera as router_papelera
from app_core.db.session import get_session
from app_core.errors import ErrorNegocio
from features.organizacion import organizacion_service as sala
from main import app

RUTA = "/api/v1/organizacion"
# Tablas con DELETE para lopdp_app antes de ORG-20: otras salas, fuera de la propiedad de esta ficha.
DELETE_PREEXISTENTE = {
    "task_dependencies", "roadmaps", "roadmap_waves", "user_tenant_roles", "areas", "mtge_auditorias",
    "mtge_informes_anuales", "mtge_politica_privacidad", "roadmap_tasks", "biblioteca_revision_acciones",
    "biblioteca_vinculos", "evidencias_vinculos", "inventario_activos_tratamientos", "task_evidence",
}


class AlmacenDoble:
    """Doble del puerto de almacén: guarda en memoria."""

    def __init__(self) -> None:
        self.objetos: dict[str, bytes] = {}

    async def subir(self, tenant_id: str, clave: str, contenido: bytes) -> None:
        self.objetos[clave] = contenido

    async def leer(self, tenant_id: str, clave: str) -> bytes:
        return self.objetos[clave]


def _adm(tenant_id: str) -> str:
    return f"u20adm{tenant_id[-13:]}"


def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Sin TEST_DATABASE_URL: la parte de BD de ORG-20 queda no verificada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def factory():
    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    yield async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    await engine.dispose()


_SQL_LIMPIEZA = (
    "DELETE FROM exportaciones WHERE tenant_id IN (:a, :b)",
    "DELETE FROM inventario_activos WHERE tenant_id IN (:a, :b)",
    "DELETE FROM clientes_encargo WHERE tenant_id IN (:a, :b)",
    "DELETE FROM sedes WHERE tenant_id IN (:a, :b)",
    "DELETE FROM audit_events WHERE tenant_id IN (:a, :b)",
    "DELETE FROM user_tenant_roles WHERE tenant_id IN (:a, :b)",
)


@pytest_asyncio.fixture
async def dos_organizaciones(factory):
    """A y B con datos distinguibles en sedes, clientes, inventario y exportaciones."""
    sufijo = uuid.uuid4().hex[:8]
    ta, tb = f"t20a-{sufijo}", f"t20b-{sufijo}"
    ids = {"a": ta, "b": tb}
    async with factory() as s:
        for tid, rol in ((ta, "ambos"), (tb, "responsable")):
            await s.execute(
                text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, rol_datos) "
                     "VALUES (:id, :nom, :razon, :ruc, :rol)"),
                {"id": tid, "nom": f"Org {tid}", "razon": f"Org Ficticia {tid} S.A.", "ruc": f"RUC{tid[:10]}", "rol": rol},
            )
            await s.execute(
                text("INSERT INTO sedes (id, tenant_id, nombre, direccion, ciudad, provincia, creado_por) "
                     "VALUES (:id, :t, :n, 'Calle Ficticia 1', 'Ciudad', 'Provincia', 'u')"),
                {"id": f"sede-{tid}", "t": tid, "n": f"MARCA-SEDE-{tid}"},
            )
            await s.execute(
                text("INSERT INTO sedes (id, tenant_id, nombre, direccion, ciudad, provincia, creado_por, retirada_en) "
                     "VALUES (:id, :t, :n, 'Calle Ficticia 2', 'Ciudad', 'Provincia', 'u', now())"),
                {"id": f"sedeR-{tid}", "t": tid, "n": f"MARCA-RETIRADA-{tid}"},
            )
            await s.execute(
                text("INSERT INTO clientes_encargo (id, tenant_id, razon_social, ruc, creado_por, retirado_en) "
                     "VALUES (:id, :t, :n, :ruc, 'u', now())"),
                {"id": f"cli-{tid}", "t": tid, "n": f"MARCA-CLIENTE-{tid}", "ruc": f"179{uuid.uuid4().int % 10**10:010d}"},
            )
            await s.execute(
                text("INSERT INTO inventario_activos (id, tenant_id, tipo, nombre, created_by) "
                     "VALUES (:id, :t, 'sistema', :n, 'u')"),
                {"id": f"act-{tid}", "t": tid, "n": f"MARCA-ACTIVO-{tid}"},
            )
        for rol, tid in (("admin_organizacion", ta), ("implementador", ta), ("dpo", ta), ("admin_organizacion", tb)):
            uid = f"u20{rol[:3]}{tid[-13:]}"
            await s.execute(
                text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, :n)"),
                {"id": uid, "e": f"{uid}@organizacion.invalid", "n": f"Usuario ficticio {uid}"},
            )
            await s.execute(
                text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, :r)"),
                {"id": f"r20-{uuid.uuid4().hex[:10]}", "u": uid, "t": tid, "r": rol},
            )
        await s.commit()

    yield {"ta": ta, "tb": tb, "admin": f"u20adm{ta[-13:]}", "badmin": f"u20adm{tb[-13:]}"}

    async with factory() as s:
        for sentencia in _SQL_LIMPIEZA:
            await s.execute(text(sentencia), ids)
        await s.execute(text("DELETE FROM users WHERE id LIKE 'u20%' AND email LIKE '%@organizacion.invalid'"))
        await s.execute(text("DELETE FROM tenants WHERE id IN (:a, :b)"), ids)
        await s.commit()


async def _como_app(factory, tenant_id: str):
    """Sesión con el rol de la aplicación (RLS forzada) dentro de una transacción abierta."""
    s = factory()
    sesion = await s.__aenter__()
    await sesion.execute(text("SET LOCAL ROLE lopdp_app"))
    return s, sesion


async def _generar(factory, tenant_id: str, almacen: AlmacenDoble, como_app: bool = False) -> tuple[str, bytes]:
    async with factory() as s:
        if como_app:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
        export_id = (await sala.solicitar_exportacion(s, tenant_id, _adm(tenant_id)))["id"]
        await sala.generar_exportacion(s, tenant_id, _adm(tenant_id), export_id, almacen)
        await s.commit()
    async with factory() as s:
        clave = f"exportaciones/{tenant_id}/{export_id}.zip"
        return export_id, almacen.objetos[clave]


def _entradas(zip_bytes: bytes) -> dict[str, str]:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        return {n: z.read(n).decode("utf-8") for n in z.namelist()}


# ------------------------------------------------------------------------------- papelera

@pytest.mark.asyncio
async def test_papelera_restaura(factory, dos_organizaciones):
    o = dos_organizaciones
    ta = o["ta"]
    async with factory() as s:
        listada = (await sala.listar_papelera(s, ta))["registros"]
        assert {r["id"] for r in listada} == {f"sedeR-{ta}", f"cli-{ta}"}
        assert all(r["id"].endswith(ta) for r in listada)  # nada de B
        await sala.restaurar_de_papelera(s, ta, _adm(ta), "sedes", f"sedeR-{ta}")
        await sala.restaurar_de_papelera(s, ta, _adm(ta), "clientes", f"cli-{ta}")
        await s.commit()
    async with factory() as s:
        assert (await sala.listar_papelera(s, ta))["registros"] == []
        activa = (await s.execute(
            text("SELECT retirada_en FROM sedes WHERE id = :id"), {"id": f"sedeR-{ta}"})).first()
        assert activa is not None and activa[0] is None  # sigue existiendo y vuelve a estar activa
        # La de B no se tocó.
        assert (await sala.listar_papelera(s, o["tb"]))["registros"] != []


@pytest.mark.asyncio
async def test_restaurar_de_otra_organizacion_o_entidad_desconocida_falla(factory, dos_organizaciones):
    o = dos_organizaciones
    async with factory() as s:
        with pytest.raises(ErrorNegocio) as ajeno:
            await sala.restaurar_de_papelera(s, o["ta"], _adm(o["ta"]), "sedes", f"sedeR-{o['tb']}")
        assert ajeno.value.code == "PAPELERA_ELEMENTO_NO_ENCONTRADO"
        with pytest.raises(ErrorNegocio) as raro:
            await sala.restaurar_de_papelera(s, o["ta"], _adm(o["ta"]), "usuarios; DROP TABLE sedes", "x")
        assert raro.value.code == "PAPELERA_ENTIDAD_DESCONOCIDA"
        await s.rollback()


@pytest.mark.asyncio
async def test_sin_delete(factory):
    async with factory() as s:
        filas = (await s.execute(text(
            "SELECT DISTINCT table_name FROM information_schema.role_table_grants "
            "WHERE grantee = 'lopdp_app' AND privilege_type = 'DELETE' AND table_schema = 'public'"))).scalars().all()
    con_delete = set(filas)
    propias = {"exportaciones", "sedes", "clientes_encargo"}
    assert not (con_delete & propias), "lopdp_app no debe poder borrar las tablas de ORG-20"
    assert con_delete <= DELETE_PREEXISTENTE, f"Nuevos DELETE para lopdp_app: {sorted(con_delete - DELETE_PREEXISTENTE)}"


# ----------------------------------------------------------------------------- exportación

@pytest.mark.asyncio
async def test_exportacion_completa(factory, dos_organizaciones):
    ta = dos_organizaciones["ta"]
    almacen = AlmacenDoble()
    export_id, contenido = await _generar(factory, ta, almacen)
    entradas = _entradas(contenido)
    assert "MANIFIESTO.sha256" in entradas
    manifiesto = json.loads(entradas["MANIFIESTO.sha256"])
    for entidad in ("sedes", "clientes_encargo", "inventario_activos"):
        assert f"{entidad}.json" in entradas and entidad in manifiesto["incluidas"]
    assert set(manifiesto["entradas"]) == set(entradas) - {"MANIFIESTO.sha256"}
    # Lo que no se incluye se declara, y la exportación no se llama completa.
    assert manifiesto["no_incluidas"] and manifiesto["completa"] is False
    async with factory() as s:
        fila = (await s.execute(
            text("SELECT estado, sha256, completa, caduca_en, lista_en FROM exportaciones WHERE id = :i"),
            {"i": export_id})).mappings().one()
        assert fila["estado"] == "lista" and fila["completa"] is False
        import hashlib
        assert fila["sha256"] == hashlib.sha256(contenido).hexdigest()
        assert timedelta(days=6, hours=23) < fila["caduca_en"] - fila["lista_en"] <= timedelta(days=7, minutes=1)
        eventos = (await s.execute(
            text("SELECT action FROM audit_events WHERE tenant_id = :t AND entity_id = :i"),
            {"t": ta, "i": export_id})).scalars().all()
        assert "exportacion_generada" in eventos
        estado = await sala.consultar_exportacion(s, ta, export_id)
        assert estado["estado"] == "lista" and estado["sha256"] == fila["sha256"] and estado["url"]


@pytest.mark.asyncio
@pytest.mark.parametrize("como_app", [False, True], ids=["dueño_solo_filtro", "lopdp_app_con_rls"])
async def test_exportacion_sin_datos_de_otra_organizacion(factory, dos_organizaciones, como_app):
    """Con dos organizaciones sembradas, la exportación de A no contiene ni un dato de B.

    Con el dueño de la base (superusuario: sin RLS) la única defensa es el filtro `tenant_id`: esa variante
    es la que se pone en rojo al quitarlo. Con `lopdp_app` se prueba además la RLS.
    """
    o = dos_organizaciones
    almacen = AlmacenDoble()
    _, contenido = await _generar(factory, o["ta"], almacen, como_app=como_app)
    texto = "\n".join(_entradas(contenido).values())
    assert o["ta"] in texto and f"MARCA-SEDE-{o['ta']}" in texto
    assert o["tb"] not in texto
    for marca in ("MARCA-SEDE", "MARCA-RETIRADA", "MARCA-CLIENTE", "MARCA-ACTIVO"):
        assert f"{marca}-{o['tb']}" not in texto
    # Cada fila exportada lleva el tenant de A.
    for nombre, cuerpo in _entradas(contenido).items():
        if nombre.endswith(".json") and nombre != "MANIFIESTO.sha256":
            assert all(f.get("tenant_id", o["ta"]) == o["ta"] for f in json.loads(cuerpo))


@pytest.mark.asyncio
async def test_rls_exportaciones(factory, dos_organizaciones):
    o = dos_organizaciones
    await _generar(factory, o["ta"], AlmacenDoble())
    async with factory() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await sala.listar_papelera(s, o["tb"])  # fija el contexto de B
        vistas_por_b = (await s.execute(text("SELECT count(*) FROM exportaciones"))).scalar_one()
        assert vistas_por_b == 0
        await s.rollback()
    async with factory() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await sala.listar_papelera(s, o["ta"])
        assert (await s.execute(text("SELECT count(*) FROM exportaciones"))).scalar_one() == 1
        await s.rollback()


@pytest.mark.asyncio
async def test_exportacion_en_curso_caducada_y_almacen_cerrado(factory, dos_organizaciones):
    ta = dos_organizaciones["ta"]
    async with factory() as s:
        primera = (await sala.solicitar_exportacion(s, ta, _adm(ta)))["id"]
        with pytest.raises(ErrorNegocio) as en_curso:
            await sala.solicitar_exportacion(s, ta, _adm(ta))
        assert en_curso.value.code == "EXPORTACION_EN_CURSO" and en_curso.value.status_code == 409
        # Sin adaptador real (EVI-04) el almacén falla cerrado.
        with pytest.raises(ErrorNegocio) as cerrado:
            await sala.generar_exportacion(s, ta, _adm(ta), primera, sala.AlmacenNoDisponible())
        assert cerrado.value.code == "ALMACEN_EXPORTACION_NO_DISPONIBLE"
        await s.rollback()
    async with factory() as s:
        # Caducidad: una exportación lista cuyo enlace venció responde 410 y pasa a caducada.
        almacen = AlmacenDoble()
        export_id = (await sala.solicitar_exportacion(s, ta, _adm(ta)))["id"]
        await sala.generar_exportacion(s, ta, _adm(ta), export_id, almacen)
        assert len(await sala.descargar_exportacion(s, ta, _adm(ta), export_id, almacen)) > 0
        await s.execute(text("UPDATE exportaciones SET caduca_en = :c WHERE id = :i"),
                        {"c": datetime.now(timezone.utc) - timedelta(minutes=1), "i": export_id})
        with pytest.raises(ErrorNegocio) as caducada:
            await sala.descargar_exportacion(s, ta, _adm(ta), export_id, almacen)
        assert caducada.value.code == "EXPORTACION_CADUCADA" and caducada.value.status_code == 410
        assert (await sala.consultar_exportacion(s, ta, export_id))["estado"] == "caducada"
        await s.rollback()


@pytest.mark.asyncio
async def test_cierre_exige_exportacion_completa_y_reciente(factory, dos_organizaciones):
    ta = dos_organizaciones["ta"]
    almacen = AlmacenDoble()
    async with factory() as s:
        with pytest.raises(ErrorNegocio) as sin_nada:
            await sala.exigir_exportacion_para_cierre(s, ta)
        assert sin_nada.value.code == "EXPORTACION_INCOMPLETA"
        export_id = (await sala.solicitar_exportacion(s, ta, _adm(ta)))["id"]
        await sala.generar_exportacion(s, ta, _adm(ta), export_id, almacen)
        # Con entidades no incluidas la exportación no es completa: no habilita el cierre.
        with pytest.raises(ErrorNegocio):
            await sala.exigir_exportacion_para_cierre(s, ta)
        await s.execute(text("UPDATE exportaciones SET completa = true WHERE id = :i"), {"i": export_id})
        assert await sala.exigir_exportacion_para_cierre(s, ta) == export_id
        await s.execute(text("UPDATE exportaciones SET lista_en = now() - interval '31 days' WHERE id = :i"),
                        {"i": export_id})
        with pytest.raises(ErrorNegocio):
            await sala.exigir_exportacion_para_cierre(s, ta)
        await s.rollback()


# ------------------------------------------------------------------------------------ HTTP

def _cab(tenant: str, rol: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-User-ID": f"u20{rol[:3]}{tenant[-13:]}", "X-Role": rol}


@pytest_asyncio.fixture
async def cliente_http(factory, monkeypatch):
    async def _sesion():
        async with factory() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    async def _sin_fondo(*args, **kwargs):
        return None

    guardado = dict(app.dependency_overrides)
    app.dependency_overrides[get_session] = _sesion
    app.dependency_overrides[router_papelera.almacen_exportaciones] = AlmacenDoble
    monkeypatch.setattr(sala, "generar_exportacion_en_segundo_plano", _sin_fondo)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    app.dependency_overrides.update(guardado)


@pytest.mark.asyncio
async def test_http_roles_y_estados(cliente_http, dos_organizaciones):
    ta = dos_organizaciones["ta"]
    c = cliente_http
    # Roles: el implementador usa la papelera pero no exporta; el dpo no entra a ninguna.
    assert (await c.get(f"{RUTA}/papelera", headers=_cab(ta, "implementador"))).status_code == 200
    assert (await c.post(f"{RUTA}/exportaciones", headers=_cab(ta, "implementador"))).status_code == 403
    assert (await c.get(f"{RUTA}/papelera", headers=_cab(ta, "dpo"))).status_code == 403
    papelera = (await c.get(f"{RUTA}/papelera?entidad=sedes", headers=_cab(ta, "admin_organizacion"))).json()
    assert [r["entidad"] for r in papelera["registros"]] == ["sedes"]
    assert (await c.get(f"{RUTA}/papelera?entidad=nada", headers=_cab(ta, "admin_organizacion"))).status_code == 404
    # Exportación: 202 y luego 409 mientras haya una pendiente.
    creada = await c.post(f"{RUTA}/exportaciones", headers=_cab(ta, "admin_organizacion"))
    assert creada.status_code == 202
    otra = await c.post(f"{RUTA}/exportaciones", headers=_cab(ta, "admin_organizacion"))
    assert otra.status_code == 409 and "EXPORTACION_EN_CURSO" in otra.text
    export_id = creada.json()["id"]
    estado = (await c.get(f"{RUTA}/exportaciones/{export_id}", headers=_cab(ta, "admin_organizacion"))).json()
    assert estado["estado"] == "pendiente" and "url" not in estado
    # Otra organización no la ve.
    assert (await c.get(f"{RUTA}/exportaciones/{export_id}",
                        headers=_cab(dos_organizaciones["tb"], "admin_organizacion"))).status_code == 404
    # Restaurar por HTTP.
    restaurada = await c.post(f"{RUTA}/papelera/sedes/sedeR-{ta}/restaurar", headers=_cab(ta, "admin_organizacion"))
    assert restaurada.status_code == 200


@pytest.mark.asyncio
async def test_http_archivar_papelera_restaurar_y_aislamiento(cliente_http, dos_organizaciones):
    """De punta a punta: retirar una sede (ruta de ORG-18) la lleva a la papelera y restaurarla la devuelve.

    Contraria: lo que retira la organización A no aparece en la papelera de B ni se restaura desde B.
    """
    ta, tb = dos_organizaciones["ta"], dos_organizaciones["tb"]
    c = cliente_http
    adm_a, adm_b = _cab(ta, "admin_organizacion"), _cab(tb, "admin_organizacion")
    sede = f"sede-{ta}"

    def ids(respuesta) -> set[str]:
        return {r["id"] for r in respuesta.json()["registros"]}

    assert sede not in ids(await c.get(f"{RUTA}/papelera", headers=adm_a))
    retirada = await c.post(f"{RUTA}/sedes/{sede}/retirar", headers=adm_a)
    assert retirada.status_code == 200, retirada.text
    assert sede in ids(await c.get(f"{RUTA}/papelera", headers=adm_a))

    # B no la ve ni la puede restaurar; en A sigue retirada.
    assert sede not in ids(await c.get(f"{RUTA}/papelera", headers=adm_b))
    assert (await c.post(f"{RUTA}/papelera/sedes/{sede}/restaurar", headers=adm_b)).status_code == 404
    assert sede in ids(await c.get(f"{RUTA}/papelera", headers=adm_a))

    restaurada = await c.post(f"{RUTA}/papelera/sedes/{sede}/restaurar", headers=adm_a)
    assert restaurada.status_code == 200, restaurada.text
    assert sede not in ids(await c.get(f"{RUTA}/papelera", headers=adm_a))
    assert sede in {s["id"] for s in (await c.get(f"{RUTA}/sedes", headers=adm_a)).json()}
