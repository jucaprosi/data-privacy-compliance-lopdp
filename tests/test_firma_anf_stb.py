# -*- coding: utf-8 -*-
"""Árbitro FIRMA-06: consumo de ANF STB v2 TEST y su API, contra TEST_DATABASE_URL (nunca producción).

ANF se sustituye con `httpx.MockTransport` siguiendo su ficha técnica; la base es real. La prueba
`test_ciclo_real_contra_anf_test` habla con ANF de verdad y solo corre con `ANF_STB_PRUEBA_REAL=1`
y credenciales en el entorno: las credenciales TEST no están en el repositorio.
"""
# ¤¤qa-engineer
# ¤firma-electronica
import asyncio
import base64
import hashlib
import json
import os
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app_core.config import config
from features.firma_electronica import firma_electronica_service as firma
from features.firma_electronica.services import anf_stb_client

pytestmark = pytest.mark.asyncio

RUTA = "/api/v1/firma/sesiones"
URL_TEST = "https://anf.invalid"
CLAVE = "clave-solo-pruebas-firma-06"
JWT = "jwt-solo-pruebas"
ID_ANF = "5d8e3e186dadc9eb5ff6ec09"
CEDULA_TEST = "1716760001"  # Publicada por ANF para su entorno de pruebas.
PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
PDF_FIRMADO = PDF + b"%firma-simulada\n"
SHA_PDF = hashlib.sha256(PDF).hexdigest()
SHA_FIRMADO = hashlib.sha256(PDF_FIRMADO).hexdigest()


class AnfFalso:
    """Servidor con las rutas y formas de respuesta de la ficha técnica de ANF."""

    def __init__(self):
        self.peticiones: list[httpx.Request] = []
        self.respuesta_signs = httpx.Response(200, json=ID_ANF)
        self.respuesta_resultado = httpx.Response(200, json="El documento doc-1 está en proceso de firma")

    def __call__(self, peticion: httpx.Request) -> httpx.Response:
        self.peticiones.append(peticion)
        if peticion.url.path == "/auth":
            return httpx.Response(200, json=JWT)
        if peticion.url.path == "/signs":
            return self.respuesta_signs
        assert peticion.url.path == f"/signs/{ID_ANF}/get-signed-documents"
        return self.respuesta_resultado

    def rutas(self, ruta: str) -> list[httpx.Request]:
        return [p for p in self.peticiones if p.url.path == ruta]

    def firmado(self, descripcion: str = "doc-1") -> None:
        self.respuesta_resultado = httpx.Response(200, json=[{
            "descripcion": descripcion,
            "firmantes": [{"id": CEDULA_TEST, "tipoCert": "1", "paginas": ["ultima(50, 50)"]}],
            "documento": base64.b64encode(PDF_FIRMADO).decode(),
        }])


@pytest.fixture
def anf(monkeypatch):
    servidor = AnfFalso()
    monkeypatch.setattr(config, "environment", "development")
    monkeypatch.setattr(config, "anf_stb_url", URL_TEST)
    monkeypatch.setattr(config, "anf_api_id", "smartcidi")
    monkeypatch.setattr(config, "anf_api_password", SecretStr(CLAVE))
    monkeypatch.setattr(config, "anf_api_token", SecretStr(""))
    monkeypatch.setattr(anf_stb_client, "_TRANSPORTE", httpx.MockTransport(servidor))
    return servidor


def _documento(descripcion: str = "doc-1") -> firma.DocumentoParaFirma:
    return firma.DocumentoParaFirma(
        documento_id=descripcion, tenant_id=str(uuid4()), nombre_archivo="doc.pdf",
        mime_type="application/pdf", sha256_original=SHA_PDF, tamano_bytes=len(PDF),
    )


# --- Cliente y compuerta, sin base de datos ---------------------------------------------------------

async def test_solicitud_cumple_el_contrato_de_anf(anf):
    solicitud = await firma.solicitar_firma_anf_stb(_documento(), CEDULA_TEST, PDF, ["1(50, 50)"])
    assert solicitud == ID_ANF

    auth = json.loads(anf.rutas("/auth")[0].content)
    assert auth == {"id": "smartcidi", "password": CLAVE}
    envio = anf.rutas("/signs")[0]
    assert envio.headers["Authorization"] == JWT  # ANF lo documenta sin el prefijo Bearer.
    cuerpo = json.loads(envio.content)
    assert cuerpo["certificadoEs"] is False and cuerpo["withTSU"] is True and "titular" not in cuerpo
    assert cuerpo["testigos"]["entorno"] == "DEV" and cuerpo["testigos"]["cliente"] == "SMART-CIDI"
    assert cuerpo["testigos"]["otp"] is True and cuerpo["testigos"]["porcentajeVerificacion"] == 100
    documento = cuerpo["documentos"][0]
    assert base64.b64decode(documento["documento"]) == PDF
    assert documento["firmantes"] == [
        {"id": CEDULA_TEST, "tipoCert": "1", "tamanioFuente": 10, "paginas": ["1(50, 50)"]}
    ]


async def test_token_fijo_sin_login(anf, monkeypatch):
    monkeypatch.setattr(config, "anf_api_id", "")
    monkeypatch.setattr(config, "anf_api_password", SecretStr(""))
    monkeypatch.setattr(config, "anf_api_token", SecretStr("jwt-fijo"))
    await firma.solicitar_firma_anf_stb(_documento(), CEDULA_TEST, PDF)
    assert anf.rutas("/auth") == []
    assert anf.rutas("/signs")[0].headers["Authorization"] == "jwt-fijo"


async def test_firmar_documento_anf_stb_consulta_hasta_terminar(anf, monkeypatch):
    llamadas = {"n": 0}
    consultar = anf_stb_client.consultar_documentos

    async def segunda_vez_listo(solicitud_id, descripcion):
        llamadas["n"] += 1
        if llamadas["n"] == 2:
            anf.firmado()
        return await consultar(solicitud_id, descripcion)

    monkeypatch.setattr(anf_stb_client, "consultar_documentos", segunda_vez_listo)
    resultado = await firma.firmar_documento_anf_stb(_documento(), CEDULA_TEST, PDF, esperas=(0, 0, 0))

    assert llamadas["n"] == 2
    assert resultado.estado == firma.EstadoFirma.FIRMADO and resultado.sha256_firmado == SHA_FIRMADO
    assert resultado.pdf_firmado == PDF_FIRMADO
    # Lo que ANF no entrega no se presenta como verificado.
    assert resultado.metadatos_auditoria["timestamp_tsa_fuente"] == "recepcion_plataforma"
    assert resultado.metadatos_auditoria["certificado_verificado"] is False
    assert resultado.certificado.acreditado_arcotel is False
    assert resultado.metadatos_auditoria["ambiente"] == "TEST"


async def test_firmar_sigue_en_proceso_tras_las_esperas(anf):
    with pytest.raises(firma.FirmaAnfEnProcesoError) as error:
        await firma.firmar_documento_anf_stb(_documento(), CEDULA_TEST, PDF, esperas=(0, 0, 0))
    assert error.value.solicitud_id == ID_ANF
    assert len(anf.rutas(f"/signs/{ID_ANF}/get-signed-documents")) == 3


async def test_esperas_por_defecto_son_las_de_anf():
    assert list(firma.ESPERAS_ANF_SEGUNDOS) == [30, 30, 30]


@pytest.mark.parametrize("estado,definitivo", [(400, True), (409, True), (500, False), (401, False)])
async def test_errores_de_anf(anf, estado, definitivo):
    anf.respuesta_signs = httpx.Response(estado, json={"code": "X", "message": "m", "typeCode": "BadConfigsSign"})
    with pytest.raises(firma.AnfStbError) as error:
        await firma.solicitar_firma_anf_stb(_documento(), CEDULA_TEST, PDF)
    assert error.value.tipo == "BadConfigsSign" and error.value.definitivo is definitivo


async def test_red_caida_no_es_rechazo(anf, monkeypatch):
    def sin_red(_):
        raise httpx.ConnectError("sin red")

    monkeypatch.setattr(anf_stb_client, "_TRANSPORTE", httpx.MockTransport(sin_red))
    with pytest.raises(firma.AnfStbError) as error:
        await firma.solicitar_firma_anf_stb(_documento(), CEDULA_TEST, PDF)
    assert error.value.tipo == "SinRespuesta" and error.value.definitivo is False


async def test_400_de_auth_no_es_rechazo_de_la_firma(anf, monkeypatch):
    def credenciales_malas(peticion):
        return httpx.Response(400, json={"code": "X", "message": "m", "typeCode": "DataNotFound"})

    monkeypatch.setattr(anf_stb_client, "_TRANSPORTE", httpx.MockTransport(credenciales_malas))
    with pytest.raises(firma.AnfStbError) as error:
        await firma.consultar_firma_anf_stb(_documento(), CEDULA_TEST, ID_ANF)
    assert error.value.definitivo is False


async def test_respuesta_que_no_es_pdf_se_rechaza(anf):
    anf.respuesta_resultado = httpx.Response(200, json=[{
        "descripcion": "doc-1", "documento": base64.b64encode(b"no soy pdf").decode(),
    }])
    with pytest.raises(firma.AnfStbError) as error:
        await firma.consultar_firma_anf_stb(_documento(), CEDULA_TEST, ID_ANF)
    assert error.value.tipo == "RespuestaInvalida" and error.value.definitivo is False


async def test_pdf_que_no_coincide_no_sale_a_la_red(anf):
    with pytest.raises(ValueError):
        await firma.solicitar_firma_anf_stb(_documento(), CEDULA_TEST, PDF + b"alterado")
    assert anf.peticiones == []


async def test_boceto_solo_como_fallback_en_app_env_test(monkeypatch):
    monkeypatch.setattr(config, "anf_stb_url", "")
    monkeypatch.setattr(config, "environment", "test")
    resultado = await firma.firmar_documento_anf_stb(_documento(), CEDULA_TEST, PDF)
    assert resultado.metadatos_auditoria["fase"] == "BBAP_boceto"

    monkeypatch.setattr(config, "environment", "development")
    with pytest.raises(firma.AnfStbNoConfiguradoError):
        await firma.firmar_documento_anf_stb(_documento(), CEDULA_TEST, PDF)


@pytest.mark.parametrize("campo,valor", [
    ("environment", "production"),
    ("anf_stb_url", "http://anf.invalid"),
    ("anf_stb_url", ""),
    ("anf_api_password", SecretStr("")),
])
async def test_falla_cerrado_sin_llamar_a_anf(anf, monkeypatch, campo, valor):
    monkeypatch.setattr(config, campo, valor)
    with pytest.raises(firma.AnfStbNoConfiguradoError):
        await firma.firmar_documento_anf_stb(_documento(), CEDULA_TEST, PDF)
    assert anf.peticiones == []


async def test_secretos_no_aparecen_al_imprimir_la_configuracion(anf):
    assert CLAVE not in repr(config)


async def test_xades_no_aplica(anf):
    with pytest.raises(ValueError):
        await firma.firmar_documento_anf_stb(_documento(), CEDULA_TEST, PDF, formato=firma.FormatoFirma.XADES_BES)
    assert anf.peticiones == []


# --- API contra la base real -------------------------------------------------------------------------

@pytest_asyncio.fixture
async def entorno(db_engine, anf):
    from app_core.db.session import fijar_contexto_rls, get_session, get_tenant_session
    from main import app

    url = os.environ.get("TEST_DATABASE_URL", "")
    assert url and "ep-late-hall-b50bpbk5" not in url, "Se requiere una rama de pruebas, nunca producción"
    sin_override = object()
    previos = {dep: app.dependency_overrides.pop(dep, sin_override) for dep in (get_session, get_tenant_session)}

    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    ta, tb = (str(uuid4()) for _ in range(2))
    try:
        async with factory() as s:
            for tenant in (ta, tb):
                await s.execute(
                    text(
                        "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                        "VALUES (:t, :t, :t, :t)"
                    ),
                    {"t": tenant},
                )
            await s.commit()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente:
            yield {"cliente": cliente, "a": ta, "b": tb, "anf": anf, "factory": factory}
    finally:
        for dep, previo in previos.items():
            if previo is not sin_override:
                app.dependency_overrides[dep] = previo
        async with factory() as s:
            for tenant in (ta, tb):
                await fijar_contexto_rls(s, tenant)
                await s.execute(text("DELETE FROM audit_events WHERE tenant_id = :t"), {"t": tenant})
                await s.execute(text("DELETE FROM firma_sessions WHERE tenant_id = :t"), {"t": tenant})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tenant})
            await s.commit()


def _h(tenant: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant}


async def _crear(entorno, tenant=None, **cambios) -> dict:
    cuerpo = {
        "documento_id": "doc-1", "firmante_id": CEDULA_TEST, "formato": "pdf",
        "proveedor": "anf", "sha256_original": SHA_PDF, **cambios,
    }
    r = await entorno["cliente"].post(RUTA, json=cuerpo, headers=_h(tenant or entorno["a"]))
    assert r.status_code == 201, r.text
    return r.json()


async def _enviar(entorno, firma_id: str, tenant=None, pdf: bytes = PDF, **cambios):
    return await entorno["cliente"].post(
        f"{RUTA}/{firma_id}/anf/enviar",
        json={"documento_base64": base64.b64encode(pdf).decode(), **cambios},
        headers=_h(tenant or entorno["a"]),
    )


async def _sincronizar(entorno, firma_id: str, tenant=None):
    return await entorno["cliente"].post(f"{RUTA}/{firma_id}/anf/sincronizar", headers=_h(tenant or entorno["a"]))


async def _estado(entorno, firma_id: str) -> dict:
    return (await entorno["cliente"].get(f"{RUTA}/{firma_id}", headers=_h(entorno["a"]))).json()


async def _acciones(entorno, tenant: str, firma_id: str) -> list[str]:
    from app_core.db.session import fijar_contexto_rls

    async with entorno["factory"]() as s:
        await fijar_contexto_rls(s, tenant)
        filas = await s.execute(
            text("SELECT action FROM audit_events WHERE tenant_id = :t AND entity_id = :e"),
            {"t": tenant, "e": firma_id},
        )
        return [f[0] for f in filas]


async def test_enviar_deja_pendiente_y_guarda_la_solicitud(entorno):
    creada = await _crear(entorno)
    r = await _enviar(entorno, creada["firma_id"], paginas=["primera(50, 100)", "2(200, 400)"])
    assert r.status_code == 202, r.text
    assert r.json()["estado"] == "pendiente_firma"
    cuerpo = json.loads(entorno["anf"].rutas("/signs")[0].content)
    assert cuerpo["documentos"][0]["firmantes"][0]["paginas"] == ["primera(50, 100)", "2(200, 400)"]
    assert "enviar_firma_anf" in await _acciones(entorno, entorno["a"], creada["firma_id"])


async def test_ciclo_completo_firma_la_sesion(entorno):
    creada = await _crear(entorno)
    assert (await _enviar(entorno, creada["firma_id"])).status_code == 202

    en_proceso = await _sincronizar(entorno, creada["firma_id"])
    assert en_proceso.status_code == 202 and en_proceso.json()["estado"] == "pendiente_firma"

    entorno["anf"].firmado()
    r = await _sincronizar(entorno, creada["firma_id"])
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "firmado" and r.json()["sha256_firmado"] == SHA_FIRMADO
    assert base64.b64decode(r.json()["documento_firmado_base64"]) == PDF_FIRMADO

    guardada = await _estado(entorno, creada["firma_id"])
    assert guardada["estado"] == "firmado" and guardada["sha256_firmado"] == SHA_FIRMADO
    assert guardada["certificado_json"]["ambiente"] == "TEST"
    assert guardada["certificado_json"]["timestamp_tsa_fuente"] == "recepcion_plataforma"
    assert guardada["certificado_json"]["anf_solicitud_id"] == ID_ANF
    acciones = await _acciones(entorno, entorno["a"], creada["firma_id"])
    assert "enviar_firma_anf" in acciones and "marcar_firmado" in acciones


async def test_doble_envio_no_paga_dos_veces(entorno):
    creada = await _crear(entorno)
    assert (await _enviar(entorno, creada["firma_id"])).status_code == 202
    segundo = await _enviar(entorno, creada["firma_id"])
    assert segundo.status_code == 409 and segundo.json()["code"] == "FIRMA_ESTADO_INVALIDO"
    assert len(entorno["anf"].rutas("/signs")) == 1


async def test_envios_simultaneos_llaman_a_anf_una_sola_vez(entorno):
    creada = await _crear(entorno)
    respuestas = await asyncio.gather(*(_enviar(entorno, creada["firma_id"]) for _ in range(3)))
    assert sorted(r.status_code for r in respuestas) == [202, 409, 409]
    assert len(entorno["anf"].rutas("/signs")) == 1


async def test_rechazo_de_anf_revierte_a_borrador(entorno):
    creada = await _crear(entorno)
    entorno["anf"].respuesta_signs = httpx.Response(
        409, json={"code": "ConflictError", "message": "m", "typeCode": "PDFEncriptado"}
    )
    r = await _enviar(entorno, creada["firma_id"])
    assert r.status_code == 422 and r.json()["code"] == "ANF_RECHAZO"
    assert r.json()["action_required"] == "PDFEncriptado"
    assert (await _estado(entorno, creada["firma_id"]))["estado"] == "borrador"

    entorno["anf"].respuesta_signs = httpx.Response(200, json=ID_ANF)
    assert (await _enviar(entorno, creada["firma_id"])).status_code == 202


async def test_error_definitivo_al_consultar_cierra_como_rechazado(entorno):
    creada = await _crear(entorno)
    await _enviar(entorno, creada["firma_id"])
    entorno["anf"].respuesta_resultado = httpx.Response(400, json={
        "code": "BadRequestError", "message": "m", "typeCode": "ErroresEncontrados",
        "errores": [{"tipo": "Desconocido", "descripcion": "dato del titular"}],
    })
    r = await _sincronizar(entorno, creada["firma_id"])
    assert r.status_code == 200 and r.json() == {
        "firma_id": creada["firma_id"], "estado": "rechazado", "anf_error": "ErroresEncontrados",
    }
    assert (await _estado(entorno, creada["firma_id"]))["estado"] == "rechazado"
    assert "rechazar_firma_anf" in await _acciones(entorno, entorno["a"], creada["firma_id"])
    assert (await _sincronizar(entorno, creada["firma_id"])).status_code == 409


async def test_anf_caido_deja_la_sesion_pendiente(entorno):
    creada = await _crear(entorno)
    await _enviar(entorno, creada["firma_id"])
    entorno["anf"].respuesta_resultado = httpx.Response(500, text="fallo")
    r = await _sincronizar(entorno, creada["firma_id"])
    assert r.status_code == 502 and r.json()["code"] == "ANF_NO_DISPONIBLE"
    assert (await _estado(entorno, creada["firma_id"]))["estado"] == "pendiente_firma"


async def test_aislamiento_entre_organizaciones(entorno):
    creada = await _crear(entorno)
    r = await _enviar(entorno, creada["firma_id"], tenant=entorno["b"])
    assert r.status_code == 404 and r.json()["code"] == "FIRMA_SESION_NO_ENCONTRADA"
    assert (await _sincronizar(entorno, creada["firma_id"], tenant=entorno["b"])).status_code == 404
    assert entorno["anf"].rutas("/signs") == []


async def test_sesion_de_otro_proveedor_no_se_envia(entorno):
    creada = await _crear(entorno, proveedor="universign")
    r = await _enviar(entorno, creada["firma_id"])
    assert r.status_code == 409 and r.json()["code"] == "FIRMA_PROVEEDOR_INVALIDO"
    assert entorno["anf"].rutas("/signs") == []


@pytest.mark.parametrize("pdf", [PDF + b"alterado", b"no soy un pdf"])
async def test_documento_invalido_no_sale_a_la_red(entorno, pdf):
    creada = await _crear(entorno)
    r = await _enviar(entorno, creada["firma_id"], pdf=pdf)
    assert r.status_code == 422 and r.json()["code"] == "FIRMA_DOCUMENTO_INVALIDO"
    assert (await _estado(entorno, creada["firma_id"]))["estado"] == "borrador"
    assert entorno["anf"].peticiones == []


async def test_paginas_con_formato_incorrecto(entorno):
    creada = await _crear(entorno)
    assert (await _enviar(entorno, creada["firma_id"], paginas=["en la 1"])).status_code == 422


async def test_sincronizar_sin_envio_previo(entorno):
    creada = await _crear(entorno)
    r = await _sincronizar(entorno, creada["firma_id"])
    assert r.status_code == 409 and r.json()["code"] == "FIRMA_ESTADO_INVALIDO"


async def test_api_nunca_usa_el_boceto(entorno, monkeypatch):
    monkeypatch.setattr(config, "anf_stb_url", "")
    monkeypatch.setattr(config, "environment", "test")
    creada = await _crear(entorno)
    r = await _enviar(entorno, creada["firma_id"])
    assert r.status_code == 503 and r.json()["code"] == "ANF_NO_CONFIGURADO"
    assert (await _estado(entorno, creada["firma_id"]))["estado"] == "borrador"


# --- ANF real -----------------------------------------------------------------------------------------

@pytest.mark.skipif(
    os.environ.get("ANF_STB_PRUEBA_REAL") != "1" or not anf_stb_client.esta_configurado(),
    reason="Requiere ANF_STB_PRUEBA_REAL=1 y credenciales TEST de ANF en el entorno.",
)
async def test_ciclo_real_contra_anf_test():
    resultado = await firma.firmar_documento_anf_stb(_documento(f"firma-06-{uuid4().hex[:8]}"), CEDULA_TEST, PDF)
    assert resultado.estado == firma.EstadoFirma.FIRMADO and resultado.pdf_firmado.startswith(b"%PDF-")
