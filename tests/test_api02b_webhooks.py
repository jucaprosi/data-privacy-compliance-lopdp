# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤qa-engineer
# ¤api-integraciones ¤seguridad ¤seguridad-tenant ¤arbitro
"""Árbitro de API-02b: Webhooks firmados HMAC-SHA256 con techo del paquete.

Verifica todos los escenarios de aceptación de governance/especificaciones/API-02b.md (§5)
y sus mutaciones m1..m5:
- m1: verificar firma con otro secreto falla (`test_firma_hmac_valida`).
- m2: aceptar una marca de tiempo fuera de ventana (>300 s) falla (`test_marca_fuera_de_ventana`).
- m3: aceptar URL http o privada/loopback/metadatos/DNS privado falla (`test_url_interna_rechazada`).
- m4: crear sobre el techo del paquete falla con 409 (`test_techo_de_webhooks`).
- m5: exponer secreto o secreto_cifrado en GET falla (`test_secreto_nunca_en_el_listado`).
- Entrega síncrona con reintentos (500/500/200 y 500x3) contra servidor HTTP local.
- Aislamiento RLS por tenant con rol `lopdp_app` en PostgreSQL local.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from conftest import exigir_base_de_pruebas
from cryptography.fernet import Fernet
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from api.errores import ErrorNegocio
from app_core.db.session import fijar_contexto_rls, get_session
from app_core.integraciones import techos as techos_svc
from app_core.integraciones import webhooks as webhooks_svc
from main import app

RAIZ = Path(__file__).resolve().parent.parent
RUTA_API = "/api/v1/integraciones/webhooks"
IP_PUBLICA_PRUEBA = "93.184.216.34"


def _resolver_publico(_host: str) -> list[str]:
    return [IP_PUBLICA_PRUEBA]


def _resolver_privado(_host: str) -> list[str]:
    return ["10.20.30.40"]


def _url_async() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "")
    if not url:
        return ""
    return url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url


async def _con_bd_lopdp_app(cuerpo):
    """Ejecuta `cuerpo(session, tenant_a, tenant_b, user_a, user_b)` bajo lopdp_app y revierte al final."""
    exigir_base_de_pruebas()
    url = _url_async()
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")

    engine = create_async_engine(url, hide_parameters=True)
    sufijo = uuid.uuid4().hex[:10]
    ta, tb = f"wh-a-{sufijo}", f"wh-b-{sufijo}"
    ua, ub = f"wh-ua-{sufijo}", f"wh-ub-{sufijo}"

    try:
        async with engine.connect() as conn:
            tx = await conn.begin()
            try:
                for tid in (ta, tb):
                    await conn.execute(
                        text(
                            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                            "VALUES (:t, :t, :t, :t)"
                        ),
                        {"t": tid},
                    )
                    await conn.execute(
                        text(
                            "INSERT INTO boveda_suscripciones_tenant "
                            "(tenant_id, paquete_codigo, cuota_almacenamiento_bytes, cuota_egress_mensual_bytes) "
                            "VALUES (:t, 'INICIAL', 53687091200, 107374182400)"
                        ),
                        {"t": tid},
                    )
                for uid, tid in ((ua, ta), (ub, tb)):
                    await conn.execute(
                        text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :n)"),
                        {"u": uid, "e": f"{uid}@ejemplo.invalid", "n": uid},
                    )
                    await conn.execute(
                        text(
                            "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
                            "VALUES (:id, :u, :t, 'admin_organizacion')"
                        ),
                        {"id": f"rol-{uid}", "u": uid, "t": tid},
                    )

                await conn.execute(text("SET LOCAL ROLE lopdp_app"))
                async with AsyncSession(
                    bind=conn,
                    expire_on_commit=False,
                    join_transaction_mode="create_savepoint",
                ) as session:
                    await cuerpo(session, ta, tb, ua, ub)
            finally:
                await tx.rollback()
    finally:
        await engine.dispose()


class _TransporteLocalHTTPS(httpx.AsyncBaseTransport):
    """Redirige peticiones HTTPS del cliente de pruebas al servidor HTTP local sin salir a la red."""

    def __init__(self, puerto: int) -> None:
        self.puerto = puerto

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        destino = httpx.URL(
            scheme="http",
            host="127.0.0.1",
            port=self.puerto,
            raw_path=request.url.raw_path,
        )
        async with httpx.AsyncClient(follow_redirects=False, timeout=5.0) as cli:
            resp = await cli.request(
                method=request.method,
                url=destino,
                content=request.content,
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
            )
        return httpx.Response(
            status_code=resp.status_code,
            headers=resp.headers,
            content=resp.content,
        )


def _servidor_local(estados: list[int], secreto: str):
    """Levanta un servidor HTTP local que verifica la firma de cada petición y responde `estados`."""
    recibidas: list[dict] = []
    indice = {"i": 0}
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            largo = int(self.headers.get("Content-Length", "0"))
            cuerpo = self.rfile.read(largo)
            marca = self.headers.get("X-Evydentia-Marca-Tiempo", "")
            firma = self.headers.get("X-Evydentia-Firma", "")
            firma_ok = webhooks_svc.verificar_firma(secreto, marca, cuerpo, firma, ahora=time.time())
            with lock:
                pos = indice["i"]
                estado = estados[pos] if pos < len(estados) else estados[-1]
                indice["i"] = pos + 1
                recibidas.append(
                    {
                        "path": self.path,
                        "marca": marca,
                        "firma": firma,
                        "firma_ok": firma_ok,
                        "cuerpo": json.loads(cuerpo.decode("utf-8")),
                        "estado": estado,
                    }
                )
            self.send_response(estado)
            if 300 <= estado < 400:
                self.send_header("Location", "https://redireccion.ejemplo.invalid/destino")
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, format, *args):
            return None

    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()
    return srv, recibidas


# ---- Pruebas unitarias de constantes, firma y validación URL (sin BD) ----


def test_constantes_y_migracion_contrato():
    assert webhooks_svc.EVENTOS_WEBHOOK == (
        "webhook.prueba",
        "incidente.registrado",
        "derecho.solicitud_recibida",
        "tarea.validada",
    )
    assert webhooks_svc.VENTANA_SEGUNDOS == 300
    assert webhooks_svc.REINTENTOS == 3
    assert webhooks_svc.ESPERAS_REINTENTO == (1, 2, 4)
    assert webhooks_svc.TIMEOUT_SEGUNDOS == 5
    assert webhooks_svc.VARIABLE_CLAVE_CIFRADO == "WEBHOOKS_CLAVE_CIFRADO"

    ruta_mig = RAIZ / "alembic" / "versions" / "api02b_webhooks_suscripciones.py"
    assert ruta_mig.exists()
    contenido = ruta_mig.read_text(encoding="utf-8")
    assert 'revision = "api02b_webhooks_suscripciones"' in contenido
    assert 'down_revision = "api02_claves_integracion"' in contenido
    assert "ENABLE ROW LEVEL SECURITY" in contenido
    assert "FORCE ROW LEVEL SECURITY" in contenido
    assert "GRANT SELECT, INSERT, UPDATE ON webhooks_suscripciones TO lopdp_app" in contenido
    assert "DELETE ON webhooks_suscripciones" not in contenido


def test_firma_hmac_valida():
    """Escenario §5 + Mutación m1: verificar con el mismo secreto pasa; con otro secreto falla."""
    secreto = webhooks_svc.generar_secreto()
    otro_secreto = webhooks_svc.generar_secreto()
    ahora = 1_750_000_000
    cuerpo = '{"evento":"webhook.prueba","datos":{"ok":true}}'

    marca, firma = webhooks_svc.firmar_carga(secreto, cuerpo, marca_tiempo=ahora)
    assert marca == ahora
    assert firma.startswith("sha256=")
    assert webhooks_svc.verificar_firma(secreto, marca, cuerpo, firma, ahora=ahora + 10) is True

    # Mutación m1: verificar con otro secreto falla
    assert webhooks_svc.verificar_firma(otro_secreto, marca, cuerpo, firma, ahora=ahora + 10) is False
    # Mutación adicional: cuerpo alterado o firma malformada fallan
    assert webhooks_svc.verificar_firma(secreto, marca, cuerpo + " ", firma, ahora=ahora + 10) is False
    assert webhooks_svc.verificar_firma(secreto, marca, cuerpo, "invalida", ahora=ahora + 10) is False


def test_marca_fuera_de_ventana():
    """Escenario §5 + Mutación m2: marca a 301 s rechazada; dentro de 300 s aceptada."""
    secreto = webhooks_svc.generar_secreto()
    ahora = 1_750_000_000
    cuerpo = '{"evento":"webhook.prueba"}'

    marca_antigua = ahora - (webhooks_svc.VENTANA_SEGUNDOS + 1)  # 301 s atrás
    _, firma_antigua = webhooks_svc.firmar_carga(secreto, cuerpo, marca_tiempo=marca_antigua)
    assert webhooks_svc.verificar_firma(secreto, marca_antigua, cuerpo, firma_antigua, ahora=ahora) is False

    marca_futura = ahora + (webhooks_svc.VENTANA_SEGUNDOS + 1)  # 301 s en el futuro
    _, firma_futura = webhooks_svc.firmar_carga(secreto, cuerpo, marca_tiempo=marca_futura)
    assert webhooks_svc.verificar_firma(secreto, marca_futura, cuerpo, firma_futura, ahora=ahora) is False

    # Justo en el borde (300 s) sigue siendo válida
    marca_borde = ahora - webhooks_svc.VENTANA_SEGUNDOS
    _, firma_borde = webhooks_svc.firmar_carga(secreto, cuerpo, marca_tiempo=marca_borde)
    assert webhooks_svc.verificar_firma(secreto, marca_borde, cuerpo, firma_borde, ahora=ahora) is True


@pytest.mark.parametrize(
    ("url", "resolver"),
    [
        ("http://receptor.ejemplo.invalid/hook", _resolver_publico),
        ("https://127.0.0.1/hook", _resolver_publico),
        ("https://10.0.0.5/hook", _resolver_publico),
        ("https://172.16.0.1/hook", _resolver_publico),
        ("https://192.168.1.10/hook", _resolver_publico),
        ("https://169.254.169.254/latest/meta-data", _resolver_publico),
        ("https://[::1]/hook", _resolver_publico),
        ("https://224.0.0.1/hook", _resolver_publico),
        ("https://interno.ejemplo.invalid/hook", _resolver_privado),
        ("https://mixto.ejemplo.invalid/hook", lambda _h: [IP_PUBLICA_PRUEBA, "169.254.169.254"]),
        ("https://sin-dns.ejemplo.invalid/hook", lambda _h: []),
    ],
)
def test_url_interna_rechazada(url: str, resolver):
    """Escenario §5 + Mutación m3: rechaza http, loopback, privadas, metadatos y DNS privado."""
    with pytest.raises(ErrorNegocio) as exc_info:
        webhooks_svc.validar_url_webhook(url, resolver=resolver)
    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "WEBHOOK_URL_NO_PERMITIDA"


@pytest.mark.asyncio
async def test_url_interna_rechazada_http_y_eventos_503(monkeypatch):
    """Verifica 422 WEBHOOK_URL_NO_PERMITIDA, 422 WEBHOOK_EVENTO_DESCONOCIDO y 503 Fernet por HTTP."""
    clave = Fernet.generate_key().decode("ascii")
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.fetchone.return_value = (1,)
    mock_session.execute.return_value = mock_result
    app.dependency_overrides[get_session] = lambda: mock_session

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = {
                "X-User-ID": "u-admin",
                "X-Tenant-ID": "t-1",
                "X-Role": "admin_organizacion",
            }
            # 1. Sin WEBHOOKS_CLAVE_CIFRADO -> 503 WEBHOOKS_CIFRADO_NO_CONFIGURADO
            monkeypatch.delenv(webhooks_svc.VARIABLE_CLAVE_CIFRADO, raising=False)
            r503 = await client.post(
                RUTA_API,
                headers=headers,
                json={"url": "https://127.0.0.1/hook", "eventos": ["webhook.prueba"]},
            )
            assert r503.status_code == 503
            assert r503.json()["code"] == "WEBHOOKS_CIFRADO_NO_CONFIGURADO"

            # 2. Clave Fernet inválida -> 503
            monkeypatch.setenv(webhooks_svc.VARIABLE_CLAVE_CIFRADO, "clave-no-fernet")
            r503_inv = await client.post(
                RUTA_API,
                headers=headers,
                json={"url": "https://receptor.ejemplo.invalid/hook", "eventos": ["webhook.prueba"]},
            )
            assert r503_inv.status_code == 503
            assert r503_inv.json()["code"] == "WEBHOOKS_CIFRADO_NO_CONFIGURADO"

            # 3. Clave válida + URL interna -> 422 WEBHOOK_URL_NO_PERMITIDA
            monkeypatch.setenv(webhooks_svc.VARIABLE_CLAVE_CIFRADO, clave)
            r422_url = await client.post(
                RUTA_API,
                headers=headers,
                json={"url": "https://169.254.169.254/latest", "eventos": ["webhook.prueba"]},
            )
            assert r422_url.status_code == 422
            assert r422_url.json()["code"] == "WEBHOOK_URL_NO_PERMITIDA"

            # 4. Evento desconocido o lista vacía -> 422 WEBHOOK_EVENTO_DESCONOCIDO
            r422_ev = await client.post(
                RUTA_API,
                headers=headers,
                json={"url": "https://receptor.ejemplo.invalid/hook", "eventos": ["evento.inventado"]},
            )
            assert r422_ev.status_code == 422
            assert r422_ev.json()["code"] == "WEBHOOK_EVENTO_DESCONOCIDO"

            r422_vacio = await client.post(
                RUTA_API,
                headers=headers,
                json={"url": "https://receptor.ejemplo.invalid/hook", "eventos": []},
            )
            assert r422_vacio.status_code == 422
            assert r422_vacio.json()["code"] == "WEBHOOK_EVENTO_DESCONOCIDO"
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.mark.asyncio
async def test_entrega_con_reintentos(monkeypatch):
    """Escenario §5: 500/500/200 -> entregado en 3 intentos; 500x3 -> no entregado tras 3."""
    clave = Fernet.generate_key().decode("ascii")
    monkeypatch.setenv(webhooks_svc.VARIABLE_CLAVE_CIFRADO, clave)

    secreto = webhooks_svc.generar_secreto()
    secreto_cifrado = Fernet(clave.encode("ascii")).encrypt(secreto.encode("utf-8")).decode("ascii")
    suscripcion = {
        "id": str(uuid.uuid4()),
        "url": "https://receptor.ejemplo.invalid/avisos",
        "secreto_cifrado": secreto_cifrado,
        "activo": True,
    }

    # Caso 1: 500, 500, 200 contra servidor HTTP local real
    esperas: list[float] = []

    async def _esperar_ficticio(seg: float) -> None:
        esperas.append(seg)

    srv, recibidas = _servidor_local([500, 500, 200], secreto)
    try:
        transporte = _TransporteLocalHTTPS(srv.server_address[1])
        resultado = await webhooks_svc.entregar(
            suscripcion,
            "webhook.prueba",
            {"prueba": True},
            resolver=_resolver_publico,
            transporte=transporte,
            esperar=_esperar_ficticio,
        )
    finally:
        srv.shutdown()
        srv.server_close()

    assert resultado == {"entregado": True, "intentos": 3, "estado_http": 200}
    assert len(recibidas) == 3
    assert all(r["firma_ok"] for r in recibidas)
    assert esperas == [1, 2]

    # Caso 2: 500 siempre -> no entregado tras 3 intentos
    srv_fail, recibidas_fail = _servidor_local([500, 500, 500], secreto)
    try:
        transporte_fail = _TransporteLocalHTTPS(srv_fail.server_address[1])
        res_fail = await webhooks_svc.entregar(
            suscripcion,
            "webhook.prueba",
            {"prueba": False},
            resolver=_resolver_publico,
            transporte=transporte_fail,
            esperar=_esperar_ficticio,
        )
    finally:
        srv_fail.shutdown()
        srv_fail.server_close()

    assert res_fail == {"entregado": False, "intentos": 3, "estado_http": 500}
    assert len(recibidas_fail) == 3

    # Caso 3: 302 no sigue redirecciones y DNS rebinding en entrega se rechaza
    srv_redir, recibidas_redir = _servidor_local([302, 302, 302], secreto)
    try:
        transporte_redir = _TransporteLocalHTTPS(srv_redir.server_address[1])
        res_redir = await webhooks_svc.entregar(
            suscripcion,
            "webhook.prueba",
            {},
            resolver=_resolver_publico,
            transporte=transporte_redir,
            esperar=_esperar_ficticio,
        )
    finally:
        srv_redir.shutdown()
        srv_redir.server_close()

    assert res_redir == {"entregado": False, "intentos": 3, "estado_http": 302}
    assert len(recibidas_redir) == 3

    with pytest.raises(ErrorNegocio) as exc_rebinding:
        await webhooks_svc.entregar(
            suscripcion,
            "webhook.prueba",
            {},
            resolver=_resolver_privado,
            esperar=_esperar_ficticio,
        )
    assert exc_rebinding.value.status_code == 422
    assert exc_rebinding.value.code == "WEBHOOK_URL_NO_PERMITIDA"


# ---- Pruebas contra PostgreSQL 16 local con rol lopdp_app ----


@pytest.mark.asyncio
async def test_techo_de_webhooks(monkeypatch):
    """Escenario §5 + Mutación m4: techo 2 -> 3ra falla 409; tras desactivar una, crear vuelve a 201."""
    clave = Fernet.generate_key().decode("ascii")
    monkeypatch.setenv(webhooks_svc.VARIABLE_CLAVE_CIFRADO, clave)
    monkeypatch.setattr(webhooks_svc, "_resolver_dns_sistema", lambda host, _p=443: _resolver_publico(host))

    async def cuerpo(s: AsyncSession, ta: str, _tb: str, ua: str, _ub: str):
        await fijar_contexto_rls(s, ta, ua)

        async def _override_session():
            yield s

        app.dependency_overrides[get_session] = _override_session
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = {"X-User-ID": ua, "X-Tenant-ID": ta, "X-Role": "admin_organizacion"}

                r1 = await client.post(
                    RUTA_API,
                    headers=headers,
                    json={"url": "https://uno.ejemplo.invalid/hook", "eventos": ["webhook.prueba"]},
                )
                assert r1.status_code == 201, r1.text
                id1 = r1.json()["webhook"]["id"]

                r2 = await client.post(
                    RUTA_API,
                    headers=headers,
                    json={"url": "https://dos.ejemplo.invalid/hook", "eventos": ["webhook.prueba"]},
                )
                assert r2.status_code == 201, r2.text

                # Techo INICIAL = 2 -> techos reporta 2 activos
                techos = await techos_svc.obtener_techos_integracion(s, ta)
                assert techos["webhooks"] == {"maximo": 2, "activos": 2}

                # Mutación m4: 3ra suscripción sobre techo -> 409 TECHO_WEBHOOKS_ALCANZADO
                r3 = await client.post(
                    RUTA_API,
                    headers=headers,
                    json={"url": "https://tres.ejemplo.invalid/hook", "eventos": ["webhook.prueba"]},
                )
                assert r3.status_code == 409
                assert r3.json()["code"] == "TECHO_WEBHOOKS_ALCANZADO"

                # Desactivar libera un lugar y es definitivo
                r_des = await client.post(f"{RUTA_API}/{id1}/desactivar", headers=headers)
                assert r_des.status_code == 200
                assert r_des.json()["webhook"]["activo"] is False

                techos_tras = await techos_svc.obtener_techos_integracion(s, ta)
                assert techos_tras["webhooks"] == {"maximo": 2, "activos": 1}

                # Ahora sí se permite crear otra suscripción -> 201
                r4 = await client.post(
                    RUTA_API,
                    headers=headers,
                    json={"url": "https://cuatro.ejemplo.invalid/hook", "eventos": ["webhook.prueba"]},
                )
                assert r4.status_code == 201, r4.text

                # No se puede rotar ni probar una suscripción desactivada
                r_rot_des = await client.post(f"{RUTA_API}/{id1}/rotar-secreto", headers=headers)
                assert r_rot_des.status_code == 409
                r_prob_des = await client.post(f"{RUTA_API}/{id1}/probar", headers=headers)
                assert r_prob_des.status_code == 409
        finally:
            app.dependency_overrides.pop(get_session, None)

    await _con_bd_lopdp_app(cuerpo)


@pytest.mark.asyncio
async def test_secreto_nunca_en_el_listado(monkeypatch):
    """Escenario §5 + Mutación m5: secreto en claro solo al crear y rotar, nunca en GET."""
    clave = Fernet.generate_key().decode("ascii")
    monkeypatch.setenv(webhooks_svc.VARIABLE_CLAVE_CIFRADO, clave)
    monkeypatch.setattr(webhooks_svc, "_resolver_dns_sistema", lambda host, _p=443: _resolver_publico(host))

    async def cuerpo(s: AsyncSession, ta: str, _tb: str, ua: str, _ub: str):
        await fijar_contexto_rls(s, ta, ua)

        async def _override_session():
            yield s

        app.dependency_overrides[get_session] = _override_session
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                headers = {"X-User-ID": ua, "X-Tenant-ID": ta, "X-Role": "admin_organizacion"}

                creada = await client.post(
                    RUTA_API,
                    headers=headers,
                    json={"url": "https://secreto.ejemplo.invalid/hook", "eventos": ["webhook.prueba"]},
                )
                assert creada.status_code == 201
                datos_creada = creada.json()
                secreto_1 = datos_creada["secreto_en_claro"]
                assert len(secreto_1) >= 32
                assert "secreto_cifrado" not in datos_creada["webhook"]
                wh_id = datos_creada["webhook"]["id"]

                rotada = await client.post(f"{RUTA_API}/{wh_id}/rotar-secreto", headers=headers)
                assert rotada.status_code == 200
                datos_rotada = rotada.json()
                secreto_2 = datos_rotada["secreto_en_claro"]
                assert secreto_2 != secreto_1
                assert datos_rotada["webhook"]["rotada_en"] is not None
                assert "secreto_cifrado" not in datos_rotada["webhook"]

                listado = await client.get(RUTA_API, headers=headers)
                assert listado.status_code == 200
                cuerpo_json = listado.text
                filas = listado.json()["webhooks"]
                assert len(filas) == 1
                for campo_prohibido in ("secreto", "secreto_en_claro", "secreto_cifrado"):
                    assert campo_prohibido not in filas[0]
                assert secreto_1 not in cuerpo_json
                assert secreto_2 not in cuerpo_json
        finally:
            app.dependency_overrides.pop(get_session, None)

    await _con_bd_lopdp_app(cuerpo)


@pytest.mark.asyncio
async def test_webhooks_rls_aislamiento_tenant(monkeypatch):
    """Escenario §5: B no ve los webhooks de A por SQL ni por API, y no puede rotar/desactivar/probar los de A."""
    clave = Fernet.generate_key().decode("ascii")
    monkeypatch.setenv(webhooks_svc.VARIABLE_CLAVE_CIFRADO, clave)
    monkeypatch.setattr(webhooks_svc, "_resolver_dns_sistema", lambda host, _p=443: _resolver_publico(host))

    async def cuerpo(s: AsyncSession, ta: str, tb: str, ua: str, ub: str):
        # 1. Crear como tenant A
        await fijar_contexto_rls(s, ta, ua)
        creada, _ = await webhooks_svc.crear_suscripcion(
            s,
            ta,
            "https://aislamiento.ejemplo.invalid/hook",
            ["webhook.prueba"],
            ua,
            resolver=_resolver_publico,
        )
        wh_id = creada["id"]

        # 2. Consultar como tenant B bajo lopdp_app (RLS forzada)
        await fijar_contexto_rls(s, tb, ub)
        filas_sql = (await s.execute(text("SELECT id FROM webhooks_suscripciones"))).all()
        assert filas_sql == []
        assert await webhooks_svc.listar_suscripciones(s, tb) == []

        # 3. Intentar operar sobre el id de A desde tenant B -> 404 WEBHOOK_NO_ENCONTRADO
        for fn in (
            lambda: webhooks_svc.rotar_secreto(s, tb, wh_id, ub),
            lambda: webhooks_svc.desactivar_suscripcion(s, tb, wh_id, ub),
            lambda: webhooks_svc.probar_suscripcion(s, tb, wh_id, ub, resolver=_resolver_publico),
        ):
            with pytest.raises(ErrorNegocio) as exc_info:
                await fn()
            assert exc_info.value.status_code == 404
            assert exc_info.value.code == "WEBHOOK_NO_ENCONTRADO"

        # 4. lopdp_app no tiene privilegio DELETE sobre webhooks_suscripciones
        async with s.begin_nested() as sp:
            with pytest.raises(ProgrammingError):
                await s.execute(text("DELETE FROM webhooks_suscripciones WHERE id = :id"), {"id": wh_id})
            await sp.rollback()

    await _con_bd_lopdp_app(cuerpo)
