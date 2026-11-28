# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤notificaciones ¤arbitro
"""NOTIF-03: correo de las versiones por revisar y de sus recordatorios, por SMTP con TLS.

Sin red real: un servidor `aiosmtpd` en 127.0.0.1 con un certificado de `trustme`. Cada prueba documenta su
mutación: el cambio en el código que la pondría en rojo.
"""
import asyncio
import json
import logging
import socket
import ssl
import threading
import time
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
import trustme
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import AuthResult

from features.notificaciones.domain import avisos as av
from features.notificaciones.domain.models import (
    CanalNotificacion,
    CorreoLoteNotificacion,
    Destinatario,
    EstadoEnvio,
)
from features.notificaciones.services import adaptadores, correo_versiones
from features.notificaciones.services.adaptadores import (
    ConfigSmtp,
    EstadoSmtp,
    NotificadorNoConfigurado,
    NotificadorSmtp,
    VentanaTope,
)

PROHIBIDAS_R3 = ["conforme", "cumple", "garantiza", "certificado", "legal"]
PROHIBIDAS_FORMA = ["undefined", "null", "None", "{", "}", ", ,", "  "]
HOY = date(2026, 11, 25)
BASE_URL = "https://app.prueba.invalid"
SECRETO = "contrasena-de-prueba-nunca-real"


# ----------------------------------------------------------------------------------------- servidor SMTP falso
class _Recibidos:
    def __init__(self):
        self.mensajes: list = []

    async def handle_DATA(self, server, session, envelope):  # noqa: N802 - nombre fijo de aiosmtpd
        self.mensajes.append(envelope)
        return "250 OK"


def _autenticar(server, session, envelope, mechanism, auth_data):
    clave = getattr(auth_data, "password", b"")
    return AuthResult(success=clave in (SECRETO, SECRETO.encode()))


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def ca():
    return trustme.CA()


@pytest.fixture(scope="module")
def ca_ajena():
    return trustme.CA()


def _contexto_servidor(autoridad) -> ssl.SSLContext:
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    autoridad.issue_cert("127.0.0.1").configure_cert(ctx)
    return ctx


def _contexto_cliente(autoridad) -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    autoridad.configure_trust(ctx)
    return ctx


@pytest.fixture
def servidor(ca, monkeypatch):
    """Fábrica de servidores: modo `starttls`, `ssl` o `plano` (sin TLS). Todos se cierran al terminar."""
    abiertos: list[Controller] = []

    def crear(modo: str = "starttls", autoridad=None):
        recibidos = _Recibidos()
        puerto = _puerto_libre()
        contexto = _contexto_servidor(autoridad or ca)
        opciones = {"authenticator": _autenticar, "auth_required": False, "auth_require_tls": modo != "plano"}
        if modo == "starttls":
            opciones.update(tls_context=contexto, require_starttls=True)
        elif modo == "ssl":
            opciones.update(ssl_context=contexto, auth_require_tls=False)  # el transporte ya es TLS
        elif modo == "plano":
            opciones.update(auth_require_tls=False)
        control = Controller(recibidos, hostname="127.0.0.1", port=puerto, ready_timeout=10, **opciones)
        control.start()
        abiertos.append(control)
        # 465 y 587 no se pueden abrir sin privilegios: la prueba registra su puerto libre con el modo que toca.
        monkeypatch.setitem(NotificadorSmtp.MODOS_POR_PUERTO, puerto, "ssl" if modo == "ssl" else "starttls")
        return recibidos, puerto

    yield crear
    for c in abiertos:
        c.stop()


def _config(puerto: int, **extra) -> ConfigSmtp:
    return ConfigSmtp(host="127.0.0.1", puerto=puerto, usuario="avisos-prueba", contrasena=SECRETO,
                      remitente="avisos@prueba.invalid", **extra)


def _correo(aviso_id="aviso-1", email="ana@prueba.invalid", **extra) -> CorreoLoteNotificacion:
    d = Destinatario(user_id="u1", email=email, nombre="Ana", tenant_id="")
    return correo_versiones.construir_correo(
        aviso_id=aviso_id, destinatario=d, plantilla="Política de privacidad",
        motivo="Motivo del cambio: petición.", enlace=f"{BASE_URL}/biblioteca?version=v1", **extra)


# ------------------------------------------------------------------------------- R1b · configuración (m2)
VALIDA = {"host": "smtp.prueba.invalid", "puerto": 587, "usuario": "u", "contrasena": SECRETO,
          "remitente": "avisos@prueba.invalid"}


def test_configuracion_valida_y_tope_por_defecto():
    cfg = adaptadores.leer_config_smtp(json.dumps(VALIDA))
    assert cfg is not None and cfg.puerto == 587 and cfg.tope_hora == 50
    assert adaptadores.leer_config_smtp(json.dumps({**VALIDA, "tope_hora": 2})).tope_hora == 2
    assert SECRETO not in repr(cfg), "la contraseña no puede salir en repr"


@pytest.mark.parametrize("valor", [
    None, "", "no es json", "[]", json.dumps({**VALIDA, "host": ""}), json.dumps({**VALIDA, "puerto": 25}),
    json.dumps({**VALIDA, "puerto": "587"}), json.dumps({**VALIDA, "tope_hora": 0}),
    json.dumps({**VALIDA, "tope_hora": "2"}), json.dumps({**VALIDA, "remitente": "sin-arroba"}),
    *[json.dumps({k: v for k, v in VALIDA.items() if k != campo}) for campo in VALIDA],
])
def test_configuracion_ausente_o_invalida_no_es_proveedor(valor):
    assert adaptadores.leer_config_smtp(valor) is None


def test_sin_configuracion_sigue_el_notificador_no_configurado(monkeypatch, caplog):
    """Mutación m2: lanzar un error cuando no hay proveedor (o devolver un SMTP vacío) da rojo."""
    monkeypatch.delenv("NOTIF_SMTP_CONFIG", raising=False)
    with caplog.at_level(logging.DEBUG):
        n = correo_versiones.notificador_de_correo()
    assert isinstance(n.interno, NotificadorNoConfigurado)
    monkeypatch.setenv("NOTIF_SMTP_CONFIG", "{no es json " + SECRETO)
    with caplog.at_level(logging.DEBUG):
        n = correo_versiones.notificador_de_correo()
    assert isinstance(n.interno, NotificadorNoConfigurado)
    assert SECRETO not in caplog.text, "el valor del secreto nunca se registra"


def test_con_configuracion_el_notificador_es_smtp(monkeypatch):
    monkeypatch.setenv("NOTIF_SMTP_CONFIG", json.dumps(VALIDA))
    n = correo_versiones.notificador_de_correo()
    assert isinstance(n.interno, NotificadorSmtp)
    assert correo_versiones.notificador_de_correo().interno is n.interno, "la ventana del tope es de la instancia"


def test_la_compuerta_entrega_el_notificador_configurado(monkeypatch):
    from features.notificaciones import notificaciones_service as svc

    monkeypatch.delenv("NOTIF_SMTP_CONFIG", raising=False)
    assert isinstance(svc.notificador_configurado().interno, NotificadorNoConfigurado)
    monkeypatch.setenv("NOTIF_SMTP_CONFIG", json.dumps(VALIDA))
    assert isinstance(svc.notificador_configurado().interno, NotificadorSmtp)
    assert svc.NotificadorSmtp is NotificadorSmtp


# ------------------------------------------------------------------------------------- R1a · TLS obligatorio
def test_solo_se_admiten_465_con_ssl_y_587_con_starttls():
    assert dict(NotificadorSmtp.MODOS_POR_PUERTO) == {465: "ssl", 587: "starttls"}
    assert NotificadorSmtp.TIMEOUT_S == 10


@pytest.mark.asyncio
@pytest.mark.parametrize("modo", ["starttls", "ssl"])
async def test_envia_con_tls_y_verifica_certificado(servidor, ca, modo):
    recibidos, puerto = servidor(modo)
    n = NotificadorSmtp(_config(puerto), contexto_ssl=_contexto_cliente(ca))
    r = await n.enviar_correo(_correo())
    assert r.estado == EstadoEnvio.ENVIADO, r.error_detalle
    assert len(recibidos.mensajes) == 1
    assert recibidos.mensajes[0].rcpt_tos == ["ana@prueba.invalid"]
    assert recibidos.mensajes[0].mail_from == "avisos@prueba.invalid"


@pytest.mark.asyncio
async def test_servidor_sin_starttls_no_recibe_nada(servidor, ca):
    """Mutación m6: aceptar texto plano cuando el servidor no ofrece STARTTLS da rojo."""
    recibidos, puerto = servidor("plano")
    n = NotificadorSmtp(_config(puerto), contexto_ssl=_contexto_cliente(ca))
    r = await n.enviar_correo(_correo())
    assert r.estado == EstadoEnvio.FALLIDO and r.error_detalle.startswith("error_de_configuracion")
    assert recibidos.mensajes == []


@pytest.mark.asyncio
@pytest.mark.parametrize("modo", ["starttls", "ssl"])
async def test_certificado_que_no_es_de_confianza_no_envia(servidor, ca, ca_ajena, modo):
    """Mutación m6: desactivar la verificación del certificado (CERT_NONE, check_hostname=False) da rojo."""
    recibidos, puerto = servidor(modo, autoridad=ca_ajena)
    n = NotificadorSmtp(_config(puerto), contexto_ssl=_contexto_cliente(ca))
    r = await n.enviar_correo(_correo())
    assert r.estado == EstadoEnvio.FALLIDO and r.error_detalle.startswith("error_de_configuracion")
    assert recibidos.mensajes == []


@pytest.mark.asyncio
async def test_el_contexto_por_defecto_verifica_certificado_y_nombre(servidor):
    """Mutación m6: un contexto sin verificación por defecto da rojo (la CA de la prueba no está en el sistema)."""
    recibidos, puerto = servidor("starttls")
    n = NotificadorSmtp(_config(puerto))
    ctx = n._contexto()
    assert ctx.verify_mode == ssl.CERT_REQUIRED and ctx.check_hostname is True
    r = await n.enviar_correo(_correo())
    assert r.estado == EstadoEnvio.FALLIDO and recibidos.mensajes == []


@pytest.mark.asyncio
async def test_otro_puerto_es_error_de_configuracion_y_no_abre_conexion(monkeypatch):
    """Mutación m6: permitir el 25 (o cualquier puerto sin TLS) da rojo."""
    def prohibido(*a, **k):
        raise AssertionError("no debe abrirse ninguna conexión")

    monkeypatch.setattr(adaptadores.smtplib, "SMTP", prohibido)
    monkeypatch.setattr(adaptadores.smtplib, "SMTP_SSL", prohibido)
    for puerto in (25, 2525, 0):
        r = await NotificadorSmtp(_config(puerto)).enviar_correo(_correo())
        assert r.estado == EstadoEnvio.FALLIDO and r.error_detalle.startswith("error_de_configuracion")


@pytest.mark.asyncio
async def test_destinatario_vacio_se_descarta(servidor, ca):
    recibidos, puerto = servidor("starttls")
    r = await NotificadorSmtp(_config(puerto), contexto_ssl=_contexto_cliente(ca)).enviar_correo(_correo(email="  "))
    assert r.estado == EstadoEnvio.DESCARTADO_SIN_DESTINATARIO and recibidos.mensajes == []


@pytest.mark.asyncio
async def test_contrasena_equivocada_falla_sin_publicarla(servidor, ca, caplog):
    recibidos, puerto = servidor("starttls")
    cfg = ConfigSmtp(host="127.0.0.1", puerto=puerto, usuario="u", contrasena="otra", remitente="a@prueba.invalid")
    r = await NotificadorSmtp(cfg, contexto_ssl=_contexto_cliente(ca)).enviar_correo(_correo())
    assert r.estado == EstadoEnvio.FALLIDO and recibidos.mensajes == []
    assert "otra" not in (r.error_detalle or "")


# ------------------------------------------------------------------------------------------- R1e · tope
def test_ventana_deslizante_en_memoria():
    t = [1000.0]
    v = VentanaTope(2, reloj=lambda: t[0])
    assert [v.reservar(), v.reservar(), v.reservar()] == [True, True, False]
    t[0] += 3599
    assert v.reservar() is False
    t[0] += 2
    assert v.reservar() is True, "pasada la hora, la ventana se libera"


@pytest.mark.asyncio
async def test_pasado_el_tope_queda_como_tope_sin_reintentos(servidor, ca):
    """Mutación m7: quitar el tope, o reintentar el correo frenado, da rojo."""
    recibidos, puerto = servidor("starttls")
    n = NotificadorSmtp(_config(puerto, tope_hora=2), contexto_ssl=_contexto_cliente(ca))
    estados = [(await n.enviar_correo(_correo(aviso_id=f"a{i}"))).estado for i in range(3)]
    assert estados == [EstadoEnvio.ENVIADO, EstadoEnvio.ENVIADO, EstadoSmtp.TOPE]
    assert len(recibidos.mensajes) == 2


# ------------------------------------------------------------------- R3 · textos (m3, m4, m5), sin base
VARIANTES = [
    av.motivo(origen="resolucion", norma="Resolución 1", articulo="artículo 4", vigencia=date(2026, 12, 5), hoy=HOY),
    av.motivo(origen="resolucion", norma="Resolución 1", vigencia=HOY, hoy=HOY),
    av.motivo(origen="resolucion", norma="Resolución 1", vigencia=date(2026, 11, 1), hoy=HOY),
    av.motivo(origen="resolucion", norma="Resolución 1", vigencia=None, hoy=HOY),
    av.motivo(origen="peticion", nombre="Ana", texto="Actualizar el plazo", hoy=HOY),
    av.motivo(origen="peticion", hoy=HOY),
]
RECORDATORIOS = [
    av.recordatorio(vigencia=date(2026, 12, 5), hoy=HOY),
    av.recordatorio(vigencia=date(2026, 11, 26), hoy=HOY),
    av.recordatorio(vigencia=HOY, hoy=HOY),
    av.recordatorio(vigencia=None, hoy=HOY, creado=HOY - timedelta(days=5)),
    av.recordatorio(vigencia=date(2026, 11, 1), hoy=HOY, creado=HOY - timedelta(days=1)),
]


def _construir(motivo, recordatorio=None, nombre="Ana"):
    d = Destinatario(user_id="u1", email="ana@prueba.invalid", nombre=nombre, tenant_id="")
    return correo_versiones.construir_correo(
        aviso_id="a1", destinatario=d, plantilla="Política de privacidad", motivo=motivo,
        enlace=f"{BASE_URL}/biblioteca?version=v1", recordatorio=recordatorio)


def _registro_de_la_plataforma(caplog) -> str:
    """Solo lo que registra la plataforma; el servidor falso (`mail.log`) registra sus propias conversaciones."""
    return " | ".join(r.getMessage() for r in caplog.records if r.name.startswith("features"))


def _sin_basura(texto: str) -> None:
    for p in PROHIBIDAS_R3 + PROHIBIDAS_FORMA:
        assert p not in texto, (p, texto)


@pytest.mark.parametrize("motivo", VARIANTES)
def test_el_correo_lleva_la_misma_linea_que_el_aviso_y_sin_basura(motivo):
    """Mutación m4: un correo sin fecha que imprime «entra en vigencia el None» da rojo.
    Mutación m5: un texto del correo distinto del del aviso da rojo."""
    c = _construir(motivo)
    assert c.asunto == "Versión por revisar: Política de privacidad" == av.titulo("Política de privacidad")
    assert motivo in c.cuerpo_texto
    assert c.cuerpo_texto == (
        f"Hola, Ana: Hay una versión nueva de la plantilla «Política de privacidad» pendiente de revisión técnica. "
        f"{motivo} Revísala en la plataforma: {BASE_URL}/biblioteca?version=v1. "
        "Recibes este correo porque tienes el permiso de revisión técnica de la Biblioteca.")
    _sin_basura(c.cuerpo_texto)
    _sin_basura(c.asunto)
    assert c.lote_id == "a1" and c.canal == CanalNotificacion.CORREO and c.tareas == ()


@pytest.mark.parametrize("recordatorio", RECORDATORIOS)
def test_recordatorio_lleva_el_texto_de_notif02_r3_tras_el_motivo(recordatorio):
    """Mutación m3: escribir «cumple» (o cualquier palabra de R3) en el texto da rojo."""
    motivo = VARIANTES[0]
    c = _construir(motivo, recordatorio)
    assert c.asunto == "Recordatorio: Política de privacidad sigue por revisar"
    assert f"{motivo} {recordatorio} Revísala en la plataforma:" in c.cuerpo_texto
    _sin_basura(c.cuerpo_texto)
    _sin_basura(c.asunto)


def test_recordatorio_de_fecha_futura_dice_faltan_n_dias():
    c = _construir(VARIANTES[0], av.recordatorio(vigencia=date(2026, 12, 2), hoy=HOY))
    assert "(faltan 7 días)" in c.cuerpo_texto


def test_sin_nombre_no_deja_huecos_ni_inyecta_cabeceras():
    assert _construir(VARIANTES[0], nombre="").cuerpo_texto.startswith("Hola: Hay una versión nueva")
    c = _construir(VARIANTES[0], nombre="Ana\r\nBcc: x@y.invalid")
    assert "\r" not in c.cuerpo_texto and "\n" not in c.cuerpo_texto
    d = Destinatario(user_id="u", email="a@b.invalid", nombre="N", tenant_id="")
    c = correo_versiones.construir_correo(aviso_id="a", destinatario=d, plantilla="P\r\nBcc: x@y.invalid",
                                          motivo="m.", enlace=f"{BASE_URL}/b")
    assert "\r" not in c.asunto and "\n" not in c.asunto
    html = correo_versiones.construir_correo(
        aviso_id="a", destinatario=d, plantilla="<b>x</b>", motivo="m.", enlace=f"{BASE_URL}/b").cuerpo_html
    assert "&lt;b&gt;x&lt;/b&gt;" in html and "<b>" not in html


# --------------------------------------------------------------- con base (PostgreSQL): envío tras el commit
from tests.test_norm05_privilegios_backend import como_app, propietario  # noqa: E402,F401 - fixtures de NORM-05
from tests.test_notif02_avisos import (  # noqa: E402,F401
    HAY_BASE,
    Pasillos,
    _avisos,
    _usuario,
    _version,
    con_base,
    pasillos,
)

if HAY_BASE:
    from features.notificaciones.services import avisos_plataforma as srv


@pytest.fixture
def operadores(monkeypatch):
    """Doble del pasillo de la plataforma: correo y nombre de cada revisor."""
    from app_core.pasillo import plataforma

    def poner(*usuarios):
        async def listar(session):
            return [{"usuario_id": u, "nombre": "Ana", "email": f"{u}@prueba.invalid", "ha_entrado": True}
                    for u in usuarios]
        monkeypatch.setattr(plataforma, "listar_operadores_activos", listar)
    return poner


@con_base
@pytest.mark.asyncio
async def test_db_aviso_nuevo_envia_un_correo_con_asunto_y_enlace(propietario, como_app, pasillos, operadores, servidor, ca, caplog):  # noqa: F811
    """Mutación m1: no enviar el correo al crear el aviso da rojo."""
    u = await _usuario(propietario)
    pasillos(Pasillos([_version("v-m1")], [u]))
    operadores(u)
    recibidos, puerto = servidor("starttls")
    n = NotificadorSmtp(_config(puerto), contexto_ssl=_contexto_cliente(ca))
    with caplog.at_level(logging.DEBUG):
        async with como_app() as s:
            assert (await srv.sincronizar(s, notificador=n, app_base_url=BASE_URL))["creados"] == 1
            await s.commit()
    assert len(recibidos.mensajes) == 1
    for dato in (f"{u}@prueba.invalid", "Hola, Ana", "pendiente de revisión", "Versión por revisar", SECRETO):
        assert dato not in _registro_de_la_plataforma(caplog), "ni el envío exitoso registra datos personales (R4)"
    cuerpo = recibidos.mensajes[0].content.decode("utf-8", "replace")
    assert "Subject: =?" in cuerpo or "Subject: Versi" in cuerpo
    from email import message_from_bytes, policy

    m = message_from_bytes(recibidos.mensajes[0].original_content, policy=policy.default)
    assert m["Subject"] == "Versión por revisar: Política"
    assert m["To"] == f"{u}@prueba.invalid"
    texto = m.get_body(("plain",)).get_content()
    assert f"{BASE_URL}/biblioteca?version=v-m1" in texto and "Hola, Ana:" in texto
    # El mismo aviso ya existe: sincronizar de nuevo no repite el correo.
    async with como_app() as s:
        assert (await srv.sincronizar(s, notificador=n, app_base_url=BASE_URL))["creados"] == 0
        await s.commit()
    assert len(recibidos.mensajes) == 1


@con_base
@pytest.mark.asyncio
async def test_db_sin_proveedor_el_aviso_se_crea_igual(propietario, como_app, pasillos, operadores, monkeypatch):  # noqa: F811
    """Mutación m2: lanzar un error cuando no hay proveedor da rojo."""
    monkeypatch.delenv("NOTIF_SMTP_CONFIG", raising=False)
    monkeypatch.setenv("APP_BASE_URL", BASE_URL)
    u = await _usuario(propietario)
    pasillos(Pasillos([_version("v-m2")], [u]))
    operadores(u)
    async with como_app() as s:
        assert (await srv.sincronizar(s))["creados"] == 1
        await s.commit()
    assert len(await _avisos(como_app, u)) == 1


@con_base
@pytest.mark.asyncio
async def test_db_recordatorio_envia_correo_con_el_texto_de_r3(propietario, como_app, pasillos, operadores, servidor, ca):  # noqa: F811
    """Mutación m3: escribir «cumple» en el recordatorio da rojo; m1: no enviarlo en el recordatorio, también."""
    u = await _usuario(propietario)
    pasillos(Pasillos([_version("v-rec")], [u], vigencia=datetime.now(timezone.utc).date() + timedelta(days=30)))
    operadores(u)
    recibidos, puerto = servidor("starttls")
    n = NotificadorSmtp(_config(puerto), contexto_ssl=_contexto_cliente(ca))
    async with como_app() as s:
        await srv.sincronizar(s, notificador=n, app_base_url=BASE_URL)
        await s.commit()
    assert len(recibidos.mensajes) == 1
    async with como_app() as s:
        r = await srv.sincronizar(s, datetime.now(timezone.utc) + timedelta(days=24, hours=1),
                                  notificador=n, app_base_url=BASE_URL)
        await s.commit()
    assert r["recordatorios"] == 1 and len(recibidos.mensajes) == 2
    from email import message_from_bytes, policy

    m = message_from_bytes(recibidos.mensajes[1].original_content, policy=policy.default)
    assert m["Subject"] == "Recordatorio: Política sigue por revisar"
    texto = m.get_body(("plain",)).get_content()
    assert "(faltan 6 días)" in texto
    _sin_basura(texto)


@con_base
@pytest.mark.asyncio
async def test_db_tope_de_dos_con_tres_avisos(propietario, como_app, pasillos, operadores, servidor, ca, caplog):  # noqa: F811
    """Mutación m7: quitar el tope, o reintentar el correo frenado, da rojo."""
    u = await _usuario(propietario)
    pasillos(Pasillos([_version("v-t1"), _version("v-t2"), _version("v-t3")], [u]))
    operadores(u)
    recibidos, puerto = servidor("starttls")
    n = NotificadorSmtp(_config(puerto, tope_hora=2), contexto_ssl=_contexto_cliente(ca))
    with caplog.at_level(logging.INFO):
        async with como_app() as s:
            assert (await srv.sincronizar(s, notificador=n, app_base_url=BASE_URL))["creados"] == 3
            await s.commit()
    assert len(recibidos.mensajes) == 2
    assert len(await _avisos(como_app, u)) == 3, "los tres avisos están en la campana"
    assert "TOPE" in caplog.text.upper() or "tope" in caplog.text
    async with como_app() as s:  # otra corrida: no hay avisos nuevos y el frenado no se reintenta
        await srv.sincronizar(s, notificador=n, app_base_url=BASE_URL)
        await s.commit()
    assert len(recibidos.mensajes) == 2


class _VerificaCommit:
    """Notificador que, al ser llamado, comprueba desde otra conexión que el aviso ya está confirmado."""

    def __init__(self, propietario, usuario):
        self.propietario, self.usuario, self.visto = propietario, usuario, None

    async def enviar_correo(self, correo):
        from sqlalchemy import text

        async with self.propietario() as s:
            self.visto = (await s.execute(text(
                "SELECT count(*) FROM avisos_plataforma WHERE id=:id"), {"id": correo.lote_id})).scalar_one()
        from features.notificaciones.domain.models import ResultadoDespacho

        return ResultadoDespacho(despacho_id="d", lote_id=correo.lote_id, destinatario_email=correo.destinatario.email,
                                 estado=EstadoEnvio.ENVIADO)


@con_base
@pytest.mark.asyncio
async def test_db_el_correo_sale_despues_del_commit(propietario, como_app, pasillos, operadores):  # noqa: F811
    """Mutación m8: enviar antes del commit da rojo (el aviso no se vería desde otra conexión)."""
    u = await _usuario(propietario)
    pasillos(Pasillos([_version("v-c")], [u]))
    operadores(u)
    n = _VerificaCommit(propietario, u)
    async with como_app() as s:
        await srv.sincronizar(s, notificador=n, app_base_url=BASE_URL)  # sin commit propio de la prueba
    assert n.visto == 1


@con_base
@pytest.mark.asyncio
async def test_db_servidor_mudo_termina_por_timeout_sin_datos_personales(propietario, como_app, pasillos, operadores, caplog):  # noqa: F811
    """Mutación m8: escribir el destinatario, el asunto o el cuerpo en el registro, o no acotar el tiempo, da rojo."""
    u = await _usuario(propietario)
    pasillos(Pasillos([_version("v-mudo")], [u]))
    operadores(u)
    mudo = socket.socket()
    mudo.bind(("127.0.0.1", 0))
    mudo.listen(5)
    puerto = mudo.getsockname()[1]
    NotificadorSmtp.MODOS_POR_PUERTO[puerto] = "starttls"
    try:
        n = NotificadorSmtp(_config(puerto), timeout=0.5)
        t0 = time.monotonic()
        with caplog.at_level(logging.DEBUG):
            async with como_app() as s:
                await srv.sincronizar(s, notificador=n, app_base_url=BASE_URL)
                await s.commit()
        assert time.monotonic() - t0 < 8
    finally:
        NotificadorSmtp.MODOS_POR_PUERTO.pop(puerto, None)
        mudo.close()
    avisos = await _avisos(como_app, u)
    assert len(avisos) == 1, "el aviso queda confirmado aunque el correo falle"
    registro = _registro_de_la_plataforma(caplog)
    assert avisos[0]["id"] in registro and "SMTPServerDisconnected" in registro  # smtplib convierte el timeout
    for dato in (f"{u}@prueba.invalid", "Versión por revisar", "Hola, Ana", "pendiente de revisión", SECRETO, BASE_URL):
        assert dato not in registro, dato


@con_base
@pytest.mark.asyncio
async def test_db_entorno_de_pruebas_retiene_destinatarios_no_permitidos(propietario, como_app, pasillos, operadores, servidor, ca, monkeypatch):  # noqa: F811
    """R5: NotificadorEntornoPermitido sigue filtrando por entorno; nada llega al servidor."""
    from features.notificaciones.services.destinatarios_entorno import NotificadorEntornoPermitido

    u = await _usuario(propietario)
    pasillos(Pasillos([_version("v-env")], [u]))
    operadores(u)
    recibidos, puerto = servidor("starttls")
    n = NotificadorEntornoPermitido(NotificadorSmtp(_config(puerto), contexto_ssl=_contexto_cliente(ca)),
                                    entorno="pruebas", permitidos="@otro.invalid")
    async with como_app() as s:
        await srv.sincronizar(s, notificador=n, app_base_url=BASE_URL)
        await s.commit()
    assert recibidos.mensajes == [] and len(await _avisos(como_app, u)) == 1


@con_base
@pytest.mark.asyncio
async def test_db_un_error_inesperado_del_notificador_no_deshace_el_aviso(propietario, como_app, pasillos, operadores):  # noqa: F811
    class Roto:
        async def enviar_correo(self, correo):
            raise RuntimeError("fallo con datos " + correo.destinatario.email)

    u = await _usuario(propietario)
    pasillos(Pasillos([_version("v-roto")], [u]))
    operadores(u)
    async with como_app() as s:
        assert (await srv.sincronizar(s, notificador=Roto(), app_base_url=BASE_URL))["creados"] == 1
        await s.commit()
    assert len(await _avisos(como_app, u)) == 1
