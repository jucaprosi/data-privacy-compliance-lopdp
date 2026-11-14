# ¤incidentes ¤hallazgos ¤rbac-tenant ¤arbitro
"""INC-02: asistente de vulneración en ocho secciones, decisión de notificar e informes.

Contra la PostgreSQL 16 de pruebas migrada (TEST_DATABASE_URL), con el rol lopdp_app y RLS. Valores
simulados; correos .invalid. Cada prueba lleva en su docstring la mutación que la pone en rojo.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

_URL = os.environ.get("TEST_DATABASE_URL", "")
if not _URL:
    pytest.skip("TEST_DATABASE_URL no configurada", allow_module_level=True)

from api.rbac import get_usuario_autenticado  # noqa: E402
from app_core.db.session import get_session  # noqa: E402
from app_core.errors import ErrorNegocio  # noqa: E402
from app_core.pasillo import evidencias as pasillo_evidencias  # noqa: E402
from app_core.storage import gcs  # noqa: E402
from features.incidentes import incidentes_service as inc  # noqa: E402
from features.incidentes.domain.vulneracion import SECCIONES_MINIMAS_INFORME  # noqa: E402
from main import app  # noqa: E402

RUTA = "/api/v1/incidentes"
CUENTAS = (
    "SELECT count(*) FROM incidentes_asistente_secciones",
    "SELECT count(*) FROM incidentes_informes",
    "SELECT count(*) FROM incidentes_notificaciones",
    "SELECT count(*) FROM incidentes_tratamientos",
    "SELECT count(*) FROM incidentes_lecciones",
)
PROHIBIDAS = (
    "UPDATE incidentes_asistente_secciones SET tenant_id = tenant_id",
    "UPDATE incidentes_informes SET tenant_id = tenant_id",
    "UPDATE incidentes_notificaciones SET tenant_id = tenant_id",
    "UPDATE incidentes_tratamientos SET tenant_id = tenant_id",
    "UPDATE incidentes_lecciones SET tenant_id = tenant_id",
    "DELETE FROM incidentes_asistente_secciones",
    "DELETE FROM incidentes_informes",
    "DELETE FROM incidentes_notificaciones",
    "DELETE FROM incidentes_tratamientos",
    "DELETE FROM incidentes_lecciones",
    "UPDATE incidentes SET titulo = titulo",
)
SECCIONES_VALIDAS = {
    1: {"fecha_conocimiento": "2026-11-10T09:00:00-05:00", "detectado_por": "Mesa de ayuda",
        "contacto_dpo": "Delegada simulada, dpo@correo.invalid"},
    2: {"tratamiento_ids": ["trat-simulado-1"]},
    3: {"titulares_aproximados": 120, "registros_aproximados": 300, "categorias_datos": ["Contacto"]},
    4: {"descripcion": "Consulta masiva simulada desde una credencial filtrada.", "tipo": "confidencialidad"},
    5: {"efectos": "Exposición de correos simulados.", "medidas": "Credencial revocada.",
        "recomendaciones_titulares": "Desconfía de correos que pidan tu clave."},
    6: {"resolucion": "Acceso cerrado y registros revisados.", "lecciones": []},
}
JUSTIFICACION = "Afecta datos de contacto de más de cien titulares."


def _url_async() -> str:
    return _URL.replace("postgresql://", "postgresql+psycopg://", 1) if _URL.startswith("postgresql://") else _URL


class AlmacenDoble:
    def __init__(self) -> None:
        self.objetos: dict[str, bytes] = {}

    def firmar_subida(self, clave, tipo_mime):  # pragma: no cover
        raise AssertionError

    def subir(self, clave, contenido, tipo_mime):
        if clave in self.objetos:
            raise gcs.ObjetoYaExiste(clave)
        self.objetos[clave] = contenido

    def descargar(self, clave, maximo_bytes):
        return self.objetos.get(clave)

    def fijar_retencion(self, clave, retener_hasta):
        return None


class HallazgosDoble:
    def __init__(self) -> None:
        self.registrados: list[tuple[str, str]] = []

    async def registrar(self, session, tenant_id, user_id, origen_ref, titulo):
        self.registrados.append((origen_ref, titulo))
        return f"hallazgo-{len(self.registrados)}"


async def _preparar(conexion, sufijo: str) -> dict:
    a, b = f"inc02-a-{sufijo}", f"inc02-b-{sufijo}"
    usuarios = {rol: (f"inc02-{rol[:6]}-{sufijo}", a, rol) for rol in ("implementador", "coordinador", "dpo")}
    usuarios["coord_b"] = (f"inc02-coordb-{sufijo}", b, "coordinador")
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
    return {"a": a, "b": b, "u": usuarios}


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


@pytest.fixture(autouse=True)
def _oidc(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "oidc")


async def _incidente(mundo, clave="coordinador", afecta=True):
    uid, t, _ = mundo["u"][clave]
    return await inc.registrar_incidente(
        mundo["s"], t, uid,
        fecha_deteccion=datetime.now(timezone.utc) - timedelta(hours=2),
        titulo="Acceso no autorizado simulado", descripcion="Consultas masivas simuladas.",
        severidad="Alta", afecta_datos_personales=afecta, categorias_datos=["Contacto (Email / Teléfono)"],
        medidas_inmediatas="Credencial revocada.",
    )


async def _api(mundo, clave, metodo, ruta, cuerpo=None):
    uid, t, rol = mundo["u"][clave]

    async def sesion():
        yield mundo["s"]

    app.dependency_overrides[get_session] = sesion
    app.dependency_overrides[get_usuario_autenticado] = lambda: uid
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://prueba") as api:
            return await api.request(
                metodo, f"{RUTA}{ruta}", headers={"X-Tenant-ID": t, "X-Role": rol}, json=cuerpo
            )
    finally:
        app.dependency_overrides.pop(get_session, None)
        app.dependency_overrides.pop(get_usuario_autenticado, None)


async def _completar_previas(mundo, incidente_id, saltar=(), hallazgos=None):
    uid, t, rol = mundo["u"]["implementador"]
    for n, datos in SECCIONES_VALIDAS.items():
        if n not in saltar:
            await inc.guardar_seccion(mundo["s"], t, uid, rol, incidente_id, n, datos, hallazgos=hallazgos)


async def _decidir(mundo, incidente_id, decision="spdp"):
    uid, t, rol = mundo["u"]["dpo"]
    return await inc.guardar_seccion(
        mundo["s"], t, uid, rol, incidente_id, 7, {"decision": decision, "justificacion": JUSTIFICACION}
    )


async def _informe(mundo, incidente_id, destino="spdp", almacen=None):
    uid, t, rol = mundo["u"]["dpo"]
    return await inc.generar_informe(
        mundo["s"], t, uid, rol, incidente_id, destino,
        pasillo_evidencias.custodiar_documento_generado, almacen=almacen or AlmacenDoble(),
    )


# ------------------------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_decision_justificada(mundo):
    """Mutación: aceptar la sección 7 con menos de 20 caracteres (o con «ninguno» sin justificar) → rojo."""
    incidente = await _incidente(mundo)
    await _completar_previas(mundo, incidente.id)

    corta = await _api(mundo, "dpo", "PUT", f"/{incidente.id}/asistente/7", {"decision": "spdp", "justificacion": "Muy breve."})
    assert corta.status_code == 422, corta.text
    assert corta.json()["code"] == "DECISION_SIN_JUSTIFICACION"

    ninguno = await _api(mundo, "dpo", "PUT", f"/{incidente.id}/asistente/7", {"decision": "ninguno", "justificacion": "No aplica."})
    assert ninguno.status_code == 422
    assert ninguno.json()["code"] == "DECISION_SIN_JUSTIFICACION"

    lectura = await _api(mundo, "dpo", "GET", f"/{incidente.id}/asistente")
    assert lectura.json()["decision"] is None

    justa = await _api(mundo, "dpo", "PUT", f"/{incidente.id}/asistente/7", {"decision": "spdp", "justificacion": "x" * 20})
    assert justa.status_code == 200, justa.text
    assert justa.json()["decision"] == "spdp"


@pytest.mark.asyncio
async def test_orden_no_avanza_a_la_decision_sin_la_seccion_3(mundo):
    """Mutación: quitar `exigir_previas` en la sección 7 → la decisión se guarda con la 3 vacía y esto falla."""
    incidente = await _incidente(mundo)
    await _completar_previas(mundo, incidente.id, saltar=(3,))
    r = await _api(mundo, "dpo", "PUT", f"/{incidente.id}/asistente/7", {"decision": "spdp", "justificacion": JUSTIFICACION})
    assert r.status_code == 409
    assert r.json()["code"] == "SECCION_ANTERIOR_INCOMPLETA"
    assert "3" in r.json()["detail"]
    estado = (await _api(mundo, "implementador", "GET", f"/{incidente.id}/asistente")).json()
    assert estado["seccion_actual"] == 3


@pytest.mark.asyncio
async def test_seccion_incompleta_dice_que_falta(mundo):
    """Mutación: no acumular los campos que faltan en `SeccionInvalida.faltan` → el detalle sale vacío y esto falla."""
    incidente = await _incidente(mundo)
    r = await _api(mundo, "implementador", "PUT", f"/{incidente.id}/asistente/3", {"titulares_aproximados": 5})
    assert r.status_code == 422
    assert r.json()["code"] == "SECCION_INCOMPLETA"
    assert "registros_aproximados" in r.json()["detail"] and "categorias_datos" in r.json()["detail"]


@pytest.mark.asyncio
async def test_roles_por_seccion(mundo):
    """Mutación: dejar que el coordinador escriba la sección 7 o genere informes → rojo."""
    incidente = await _incidente(mundo)
    await _completar_previas(mundo, incidente.id)
    r7 = await _api(mundo, "coordinador", "PUT", f"/{incidente.id}/asistente/7", {"decision": "spdp", "justificacion": JUSTIFICACION})
    assert r7.status_code == 403
    rinf = await _api(mundo, "coordinador", "POST", f"/{incidente.id}/informes", {"destino": "spdp"})
    assert rinf.status_code == 403
    r1 = await _api(mundo, "dpo", "PUT", f"/{incidente.id}/asistente/1", SECCIONES_VALIDAS[1])
    assert r1.status_code == 403
    lectura = await _api(mundo, "coordinador", "GET", f"/{incidente.id}/asistente")
    assert lectura.status_code == 200


@pytest.mark.asyncio
async def test_informe_minimo(mundo):
    """Mutación: quitar la sección «Contacto del delegado» del informe, o no custodiarlo → rojo."""
    s = mundo["s"]
    incidente = await _incidente(mundo)
    await _completar_previas(mundo, incidente.id)
    await _decidir(mundo, incidente.id, "spdp")
    almacen = AlmacenDoble()
    salida = await _informe(mundo, incidente.id, "spdp", almacen)
    contenido = next(iter(almacen.objetos.values())).decode("utf-8")
    for titulo in SECCIONES_MINIMAS_INFORME["spdp"]:
        assert titulo in contenido
    assert "dpo@correo.invalid" in contenido and "120" in contenido
    assert not any(palabra in contenido.lower() for palabra in ("cumple", "dentro del plazo"))
    custodiado = (
        await s.execute(text("SELECT sha256 FROM evidencias_documentos WHERE id = :i"), {"i": salida["evidencia_id"]})
    ).scalar_one()
    assert custodiado == salida["sha256"]

    with pytest.raises(ErrorNegocio) as exc:
        await _informe(mundo, incidente.id, "titulares")
    assert exc.value.code == "INFORME_NO_PEDIDO"

    await _informe(mundo, incidente.id, "spdp", almacen)
    _, t, _ = mundo["u"]["dpo"]
    filas = (
        await s.execute(text("SELECT count(*) FROM incidentes_informes WHERE incidente_id = :i"), {"i": incidente.id})
    ).scalar_one()
    assert filas == 2


@pytest.mark.asyncio
async def test_informe_titulares_contenido_minimo_art_10_1(mundo):
    """Mutación: omitir «Qué te recomendamos» en la comunicación a titulares → rojo."""
    incidente = await _incidente(mundo)
    await _completar_previas(mundo, incidente.id)
    await _decidir(mundo, incidente.id, "ambos")
    almacen = AlmacenDoble()
    await _informe(mundo, incidente.id, "titulares", almacen)
    contenido = next(iter(almacen.objetos.values())).decode("utf-8")
    for titulo in SECCIONES_MINIMAS_INFORME["titulares"]:
        assert titulo in contenido
    assert "Desconfía de correos" in contenido


@pytest.mark.asyncio
async def test_informe_exige_secciones_previas(mundo):
    """Mutación: no exigir 1 a 7 antes de generar el informe → rojo."""
    incidente = await _incidente(mundo)
    await _completar_previas(mundo, incidente.id, saltar=(5,))
    r = await _api(mundo, "dpo", "POST", f"/{incidente.id}/informes", {"destino": "spdp"})
    assert r.status_code == 409
    assert r.json()["code"] == "SECCION_ANTERIOR_INCOMPLETA"


@pytest.mark.asyncio
async def test_lecciones_hallazgos(mundo):
    """Mutación: registrar solo la primera lección, o no pasar origen_ref por lección → rojo."""
    s = mundo["s"]
    incidente = await _incidente(mundo)
    uid, t, rol = mundo["u"]["implementador"]
    hallazgos = HallazgosDoble()
    datos = {**SECCIONES_VALIDAS[6], "lecciones": ["Rotar credenciales cada trimestre", "Alertar consultas masivas"]}
    await inc.guardar_seccion(s, t, uid, rol, incidente.id, 6, datos, hallazgos=hallazgos)
    assert [r[0] for r in hallazgos.registrados] == [f"{incidente.id}:leccion:1", f"{incidente.id}:leccion:2"]
    # Guardar otra versión con las mismas lecciones no duplica hallazgos.
    await inc.guardar_seccion(s, t, uid, rol, incidente.id, 6, datos, hallazgos=hallazgos)
    assert len(hallazgos.registrados) == 2
    filas = (
        await s.execute(
            text("SELECT numero, hallazgo_id FROM incidentes_lecciones WHERE incidente_id = :i ORDER BY numero"),
            {"i": incidente.id},
        )
    ).all()
    assert [tuple(f) for f in filas] == [(1, "hallazgo-1"), (2, "hallazgo-2")]


@pytest.mark.asyncio
async def test_lecciones_fallan_cerrado_sin_capacidad_de_hallazgos(mundo):
    """Mutación: que el adaptador real ignore la falta de la capacidad en el pasillo → la lección se pierde y esto falla."""
    from app_core.pasillo import roadmap

    if hasattr(roadmap, "registrar_hallazgo_incidente"):
        pytest.skip("La capacidad del pasillo de la hoja de ruta ya existe: esta prueba deja de aplicar.")
    s = mundo["s"]
    incidente = await _incidente(mundo)
    uid, t, rol = mundo["u"]["implementador"]
    datos = {**SECCIONES_VALIDAS[6], "lecciones": ["Rotar credenciales"]}
    with pytest.raises(ErrorNegocio) as exc:
        async with s.begin_nested():
            await inc.guardar_seccion(s, t, uid, rol, incidente.id, 6, datos)
    assert exc.value.code == "LECCIONES_NO_DISPONIBLES"
    assert (await s.execute(text("SELECT count(*) FROM incidentes_asistente_secciones"))).scalar_one() == 0


@pytest.mark.asyncio
async def test_asistente_solo_agrega(mundo):
    """Mutación: conceder UPDATE (o DELETE) a lopdp_app sobre una de las tablas → rojo."""
    s = mundo["s"]
    incidente = await _incidente(mundo)
    uid, t, rol = mundo["u"]["implementador"]
    await inc.guardar_seccion(s, t, uid, rol, incidente.id, 3, SECCIONES_VALIDAS[3])
    await inc.guardar_seccion(s, t, uid, rol, incidente.id, 3, {**SECCIONES_VALIDAS[3], "titulares_aproximados": 150})
    versiones = (
        await s.execute(text("SELECT count(*) FROM incidentes_asistente_secciones WHERE incidente_id = :i AND seccion = 3"),
                        {"i": incidente.id})
    ).scalar_one()
    assert versiones == 2
    estado = (await _api(mundo, "implementador", "GET", f"/{incidente.id}/asistente")).json()
    assert estado["secciones"][2]["datos"]["titulares_aproximados"] == 150

    for sentencia in PROHIBIDAS:
        with pytest.raises(DBAPIError) as exc:
            async with s.begin_nested():
                await s.execute(text(sentencia))
        assert "permission denied" in str(exc.value.orig).lower() or "permiso denegado" in str(exc.value.orig).lower()


@pytest.mark.asyncio
async def test_check_de_la_base_rechaza_decision_sin_justificacion(mundo):
    """Mutación: quitar `ck_inc_secciones_decision` de la migración → el INSERT directo pasa y esto falla."""
    s = mundo["s"]
    incidente = await _incidente(mundo)
    uid, t, _ = mundo["u"]["dpo"]
    with pytest.raises(DBAPIError):
        async with s.begin_nested():
            await s.execute(
                text(
                    "INSERT INTO incidentes_asistente_secciones (id, tenant_id, incidente_id, seccion, version, datos, "
                    "registrado_por) VALUES (:id, :t, :i, 7, 1, CAST(:d AS JSONB), :u)"
                ),
                {"id": str(uuid.uuid4()), "t": t, "i": incidente.id, "u": uid,
                 "d": '{"decision": "spdp", "justificacion": "corta"}'},
            )


@pytest.mark.asyncio
async def test_notificacion_con_evidencia_custodiada(mundo):
    """Mutación: validar la evidencia con `huella_registrada` (repositorio en memoria) en vez de
    evidencias_documentos → la huella real da 422 y esto falla."""
    incidente = await _incidente(mundo)
    await _completar_previas(mundo, incidente.id)
    await _decidir(mundo, incidente.id, "spdp")
    salida = await _informe(mundo, incidente.id, "spdp")

    ajena = await _api(mundo, "implementador", "PUT", f"/{incidente.id}/asistente/8",
                       {"destino": "spdp", "notificado_en": "2026-11-12T10:00:00-05:00", "evidencia_sha256": "a" * 64})
    assert ajena.status_code == 422
    assert ajena.json()["code"] == "EVIDENCIA_NO_CUSTODIADA"

    r = await _api(mundo, "implementador", "PUT", f"/{incidente.id}/asistente/8",
                   {"destino": "spdp", "notificado_en": "2026-11-12T10:00:00-05:00", "evidencia_sha256": salida["sha256"]})
    assert r.status_code == 200, r.text
    assert r.json()["secciones"][7]["completa"] is True

    uid, t, _ = mundo["u"]["dpo"]
    bandeja = await inc.notificaciones_por_implementador(mundo["s"], t, uid)
    assert [f["incidente_id"] for f in bandeja] == [incidente.id]


@pytest.mark.asyncio
async def test_precondicion_de_cierre(mundo):
    """Mutación: que `exigir_decision_para_cierre` no consulte la sección 7 → rojo.

    Prueba de unidad: la precondición todavía no está enganchada a `cerrar_incidente` (sección INC-03).
    """
    s = mundo["s"]
    incidente = await _incidente(mundo)
    _, t, _ = mundo["u"]["dpo"]
    with pytest.raises(ErrorNegocio) as exc:
        await inc.exigir_decision_para_cierre(s, t, incidente.id)
    assert exc.value.code == "DECISION_NOTIFICAR_PENDIENTE"
    sin_datos = await _incidente(mundo, afecta=False)
    await inc.exigir_decision_para_cierre(s, t, sin_datos.id)
    await _completar_previas(mundo, incidente.id)
    await _decidir(mundo, incidente.id, "ninguno")
    await inc.exigir_decision_para_cierre(s, t, incidente.id)


@pytest.mark.xfail(strict=True, reason="Precondición no enganchada: falta la propiedad de incidentes_service.py#INC-03.")
@pytest.mark.asyncio
async def test_cierre_exige_decision(mundo):
    """Mutación: quitar la llamada a la precondición en `cerrar_incidente` → el cierre pasa y esto falla.

    Estricta: cuando se enganche, pasa y hay que retirar la marca xfail.
    """
    incidente = await _incidente(mundo)
    r = await _api(mundo, "coordinador", "POST", f"/{incidente.id}/cerrar", {"motivo": "Contención verificada por el equipo"})
    assert r.status_code == 409
    assert r.json()["code"] == "DECISION_NOTIFICAR_PENDIENTE"


@pytest.mark.asyncio
async def test_rls_incidentes_asistente(mundo):
    """Mutación: quitar la política RLS (o el FORCE) de una de las tablas → B ve filas de A y esto falla."""
    s = mundo["s"]
    incidente = await _incidente(mundo)
    await _completar_previas(mundo, incidente.id, hallazgos=HallazgosDoble())
    await _decidir(mundo, incidente.id)
    await _informe(mundo, incidente.id)
    uid_b, t_b, _ = mundo["u"]["coord_b"]
    from app_core.db.session import fijar_contexto_rls

    await fijar_contexto_rls(s, t_b, uid_b)
    for consulta in CUENTAS:
        assert (await s.execute(text(consulta))).scalar_one() == 0, consulta
    r = await _api(mundo, "coord_b", "GET", f"/{incidente.id}/asistente")
    assert r.status_code == 404
