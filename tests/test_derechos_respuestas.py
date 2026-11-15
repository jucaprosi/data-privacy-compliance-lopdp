# ¤evidencias ¤rbac-tenant ¤arbitro
"""DER-01 · verificación de identidad, modelos de respuesta y la respuesta como evidencia.

Contra la PostgreSQL 16 de pruebas migrada (TEST_DATABASE_URL), con el rol lopdp_app y RLS. Valores
simulados; correos .invalid. Cada prueba lleva en su docstring la mutación que la pone en rojo.
"""
import hashlib
import importlib.util
import os
import uuid
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

_URL = os.environ.get("TEST_DATABASE_URL", "")
if not _URL:
    pytest.skip("TEST_DATABASE_URL no configurada", allow_module_level=True)

from api.routers import derechos_respuestas as router_respuestas  # noqa: E402
from api.rbac import get_usuario_autenticado  # noqa: E402
from app_core.db.session import fijar_contexto_rls, get_session  # noqa: E402
from app_core.pasillo import evidencias as pasillo_evidencias  # noqa: E402
from app_core.storage import gcs  # noqa: E402
from main import app  # noqa: E402

pytestmark = pytest.mark.asyncio

RAIZ = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("der01_migracion", RAIZ / "alembic/versions/der01_derechos_respuestas.py")
migracion = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migracion)

RUTA = "/api/v1/derechos"
ROLES = ("admin_organizacion", "implementador", "coordinador", "responsable_area", "dpo")
HASH_VALIDO = "a" * 64
VARIABLES = {
    "organizacion": "Cooperativa Demo", "nombre_titular": "Titular Simulado", "fecha_solicitud": "2026-11-10",
    "numero_solicitud": "S-0001", "fecha_respuesta": "2026-11-20", "contacto_dpo": "dpo@demo.invalid",
    "actuacion": "Te entregamos una copia de tus datos.",
}


class AlmacenDoble:
    def __init__(self) -> None:
        self.objetos: dict[str, bytes] = {}

    def subir(self, clave, contenido, tipo_mime):
        if clave in self.objetos:
            raise gcs.ObjetoYaExiste(clave)
        self.objetos[clave] = contenido

    def descargar(self, clave, maximo_bytes):
        return self.objetos.get(clave)

    def fijar_retencion(self, clave, retener_hasta):
        return None


class PasilloConAlmacenDoble:
    """Custodia real de evidencias (EVI-04) con un almacén en memoria: sin nube en las pruebas."""

    def __init__(self) -> None:
        self.almacen = AlmacenDoble()

    async def custodiar_documento_generado(self, session, tenant_id, user_id, **datos):
        return await pasillo_evidencias.custodiar_documento_generado(
            session, tenant_id, user_id, almacen=self.almacen, **datos
        )


def _url_async() -> str:
    return _URL.replace("postgresql://", "postgresql+psycopg://", 1) if _URL.startswith("postgresql://") else _URL


async def _preparar(conexion, sufijo: str) -> dict:
    a, b = f"der01-a-{sufijo}", f"der01-b-{sufijo}"
    usuarios = {rol: (f"der01-{rol[:6]}-{sufijo}", a, rol) for rol in ROLES}
    usuarios["admin_b"] = (f"der01-adminb-{sufijo}", b, "admin_organizacion")
    for t in (a, b):
        await conexion.execute(
            text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :t)"),
            {"t": t},
        )
    for uid, tenant, rol in usuarios.values():
        await conexion.execute(
            text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"), {"u": uid, "e": f"{uid}@correo.invalid"}
        )
        await conexion.execute(
            text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"),
            {"i": str(uuid.uuid4()), "u": uid, "t": tenant, "r": rol},
        )
    modelos = {t: f"{t}:ACCESO:concedido" for t in (a, b)}  # asegurar_modelos los siembra al listar o responder
    return {"a": a, "b": b, "u": usuarios, "modelo": modelos}


@pytest_asyncio.fixture
async def mundo():
    """Todo dentro de una transacción que se revierte: nada queda en la base."""
    engine = create_async_engine(_url_async(), hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            datos = await _preparar(conexion, uuid.uuid4().hex[:10])
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False, join_transaction_mode="create_savepoint") as s:
                yield {"s": s, **datos}
        finally:
            await transaccion.rollback()
    await engine.dispose()


async def _solicitud(mundo, tenant="a", verificada=False, tipo="ACCESO") -> str:
    t = mundo[tenant]
    uid = mundo["u"]["admin_organizacion" if tenant == "a" else "admin_b"][0]
    await fijar_contexto_rls(mundo["s"], t, uid)
    sid = str(uuid.uuid4())
    await mundo["s"].execute(
        text(
            "INSERT INTO derechos_arco_solicitudes (id, tenant_id_texto, tipo_solicitud, estado, cedula_solicitante, "
            "nombre_solicitante, fecha_recepcion, fecha_vencimiento) VALUES (:i, :t, CAST(:p AS tiposolicitud), 'RECIBIDA', "
            "'1700000001', 'Titular Simulado', now(), now() + interval '15 days')"
        ),
        {"i": sid, "t": t, "p": tipo},
    )
    if verificada:
        await mundo["s"].execute(
            text(
                "UPDATE derechos_arco_solicitudes SET identidad_verificada_en = now(), identidad_metodo = 'documento', "
                "identidad_verificada_por = :u WHERE id::text = :i"
            ),
            {"i": sid, "u": uid},
        )
    return sid


async def _estado(mundo, sid, tenant="a"):
    await fijar_contexto_rls(mundo["s"], mundo[tenant], mundo["u"]["admin_organizacion"][0])
    return (await mundo["s"].execute(
        text(
            "SELECT estado::text AS estado, evidencia_respuesta_hash AS h, respondida_en AS r, resultado "
            "FROM derechos_arco_solicitudes WHERE id::text = :i"
        ),
        {"i": sid},
    )).mappings().first()


async def _api(mundo, clave, metodo, ruta, cuerpo=None, tenant=None):
    uid, t, rol = mundo["u"][clave]

    async def sesion():
        yield mundo["s"]

    app.dependency_overrides[get_session] = sesion
    app.dependency_overrides[get_usuario_autenticado] = lambda: uid
    try:
        await fijar_contexto_rls(mundo["s"], tenant or t, uid)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://prueba") as api:
            return await api.request(metodo, f"{RUTA}{ruta}", headers={"X-Tenant-ID": tenant or t, "X-Role": rol}, json=cuerpo)
    finally:
        app.dependency_overrides.pop(get_session, None)
        app.dependency_overrides.pop(get_usuario_autenticado, None)


def _cuerpo(mundo, tenant="a", **cambios):
    base = {"modelo_id": mundo["modelo"][mundo[tenant]], "variables": dict(VARIABLES), "resultado": "concedido"}
    return {**base, **cambios}


@pytest.fixture(autouse=True)
def _oidc(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "oidc")


@pytest.fixture
def custodia_real(monkeypatch):
    doble = PasilloConAlmacenDoble()
    monkeypatch.setattr(router_respuestas, "pasillo_evidencias", doble)
    return doble


async def test_verificar_identidad_registra_metodo_y_actor(mundo):
    sid = await _solicitud(mundo)
    r = await _api(mundo, "coordinador", "POST", f"/solicitudes/{sid}/verificar-identidad", {"metodo": "correo"})
    assert r.status_code == 200, r.text
    assert r.json()["identidad_metodo"] == "correo" and r.json()["identidad_verificada_por"] == mundo["u"]["coordinador"][0]
    assert r.json()["identidad_verificada_en"] is not None


async def test_ficha_de_la_solicitud_con_quien_verifico(mundo):
    sid = await _solicitud(mundo, verificada=True)
    r = await _api(mundo, "dpo", "GET", f"/solicitudes/{sid}")
    assert r.status_code == 200, r.text
    assert r.json()["identidad_metodo"] == "documento" and r.json()["identidad_verificada_por_nombre"]
    ajena = await _api(mundo, "admin_b", "GET", f"/solicitudes/{sid}")
    assert ajena.status_code == 404


async def test_verificar_identidad_rechaza_metodo_y_rol_ajenos(mundo):
    sid = await _solicitud(mundo)
    assert (await _api(mundo, "coordinador", "POST", f"/solicitudes/{sid}/verificar-identidad", {"metodo": "x"})).status_code == 422
    assert (await _api(mundo, "dpo", "POST", f"/solicitudes/{sid}/verificar-identidad", {"metodo": "correo"})).status_code == 403


async def test_responder_exige_identidad(mundo, custodia_real):
    """Mutación: omitir la comprobación de identidad en `responder` hace fallar la prueba."""
    sid = await _solicitud(mundo)
    r = await _api(mundo, "implementador", "POST", f"/solicitudes/{sid}/respuesta", _cuerpo(mundo))
    assert r.status_code == 409 and r.json()["code"] == "IDENTIDAD_NO_VERIFICADA"
    assert (await _estado(mundo, sid))["estado"] == "RECIBIDA"
    assert custodia_real.almacen.objetos == {}


async def test_respuesta_como_evidencia(mundo, custodia_real):
    sid = await _solicitud(mundo, verificada=True)
    r = await _api(mundo, "implementador", "POST", f"/solicitudes/{sid}/respuesta", _cuerpo(mundo))
    assert r.status_code == 201, r.text
    esperado = (
        "Cooperativa Demo · Respuesta a la solicitud n.º S-0001, presentada el 2026-11-10.\n"
        "Estimado/a Titular Simulado:\n\n"
        "Atendimos tu solicitud de acceso a tus datos personales (LOPDP, art. 13). Te entregamos una copia de tus datos.\n\n"
        "Si tienes preguntas sobre esta respuesta, escríbenos a dpo@demo.invalid.\n\n"
        "Cooperativa Demo · 2026-11-20"
    )
    huella = hashlib.sha256(esperado.encode("utf-8")).hexdigest()
    assert r.json() == {"evidencia_respuesta_hash": huella}
    fila = await _estado(mundo, sid)
    assert fila["estado"] == "CONTESTADA" and fila["h"] == huella and fila["r"] is not None and fila["resultado"] == "concedido"
    assert custodia_real.almacen.objetos == {f"{mundo['a']}/{huella}": esperado.encode("utf-8")}
    en_evidencias = (await mundo["s"].execute(
        text("SELECT count(*) FROM evidencias_documentos WHERE tenant_id = :t AND sha256 = :h"), {"t": mundo["a"], "h": huella}
    )).scalar()
    assert en_evidencias == 1


async def test_contestar_sin_evidencia_422(mundo, monkeypatch):
    """Mutación: quitar la comprobación del sha256 (o del manejo de fallos) en el servicio hace fallar la prueba."""
    sid = await _solicitud(mundo, verificada=True)

    class SinHuella:
        async def custodiar_documento_generado(self, *a, **k):
            return {"evidencia_id": "x"}

    class Falla:
        async def custodiar_documento_generado(self, *a, **k):
            raise RuntimeError("almacén caído")

    for doble in (SinHuella(), Falla()):
        monkeypatch.setattr(router_respuestas, "pasillo_evidencias", doble)
        r = await _api(mundo, "implementador", "POST", f"/solicitudes/{sid}/respuesta", _cuerpo(mundo))
        assert r.status_code == 422 and r.json()["code"] == "RESPUESTA_SIN_EVIDENCIA"
        fila = await _estado(mundo, sid)
        assert fila["estado"] == "RECIBIDA" and fila["h"] is None and fila["r"] is None


async def test_hash_del_cliente_rechazado(mundo, custodia_real):
    """Mutación: aceptar el hash del cliente (quitar extra="forbid") hace fallar la prueba."""
    sid = await _solicitud(mundo, verificada=True)
    for extra in ({"evidencia_respuesta_hash": HASH_VALIDO}, {"evidenciaUrl": "https://ejemplo.invalid/r.pdf"}):
        r = await _api(mundo, "implementador", "POST", f"/solicitudes/{sid}/respuesta", _cuerpo(mundo, **extra))
        assert r.status_code == 422
        fila = await _estado(mundo, sid)
        assert fila["estado"] == "RECIBIDA" and fila["h"] is None
    assert custodia_real.almacen.objetos == {}


async def test_check_contestada_exige_hash(mundo):
    """Mutación: quitar ck_arco_contestada_con_evidencia de la migración hace fallar la prueba."""
    sid = await _solicitud(mundo, verificada=True)
    casos = (
        ("CONTESTADA", None, False),
        ("CONTESTADA", None, True),
        ("CONTESTADA", "no-es-sha256", True),
        ("CONTESTADA", HASH_VALIDO, False),
    )
    for estado, hash_, con_fecha in casos:
        await mundo["s"].execute(text("SAVEPOINT antes"))
        with pytest.raises(DBAPIError) as error:
            await mundo["s"].execute(
                text(
                    "UPDATE derechos_arco_solicitudes SET estado = :e, evidencia_respuesta_hash = :h, "
                    "respondida_en = CASE WHEN :f THEN now() END WHERE id::text = :i"
                ),
                {"e": estado, "h": hash_, "f": con_fecha, "i": sid},
            )
        assert "ck_arco_contestada_con_evidencia" in str(error.value)
        await mundo["s"].execute(text("ROLLBACK TO SAVEPOINT antes"))
    await mundo["s"].execute(
        text(
            "UPDATE derechos_arco_solicitudes SET estado = 'CONTESTADA', respondida_en = now(), "
            "evidencia_respuesta_hash = :h WHERE id::text = :i"
        ),
        {"i": sid, "h": HASH_VALIDO},
    )
    assert (await _estado(mundo, sid))["estado"] == "CONTESTADA"


@pytest.mark.parametrize("fila", [
    ("CONTESTADA", None, None),
    ("CONTESTADA", "xyz", "now()"),
    ("CONTESTADA", HASH_VALIDO, None),  # con hash y sin respondida_en
])
async def test_migracion_der01_aborta_con_contestadas_sin_hash(mundo, fila):
    """Con una fila CONTESTADA sin hash válido (o sin respondida_en) la guardia aborta con el recuento y la fila queda igual.

    Mutación: reemplazar el recuento por un UPDATE que rellene el hash hace fallar la prueba. Se usa una tabla
    temporal con el esquema posterior a las columnas, que en esta sesión tapa a la real.
    """
    estado, hash_, respondida = fila
    s = mundo["s"]
    await s.execute(text("RESET ROLE"))
    await s.execute(text(
        "CREATE TEMP TABLE derechos_arco_solicitudes (id uuid PRIMARY KEY, estado text, "
        "evidencia_respuesta_hash varchar(64), respondida_en timestamptz) ON COMMIT DROP"
    ))
    await s.execute(text("INSERT INTO pg_temp.derechos_arco_solicitudes VALUES (gen_random_uuid(), 'RECIBIDA', NULL, NULL)"))
    await s.execute(text(
        "INSERT INTO pg_temp.derechos_arco_solicitudes VALUES (gen_random_uuid(), 'CONTESTADA', :h, :r)"
        .replace(":r", respondida or "NULL")
    ), {"h": hash_})
    await s.execute(text(
        "INSERT INTO pg_temp.derechos_arco_solicitudes VALUES (gen_random_uuid(), 'CONTESTADA', :h, now())"
    ), {"h": HASH_VALIDO})
    await s.execute(text("SAVEPOINT antes"))
    with pytest.raises(DBAPIError) as error:
        await s.execute(text(migracion.SQL_GUARDIA))
    assert "1 solicitud(es) ARCO" in str(error.value)
    await s.execute(text("ROLLBACK TO SAVEPOINT antes"))
    filas = (await s.execute(text(
        "SELECT estado, evidencia_respuesta_hash, respondida_en IS NULL AS sin_fecha "
        "FROM pg_temp.derechos_arco_solicitudes WHERE estado = 'CONTESTADA' AND respondida_en IS NULL "
        "OR estado = 'CONTESTADA' AND evidencia_respuesta_hash IS DISTINCT FROM :v"), {"v": HASH_VALIDO})).all()
    # La fila inválida sigue exactamente como se sembró: sin relleno de hash ni de fecha.
    assert [(f[0], f[1], f[2]) for f in filas] == [("CONTESTADA", hash_, respondida is None)]


async def test_migracion_der01_pasa_sin_filas_invalidas(mundo):
    s = mundo["s"]
    await s.execute(text("RESET ROLE"))
    await s.execute(text(
        "CREATE TEMP TABLE derechos_arco_solicitudes (id uuid PRIMARY KEY, estado text, "
        "evidencia_respuesta_hash varchar(64), respondida_en timestamptz) ON COMMIT DROP"
    ))
    await s.execute(text("INSERT INTO pg_temp.derechos_arco_solicitudes VALUES (gen_random_uuid(), 'RECIBIDA', NULL, NULL)"))
    await s.execute(text(migracion.SQL_GUARDIA))


def test_modelos_sembrados_segun_especificacion():
    """Mutación: cambiar una frase sembrada (en la migración o en el motor) hace fallar la prueba."""
    from features.derechos_arco.services import respuestas_engine as motor

    sembrados = {(d, r): t for d, r, t in migracion.MODELOS}
    assert len(migracion.MODELOS) == 24 and sembrados == motor.catalogo_modelos()
    assert sembrados[("ACCESO", "concedido")].split("\n\n")[1] == (
        "Atendimos tu solicitud de acceso a tus datos personales (LOPDP, art. 13). {actuacion}"
    )
    assert sembrados[("DECISIONES_AUTOMATIZADAS", "denegado")].split("\n\n")[1] == (
        "No podemos atender tu solicitud de no ser objeto de una decisión basada en valoraciones automatizadas "
        "(LOPDP, art. 20) por este motivo: {motivo}"
    )
    assert sembrados[("QUEJA", "parcial")].split("\n\n")[1] == (
        "Revisamos tu queja en parte. {actuacion} Sobre el resto: {motivo}"
    )
    for (derecho, resultado), texto in sembrados.items():
        usadas = set(motor.variables_de(texto))
        comunes = {"organizacion", "nombre_titular", "fecha_solicitud", "numero_solicitud", "fecha_respuesta", "contacto_dpo"}
        extra = {"concedido": {"actuacion"}, "parcial": {"actuacion", "motivo"}, "denegado": {"motivo"}}[resultado]
        assert usadas == comunes | extra, (derecho, resultado)
        assert ("APDP" in texto or "Autoridad de Protección" in texto) == (resultado != "concedido")
        assert "LOPDP" not in texto if derecho == "QUEJA" else texto.count("LOPDP, art.") == 1
        for prohibido in ("conforme a la ley", "en cumplimiento de", "garantizamos", "plazo", "art. 62"):
            assert prohibido not in texto


async def test_queja_reutiliza_resultados(mundo, custodia_real):
    sid = await _solicitud(mundo, verificada=True, tipo="QUEJA")
    uid = mundo["u"]["implementador"][0]
    await fijar_contexto_rls(mundo["s"], mundo["a"], uid)
    r = await _api(mundo, "implementador", "POST", f"/solicitudes/{sid}/respuesta", {
        "modelo_id": f"{mundo['a']}:QUEJA:parcial", "variables": {**VARIABLES, "motivo": "Falta información."},
        "resultado": "parcial",
    })
    assert r.status_code == 201, r.text
    assert (await _estado(mundo, sid))["resultado"] == "parcial"
    await mundo["s"].execute(text("SAVEPOINT antes"))
    with pytest.raises(DBAPIError) as error:
        await mundo["s"].execute(text("UPDATE derechos_arco_solicitudes SET resultado = 'atendida' WHERE id::text = :i"), {"i": sid})
    assert "ck_arco_resultado" in str(error.value)
    await mundo["s"].execute(text("ROLLBACK TO SAVEPOINT antes"))


async def test_segunda_respuesta_409(mundo, custodia_real):
    sid = await _solicitud(mundo, verificada=True)
    assert (await _api(mundo, "implementador", "POST", f"/solicitudes/{sid}/respuesta", _cuerpo(mundo))).status_code == 201
    r = await _api(mundo, "admin_organizacion", "POST", f"/solicitudes/{sid}/respuesta", _cuerpo(mundo))
    assert r.status_code == 409 and r.json()["code"] == "SOLICITUD_RESPONDIDA"


async def test_variables_incompletas_422(mundo, custodia_real):
    sid = await _solicitud(mundo, verificada=True)
    r = await _api(mundo, "implementador", "POST", f"/solicitudes/{sid}/respuesta",
                   _cuerpo(mundo, variables={**VARIABLES, "actuacion": "  "}))
    assert r.status_code == 422 and r.json()["code"] == "VARIABLES_INCOMPLETAS"
    assert (await _estado(mundo, sid))["estado"] == "RECIBIDA" and custodia_real.almacen.objetos == {}


async def test_dpo_no_responde_derechos(mundo, custodia_real):
    sid = await _solicitud(mundo, verificada=True)
    for rol in ("dpo", "coordinador", "responsable_area"):
        r = await _api(mundo, rol, "POST", f"/solicitudes/{sid}/respuesta", _cuerpo(mundo))
        assert r.status_code == 403
    assert (await _estado(mundo, sid))["estado"] == "RECIBIDA"


async def test_dpo_consulta_los_modelos(mundo):
    r = await _api(mundo, "dpo", "GET", "/modelos?derecho=ACCESO&resultado=concedido")
    assert r.status_code == 200
    assert [m["id"] for m in r.json()["modelos"]] == [mundo["modelo"][mundo["a"]]]
    assert r.json()["modelos"][0]["variables"] == [
        "organizacion", "numero_solicitud", "fecha_solicitud", "nombre_titular", "actuacion", "contacto_dpo", "fecha_respuesta"
    ]


async def test_rls_derechos_respuestas(mundo):
    """Mutación: quitar FORCE o la política de derechos_modelos hace fallar la prueba."""
    sid = await _solicitud(mundo, verificada=True)
    await fijar_contexto_rls(mundo["s"], mundo["b"], mundo["u"]["admin_b"][0])
    from features.derechos_arco.services.respuestas_engine import asegurar_modelos

    await asegurar_modelos(mundo["s"], mundo["b"])
    tenants = (await mundo["s"].execute(text("SELECT DISTINCT tenant_id FROM derechos_modelos"))).scalars().all()
    assert tenants == [mundo["b"]]
    # Sembrar modelos de otra organización con el contexto de B lo rechaza la política (WITH CHECK).
    await mundo["s"].execute(text("SAVEPOINT ajeno"))
    with pytest.raises(DBAPIError):
        await mundo["s"].execute(text(
            "INSERT INTO derechos_modelos (id, tenant_id, derecho, resultado, texto) VALUES ('x', :t, 'ACCESO', 'concedido', 'x')"
        ), {"t": mundo["a"]})
    await mundo["s"].execute(text("ROLLBACK TO SAVEPOINT ajeno"))
    assert (await mundo["s"].execute(
        text("SELECT count(*) FROM derechos_arco_solicitudes WHERE id::text = :i"), {"i": sid})).scalar() == 0
    # Una respuesta en B a la solicitud de A no la encuentra.
    r = await _api(mundo, "admin_b", "POST", f"/solicitudes/{sid}/respuesta", _cuerpo(mundo, tenant="b"))
    assert r.status_code == 404
