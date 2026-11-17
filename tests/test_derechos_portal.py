# ¤¤developer-architect ¤derechos ¤seguridad ¤arbitro
"""Pruebas del portal público de solicitudes de titulares por organización (DER-02).

Contrato: governance/especificaciones/DER-02.md
- R1 Mínimo: derecho, nombre, correo y descripción.
- R2 Seguimiento: devuelve estado, recibida_en, respondida_en; nunca respuesta ni datos privados.
- R3 No enumeración: 404 idéntico para slug inexistente, inactivo o código ajeno.
- R4 Tasa: 5 solicitudes por IP y hora; la 6.ª responde 429 PORTAL_LIMITE.
"""
import uuid
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio
from features.derechos_arco import derechos_arco_service
from features.derechos_arco.services.portal_engine import (
    TASA_LIMITE_IP_HORA,
    limpiar_registro_ips,
)
from main import app


@pytest.fixture(autouse=True)
def resetear_tasa():
    limpiar_registro_ips()
    yield
    limpiar_registro_ips()


@pytest_asyncio.fixture
async def tenant_con_portal(db_session: AsyncSession) -> tuple[str, str]:
    """Crea una organización y le configura un portal activo."""
    token = uuid.uuid4().hex[:8]
    tenant_id = f"t_portal_{token}"
    slug = f"org-prueba-{token}"
    ruc = f"179{int(uuid.uuid4().hex[:10], 16) % 10000000000:010d}"
    
    # 1. Crear tenant en base
    await db_session.execute(
        text(
            """
            INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, sector, activo)
            VALUES (:t, 'Empresa Demo S.A.', 'Empresa Demo S.A.', :ruc, 'comercio', true)
            ON CONFLICT (id) DO NOTHING;
            """
        ),
        {"t": tenant_id, "ruc": ruc},
    )
    
    # 2. Configurar portal activo
    await db_session.execute(
        text(
            """
            INSERT INTO portal_config (tenant_id, activo, slug, texto_bienvenida)
            VALUES (:t, true, :s, 'Bienvenidos al portal de privacidad')
            ON CONFLICT (tenant_id) DO UPDATE SET activo = true, slug = :s;
            """
        ),
        {"t": tenant_id, "s": slug},
    )
    await db_session.commit()
    return tenant_id, slug


@pytest.mark.asyncio
async def test_portal_info_publica(tenant_con_portal):
    """GET /publico/solicitud/{slug} entrega los datos del portal sin exigir autenticación."""
    _, slug = tenant_con_portal
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get(f"/api/v1/publico/solicitud/{slug}")
        assert res.status_code == 200
        data = res.json()
        assert data["organizacion"] == "Empresa Demo S.A."
        assert "ACCESO" in data["derechos"]
        assert "RECTIFICACION" in data["derechos"]
        assert data["texto"] == "Bienvenidos al portal de privacidad"


@pytest.mark.asyncio
async def test_no_enumeracion(tenant_con_portal):
    """R3: 404 idéntico para slug inexistente, inactivo o código ajeno."""
    tenant_id, slug = tenant_con_portal
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Slug inexistente
        r1 = await ac.get("/api/v1/publico/solicitud/slug-inexistente-total")
        assert r1.status_code == 404

        # Código de seguimiento ajeno o inexistente
        r2 = await ac.get("/api/v1/publico/solicitud/seguir/sol_codigo_falso_123456")
        assert r2.status_code == 404
        assert r1.json() == r2.json()  # Cuerpo de error uniforme


@pytest.mark.asyncio
async def test_portal_crea_solicitud(tenant_con_portal, db_session: AsyncSession):
    """POST /publico/solicitud/{slug} crea la solicitud con canal='portal' y devuelve el código."""
    tenant_id, slug = tenant_con_portal
    payload = {
        "derecho": "ACCESO",
        "nombre": "Titular de Prueba",
        "email": "titular@ejemplo.com",
        "descripcion": "Solicito copia íntegra de mis datos de facturación.",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(f"/api/v1/publico/solicitud/{slug}", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert "codigo" in data
        codigo = data["codigo"]
        assert codigo.startswith("sol_")

        # Verificar en base de datos interna que se creó con canal 'portal'
        row = (
            await db_session.execute(
                text("SELECT canal, estado::text, nombre_solicitante FROM derechos_arco_solicitudes WHERE tenant_id_texto = :t"),
                {"t": tenant_id},
            )
        ).mappings().first()
        assert row is not None
        assert row["canal"] == "portal"
        assert row["estado"] == "RECIBIDA"
        assert row["nombre_solicitante"] == "Titular de Prueba"


@pytest.mark.asyncio
async def test_seguimiento_no_revela(tenant_con_portal):
    """R2: Seguimiento devuelve solo estado y fechas. Mutación documentada contra fuga de datos."""
    _, slug = tenant_con_portal
    payload = {
        "derecho": "CANCELACION",
        "nombre": "Titular Confidencial",
        "email": "confidencial@ejemplo.com",
        "descripcion": "Eliminación de cuenta.",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        crea = await ac.post(f"/api/v1/publico/solicitud/{slug}", json=payload)
        assert crea.status_code == 201
        codigo = crea.json()["codigo"]

        res = await ac.get(f"/api/v1/publico/solicitud/seguir/{codigo}")
        assert res.status_code == 200
        data = res.json()
        assert data["estado"] == "RECIBIDA"
        assert "recibida_en" in data
        assert "respondida_en" in data

        # MUTACIÓN DOCUMENTADA: Si se devuelven datos privados o texto de respuesta, la prueba DEBE fallar.
        assert "respuesta" not in data, "Mutación detectada: no se debe exponer texto de respuesta"
        assert "descripcion" not in data, "Mutación detectada: no se debe exponer la descripción enviada"
        assert "nombre_solicitante" not in data, "Mutación detectada: no se debe exponer el nombre"
        assert "email_solicitante" not in data, "Mutación detectada: no se debe exponer el email"
        assert "cedula_solicitante" not in data, "Mutación detectada: no se debe exponer la cédula"


@pytest.mark.asyncio
async def test_portal_tasa(tenant_con_portal):
    """R4: Más de 5 solicitudes por IP y hora responden 429 PORTAL_LIMITE."""
    _, slug = tenant_con_portal
    headers_ip1 = {"X-Forwarded-For": "198.51.100.10"}
    payload = {
        "derecho": "ACCESO",
        "nombre": "Usuario Tasa",
        "email": "tasa@ejemplo.com",
        "descripcion": "Petición repetida.",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Primeras 5 solicitudes exitosas
        for i in range(5):
            res = await ac.post(f"/api/v1/publico/solicitud/{slug}", json=payload, headers=headers_ip1)
            assert res.status_code == 201, f"Fallo en la peticion {i+1}: {res.text}"

        # La 6.ª solicitud desde la misma IP debe ser rechazada con 429
        res_bloqueada = await ac.post(f"/api/v1/publico/solicitud/{slug}", json=payload, headers=headers_ip1)
        assert res_bloqueada.status_code == 429

        # Otra IP distinta puede solicitar con normalidad
        headers_ip2 = {"X-Forwarded-For": "198.51.100.20"}
        res_otra_ip = await ac.post(f"/api/v1/publico/solicitud/{slug}", json=payload, headers=headers_ip2)
        assert res_otra_ip.status_code == 201


@pytest.mark.asyncio
async def test_validaciones_entrada(tenant_con_portal):
    """Valida códigos 422 en derecho fuera de catálogo, email inválido o descripción excesiva."""
    _, slug = tenant_con_portal
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Derecho inválido
        r1 = await ac.post(
            f"/api/v1/publico/solicitud/{slug}",
            json={"derecho": "INVENTADO", "nombre": "Juan", "email": "j@e.com", "descripcion": "ok"},
        )
        assert r1.status_code == 422

        # Email inválido
        r2 = await ac.post(
            f"/api/v1/publico/solicitud/{slug}",
            json={"derecho": "ACCESO", "nombre": "Juan", "email": "no-es-correo", "descripcion": "ok"},
        )
        assert r2.status_code == 422

        # Descripción > 4000 caracteres
        r3 = await ac.post(
            f"/api/v1/publico/solicitud/{slug}",
            json={"derecho": "ACCESO", "nombre": "Juan", "email": "j@e.com", "descripcion": "A" * 4001},
        )
        assert r3.status_code == 422


@pytest.mark.asyncio
async def test_configuracion_portal_rbac(tenant_con_portal, monkeypatch):
    """PUT /derechos/portal requiere rol admin_organizacion."""
    from unittest.mock import AsyncMock
    from features.organizacion import organizacion_service

    monkeypatch.setattr(organizacion_service, "has_active_role", AsyncMock(return_value=True))

    tenant_id, _ = tenant_con_portal
    nuevo_slug = f"nuevo-slug-{uuid.uuid4().hex[:6]}"
    body = {"activo": True, "slug": nuevo_slug, "texto_bienvenida": "Texto nuevo"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Con admin_organizacion: éxito
        res_admin = await ac.put(
            "/api/v1/derechos/portal",
            json=body,
            headers={
                "X-Tenant-ID": tenant_id,
                "X-Role": "admin_organizacion",
                "X-User-ID": "u_admin_1",
            },
        )
        assert res_admin.status_code == 200
        assert res_admin.json()["slug"] == nuevo_slug

        # Con rol dpo: no tiene permiso de escritura (403)
        res_dpo = await ac.put(
            "/api/v1/derechos/portal",
            json=body,
            headers={
                "X-Tenant-ID": tenant_id,
                "X-Role": "dpo",
                "X-User-ID": "u_dpo_1",
            },
        )
        assert res_dpo.status_code == 403
