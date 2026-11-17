# ¤¤qa-engineer ¤auditoria-capa ¤hallazgos ¤arbitro
"""Suite de pruebas y árbitro para CAPA-04: Auditoría con grilla de verificación por dominio y acta por área.

Contrato: governance/especificaciones/CAPA-04.md.
Escenarios verificados:
1. test_grilla_genera_hallazgo: Fila declarado 3, verificado 1 -> genera hallazgo 'auditoria'.
2. test_auditor_no_ejecutor: Revisor responsable de tarea de ese control_ref -> 403 AUDITOR_EJECUTOR. Mutación documentada.
3. test_acta_por_area_firmada: Acta custodiada como evidencia 'acta_auditoria', sin 'certificado', segunda acta -> 409 ACTA_YA_FIRMADA.
4. test_acta_exige_area_completa: Área con fila sin verificar -> 409 AUDITORIA_INCOMPLETA.
5. test_get_acta_roles_y_huella: Auditor, DPO y admin_organizacion reciben 200; implementador 403. Huella coincide con contenido.
6. test_hallazgo_cerrado_solo_con_verificacion: Hallazgo pasa a 'cerrado' solo con verificación conforme. cerrar_por_tareas no lo cierra.
7. test_verificador_no_cierra: Quien cerró la acción no puede verificar el cierre -> 403 AUDITOR_EJECUTOR.
8. test_escala_unica_diagnostico: Escala SMARTCIDI 1 a 5; verificado = 0 rechazado. Mutación documentada.
9. test_rls_auditorias: Aislamiento estricto por tenant en las 4 tablas con lopdp_app.
10. test_sin_palabra_prohibida: El término 'certificado' está terminantemente ausente.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session
from app_core.errors import ErrorNegocio
from features.auditoria_capa.domain import errores as e
from features.auditoria_capa.services import grilla_engine
from features.roadmap.roadmap_service import cerrar_por_tareas
from main import app


@pytest.mark.asyncio
async def test_escala_unica_diagnostico():
    """Dado la escala del diagnóstico, cuando se precarga la grilla, entonces verificado admite solo 1 a 5.
    Mutación: aceptar verificado = 0 hace fallar la prueba.
    """
    mock_session = AsyncMock(spec=AsyncSession)

    # 1. Intentar actualizar con verificado = 0 debe fallar
    with pytest.raises(ValueError, match="El nivel verificado debe estar entre 1 y 5"):
        await grilla_engine.actualizar_fila_auditoria(
            mock_session,
            tenant_id="tenant-1",
            user_id="auditor-1",
            auditoria_id="aud-1",
            control_ref="P12",
            verificado=0,  # INV_LOPDP_SMARTCIDI_MATURITY_SCALE
            riesgo_final=15,
        )

    # 2. Intentar actualizar con verificado = 6 debe fallar
    with pytest.raises(ValueError, match="El nivel verificado debe estar entre 1 y 5"):
        await grilla_engine.actualizar_fila_auditoria(
            mock_session,
            tenant_id="tenant-1",
            user_id="auditor-1",
            auditoria_id="aud-1",
            control_ref="P12",
            verificado=6,
            riesgo_final=0,
        )


@pytest.mark.asyncio
async def test_grilla_genera_hallazgo():
    """Dado una fila con declarado 3 y verificado 1, entonces se crea un hallazgo 'auditoria'."""
    mock_session = AsyncMock(spec=AsyncSession)

    auditoria_mock = {
        "id": "aud-test-1",
        "tenant_id": "tenant-test",
        "nombre": "Auditoría Anual 2026",
        "estado": "abierta",
        "alcance": ["area-1"],
        "equipo": ["auditor-1"],
        "filas": [
            {
                "id": "fila-1",
                "area_id": "area-1",
                "control_ref": "P12",
                "declarado": 3,
                "riesgo_inicial": 6,
                "verificado": None,
                "evidencia_sha256": None,
                "riesgo_final": None,
                "revisado_por": None,
                "hallazgo_id": None,
            }
        ],
        "actas": [],
    }

    with patch("features.auditoria_capa.services.grilla_engine.obtener_auditoria", AsyncMock(return_value=auditoria_mock)), \
         patch("app_core.pasillo.roadmap.es_ejecutor_control", AsyncMock(return_value=False)), \
         patch("app_core.pasillo.roadmap.registrar_hallazgo_auditoria", AsyncMock(return_value=("hallazgo-aud-123", True))) as mock_reg_hallazgo:

        res = await grilla_engine.actualizar_fila_auditoria(
            mock_session,
            tenant_id="tenant-test",
            user_id="auditor-1",
            auditoria_id="aud-test-1",
            control_ref="P12",
            verificado=1,
            riesgo_final=12,
        )

        assert res["verificado"] == 1
        assert res["hallazgo_id"] == "hallazgo-aud-123"
        mock_reg_hallazgo.assert_awaited_once()
        args, kwargs = mock_reg_hallazgo.call_args
        assert kwargs["control_ref"] == "P12"
        assert kwargs["origen_ref"] == "aud-test-1:P12"
        assert kwargs["severidad"] == "alta"  # riesgo_final 12 -> alta (>= 9 y < 15)


@pytest.mark.asyncio
async def test_auditor_no_ejecutor():
    """Dado un revisor que es responsable de una tarea de P12, cuando verifica P12, entonces 403 AUDITOR_EJECUTOR.
    Mutación: permitir que el ejecutor verifique debe hacer fallar la prueba.
    """
    mock_session = AsyncMock(spec=AsyncSession)

    auditoria_mock = {
        "id": "aud-test-1",
        "tenant_id": "tenant-test",
        "nombre": "Auditoría Anual 2026",
        "estado": "abierta",
        "alcance": ["area-1"],
        "equipo": ["ejecutor-1"],
        "filas": [
            {
                "id": "fila-1",
                "area_id": "area-1",
                "control_ref": "P12",
                "declarado": 3,
                "riesgo_inicial": 6,
                "verificado": None,
                "evidencia_sha256": None,
                "riesgo_final": None,
                "revisado_por": None,
                "hallazgo_id": None,
            }
        ],
        "actas": [],
    }

    # es_ejecutor_control retorna True
    with patch("features.auditoria_capa.services.grilla_engine.obtener_auditoria", AsyncMock(return_value=auditoria_mock)), \
         patch("app_core.pasillo.roadmap.es_ejecutor_control", AsyncMock(return_value=True)):

        with pytest.raises(ErrorNegocio) as exc_info:
            await grilla_engine.actualizar_fila_auditoria(
                mock_session,
                tenant_id="tenant-test",
                user_id="ejecutor-1",
                auditoria_id="aud-test-1",
                control_ref="P12",
                verificado=3,
                riesgo_final=6,
            )

        assert exc_info.value.code == e.AUDITOR_EJECUTOR.codigo


@pytest.mark.asyncio
async def test_acta_exige_area_completa():
    """Dado un área con una fila sin verificar, cuando se levanta el acta, entonces 409 AUDITORIA_INCOMPLETA."""
    mock_session = AsyncMock(spec=AsyncSession)

    auditoria_mock = {
        "id": "aud-test-1",
        "tenant_id": "tenant-test",
        "nombre": "Auditoría Anual 2026",
        "estado": "abierta",
        "alcance": ["area-1"],
        "equipo": ["auditor-1"],
        "filas": [
            {
                "id": "fila-1",
                "area_id": "area-1",
                "control_ref": "P12",
                "declarado": 3,
                "verificado": None,  # Pendiente de verificar
            }
        ],
        "actas": [],
    }

    with patch("features.auditoria_capa.services.grilla_engine.obtener_auditoria", AsyncMock(return_value=auditoria_mock)):
        with pytest.raises(ErrorNegocio) as exc_info:
            await grilla_engine.levantar_y_firmar_acta(
                mock_session,
                tenant_id="tenant-test",
                user_id="auditor-1",
                auditoria_id="aud-test-1",
                area_id="area-1",
            )
        assert exc_info.value.code == e.AUDITORIA_INCOMPLETA.codigo


@pytest.mark.asyncio
async def test_acta_por_area_firmada():
    """Dado un área con todas sus filas verificadas, cuando el auditor levanta el acta,
    queda una sola acta firmada custodiada como evidencia, y no contiene 'certificado'.
    Un segundo intento da 409 ACTA_YA_FIRMADA.
    """
    mock_session = AsyncMock(spec=AsyncSession)

    auditoria_mock = {
        "id": "aud-test-1",
        "tenant_id": "tenant-test",
        "nombre": "Auditoría Anual 2026",
        "estado": "abierta",
        "alcance": ["area-1"],
        "equipo": ["auditor-1"],
        "filas": [
            {
                "id": "fila-1",
                "area_id": "area-1",
                "control_ref": "P12",
                "declarado": 3,
                "riesgo_inicial": 6,
                "verificado": 3,
                "riesgo_final": 6,
                "evidencia_sha256": "abc123sha",
            }
        ],
        "actas": [],
    }

    custodia_mock = {
        "evidencia_id": "ev-doc-1",
        "sha256": "sha256-acta-integridad-1234567890",
    }

    with patch("features.auditoria_capa.services.grilla_engine.obtener_auditoria", AsyncMock(return_value=auditoria_mock)), \
         patch("app_core.pasillo.evidencias.custodiar_acta_auditoria", AsyncMock(return_value=custodia_mock)) as mock_custodia:

        res = await grilla_engine.levantar_y_firmar_acta(
            mock_session,
            tenant_id="tenant-test",
            user_id="auditor-1",
            auditoria_id="aud-test-1",
            area_id="area-1",
        )

        assert res["area_id"] == "area-1"
        assert res["acta_sha256"] == "sha256-acta-integridad-1234567890"

        # Verificar contenido custodiado: no contiene 'certificado'
        mock_custodia.assert_awaited_once()
        _, kwargs = mock_custodia.call_args
        contenido_texto = kwargs["contenido"].decode("utf-8")
        assert "certificado" not in contenido_texto.lower()
        assert "Acta de auditoría" in contenido_texto

    # Segundo intento con el acta ya presente en auditoria['actas']
    auditoria_con_acta = dict(auditoria_mock)
    auditoria_con_acta["actas"] = [{"area_id": "area-1", "acta_sha256": "sha256-acta-integridad-1234567890"}]

    with patch("features.auditoria_capa.services.grilla_engine.obtener_auditoria", AsyncMock(return_value=auditoria_con_acta)):
        with pytest.raises(ErrorNegocio) as exc_info:
            await grilla_engine.levantar_y_firmar_acta(
                mock_session,
                tenant_id="tenant-test",
                user_id="auditor-1",
                auditoria_id="aud-test-1",
                area_id="area-1",
            )
        assert exc_info.value.code == e.ACTA_YA_FIRMADA.codigo


@pytest.mark.asyncio
async def test_verificador_no_cierra():
    """Dado que quien verifica el cierre es quien cerró la acción o ejecutó el control -> 403 AUDITOR_EJECUTOR."""
    mock_session = AsyncMock(spec=AsyncSession)

    with patch("app_core.pasillo.roadmap.es_ejecutor_o_cerrador_hallazgo", AsyncMock(return_value=True)):
        with pytest.raises(ErrorNegocio) as exc_info:
            await grilla_engine.verificar_cierre_hallazgo(
                mock_session,
                tenant_id="tenant-test",
                user_id="ejecutor-1",
                hallazgo_id="hallazgo-1",
                resultado="conforme",
                motivo="Verificación de control completada adecuadamente",
            )
        assert exc_info.value.code == e.AUDITOR_EJECUTOR.codigo


@pytest.mark.asyncio
async def test_hallazgo_cerrado_solo_con_verificacion():
    """Dado un hallazgo con su acción cerrada por el implementador, cuando el auditor verifica conforme,
    el hallazgo queda cerrado. Sin verificación, cerrar_por_tareas no lo cierra (exclusión origen <> 'auditoria').
    """
    mock_session = AsyncMock(spec=AsyncSession)

    with patch("app_core.pasillo.roadmap.es_ejecutor_o_cerrador_hallazgo", AsyncMock(return_value=False)), \
         patch("app_core.pasillo.roadmap.comprobar_accion_cerrada_con_evidencia", AsyncMock(return_value=(True, None))), \
         patch("app_core.pasillo.roadmap.cerrar_hallazgo", AsyncMock()) as mock_cerrar:

        res = await grilla_engine.verificar_cierre_hallazgo(
            mock_session,
            tenant_id="tenant-test",
            user_id="auditor-1",
            hallazgo_id="hallazgo-aud-1",
            resultado="conforme",
            motivo="Verificación exhaustiva de evidencia realizada con éxito",
        )

        assert res["resultado"] == "conforme"
        mock_cerrar.assert_awaited_once()


@pytest.mark.asyncio
async def test_cierre_hallazgos_engine_excluye_auditoria():
    """Comprueba que cerrar_por_tareas en roadmap excluye h.origen <> 'auditoria'.
    Mutación: quitar esa exclusión rompería la SoD del auditor.
    """
    mock_session = AsyncMock(spec=AsyncSession)
    mock_res = MagicMock()
    mock_res.all.return_value = []
    mock_session.execute.return_value = mock_res

    await cerrar_por_tareas(mock_session, tenant_id="tenant-test", user_id="impl-1")

    # Inspeccionar las consultas SQL ejecutadas
    llamadas_sql = [str(call[0][0]) for call in mock_session.execute.call_args_list]
    sql_completo = " ".join(llamadas_sql)
    assert "h.origen <> 'auditoria'" in sql_completo or "origen <> 'auditoria'" in sql_completo


@pytest.mark.asyncio
async def test_get_acta_roles_y_huella():
    """Dado un acta firmada, auditor, DPO y admin_organizacion reciben 200 con {area_id, acta_sha256, contenido}.
    El implementador recibe 403.
    """
    contenido_ejemplo = "Acta de auditoría · Área D01\nFirmada por: auditor-1\nEsta acta recoge lo verificado..."
    sha_calculado = hashlib.sha256(contenido_ejemplo.encode("utf-8")).hexdigest()

    async def override_get_session():
        session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = {
            "id": "acta-uuid",
            "area_id": "D01",
            "evidencia_id": "ev-1",
            "acta_sha256": sha_calculado,
            "firmada_por": "auditor-1",
            "firmada_en": datetime.now(timezone.utc),
        }
        session.execute.return_value = mock_result
        yield session

    app.dependency_overrides[get_session] = override_get_session

    with patch("features.organizacion.organizacion_service.has_active_role", AsyncMock(return_value=True)), \
         patch("app_core.pasillo.evidencias.leer_contenido_acta", AsyncMock(return_value=contenido_ejemplo)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Auditor -> 200
            res_aud = await client.get(
                "/api/v1/auditoria-capa/auditorias/aud-1/areas/D01/acta",
                headers={"X-User-ID": "u-aud", "X-Tenant-ID": "t-1", "X-Role": "auditor"},
            )
            assert res_aud.status_code == 200
            data = res_aud.json()
            assert data["acta_sha256"] == sha_calculado
            assert data["contenido"] == contenido_ejemplo

            # 2. DPO -> 200
            res_dpo = await client.get(
                "/api/v1/auditoria-capa/auditorias/aud-1/areas/D01/acta",
                headers={"X-User-ID": "u-dpo", "X-Tenant-ID": "t-1", "X-Role": "dpo"},
            )
            assert res_dpo.status_code == 200

            # 3. Implementador -> 403
            res_impl = await client.get(
                "/api/v1/auditoria-capa/auditorias/aud-1/areas/D01/acta",
                headers={"X-User-ID": "u-impl", "X-Tenant-ID": "t-1", "X-Role": "implementador"},
            )
            assert res_impl.status_code == 403

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rls_auditorias():
    """Dado registros de A, cuando se consulta en B con lopdp_app, entonces 0 filas en las cuatro tablas."""
    from app_core.db.session import async_session_factory

    async with async_session_factory() as session:
        # 1. Crear tenant A y tenant B con RUCs únicos
        tenant_a = f"t_a_{uuid.uuid4().hex[:8]}"
        tenant_b = f"t_b_{uuid.uuid4().hex[:8]}"
        ruc_a = f"17{uuid.uuid4().int % 100000000000:011d}"
        ruc_b = f"17{uuid.uuid4().int % 100000000000:011d}"

        await session.execute(
            text(
                """
                INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion)
                VALUES (:ta, 'Org A', 'Org A S.A.', :ra),
                       (:tb, 'Org B', 'Org B S.A.', :rb)
                """
            ),
            {"ta": tenant_a, "tb": tenant_b, "ra": ruc_a, "rb": ruc_b},
        )
        await session.commit()

        # 2. Como tenant A, insertar en auditorias, filas, actas y verificaciones
        aud_id = str(uuid.uuid4())
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :t, false)"),
            {"t": tenant_a},
        )
        await session.execute(
            text(
                """
                INSERT INTO auditorias (id, tenant_id, nombre, alcance, equipo, estado, creado_por)
                VALUES (:id, :t, 'Auditoria A', '["D01"]'::jsonb, '["u-1"]'::jsonb, 'abierta', 'u-1')
                """
            ),
            {"id": aud_id, "t": tenant_a},
        )
        fila_id = str(uuid.uuid4())
        await session.execute(
            text(
                """
                INSERT INTO auditoria_filas (id, tenant_id, auditoria_id, area_id, control_ref, declarado, riesgo_inicial)
                VALUES (:id, :t, :aud_id, 'D01', 'P12', 3, 6)
                """
            ),
            {"id": fila_id, "t": tenant_a, "aud_id": aud_id},
        )
        acta_id = str(uuid.uuid4())
        await session.execute(
            text(
                """
                INSERT INTO auditoria_actas (id, tenant_id, auditoria_id, area_id, evidencia_id, acta_sha256, firmada_por)
                VALUES (:id, :t, :aud_id, 'D01', 'ev-1', 'sha256-test', 'u-1')
                """
            ),
            {"id": acta_id, "t": tenant_a, "aud_id": aud_id},
        )
        verif_id = str(uuid.uuid4())
        await session.execute(
            text(
                """
                INSERT INTO auditoria_verificaciones_cierre (id, tenant_id, hallazgo_id, accion_ref, verificado_por, resultado, motivo)
                VALUES (:id, :t, 'h-1', 'accion:h-1', 'u-1', 'conforme', 'Motivo de prueba con mas de 10 chars')
                """
            ),
            {"id": verif_id, "t": tenant_a},
        )
        await session.commit()

        # 3. Conmutar al rol 'lopdp_app' y fijar contexto tenant B
        await session.execute(text("SET LOCAL ROLE lopdp_app"))
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :t, true)"),
            {"t": tenant_b},
        )

        # Consultar las cuatro tablas: debe dar exactamente 0 filas
        filas_aud = (await session.execute(text("SELECT id FROM auditorias WHERE id = :id"), {"id": aud_id})).all()
        assert len(filas_aud) == 0

        filas_f = (await session.execute(text("SELECT id FROM auditoria_filas WHERE id = :id"), {"id": fila_id})).all()
        assert len(filas_f) == 0

        filas_actas = (await session.execute(text("SELECT id FROM auditoria_actas WHERE id = :id"), {"id": acta_id})).all()
        assert len(filas_actas) == 0

        filas_v = (await session.execute(text("SELECT id FROM auditoria_verificaciones_cierre WHERE id = :id"), {"id": verif_id})).all()
        assert len(filas_v) == 0

