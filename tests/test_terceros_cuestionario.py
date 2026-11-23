# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""Árbitro TER-02 contra PostgreSQL 16 local (TEST_DATABASE_URL).
Contrato: governance/especificaciones/TER-02.md
"""
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from uuid import uuid4
import json
from unittest.mock import AsyncMock, patch
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from conftest import exigir_base_de_pruebas
from features.terceros.domain.cuestionario import (
    CODIGO_ENLACE_NO_VALIDO,
    PREGUNTAS_TER_02_1,
)

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def ter02_env(db_engine):
    exigir_base_de_pruebas()
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    ta, tb = f"ter02-ta-{uuid4().hex[:8]}", f"ter02-tb-{uuid4().hex[:8]}"
    ruc_a = f"179{uuid4().int % 10000000000:010d}"
    ruc_b = f"179{uuid4().int % 10000000000:010d}"
    u_admin = f"u-admin-{uuid4().hex[:8]}"
    u_coord = f"u-coord-{uuid4().hex[:8]}"
    u_otro = f"u-otro-{uuid4().hex[:8]}"

    tercero_a_id = str(uuid4())
    tercero_b_id = str(uuid4())

    async with factory() as s:
        # Tenants
        await s.execute(
            text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:id, :n, :n, :r)"),
            {"id": ta, "n": "Organización Alfa", "r": ruc_a},
        )
        await s.execute(
            text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:id, :n, :n, :r)"),
            {"id": tb, "n": "Organización Beta", "r": ruc_b},
        )

        # Users
        for u, rol, t in [(u_admin, "admin_organizacion", ta), (u_coord, "coordinador", ta), (u_otro, "coordinador", tb)]:
            await s.execute(
                text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :n)"),
                {"u": u, "e": f"{u}@ter02.test", "n": u},
            )
            await s.execute(
                text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, :r)"),
                {"id": str(uuid4()), "u": u, "t": t, "r": rol},
            )

        # Terceros en transferencias_terceros
        await s.execute(text("""
            INSERT INTO transferencias_terceros (id, tenant_id, nombre, rol, pais_destino, nivel_proteccion)
            VALUES (:id, :t, 'Proveedor Alfa TI', 'ENCARGADO', 'Ecuador', 'ADECUADO')
        """), {"id": tercero_a_id, "t": ta})

        await s.execute(text("""
            INSERT INTO transferencias_terceros (id, tenant_id, nombre, rol, pais_destino, nivel_proteccion)
            VALUES (:id, :t, 'Proveedor Beta Cloud', 'ENCARGADO', 'Ecuador', 'ADECUADO')
        """), {"id": tercero_b_id, "t": tb})

        await s.commit()

    try:
        yield {
            "factory": factory,
            "ta": ta,
            "tb": tb,
            "admin": u_admin,
            "coord": u_coord,
            "otro": u_otro,
            "tercero_a": tercero_a_id,
            "tercero_b": tercero_b_id,
        }
    finally:
        async with factory() as s:
            for t in (ta, tb):
                await s.execute(text("DELETE FROM audit_events WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM terceros_cuestionarios WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM hallazgos WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM transferencias_terceros WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            for u in (u_admin, u_coord, u_otro):
                await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": u})
            await s.commit()


@pytest_asyncio.fixture
async def ter02_client(ter02_env):
    from api.routers.publico_terceros import router as publico_router
    from api.routers.terceros_cuestionario import router as cuestionario_router
    from app_core.db.session import get_session, fijar_contexto_rls

    app = FastAPI()
    app.include_router(publico_router, prefix="/api/v1")
    app.include_router(cuestionario_router, prefix="/api/v1")

    async def sesion_override(
        x_tenant_id: str = "tenant-default",
        x_user_id: str = "",
    ):
        async with ter02_env["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            if x_tenant_id:
                await fijar_contexto_rls(s, x_tenant_id, x_user_id)
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    app.dependency_overrides[get_session] = sesion_override
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=True),
        base_url="http://test",
    ) as cliente:
        yield cliente


async def test_cuestionario_token(ter02_env, ter02_client):
    """Escenario 1: token desconocido, caducado o respondido devuelve CODIGO_ENLACE_NO_VALIDO con cuerpo idéntico."""
    ta = ter02_env["ta"]
    tid = ter02_env["tercero_a"]

    # 1. Crear un cuestionario
    cabeceras = {"X-Tenant-ID": ta, "X-User-ID": ter02_env["coord"], "X-Role": "coordinador"}
    r_crear = await ter02_client.post(f"/api/v1/terceros/{tid}/cuestionarios", json={"dias_vigencia": 7}, headers=cabeceras)
    assert r_crear.status_code == 201
    datos_cues = r_crear.json()
    token_valido = datos_cues["token"]
    cues_id = datos_cues["id"]

    # Caso A: Token desconocido
    r_desc = await ter02_client.get("/api/v1/publico/proveedor/token-totalmente-inventado-123")
    assert r_desc.status_code == CODIGO_ENLACE_NO_VALIDO
    cuerpo_patron = r_desc.json()

    # Caso B: Token caducado
    async with ter02_env["factory"]() as s:
        await s.execute(
            text("UPDATE terceros_cuestionarios SET caduca_en = NOW() - INTERVAL '1 day' WHERE id = :id"),
            {"id": cues_id},
        )
        await s.commit()

    r_cad = await ter02_client.get(f"/api/v1/publico/proveedor/{token_valido}")
    assert r_cad.status_code == CODIGO_ENLACE_NO_VALIDO
    assert r_cad.json() == cuerpo_patron

    # Caso C: Token ya respondido
    async with ter02_env["factory"]() as s:
        await s.execute(
            text("UPDATE terceros_cuestionarios SET caduca_en = NOW() + INTERVAL '5 days', estado = 'respondido' WHERE id = :id"),
            {"id": cues_id},
        )
        await s.commit()

    r_resp = await ter02_client.get(f"/api/v1/publico/proveedor/{token_valido}")
    assert r_resp.status_code == CODIGO_ENLACE_NO_VALIDO
    assert r_resp.json() == cuerpo_patron


async def test_portal_minimo(ter02_env, ter02_client):
    """Escenario 2: con token válido solo se ven sus preguntas y el nombre de su organización."""
    ta = ter02_env["ta"]
    tid = ter02_env["tercero_a"]

    cabeceras = {"X-Tenant-ID": ta, "X-User-ID": ter02_env["coord"], "X-Role": "coordinador"}
    r_crear = await ter02_client.post(f"/api/v1/terceros/{tid}/cuestionarios", json={"dias_vigencia": 5}, headers=cabeceras)
    token = r_crear.json()["token"]

    r_portal = await ter02_client.get(f"/api/v1/publico/proveedor/{token}")
    assert r_portal.status_code == 200
    info = r_portal.json()

    assert info["organizacion"] == "Organización Alfa"
    assert len(info["preguntas"]) == len(PREGUNTAS_TER_02_1)
    # No expone datos sensibles ni usuarios internos
    assert "creado_por" not in info
    assert "token_hash" not in info


async def test_vigencia(ter02_env, ter02_client):
    """Escenario 3: dias_vigencia 0 o 31 da 422 DIAS_VIGENCIA_FUERA_DE_RANGO; por defecto 7 días."""
    ta = ter02_env["ta"]
    tid = ter02_env["tercero_a"]
    cabeceras = {"X-Tenant-ID": ta, "X-User-ID": ter02_env["coord"], "X-Role": "coordinador"}

    # 0 días
    r0 = await ter02_client.post(f"/api/v1/terceros/{tid}/cuestionarios", json={"dias_vigencia": 0}, headers=cabeceras)
    assert r0.status_code == 422
    assert "DIAS_VIGENCIA_FUERA_DE_RANGO" in r0.text

    # 31 días
    r31 = await ter02_client.post(f"/api/v1/terceros/{tid}/cuestionarios", json={"dias_vigencia": 31}, headers=cabeceras)
    assert r31.status_code == 422
    assert "DIAS_VIGENCIA_FUERA_DE_RANGO" in r31.text

    # Por defecto (sin valor) -> 7 días
    r_def = await ter02_client.post(f"/api/v1/terceros/{tid}/cuestionarios", json={}, headers=cabeceras)
    assert r_def.status_code == 201
    datos = r_def.json()
    caduca = datetime.fromisoformat(datos["caduca_en"])
    diff = caduca - datetime.now(timezone.utc)
    assert 6 <= diff.days <= 7


async def test_respuestas_validadas(ter02_env, ter02_client):
    """Escenario 4: respuestas incompletas o sin evidencia obligatoria responden 422 RESPUESTA_INCOMPLETA."""
    ta = ter02_env["ta"]
    tid = ter02_env["tercero_a"]
    cabeceras = {"X-Tenant-ID": ta, "X-User-ID": ter02_env["coord"], "X-Role": "coordinador"}

    r_crear = await ter02_client.post(f"/api/v1/terceros/{tid}/cuestionarios", headers=cabeceras)
    token = r_crear.json()["token"]

    # 1. Falta una obligatoria (G01)
    r_incomp = await ter02_client.post(
        f"/api/v1/publico/proveedor/{token}",
        data={"respuestas": json.dumps({"G02": True})},
    )
    assert r_incomp.status_code == 422
    assert "RESPUESTA_INCOMPLETA" in r_incomp.text

    # 2. G01 es sí (si_no_evidencia) pero no adjunta archivo
    respuestas_sin_archivo = {p.id: ("si" if "si_no" in p.tipo else "texto") for p in PREGUNTAS_TER_02_1 if p.obligatoria}
    r_sin_arch = await ter02_client.post(
        f"/api/v1/publico/proveedor/{token}",
        data={"respuestas": json.dumps(respuestas_sin_archivo)},
    )
    assert r_sin_arch.status_code == 422
    assert "RESPUESTA_INCOMPLETA" in r_sin_arch.text

    # 3. G06 = sí pero falta G07
    respuestas_g06 = {p.id: False for p in PREGUNTAS_TER_02_1 if p.obligatoria}
    respuestas_g06["G06"] = True
    respuestas_g06["G10"] = "Contacto Emergencia"
    r_sin_g07 = await ter02_client.post(
        f"/api/v1/publico/proveedor/{token}",
        data={"respuestas": json.dumps(respuestas_g06)},
    )
    assert r_sin_g07.status_code == 422
    assert "RESPUESTA_INCOMPLETA" in r_sin_g07.text


async def test_revision_conforme(ter02_env, ter02_client):
    """Escenario 5: revisión conforme exige proxima_revision, cierra hallazgo y guarda informe_sha256."""
    ta = ter02_env["ta"]
    tid = ter02_env["tercero_a"]
    user_coord = ter02_env["coord"]
    cabeceras = {"X-Tenant-ID": ta, "X-User-ID": user_coord, "X-Role": "coordinador"}

    # Crear hallazgo previo de garantia
    async with ter02_env["factory"]() as s:
        await s.execute(text("""
            INSERT INTO hallazgos (id, tenant_id, origen, origen_ref, severidad, titulo, estado, creado_por, creado_en)
            VALUES (:id, :t, 'tercero', :ref, 'alta', 'Garantía pendiente', 'abierto', :u, NOW())
        """), {"id": str(uuid4()), "t": ta, "ref": f"{tid}:garantia", "u": user_coord})
        await s.commit()

    # Crear cuestionario y marcarlo como respondido
    r_crear = await ter02_client.post(f"/api/v1/terceros/{tid}/cuestionarios", headers=cabeceras)
    cues_id = r_crear.json()["id"]

    async with ter02_env["factory"]() as s:
        await s.execute(
            text("UPDATE terceros_cuestionarios SET estado = 'respondido', respuestas = '{}' WHERE id = :id"),
            {"id": cues_id},
        )
        await s.commit()

    # Intentar conforme sin fecha de proxima_revision -> 422 PROXIMA_REVISION_OBLIGATORIA
    r_sin_fecha = await ter02_client.post(
        f"/api/v1/terceros/cuestionarios/{cues_id}/revision",
        json={"decision": "conforme"},
        headers=cabeceras,
    )
    assert r_sin_fecha.status_code == 422
    assert "PROXIMA_REVISION_OBLIGATORIA" in r_sin_fecha.text

    # Conforme con fecha válida
    with patch("app_core.pasillo.evidencias.custodiar_informe_garantias", new_callable=AsyncMock) as mock_cust:
        mock_cust.return_value = {
            "evidencia_id": str(uuid4()),
            "sha256": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
        }
        r_conforme = await ter02_client.post(
            f"/api/v1/terceros/cuestionarios/{cues_id}/revision",
            json={"decision": "conforme", "proxima_revision": "2027-11-16", "comentario": "Todo verificado"},
            headers=cabeceras,
        )
    assert r_conforme.status_code == 200
    res_data = r_conforme.json()
    assert res_data["estado"] == "conforme"
    assert res_data["informe_sha256"] is not None

    # Verificar que el hallazgo garantia fue cerrado
    async with ter02_env["factory"]() as s:
        h_estado = (await s.execute(
            text("SELECT estado FROM hallazgos WHERE tenant_id = :t AND origen_ref = :ref"),
            {"t": ta, "ref": f"{tid}:garantia"},
        )).scalar()
        assert h_estado == "cerrado"

        # Verificar que el tercero recibió proxima_revision
        t_prox = (await s.execute(
            text("SELECT proxima_revision FROM transferencias_terceros WHERE id = :id"),
            {"id": tid},
        )).scalar()
        assert str(t_prox) == "2027-11-16"


async def test_revision_rechazo(ter02_env, ter02_client):
    """Escenario 6: rechazo abre hallazgo tercero de severidad alta; corrección devuelve url_nueva."""
    ta = ter02_env["ta"]
    tid = ter02_env["tercero_a"]
    user_coord = ter02_env["coord"]
    cabeceras = {"X-Tenant-ID": ta, "X-User-ID": user_coord, "X-Role": "coordinador"}

    # 1. Prueba de corrección
    r1 = await ter02_client.post(f"/api/v1/terceros/{tid}/cuestionarios", headers=cabeceras)
    cues1_id = r1.json()["id"]

    async with ter02_env["factory"]() as s:
        await s.execute(text("UPDATE terceros_cuestionarios SET estado = 'respondido' WHERE id = :id"), {"id": cues1_id})
        await s.commit()

    r_corr = await ter02_client.post(
        f"/api/v1/terceros/cuestionarios/{cues1_id}/revision",
        json={"decision": "correccion", "comentario": "Falta adjunto de contrato"},
        headers=cabeceras,
    )
    assert r_corr.status_code == 200
    assert r_corr.json()["estado"] == "correccion"
    assert r_corr.json()["url_nueva"] is not None

    # 2. Prueba de rechazo
    r2 = await ter02_client.post(f"/api/v1/terceros/{tid}/cuestionarios", headers=cabeceras)
    cues2_id = r2.json()["id"]

    async with ter02_env["factory"]() as s:
        await s.execute(text("UPDATE terceros_cuestionarios SET estado = 'respondido' WHERE id = :id"), {"id": cues2_id})
        await s.commit()

    r_rech = await ter02_client.post(
        f"/api/v1/terceros/cuestionarios/{cues2_id}/revision",
        json={"decision": "rechazado", "comentario": "Medidas de seguridad deficientes"},
        headers=cabeceras,
    )
    assert r_rech.status_code == 200
    assert r_rech.json()["estado"] == "rechazado"

    # Verificar hallazgo de severidad alta
    async with ter02_env["factory"]() as s:
        h = (await s.execute(
            text("SELECT severidad, estado FROM hallazgos WHERE tenant_id = :t AND origen_ref = :ref"),
            {"t": ta, "ref": f"{tid}:cuestionario_rechazado"},
        )).mappings().first()
        assert h is not None
        assert h["severidad"] == "alta"
        assert h["estado"] == "abierto"


async def test_rls(ter02_env, ter02_client):
    """Escenario 7: aislamiento tenant: otra organización no ve ni revisa el cuestionario."""
    ta, tb = ter02_env["ta"], ter02_env["tb"]
    tid = ter02_env["tercero_a"]

    cab_a = {"X-Tenant-ID": ta, "X-User-ID": ter02_env["coord"], "X-Role": "coordinador"}
    r = await ter02_client.post(f"/api/v1/terceros/{tid}/cuestionarios", headers=cab_a)
    cues_id = r.json()["id"]

    # Usuario de Tenant B intentando ver o revisar cuestionario de Tenant A
    cab_b = {"X-Tenant-ID": tb, "X-User-ID": ter02_env["otro"], "X-Role": "coordinador"}
    r_rev_b = await ter02_client.post(
        f"/api/v1/terceros/cuestionarios/{cues_id}/revision",
        json={"decision": "conforme", "proxima_revision": "2027-01-01"},
        headers=cab_b,
    )
    assert r_rev_b.status_code == 404
    assert "CUESTIONARIO_NO_ENCONTRADO" in r_rev_b.text


async def test_cabeceras_portal(ter02_env, ter02_client):
    """Escenario 8: portal devuelve cabeceras obligatorias SEC-12."""
    r = await ter02_client.get("/api/v1/publico/proveedor/cualquier-token")
    assert r.headers.get("x-robots-tag") == "noindex"
    assert r.headers.get("referrer-policy") == "no-referrer"
    assert r.headers.get("cache-control") == "no-store"
