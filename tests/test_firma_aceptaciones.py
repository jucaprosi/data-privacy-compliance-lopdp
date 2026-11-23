# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""Árbitro FIRMA-02 contra TEST_DATABASE_URL (PostgreSQL 16 local o servicio PostgreSQL 16 del CI).

Cubre los cuatro escenarios de aceptación exigidos por la especificación:
- test_aceptacion_registra_acuse   → aceptado_en, ip y acuse_sha256 rellenados; evidencia creada.
- test_aceptacion_un_uso           → segundo intento sobre el mismo enlace → 410.
- test_verificar_hash              → archivo alterado en un byte → coincide = false.
- test_solo_aprobados              → documento no aprobado → 409 DOCUMENTO_NO_APROBADO.

MUTACIÓN DOCUMENTADA:
  Archivo: features/firma_electronica/services/aceptacion_engine.py
  Línea mutada: en el UPDATE de `registrar_aceptacion`, pasar `"ip": None` en lugar de `ip_str or None`
  (aceptar sin registrar la IP). test_aceptacion_registra_acuse FALLA: la fila no guarda la IP y el PDF
  del acuse no la contiene.
MUTACIÓN 3: guardar en `acuse_sha256` un hash calculado por la sala de firma en lugar del `sha256` de la
  custodia. test_acuse_hash_es_el_de_la_custodia FALLA.

MUTACIÓN 2 (comprobada el 2026-11-14): en `registrar_aceptacion`, quitar `await fijar_contexto_rls(...)` antes del
  UPDATE. Con `lopdp_app` (RLS real) el UPDATE no ve la fila, `rowcount` es 0 y
  test_aceptar_sin_contexto_con_rol_de_aplicacion FALLA con ACEPTACION_CADUCADA. Antes, el acuse se devolvía sin guardarse.
"""
# ¤¤qa-engineer
# ¤firma-electronica ¤arbitro
import hashlib
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from conftest import exigir_base_de_pruebas

pytestmark = pytest.mark.asyncio

SHA_APROBADO = "a" * 64
SHA_BORRADOR = "b" * 64
CONTENIDO_APROBADO = b"contenido-aprobado"
IP_TEST = "192.168.1.100"


# --------------------------------------------------------------------------- #
# Fixtures                                                                      #
# --------------------------------------------------------------------------- #

@pytest_asyncio.fixture
async def firma2_env(db_engine, monkeypatch):
    """Entorno con dos tenants, dos usuarios y la compuerta BIB-107 simulada."""
    from app_core.db.session import fijar_contexto_rls
    import features.biblioteca.biblioteca_service as _bib
    from features.firma_electronica.domain.aceptacion import DocumentoParaAceptacion, PersonaParaAceptacion

    exigir_base_de_pruebas()

    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    ta = str(uuid4())
    ua = str(uuid4())
    ub = str(uuid4())
    doc_id = str(uuid4())
    doc_borrador_id = str(uuid4())

    # Documento aprobado simulado por BIB-107
    doc_aprobado = DocumentoParaAceptacion(
        id=doc_id,  # type: ignore[arg-type]
        tenant_id=ta,  # type: ignore[arg-type]
        nombre="Política de Privacidad v2",
        sha256=SHA_APROBADO,
        estado="aprobado",
    )
    doc_borrador = DocumentoParaAceptacion(
        id=doc_borrador_id,  # type: ignore[arg-type]
        tenant_id=ta,  # type: ignore[arg-type]
        nombre="Borrador sin publicar",
        sha256=SHA_BORRADOR,
        estado="borrador",
    )

    async def _obtener_doc(db, tenant_id, documento_id):
        if str(documento_id) == doc_id:
            return doc_aprobado
        if str(documento_id) == doc_borrador_id:
            return doc_borrador
        raise ValueError(f"documento no encontrado: {documento_id}")

    async def _obtener_persona(db, tenant_id, persona_id):
        # Simula el inventario de ORG-17: solo conoce a las dos personas del entorno.
        if str(persona_id) in (ua, ub):
            return PersonaParaAceptacion(
                id=persona_id, nombre="Persona " + str(persona_id)[:4], email=f"{str(persona_id)[:8]}@correo.invalid"
            )
        return None

    custodias: list[dict] = []

    async def _custodiar_falso(db, **datos):
        """Custodio de prueba: devuelve el sha256 de los bytes, como lo hace la custodia real."""
        custodias.append(datos)
        return {"evidencia_id": str(uuid4()), "sha256": hashlib.sha256(datos["contenido"]).hexdigest(),
                "tipo_evidencia": "acuse"}


    try:
        async with factory() as s:
            await s.execute(
                text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                    "VALUES (:t, :n, :r, :ruc)"
                ),
                {"t": ta, "n": "Empresa Test FIRMA-02", "r": "Empresa Test SA", "ruc": f"RUC{ta[:13]}"},
            )
            await s.execute(
                text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, :n)"),
                {"id": ua, "e": f"{ua[:8]}@test.firma02", "n": "Usuario Alpha"},
            )
            await s.execute(
                text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, :n)"),
                {"id": ub, "e": f"{ub[:8]}@test.firma02", "n": "Usuario Beta"},
            )
            await s.commit()

        yield {
            "factory": factory,
            "tenant": ta,
            "user_a": ua,
            "user_b": ub,
            "doc_id": doc_id,
            "doc_borrador_id": doc_borrador_id,
            "obtener_doc": _obtener_doc,
            "obtener_persona": _obtener_persona,
            "custodiar": _custodiar_falso,
            "custodias": custodias,
        }
    finally:
        async with factory() as s:
            await fijar_contexto_rls(s, ta)
            await s.execute(text("DELETE FROM aceptaciones WHERE tenant_id = CAST(:t AS uuid)"), {"t": ta})
            await s.commit()
        async with factory() as s:
            await s.execute(text("DELETE FROM users WHERE id IN (:ua, :ub)"), {"ua": ua, "ub": ub})
            await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": ta})
            await s.commit()


@asynccontextmanager
async def _db_app(env, tenant=None):
    """Sesión con rol lopdp_app y tenant fijado."""
    from app_core.db.session import fijar_contexto_rls
    tenant = tenant or env["tenant"]
    async with env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, tenant)
        yield s


async def _crear_enlace(env, doc_id=None, persona_ids=None, dias=7) -> tuple[str, str]:
    """Crea un enlace de aceptación y devuelve (token_raw, persona_id)."""
    from features.firma_electronica.services.aceptacion_engine import crear_enlaces

    pid = persona_ids or [env["user_a"]]
    async with _db_app(env) as s:
        enlaces = await crear_enlaces(
            s,
            tenant_id=env["tenant"],
            user_id=env["user_a"],
            documento_id=doc_id or env["doc_id"],
            persona_ids=pid,
            dias_vigencia=dias,
            obtener_doc=env["obtener_doc"],
            obtener_persona=env["obtener_persona"],
        )
    assert enlaces
    token_raw = enlaces[0].url.split("/")[-1]
    return token_raw, pid[0]


# --------------------------------------------------------------------------- #
# Pruebas requeridas                                                            #
# --------------------------------------------------------------------------- #

async def test_aceptacion_registra_acuse(firma2_env):
    """F02-01 · Enlace vigente → acepta → aceptado_en, ip y acuse_sha256 rellenados; acuse PDF custodiado.

    DETECTOR DE MUTACIÓN: aceptar sin registrar la IP hace fallar esta prueba.
    """
    from features.firma_electronica.services.aceptacion_engine import registrar_aceptacion

    env = firma2_env
    token_raw, pid = await _crear_enlace(env)
    async with env["factory"]() as s:
        resultado = await registrar_aceptacion(s, token_raw, IP_TEST, custodiar=env["custodiar"])
    assert len(resultado.acuse_sha256) == 64
    assert resultado.acuse_pdf.startswith(b"%PDF")

    async with _db_app(env) as s:
        fila = (
            await s.execute(
                text("SELECT aceptado_en, host(ip) AS ip, acuse_sha256 FROM aceptaciones WHERE token_hash = :h"),
                {"h": hashlib.sha256(bytes.fromhex(token_raw)).hexdigest()},
            )
        ).fetchone()
    assert fila is not None and fila.aceptado_en is not None
    assert fila.ip == IP_TEST, "la IP no se registró (mutación detectada)"
    assert fila.acuse_sha256 == resultado.acuse_sha256
    assert len(env["custodias"]) == 1
    c = env["custodias"][0]
    assert c["contenido"] == resultado.acuse_pdf and c["documento_id"] == env["doc_id"]


async def test_acuse_hash_es_el_de_la_custodia(firma2_env):
    """acuse_sha256 = sha256 que devuelve la custodia = sha256 de los bytes del PDF devueltos."""
    from features.firma_electronica.services.aceptacion_engine import registrar_aceptacion

    env = firma2_env
    token_raw, _ = await _crear_enlace(env)
    async with env["factory"]() as s:
        resultado = await registrar_aceptacion(s, token_raw, IP_TEST, custodiar=env["custodiar"])
    esperado = hashlib.sha256(env["custodias"][0]["contenido"]).hexdigest()
    assert resultado.acuse_sha256 == esperado == hashlib.sha256(resultado.acuse_pdf).hexdigest()
    async with _db_app(env) as s:
        guardado = (
            await s.execute(
                text("SELECT acuse_sha256 FROM aceptaciones WHERE token_hash = :h"),
                {"h": hashlib.sha256(bytes.fromhex(token_raw)).hexdigest()},
            )
        ).scalar()
    assert guardado == esperado


async def test_verificar_acuse(firma2_env):
    """El acuse descargado verifica como `acuse`; con un byte cambiado, no."""
    from features.firma_electronica.services.aceptacion_engine import registrar_aceptacion, verificar_hash

    env = firma2_env
    token_raw, _ = await _crear_enlace(env)
    async with env["factory"]() as s:
        resultado = await registrar_aceptacion(s, token_raw, IP_TEST, custodiar=env["custodiar"])

    async def _custodiado(db, tenant_id, huella):
        return huella == resultado.acuse_sha256

    async with _db_app(env) as s:
        ok = await verificar_hash(s, env["tenant"], resultado.acuse_pdf, acuse_custodiado=_custodiado)
    assert ok == (True, "acuse")
    alterado = resultado.acuse_pdf[:-1] + bytes([resultado.acuse_pdf[-1] ^ 1])
    async with _db_app(env) as s:
        assert await verificar_hash(s, env["tenant"], alterado, acuse_custodiado=_custodiado) == (False, None)
    async def _no_custodiado(db, tenant_id, huella):
        return False

    async with _db_app(env) as s:  # sin huella custodiada no hay coincidencia
        assert await verificar_hash(s, env["tenant"], resultado.acuse_pdf, acuse_custodiado=_no_custodiado) == (False, None)


async def test_aceptacion_un_uso(firma2_env):
    """F02-02 · Mismo enlace aceptado dos veces → segunda aceptación → 410 ACEPTACION_CADUCADA."""
    from features.firma_electronica.services.aceptacion_engine import registrar_aceptacion
    from features.firma_electronica.domain.aceptacion import ACEPTACION_CADUCADA

    env = firma2_env
    token_raw, _ = await _crear_enlace(env)

    async with env["factory"]() as s:
        await registrar_aceptacion(s, token_raw, IP_TEST, custodiar=env["custodiar"])

    with pytest.raises(Exception) as exc_info:
        async with env["factory"]() as s:
            await registrar_aceptacion(s, token_raw, IP_TEST, custodiar=env["custodiar"])

    from api.errores import ErrorNegocio
    assert isinstance(exc_info.value, ErrorNegocio)
    assert exc_info.value.code == ACEPTACION_CADUCADA.codigo
    assert exc_info.value.status_code == 410


async def test_verificar_hash(firma2_env):
    """F02-03 · Archivo aprobado alterado en un byte → verificar → coincide = false."""
    from features.firma_electronica.services.aceptacion_engine import (
        crear_enlaces,
        registrar_aceptacion,
        verificar_hash,
    )

    env = firma2_env
    token_raw, _ = await _crear_enlace(env)
    async with env["factory"]() as s:
        await registrar_aceptacion(s, token_raw, IP_TEST, custodiar=env["custodiar"])

    # Archivo original → coincide = true (por documento_sha256 en la tabla).
    contenido_original = bytes.fromhex(
        "aa" * 32  # sha256 = SHA_APROBADO ("a"*64)
    )
    # Calcular contenido cuyo sha256 sea SHA_APROBADO.
    # Para esta prueba construimos el contenido tal que su sha256 coincida con SHA_APROBADO.
    # En la práctica es imposible (colisión), así que verificamos el caso negativo:
    # un archivo aleatorio NO debe coincidir.
    contenido_aleatorio = b"archivo-alterado-" + bytes(range(256))
    async def _solo_original(db, tenant_id, sha256):
        return sha256 == hashlib.sha256(CONTENIDO_APROBADO).hexdigest()

    async with _db_app(env) as s:
        coincide, tipo = await verificar_hash(s, env["tenant"], contenido_aleatorio, es_aprobado=_solo_original)
    assert coincide is False and tipo is None

    # El archivo íntegro coincide con un documento aprobado aunque aún no se haya enviado a nadie.
    async with _db_app(env) as s:
        coincide, tipo = await verificar_hash(s, env["tenant"], CONTENIDO_APROBADO, es_aprobado=_solo_original)
    assert (coincide, tipo) == (True, "documento")

    # Un solo byte distinto y deja de coincidir.
    async with _db_app(env) as s:
        coincide, _ = await verificar_hash(s, env["tenant"], CONTENIDO_APROBADO + b"x", es_aprobado=_solo_original)
    assert coincide is False


async def test_solo_aprobados(firma2_env):
    """F02-04 · Documento en estado borrador → POST /firma/aceptaciones → 409 DOCUMENTO_NO_APROBADO."""
    from features.firma_electronica.services.aceptacion_engine import crear_enlaces
    from features.firma_electronica.domain.aceptacion import DOCUMENTO_NO_APROBADO
    from api.errores import ErrorNegocio

    env = firma2_env
    with pytest.raises(ErrorNegocio) as exc_info:
        async with _db_app(env) as s:
            await crear_enlaces(
                s,
                tenant_id=env["tenant"],
                user_id=env["user_a"],
                documento_id=env["doc_borrador_id"],
                persona_ids=[env["user_a"]],
                dias_vigencia=7,
                obtener_doc=env["obtener_doc"],
                obtener_persona=env["obtener_persona"],
            )
    assert exc_info.value.code == DOCUMENTO_NO_APROBADO.codigo
    assert exc_info.value.status_code == 409


# --------------------------------------------------------------------------- #
# Pruebas adicionales                                                           #
# --------------------------------------------------------------------------- #

async def test_token_caducado(firma2_env):
    """F02-05 · Token caducado (dias_vigencia=0 equivale a caduca en el pasado) → 410."""
    from features.firma_electronica.services.aceptacion_engine import (
        crear_enlaces,
        registrar_aceptacion,
    )
    from app_core.db.session import fijar_contexto_rls
    from features.firma_electronica.domain.aceptacion import ACEPTACION_CADUCADA
    from api.errores import ErrorNegocio

    env = firma2_env
    # Crear con 1 día y luego actualizar la fecha de caducidad al pasado manualmente.
    token_raw, _ = await _crear_enlace(env, dias=1)
    token_hash = hashlib.sha256(bytes.fromhex(token_raw)).hexdigest()
    async with env["factory"]() as s:
        await fijar_contexto_rls(s, env["tenant"])
        await s.execute(
            text("UPDATE aceptaciones SET caduca_en = now() - interval '1 day' WHERE token_hash = :h"),
            {"h": token_hash},
        )
        await s.commit()

    with pytest.raises(ErrorNegocio) as exc_info:
        async with env["factory"]() as s:
            await registrar_aceptacion(s, token_raw, IP_TEST, custodiar=env["custodiar"])
    assert exc_info.value.code == ACEPTACION_CADUCADA.codigo


async def test_listar_sin_token(firma2_env):
    """F02-06 · Listar aceptaciones no expone el campo token."""
    from features.firma_electronica.services.aceptacion_engine import (
        crear_enlaces,
        listar_aceptaciones,
    )

    env = firma2_env
    await _crear_enlace(env)

    async with _db_app(env) as s:
        lista = await listar_aceptaciones(s, env["tenant"])

    assert len(lista) >= 1
    for item in lista:
        assert "token" not in item
        assert "token_hash" not in item


# --------------------------------------------------------------------------- #
# FIRMA-02 con rol de aplicación, custodia del acuse y pasillos                  #
# --------------------------------------------------------------------------- #

async def test_aceptar_sin_contexto_con_rol_de_aplicacion(firma2_env):
    """La ruta pública llega sin organización: con lopdp_app (RLS real) el acuse igual se guarda.

    Sin fijar el contexto de la fila, el UPDATE no veía nada y el acuse se devolvía sin guardarse.
    """
    from features.firma_electronica.services.aceptacion_engine import registrar_aceptacion

    env = firma2_env
    token_raw, _ = await _crear_enlace(env)
    async with env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        acuse = (await registrar_aceptacion(s, token_raw, IP_TEST, custodiar=env["custodiar"])).acuse_sha256

    token_hash = hashlib.sha256(bytes.fromhex(token_raw)).hexdigest()
    async with _db_app(env) as s:
        fila = (
            await s.execute(
                text("SELECT aceptado_en, acuse_sha256 FROM aceptaciones WHERE token_hash = :h"), {"h": token_hash}
            )
        ).fetchone()
    assert fila.aceptado_en is not None and fila.acuse_sha256 == acuse


async def test_acuse_se_custodia_y_si_falla_no_hay_aceptacion(firma2_env):
    """R2: el acuse se custodia en la misma transacción; si la custodia falla no queda aceptación."""
    from features.firma_electronica.services.aceptacion_engine import registrar_aceptacion

    env = firma2_env
    llamadas: list[dict] = []

    async def _custodia_ok(db, **datos):
        llamadas.append(datos)
        return {"sha256": hashlib.sha256(datos["contenido"]).hexdigest()}

    async def _custodia_falla(db, **datos):
        raise RuntimeError("almacén no disponible")

    token_raw, pid = await _crear_enlace(env)
    with pytest.raises(RuntimeError):
        async with env["factory"]() as s:
            await registrar_aceptacion(s, token_raw, IP_TEST, custodiar=_custodia_falla)
    token_hash = hashlib.sha256(bytes.fromhex(token_raw)).hexdigest()
    async with _db_app(env) as s:
        fila = (
            await s.execute(text("SELECT aceptado_en FROM aceptaciones WHERE token_hash = :h"), {"h": token_hash})
        ).fetchone()
    assert fila.aceptado_en is None, "la aceptación no debe quedar si el acuse no se pudo custodiar"

    async with env["factory"]() as s:
        resultado = await registrar_aceptacion(s, token_raw, IP_TEST, custodiar=_custodia_ok)
    assert len(llamadas) == 1
    assert hashlib.sha256(llamadas[0]["contenido"]).hexdigest() == resultado.acuse_sha256
    assert llamadas[0]["documento_id"] == env["doc_id"]


async def test_persona_fuera_del_inventario(firma2_env):
    """La persona sale del inventario (ORG-17): una desconocida responde 404 PERSONA_NO_ENCONTRADA."""
    from api.errores import ErrorNegocio
    from features.firma_electronica.domain.aceptacion import PERSONA_NO_ENCONTRADA
    from features.firma_electronica.services.aceptacion_engine import crear_enlaces

    env = firma2_env
    with pytest.raises(ErrorNegocio) as exc_info:
        async with _db_app(env) as s:
            await crear_enlaces(
                s, tenant_id=env["tenant"], user_id=env["user_a"], documento_id=env["doc_id"],
                persona_ids=[str(uuid4())], dias_vigencia=3,
                obtener_doc=env["obtener_doc"], obtener_persona=env["obtener_persona"],
            )
    assert exc_info.value.code == PERSONA_NO_ENCONTRADA.codigo
    assert exc_info.value.status_code == 404


async def test_info_publica_muestra_nombre_del_documento(firma2_env):
    """La página pública muestra el nombre del documento (no su id) y nunca otras aceptaciones."""
    from features.firma_electronica.services.aceptacion_engine import obtener_info_publica

    env = firma2_env
    token_raw, _ = await _crear_enlace(env)
    async with env["factory"]() as s:
        info = await obtener_info_publica(s, token_raw, obtener_doc=env["obtener_doc"])
    assert info.nombre_documento == "Política de Privacidad v2"
    assert info.sha256 == SHA_APROBADO


async def test_pasillos_biblioteca_y_organizacion(firma2_env):
    """Los lectores reales: documento aprobado con su huella (BIB-107) y persona del inventario (ORG-17)."""
    from app_core.db.session import fijar_contexto_rls
    from app_core.pasillo import biblioteca as pas_bib
    from app_core.pasillo import organizacion as pas_org
    from app_core.errors import ErrorNegocio

    env = firma2_env
    t, u = env["tenant"], env["user_a"]
    doc_ok, doc_bor, persona = str(uuid4()), str(uuid4()), str(uuid4())
    cuerpo_ok, cuerpo_bor = "cuerpo aprobado", "cuerpo borrador"
    sha_ok = hashlib.sha256(cuerpo_ok.encode("utf-8")).hexdigest()  # el trigger exige sha256(contenido)
    sha_bor = hashlib.sha256(cuerpo_bor.encode("utf-8")).hexdigest()
    async with env["factory"]() as s:
        await fijar_contexto_rls(s, t, u)
        for did, est, sha, cuerpo in (
            (doc_ok, "aprobado", sha_ok, cuerpo_ok), (doc_bor, "borrador", sha_bor, cuerpo_bor),
        ):
            await s.execute(
                text(
                    "INSERT INTO biblioteca_documentos (id, tenant_id, codigo, nombre, origen, contenido_markdown, "
                    "estado, aprobado_por, aprobado_en, sha256, fecha_emision, proxima_revision, creado_por) "
                    "VALUES (:id, :t, :c, :n, 'propio', :cu, :e, :ap, :aen, :h, current_date, current_date + 365, :u)"
                ),
                {"id": did, "t": t, "c": "FIRMA02-" + did[:6], "n": f"Doc {est}", "e": est,
                 "ap": u if est == "aprobado" else None,
                 "aen": datetime.now(timezone.utc) if est == "aprobado" else None,
                 "h": sha, "u": u, "cu": cuerpo},
            )
        await s.execute(
            text(
                "INSERT INTO inventario_personas (id, tenant_id, nombre, cargo, email, created_by) "
                "VALUES (:id, :t, 'Ana Prueba', 'Analista', 'ana@correo.invalid', :u)"
            ),
            {"id": persona, "t": t, "u": u},
        )
        await s.commit()
    try:
        async with env["factory"]() as s:
            await fijar_contexto_rls(s, t, u)
            d = await pas_bib.obtener_documento_para_firma(s, t, doc_ok)
            assert (d["estado"], d["sha256"], d["nombre"]) == ("aprobado", sha_ok, "Doc aprobado")
            assert (await pas_bib.obtener_documento_para_firma(s, t, doc_bor))["estado"] == "borrador"
            with pytest.raises(ErrorNegocio):
                await pas_bib.obtener_documento_para_firma(s, t, str(uuid4()))
            assert await pas_bib.hay_documento_aprobado_con_huella(s, t, sha_ok) is True
            assert await pas_bib.hay_documento_aprobado_con_huella(s, t, sha_bor) is False  # borrador no cuenta
            p = await pas_org.obtener_persona_para_firma(s, t, persona)
            assert p == {"id": persona, "nombre": "Ana Prueba", "email": "ana@correo.invalid"}
            assert await pas_org.obtener_persona_para_firma(s, t, str(uuid4())) is None
    finally:
        async with env["factory"]() as s:
            await fijar_contexto_rls(s, t, u)
            await s.execute(text("DELETE FROM inventario_personas WHERE tenant_id = :t"), {"t": t})
            await s.execute(text("DELETE FROM biblioteca_documentos WHERE tenant_id = :t"), {"t": t})
            await s.commit()
