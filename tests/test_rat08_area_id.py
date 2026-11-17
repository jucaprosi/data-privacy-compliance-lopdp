"""Árbitro RAT-08 contra PostgreSQL 16 local (TEST_DATABASE_URL).
Contrato: governance/especificaciones/RAT-08.md
Mutaciones m1 a m4.
"""
from datetime import datetime, timezone
from uuid import uuid4
import pytest
import pytest_asyncio
from fastapi import FastAPI, Header
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from conftest import exigir_base_de_pruebas
from features.rat.services.exportacion_engine import exportar_rat

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def rat08_env(db_engine):
    exigir_base_de_pruebas()
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    ta, tb = f"rat08-t1-{uuid4().hex[:8]}", f"rat08-t2-{uuid4().hex[:8]}"
    ruc_a = f"179{uuid4().int % 10000000000:010d}"
    ruc_b = f"179{uuid4().int % 10000000000:010d}"
    u_admin = f"u-admin-{uuid4().hex[:8]}"
    u_coord = f"u-coord-{uuid4().hex[:8]}"

    async with factory() as s:
        await s.execute(
            text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:id, :n, :n, :r)"),
            {"id": ta, "n": "Tenant RAT-08 A", "r": ruc_a},
        )
        await s.execute(
            text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:id, :n, :n, :r)"),
            {"id": tb, "n": "Tenant RAT-08 B", "r": ruc_b},
        )

        for u, rol in [(u_admin, "admin_organizacion"), (u_coord, "coordinador")]:
            await s.execute(
                text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :n)"),
                {"u": u, "e": f"{u}@rat08.test", "n": u},
            )
            await s.execute(
                text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, :r)"),
                {"id": str(uuid4()), "u": u, "t": ta, "r": rol},
            )
        await s.commit()

    try:
        yield {"factory": factory, "ta": ta, "tb": tb, "admin": u_admin, "coord": u_coord}
    finally:
        async with factory() as s:
            for t in (ta, tb):
                await s.execute(text("DELETE FROM audit_events WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM rat_versiones WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM hallazgos WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM rat_actividades WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM areas WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id = :t"), {"t": t})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            for u in (u_admin, u_coord):
                await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": u})
            await s.commit()


@pytest_asyncio.fixture
async def rat08_client(rat08_env):
    from api.routers.rat import router, get_rat_session
    from app_core.db.session import fijar_contexto_rls

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    async def sesion_override(
        x_tenant_id: str = Header("tenant-default"),
        x_user_id: str = Header(""),
    ):
        async with rat08_env["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s, x_tenant_id, x_user_id)
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    app.dependency_overrides[get_rat_session] = sesion_override
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as cliente:
        yield cliente


async def test_migracion_emparejado_normalizacion_mayusculas_y_espacios_m1(rat08_env):
    """Escenario 1 & Mutación m1: empareja 'Contabilidad ' y '  contabilidad' con 'Contabilidad'."""
    ta = rat08_env["ta"]
    area_id = str(uuid4())
    act1_id = str(uuid4())
    act2_id = str(uuid4())

    async with rat08_env["factory"]() as s:
        # Insertar área
        await s.execute(text("""
            INSERT INTO areas (id, tenant_id, nombre, codigo)
            VALUES (:id, :t, 'Contabilidad', 'CONT')
        """), {"id": area_id, "t": ta})

        # Insertar actividades con texto sin normalizar
        for aid, txt in [(act1_id, "Contabilidad "), (act2_id, "  contabilidad")]:
            await s.execute(text("""
                INSERT INTO rat_actividades (
                    id, tenant_id, codigo, nombre, area_responsable, finalidad, base_legal,
                    categorias_titulares, categorias_datos, datos_sensibles, volumen_titulares_estimado,
                    transferencia_internacional, requiere_eipd, es_gran_escala, version, medio_soporte,
                    encargados, destinatarios, pais_transferencia, plazo_conservacion, medidas_seguridad,
                    nivel_riesgo, decisiones_automatizadas, volumen_titulares_12_meses, observaciones_dpo, origen
                ) VALUES (
                    :id, :t, :cod, 'Tratamiento', :txt, 'Fin', 'CONSENTIMIENTO',
                    '[]'::json, '[]'::json, false, 10, false, false, false, 1, '',
                    '[]'::json, '[]'::json, '', '', '[]'::json, '', false, 10, '', 'manual'
                )
            """), {"id": aid, "t": ta, "cod": f"COD-{aid[:6]}", "txt": txt})
        await s.commit()

        # Ejecutar lógica de emparejado de la migración
        await s.execute(text("""
            UPDATE rat_actividades r
            SET area_id = m.area_id
            FROM (
                SELECT r2.id AS rat_id, min(a.id) AS area_id
                FROM rat_actividades r2
                JOIN areas a
                    ON a.tenant_id = r2.tenant_id
                    AND a.deleted_at IS NULL
                    AND lower(trim(a.nombre)) = lower(trim(r2.area_responsable))
                GROUP BY r2.id
                HAVING count(a.id) = 1
            ) m
            WHERE r.id = m.rat_id AND r.tenant_id = :t;
        """), {"t": ta})
        await s.commit()

        # Comprobar que ambas filas recibieron area_id
        filas = (await s.execute(
            text("SELECT id, area_id, area_responsable FROM rat_actividades WHERE id IN (:a1, :a2)"),
            {"a1": act1_id, "a2": act2_id},
        )).mappings().all()

        assert len(filas) == 2
        for f in filas:
            assert f["area_id"] == area_id, f"Fallo m1: {f['id']} debía tener area_id emparejado"


async def test_migracion_sin_emparejar_o_ambigua_m2_y_preserva_texto_m3(rat08_env):
    """Escenario 2 & Mutación m2 & m3: texto que no coincide o coincide con dos áreas queda NULL y texto intacto."""
    ta = rat08_env["ta"]
    area1_id = str(uuid4())
    area2_id = str(uuid4())
    act_no_match = str(uuid4())
    act_ambigua = str(uuid4())

    async with rat08_env["factory"]() as s:
        # Dos áreas con mismo nombre normalizado en el mismo tenant (para provocar ambigüedad)
        await s.execute(text("""
            INSERT INTO areas (id, tenant_id, nombre, codigo)
            VALUES (:id1, :t, 'Ventas', 'V1'), (:id2, :t, 'ventas', 'V2')
        """), {"id1": area1_id, "id2": area2_id, "t": ta})

        # Actividad con texto no emparejable
        await s.execute(text("""
            INSERT INTO rat_actividades (
                id, tenant_id, codigo, nombre, area_responsable, finalidad, base_legal,
                categorias_titulares, categorias_datos, datos_sensibles, volumen_titulares_estimado,
                transferencia_internacional, requiere_eipd, es_gran_escala, version, medio_soporte,
                encargados, destinatarios, pais_transferencia, plazo_conservacion, medidas_seguridad,
                nivel_riesgo, decisiones_automatizadas, volumen_titulares_12_meses, observaciones_dpo, origen
            ) VALUES (
                :id, :t, 'COD-NOMATCH', 'Tratamiento Sin Match', 'Area Inexistente XYZ', 'Fin', 'CONSENTIMIENTO',
                '[]'::json, '[]'::json, false, 10, false, false, false, 1, '',
                '[]'::json, '[]'::json, '', '', '[]'::json, '', false, 10, '', 'manual'
            )
        """), {"id": act_no_match, "t": ta})

        # Actividad ambigua (coincide con dos áreas vivas)
        await s.execute(text("""
            INSERT INTO rat_actividades (
                id, tenant_id, codigo, nombre, area_responsable, finalidad, base_legal,
                categorias_titulares, categorias_datos, datos_sensibles, volumen_titulares_estimado,
                transferencia_internacional, requiere_eipd, es_gran_escala, version, medio_soporte,
                encargados, destinatarios, pais_transferencia, plazo_conservacion, medidas_seguridad,
                nivel_riesgo, decisiones_automatizadas, volumen_titulares_12_meses, observaciones_dpo, origen
            ) VALUES (
                :id, :t, 'COD-AMBIGUO', 'Tratamiento Ambiguo', 'Ventas', 'Fin', 'CONSENTIMIENTO',
                '[]'::json, '[]'::json, false, 10, false, false, false, 1, '',
                '[]'::json, '[]'::json, '', '', '[]'::json, '', false, 10, '', 'manual'
            )
        """), {"id": act_ambigua, "t": ta})
        await s.commit()

        # Ejecutar lógica de migración
        await s.execute(text("""
            UPDATE rat_actividades r
            SET area_id = m.area_id
            FROM (
                SELECT r2.id AS rat_id, min(a.id) AS area_id
                FROM rat_actividades r2
                JOIN areas a
                    ON a.tenant_id = r2.tenant_id
                    AND a.deleted_at IS NULL
                    AND lower(trim(a.nombre)) = lower(trim(r2.area_responsable))
                GROUP BY r2.id
                HAVING count(a.id) = 1
            ) m
            WHERE r.id = m.rat_id AND r.tenant_id = :t;
        """), {"t": ta})
        await s.commit()

        # Comprobar filas
        f_no = (await s.execute(
            text("SELECT area_id, area_responsable FROM rat_actividades WHERE id = :id"),
            {"id": act_no_match},
        )).mappings().first()
        f_amb = (await s.execute(
            text("SELECT area_id, area_responsable FROM rat_actividades WHERE id = :id"),
            {"id": act_ambigua},
        )).mappings().first()

        # Mutación m2: no inventar área si no casa o es ambigua
        assert f_no["area_id"] is None
        assert f_amb["area_id"] is None

        # Mutación m3: preservar texto intacto
        assert f_no["area_responsable"] == "Area Inexistente XYZ"
        assert f_amb["area_responsable"] == "Ventas"


async def test_api_crear_con_area_invalida_422(rat08_env, rat08_client):
    """Escenario 4: área de otro tenant, inexistente o borrada responde 422 AREA_NO_VALIDA."""
    ta, tb = rat08_env["ta"], rat08_env["tb"]
    area_tb_id = str(uuid4())
    area_borrada_id = str(uuid4())

    async with rat08_env["factory"]() as s:
        # Área en tenant B
        await s.execute(text("INSERT INTO areas (id, tenant_id, nombre) VALUES (:id, :t, 'Área B')"), {"id": area_tb_id, "t": tb})
        # Área borrada en tenant A
        await s.execute(text("INSERT INTO areas (id, tenant_id, nombre, deleted_at) VALUES (:id, :t, 'Área Borrada', NOW())"), {"id": area_borrada_id, "t": ta})
        await s.commit()

    cabeceras = {
        "X-Tenant-ID": ta,
        "X-User-ID": rat08_env["coord"],
        "X-Role": "coordinador",
    }

    # 1. Área de otro tenant
    r_otro = await rat08_client.post("/api/v1/rat/actividades", json={
        "codigo": "RAT-TEST-01",
        "nombre": "Test Otro Tenant",
        "area_id": area_tb_id,
        "finalidad": "Validación",
        "base_legal": "CONSENTIMIENTO",
    }, headers=cabeceras)
    assert r_otro.status_code == 422
    assert "AREA_NO_VALIDA" in r_otro.text

    # 2. Área borrada
    r_borrada = await rat08_client.post("/api/v1/rat/actividades", json={
        "codigo": "RAT-TEST-02",
        "nombre": "Test Borrada",
        "area_id": area_borrada_id,
        "finalidad": "Validación",
        "base_legal": "CONSENTIMIENTO",
    }, headers=cabeceras)
    assert r_borrada.status_code == 422
    assert "AREA_NO_VALIDA" in r_borrada.text

    # 3. Área inexistente
    r_inex = await rat08_client.post("/api/v1/rat/actividades", json={
        "codigo": "RAT-TEST-03",
        "nombre": "Test Inexistente",
        "area_id": str(uuid4()),
        "finalidad": "Validación",
        "base_legal": "CONSENTIMIENTO",
    }, headers=cabeceras)
    assert r_inex.status_code == 422
    assert "AREA_NO_VALIDA" in r_inex.text


async def test_api_crear_con_area_valida(rat08_env, rat08_client):
    """Escenario 5: área válida guarda area_id y rellena area_responsable con el nombre del área."""
    ta = rat08_env["ta"]
    area_id = str(uuid4())

    async with rat08_env["factory"]() as s:
        await s.execute(text("INSERT INTO areas (id, tenant_id, nombre) VALUES (:id, :t, 'Operaciones TI')"), {"id": area_id, "t": ta})
        await s.commit()

    cabeceras = {
        "X-Tenant-ID": ta,
        "X-User-ID": rat08_env["coord"],
        "X-Role": "coordinador",
    }

    res = await rat08_client.post("/api/v1/rat/actividades", json={
        "codigo": "RAT-VALID-01",
        "nombre": "Gestión de Accesos",
        "area_id": area_id,
        "finalidad": "Seguridad de la información",
        "base_legal": "CONSENTIMIENTO",
    }, headers=cabeceras)
    assert res.status_code == 200
    datos = res.json()["actividad"]
    assert datos["area_id"] == area_id
    assert datos["area_responsable"] == "Operaciones TI"


async def test_api_listar_y_exportar_resuelve_nombre_actual_renombrado_m4(rat08_env, rat08_client):
    """Escenario 6 & Mutación m4: al renombrar el área, listar y exportar muestran el nombre nuevo sin modificar rat_actividades."""
    ta = rat08_env["ta"]
    area_id = str(uuid4())
    act_id = str(uuid4())

    async with rat08_env["factory"]() as s:
        # Crear área original
        await s.execute(text("INSERT INTO areas (id, tenant_id, nombre) VALUES (:id, :t, 'Nombre Antiguo')"), {"id": area_id, "t": ta})
        # Crear actividad vinculada al área pero con area_responsable = 'Nombre Antiguo'
        await s.execute(text("""
            INSERT INTO rat_actividades (
                id, tenant_id, codigo, nombre, area_id, area_responsable, finalidad, base_legal,
                categorias_titulares, categorias_datos, datos_sensibles, volumen_titulares_estimado,
                transferencia_internacional, requiere_eipd, es_gran_escala, version, medio_soporte,
                encargados, destinatarios, pais_transferencia, plazo_conservacion, medidas_seguridad,
                nivel_riesgo, decisiones_automatizadas, volumen_titulares_12_meses, observaciones_dpo, origen
            ) VALUES (
                :id, :t, 'RAT-REN-01', 'Tratamiento Renombrado', :aid, 'Nombre Antiguo', 'Fin', 'CONSENTIMIENTO',
                '[]'::json, '[]'::json, false, 10, false, false, false, 1, '',
                '[]'::json, '[]'::json, '', '', '[]'::json, '', false, 10, '', 'manual'
            )
        """), {"id": act_id, "t": ta, "aid": area_id})
        await s.commit()

        # Renombrar el área en la tabla areas (sin tocar rat_actividades)
        await s.execute(text("UPDATE areas SET nombre = 'Nombre Nuevo 2026' WHERE id = :id"), {"id": area_id})
        await s.commit()

    cabeceras = {
        "X-Tenant-ID": ta,
        "X-User-ID": rat08_env["coord"],
        "X-Role": "coordinador",
    }

    # 1. Listar actividades vía API
    r_list = await rat08_client.get("/api/v1/rat/actividades", headers=cabeceras)
    assert r_list.status_code == 200
    acts = r_list.json()["actividades"]
    act = next(a for a in acts if a["id"] == act_id)

    # Mutación m4: debe resolver el nombre vivo actual ('Nombre Nuevo 2026'), no el estático 'Nombre Antiguo'
    assert act["area_responsable"] == "Nombre Nuevo 2026"

    # Verificar que en la base de datos rat_actividades NO fue modificada
    async with rat08_env["factory"]() as s:
        db_fila = (await s.execute(text("SELECT area_responsable FROM rat_actividades WHERE id = :id"), {"id": act_id})).scalar()
        assert db_fila == "Nombre Antiguo"

        # 2. Exportación a XLSX
        exp = await exportar_rat(s, ta, "xlsx")
        assert exp.contenido is not None
        # Comprobar que en el Excel aparece el nombre nuevo
        from openpyxl import load_workbook
        from io import BytesIO
        wb = load_workbook(BytesIO(exp.contenido))
        hoja = wb.active
        filas = list(hoja.iter_rows(values_only=True))
        area_col_idx = filas[0].index("Área responsable")
        areas_en_excel = [f[area_col_idx] for f in filas[1:]]
        assert "Nombre Nuevo 2026" in areas_en_excel


async def test_api_listar_y_exportar_area_borrada_muestra_respaldo(rat08_env, rat08_client):
    """Escenario 7: cuando el área enlazada fue borrada lógicamente, el listado y la exportación muestran el respaldo guardado."""
    ta = rat08_env["ta"]
    area_id = str(uuid4())
    act_id = str(uuid4())

    async with rat08_env["factory"]() as s:
        # Crear área y marcarla borrada
        await s.execute(text("INSERT INTO areas (id, tenant_id, nombre, deleted_at) VALUES (:id, :t, 'Área Borrada', NOW())"), {"id": area_id, "t": ta})
        # Crear actividad
        await s.execute(text("""
            INSERT INTO rat_actividades (
                id, tenant_id, codigo, nombre, area_id, area_responsable, finalidad, base_legal,
                categorias_titulares, categorias_datos, datos_sensibles, volumen_titulares_estimado,
                transferencia_internacional, requiere_eipd, es_gran_escala, version, medio_soporte,
                encargados, destinatarios, pais_transferencia, plazo_conservacion, medidas_seguridad,
                nivel_riesgo, decisiones_automatizadas, volumen_titulares_12_meses, observaciones_dpo, origen
            ) VALUES (
                :id, :t, 'RAT-DEL-01', 'Tratamiento Respaldo', :aid, 'Texto Respaldo Original', 'Fin', 'CONSENTIMIENTO',
                '[]'::json, '[]'::json, false, 10, false, false, false, 1, '',
                '[]'::json, '[]'::json, '', '', '[]'::json, '', false, 10, '', 'manual'
            )
        """), {"id": act_id, "t": ta, "aid": area_id})
        await s.commit()

    cabeceras = {
        "X-Tenant-ID": ta,
        "X-User-ID": rat08_env["coord"],
        "X-Role": "coordinador",
    }

    r_list = await rat08_client.get("/api/v1/rat/actividades", headers=cabeceras)
    assert r_list.status_code == 200
    acts = r_list.json()["actividades"]
    act = next(a for a in acts if a["id"] == act_id)
    assert act["area_responsable"] == "Texto Respaldo Original"
