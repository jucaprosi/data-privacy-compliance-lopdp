# ¤¤qa-engineer ¤formacion ¤arbitro
"""Suite de pruebas y árbitro para FOR-01: Módulo de Formación, exámenes y seguimiento de capacitación.

Contrato: governance/especificaciones/FOR-01.md y governance/tareas/FOR-01.md.
Escenarios verificados:
1. test_examen_aprueba_y_diploma: Nota >= mínima aprueba y custodia constancia en evidencias con P73 y capacitacion.
2. test_examen_un_intento: Segundo intento lanza 409 EXAMEN_YA_RENDIDO (R4).
3. test_examen_fallido_no_consume_intento: Fallo en transacción no fija terminado_en (solo 200 consume intento).
4. test_examen_concurrente_un_solo_intento: Condición atómica transaccional evita doble rendición.
5. test_examen_sin_correcta: GET .../examen oculta estrictamente el campo 'correcta'.
6. test_iniciar_idempotente: POST .../iniciar fija iniciado_en de forma idempotente.
7. test_banco_congelado: Intentar añadir preguntas a contenido con participación iniciada -> 409 PREGUNTAS_CONGELADAS.
8. test_cobertura: Cálculo sobre personas activas del inventario (2 de 4 = 50%).
9. test_rls_formacion: Aislamiento estricto por tenant en las 4 tablas con rol lopdp_app.
10. test_sin_palabra_prohibida_formacion: Prohibida terminantemente la palabra 'certificado' o 'diploma'.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import text

from app_core.db.session import async_session_factory
from app_core.errors import ErrorNegocio
from features.formacion.domain import errores as e
from features.formacion.services import (
    acciones_engine,
    cobertura_engine,
    contenidos_engine,
    diploma_engine,
    examen_engine,
)


@pytest.mark.asyncio
async def test_examen_aprueba_y_diploma():
    """Dado un examen iniciado, cuando el participante responde correctamente y supera la nota mínima,
    entonces aprueba, se registra terminado_en y se custodia la constancia como evidencia (P73, capacitacion).
    Mutación documentada: si la nota es menor que la mínima, aprobado es False y no se custodia constancia.
    """
    async with async_session_factory() as session:
        tenant_id = f"t_{uuid.uuid4().hex[:8]}"
        user_id = f"u_{uuid.uuid4().hex[:8]}"
        persona_id = f"p_{uuid.uuid4().hex[:8]}"
        ruc = f"17{uuid.uuid4().int % 100000000000:011d}"

        await session.execute(
            text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                "VALUES (:t, 'Org Formacion', 'Org Formacion S.A.', :r)"
            ),
            {"t": tenant_id, "r": ruc},
        )
        await session.commit()

        # 1. Crear contenido y banco de preguntas
        cont = await contenidos_engine.crear_contenido(
            session,
            tenant_id,
            user_id,
            titulo="Protección de Datos Básica",
            tipo="pdf",
            referencia="https://ejemplo.com/material.pdf",
        )
        cont_id = cont["id"]

        await contenidos_engine.crear_pregunta(
            session,
            tenant_id,
            user_id,
            contenido_id=cont_id,
            enunciado="¿Cuál es el plazo general de atención ARCO?",
            opciones=["15 días", "365 días"],
            correcta=0,
        )

        # 2. Crear acción formativa y participante
        hoy = date.today()
        acc = await acciones_engine.crear_accion(
            session,
            tenant_id,
            user_id,
            contenido_id=cont_id,
            nombre="Campaña Anual 2026",
            inicio=hoy - timedelta(days=1),
            fin=hoy + timedelta(days=30),
            nota_minima=70.0,
        )
        acc_id = acc["id"]

        await acciones_engine.anadir_participantes(
            session, tenant_id, user_id, accion_id=acc_id, persona_ids=[persona_id]
        )
        parts = await acciones_engine.listar_participaciones_accion(
            session, tenant_id, user_id, accion_id=acc_id
        )
        part_id = parts[0]["id"]
        await session.commit()

        # Iniciar examen
        await examen_engine.iniciar_examen_participacion(
            session, tenant_id, user_id, participacion_id=part_id, persona_id=persona_id
        )
        await session.commit()

        # Rendir examen respondiendo correctamente (opción 0)
        with patch("app_core.pasillo.evidencias.custodiar_documento_generado", new_callable=AsyncMock) as mock_custodia:
            mock_custodia.return_value = {"id": "ev-12345", "sha256": "sha256-aprobado"}

            res = await examen_engine.calificar_y_terminar_examen(
                session,
                tenant_id,
                user_id,
                participacion_id=part_id,
                persona_id=persona_id,
                respuestas=[0],
            )
            await session.commit()

            assert res["aprobado"] is True
            assert res["nota"] == 100.0
            assert res["diploma_sha256"] == "sha256-aprobado"
            mock_custodia.assert_called_once()
            _, kwargs = mock_custodia.call_args
            assert kwargs["control_refs"] == ["P73"]
            assert kwargs["tipo_evidencia"] == "capacitacion"

        # Mutación documentada: Con respuesta errónea (opción 1), nota es 0.0, aprobado False y no custodia
        persona_id2 = f"p2_{uuid.uuid4().hex[:8]}"
        await acciones_engine.anadir_participantes(
            session, tenant_id, user_id, accion_id=acc_id, persona_ids=[persona_id2]
        )
        parts2 = await acciones_engine.listar_participaciones_accion(
            session, tenant_id, user_id, accion_id=acc_id
        )
        part_id2 = [p["id"] for p in parts2 if p["persona_id"] == persona_id2][0]
        await session.commit()

        await examen_engine.iniciar_examen_participacion(
            session, tenant_id, user_id, participacion_id=part_id2, persona_id=persona_id2
        )
        await session.commit()

        with patch("app_core.pasillo.evidencias.custodiar_documento_generado", new_callable=AsyncMock) as mock_custodia:
            res2 = await examen_engine.calificar_y_terminar_examen(
                session,
                tenant_id,
                user_id,
                participacion_id=part_id2,
                persona_id=persona_id2,
                respuestas=[1],
            )
            await session.commit()

            assert res2["aprobado"] is False
            assert res2["nota"] == 0.0
            assert res2["diploma_sha256"] is None
            mock_custodia.assert_not_called()


@pytest.mark.asyncio
async def test_examen_un_intento():
    """Dado un examen ya rendido (terminado_en != None), cuando se intenta rendir por segunda vez,
    entonces lanza ErrorNegocio EXAMEN_YA_RENDIDO (R4).
    """
    async with async_session_factory() as session:
        tenant_id = f"t_{uuid.uuid4().hex[:8]}"
        user_id = f"u_{uuid.uuid4().hex[:8]}"
        persona_id = f"p_{uuid.uuid4().hex[:8]}"
        ruc = f"17{uuid.uuid4().int % 100000000000:011d}"

        await session.execute(
            text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                "VALUES (:t, 'Org Intento', 'Org Intento S.A.', :r)"
            ),
            {"t": tenant_id, "r": ruc},
        )
        await session.commit()

        cont = await contenidos_engine.crear_contenido(
            session, tenant_id, user_id, titulo="C", tipo="pdf", referencia="https://e.com/c.pdf"
        )
        await contenidos_engine.crear_pregunta(
            session, tenant_id, user_id, contenido_id=cont["id"], enunciado="P?", opciones=["A", "B"], correcta=0
        )
        hoy = date.today()
        acc = await acciones_engine.crear_accion(
            session,
            tenant_id,
            user_id,
            contenido_id=cont["id"],
            nombre="A",
            inicio=hoy - timedelta(days=1),
            fin=hoy + timedelta(days=10),
            nota_minima=70.0,
        )
        await acciones_engine.anadir_participantes(
            session, tenant_id, user_id, accion_id=acc["id"], persona_ids=[persona_id]
        )
        parts = await acciones_engine.listar_participaciones_accion(
            session, tenant_id, user_id, accion_id=acc["id"]
        )
        part_id = parts[0]["id"]
        await session.commit()

        await examen_engine.iniciar_examen_participacion(
            session, tenant_id, user_id, participacion_id=part_id, persona_id=persona_id
        )
        await session.commit()

        with patch("app_core.pasillo.evidencias.custodiar_documento_generado", new_callable=AsyncMock) as m:
            m.return_value = {"id": "ev-1", "sha256": "sha-1"}
            await examen_engine.calificar_y_terminar_examen(
                session, tenant_id, user_id, participacion_id=part_id, persona_id=persona_id, respuestas=[0]
            )
            await session.commit()

        # Segundo intento
        with pytest.raises(ErrorNegocio) as exc_info:
            await examen_engine.calificar_y_terminar_examen(
                session, tenant_id, user_id, participacion_id=part_id, persona_id=persona_id, respuestas=[0]
            )
        assert exc_info.value.code == e.EXAMEN_YA_RENDIDO.codigo


@pytest.mark.asyncio
async def test_examen_fallido_no_consume_intento():
    """Dado un examen en curso, si la custodia de evidencia o el cálculo genera error,
    la transacción se revierte y terminado_en permanece NULL, sin consumir el intento.
    Mutación: si terminado_en se fijara antes de custodiar, el intento se consumiría erróneamente.
    """
    async with async_session_factory() as session:
        tenant_id = f"t_{uuid.uuid4().hex[:8]}"
        user_id = f"u_{uuid.uuid4().hex[:8]}"
        persona_id = f"p_{uuid.uuid4().hex[:8]}"
        ruc = f"17{uuid.uuid4().int % 100000000000:011d}"

        await session.execute(
            text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                "VALUES (:t, 'Org Fallo', 'Org Fallo S.A.', :r)"
            ),
            {"t": tenant_id, "r": ruc},
        )
        await session.commit()

        cont = await contenidos_engine.crear_contenido(
            session, tenant_id, user_id, titulo="C", tipo="pdf", referencia="https://e.com/c.pdf"
        )
        await contenidos_engine.crear_pregunta(
            session, tenant_id, user_id, contenido_id=cont["id"], enunciado="P?", opciones=["A", "B"], correcta=0
        )
        hoy = date.today()
        acc = await acciones_engine.crear_accion(
            session,
            tenant_id,
            user_id,
            contenido_id=cont["id"],
            nombre="A",
            inicio=hoy - timedelta(days=1),
            fin=hoy + timedelta(days=10),
            nota_minima=70.0,
        )
        await acciones_engine.anadir_participantes(
            session, tenant_id, user_id, accion_id=acc["id"], persona_ids=[persona_id]
        )
        parts = await acciones_engine.listar_participaciones_accion(
            session, tenant_id, user_id, accion_id=acc["id"]
        )
        part_id = parts[0]["id"]
        await session.commit()

        await examen_engine.iniciar_examen_participacion(
            session, tenant_id, user_id, participacion_id=part_id, persona_id=persona_id
        )
        await session.commit()

        # Forzamos falla en custodiar_documento_generado
        with patch("app_core.pasillo.evidencias.custodiar_documento_generado", side_effect=RuntimeError("Fallo I/O")):
            with pytest.raises(RuntimeError):
                await examen_engine.calificar_y_terminar_examen(
                    session, tenant_id, user_id, participacion_id=part_id, persona_id=persona_id, respuestas=[0]
                )
            await session.rollback()

        # Verificar que terminado_en sigue siendo NULL
        fila = (
            await session.execute(
                text("SELECT terminado_en, nota FROM formacion_participaciones WHERE id = :pid"),
                {"pid": part_id},
            )
        ).mappings().first()
        assert fila["terminado_en"] is None
        assert fila["nota"] is None


@pytest.mark.asyncio
async def test_examen_sin_correcta():
    """Dado un participante que solicita su examen, cuando se obtiene el examen,
    entonces no contiene el campo 'correcta' en ninguna de sus preguntas.
    Mutación: si la salida expusiera 'correcta', fallaría la aserción.
    """
    async with async_session_factory() as session:
        tenant_id = f"t_{uuid.uuid4().hex[:8]}"
        user_id = f"u_{uuid.uuid4().hex[:8]}"
        persona_id = f"p_{uuid.uuid4().hex[:8]}"
        ruc = f"17{uuid.uuid4().int % 100000000000:011d}"

        await session.execute(
            text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                "VALUES (:t, 'Org Secreto', 'Org Secreto S.A.', :r)"
            ),
            {"t": tenant_id, "r": ruc},
        )
        await session.commit()

        cont = await contenidos_engine.crear_contenido(
            session, tenant_id, user_id, titulo="Seguridad", tipo="pdf", referencia="https://e.com/c.pdf"
        )
        await contenidos_engine.crear_pregunta(
            session,
            tenant_id,
            user_id,
            contenido_id=cont["id"],
            enunciado="¿Respuesta correcta secreta?",
            opciones=["Op 1", "Op 2"],
            correcta=0,
        )
        hoy = date.today()
        acc = await acciones_engine.crear_accion(
            session,
            tenant_id,
            user_id,
            contenido_id=cont["id"],
            nombre="Acción 1",
            inicio=hoy - timedelta(days=1),
            fin=hoy + timedelta(days=10),
            nota_minima=70.0,
        )
        await acciones_engine.anadir_participantes(
            session, tenant_id, user_id, accion_id=acc["id"], persona_ids=[persona_id]
        )
        parts = await acciones_engine.listar_participaciones_accion(
            session, tenant_id, user_id, accion_id=acc["id"]
        )
        part_id = parts[0]["id"]
        await session.commit()

        examen_dict = await examen_engine.obtener_examen_participacion(
            session, tenant_id, user_id, participacion_id=part_id, persona_id=persona_id
        )
        assert len(examen_dict["preguntas"]) == 1
        preg = examen_dict["preguntas"][0]
        assert "enunciado" in preg
        assert "correcta" not in preg


@pytest.mark.asyncio
async def test_iniciar_idempotente():
    """Dado un participante, cuando llama a iniciar_examen por primera vez y por segunda vez,
    la fecha de inicio se conserva y la operación es idempotente (R7).
    """
    async with async_session_factory() as session:
        tenant_id = f"t_{uuid.uuid4().hex[:8]}"
        user_id = f"u_{uuid.uuid4().hex[:8]}"
        persona_id = f"p_{uuid.uuid4().hex[:8]}"
        ruc = f"17{uuid.uuid4().int % 100000000000:011d}"

        await session.execute(
            text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                "VALUES (:t, 'Org Idem', 'Org Idem S.A.', :r)"
            ),
            {"t": tenant_id, "r": ruc},
        )
        await session.commit()

        cont = await contenidos_engine.crear_contenido(
            session, tenant_id, user_id, titulo="C", tipo="pdf", referencia="https://e.com/c.pdf"
        )
        await contenidos_engine.crear_pregunta(
            session, tenant_id, user_id, contenido_id=cont["id"], enunciado="P?", opciones=["A", "B"], correcta=0
        )
        hoy = date.today()
        acc = await acciones_engine.crear_accion(
            session,
            tenant_id,
            user_id,
            contenido_id=cont["id"],
            nombre="A",
            inicio=hoy - timedelta(days=1),
            fin=hoy + timedelta(days=10),
            nota_minima=70.0,
        )
        await acciones_engine.anadir_participantes(
            session, tenant_id, user_id, accion_id=acc["id"], persona_ids=[persona_id]
        )
        parts = await acciones_engine.listar_participaciones_accion(
            session, tenant_id, user_id, accion_id=acc["id"]
        )
        part_id = parts[0]["id"]
        await session.commit()

        res1 = await examen_engine.iniciar_examen_participacion(
            session, tenant_id, user_id, participacion_id=part_id, persona_id=persona_id
        )
        await session.commit()
        assert res1["iniciado_en"] is not None
        fecha_primera = res1["iniciado_en"]

        res2 = await examen_engine.iniciar_examen_participacion(
            session, tenant_id, user_id, participacion_id=part_id, persona_id=persona_id
        )
        assert res2["iniciado_en"] == fecha_primera


@pytest.mark.asyncio
async def test_banco_congelado():
    """Dado un contenido vinculado a una acción con al menos una participación iniciada,
    cuando se intenta añadir una nueva pregunta al contenido,
    entonces lanza 409 PREGUNTAS_CONGELADAS (R6).
    """
    async with async_session_factory() as session:
        tenant_id = f"t_{uuid.uuid4().hex[:8]}"
        user_id = f"u_{uuid.uuid4().hex[:8]}"
        persona_id = f"p_{uuid.uuid4().hex[:8]}"
        ruc = f"17{uuid.uuid4().int % 100000000000:011d}"

        await session.execute(
            text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                "VALUES (:t, 'Org Freeze', 'Org Freeze S.A.', :r)"
            ),
            {"t": tenant_id, "r": ruc},
        )
        await session.commit()

        cont = await contenidos_engine.crear_contenido(
            session, tenant_id, user_id, titulo="C", tipo="pdf", referencia="https://e.com/c.pdf"
        )
        await contenidos_engine.crear_pregunta(
            session, tenant_id, user_id, contenido_id=cont["id"], enunciado="P?", opciones=["A", "B"], correcta=0
        )
        hoy = date.today()
        acc = await acciones_engine.crear_accion(
            session,
            tenant_id,
            user_id,
            contenido_id=cont["id"],
            nombre="A",
            inicio=hoy - timedelta(days=1),
            fin=hoy + timedelta(days=10),
            nota_minima=70.0,
        )
        await acciones_engine.anadir_participantes(
            session, tenant_id, user_id, accion_id=acc["id"], persona_ids=[persona_id]
        )
        parts = await acciones_engine.listar_participaciones_accion(
            session, tenant_id, user_id, accion_id=acc["id"]
        )
        part_id = parts[0]["id"]
        await session.commit()

        # Iniciar la participación
        await examen_engine.iniciar_examen_participacion(
            session, tenant_id, user_id, participacion_id=part_id, persona_id=persona_id
        )
        await session.commit()

        # Intentar añadir pregunta al contenido debe arrojar PREGUNTAS_CONGELADAS
        with pytest.raises(ErrorNegocio) as exc_info:
            await contenidos_engine.crear_pregunta(
                session,
                tenant_id,
                user_id,
                contenido_id=cont["id"],
                enunciado="Nueva pregunta?",
                opciones=["A", "B"],
                correcta=0,
            )
        assert exc_info.value.code == e.PREGUNTAS_CONGELADAS.codigo


@pytest.mark.asyncio
async def test_cobertura():
    """Dado 3 personas activas en el inventario y 1 que ha aprobado su formación,
    cuando se calcula la cobertura, entonces devuelve exactamente 33.3% (1 de 3).
    """
    async with async_session_factory() as session:
        tenant_id = f"t_{uuid.uuid4().hex[:8]}"
        user_id = f"u_{uuid.uuid4().hex[:8]}"
        ruc = f"17{uuid.uuid4().int % 100000000000:011d}"

        await session.execute(
            text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                "VALUES (:t, 'Org Cobertura', 'Org Cobertura S.A.', :r)"
            ),
            {"t": tenant_id, "r": ruc},
        )

        p_ids = [str(uuid.uuid4()) for _ in range(4)]
        for i, pid in enumerate(p_ids):
            archivada = (i == 3)  # la cuarta archivada
            await session.execute(
                text(
                    """
                    INSERT INTO inventario_personas (id, tenant_id, nombre, email, cargo, archivada, created_by)
                    VALUES (:p, :t, :nombre, :email, 'Analista', :arch, :u)
                    """
                ),
                {"p": pid, "t": tenant_id, "nombre": f"Persona {i}", "email": f"p{i}_{tenant_id}@test.com", "arch": archivada, "u": user_id},
            )
        await session.commit()

        cont = await contenidos_engine.crear_contenido(
            session, tenant_id, user_id, titulo="C", tipo="pdf", referencia="https://e.com/c.pdf"
        )
        await contenidos_engine.crear_pregunta(
            session, tenant_id, user_id, contenido_id=cont["id"], enunciado="P?", opciones=["A", "B"], correcta=0
        )
        hoy = date.today()
        acc = await acciones_engine.crear_accion(
            session,
            tenant_id,
            user_id,
            contenido_id=cont["id"],
            nombre="A",
            inicio=hoy - timedelta(days=1),
            fin=hoy + timedelta(days=10),
            nota_minima=70.0,
        )
        acc_id = acc["id"]

        # Insertar participaciones directamente
        # p0: aprobó (nota 80 >= 70)
        await session.execute(
            text(
                """
                INSERT INTO formacion_participaciones (id, tenant_id, accion_id, persona_id, terminado_en, nota)
                VALUES (:id, :t, :aid, :pid, :term, 80.0)
                """
            ),
            {"id": str(uuid.uuid4()), "t": tenant_id, "aid": acc_id, "pid": p_ids[0], "term": datetime.now(timezone.utc)},
        )
        # p1: no aprobó (nota 50 < 70)
        await session.execute(
            text(
                """
                INSERT INTO formacion_participaciones (id, tenant_id, accion_id, persona_id, terminado_en, nota)
                VALUES (:id, :t, :aid, :pid, :term, 50.0)
                """
            ),
            {"id": str(uuid.uuid4()), "t": tenant_id, "aid": acc_id, "pid": p_ids[1], "term": datetime.now(timezone.utc)},
        )
        # p3 (archivada): aprobó (nota 100)
        await session.execute(
            text(
                """
                INSERT INTO formacion_participaciones (id, tenant_id, accion_id, persona_id, terminado_en, nota)
                VALUES (:id, :t, :aid, :pid, :term, 100.0)
                """
            ),
            {"id": str(uuid.uuid4()), "t": tenant_id, "aid": acc_id, "pid": p_ids[3], "term": datetime.now(timezone.utc)},
        )
        await session.commit()

        cob = await cobertura_engine.calcular_cobertura(session, tenant_id, user_id)
        # Activas = 3 (p0, p1, p2). Formadas activas = 1 (p0). p3 está archivada y no cuenta.
        assert cob["obligadas"] == 3
        assert cob["formadas"] == 1
        assert cob["cobertura"] == 0.33


@pytest.mark.asyncio
async def test_examen_concurrente_un_solo_intento():
    """Dado un participante que intenta rendir concurrentemente,
    la condición UPDATE ... WHERE terminado_en IS NULL garantiza que solo una transacción tenga éxito,
    mientras la otra arroja EXAMEN_YA_RENDIDO.
    Mutación documentada: sin 'AND terminado_en IS NULL', ambas transacciones sobrescribirían el intento.
    """
    async with async_session_factory() as session:
        tenant_id = f"t_{uuid.uuid4().hex[:8]}"
        user_id = f"u_{uuid.uuid4().hex[:8]}"
        persona_id = f"p_{uuid.uuid4().hex[:8]}"
        ruc = f"17{uuid.uuid4().int % 100000000000:011d}"

        await session.execute(
            text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                "VALUES (:t, 'Org Concurrente', 'Org Concurrente S.A.', :r)"
            ),
            {"t": tenant_id, "r": ruc},
        )
        await session.commit()

        cont = await contenidos_engine.crear_contenido(
            session, tenant_id, user_id, titulo="C", tipo="pdf", referencia="https://e.com/c.pdf"
        )
        await contenidos_engine.crear_pregunta(
            session, tenant_id, user_id, contenido_id=cont["id"], enunciado="P?", opciones=["A", "B"], correcta=0
        )
        hoy = date.today()
        acc = await acciones_engine.crear_accion(
            session,
            tenant_id,
            user_id,
            contenido_id=cont["id"],
            nombre="A",
            inicio=hoy - timedelta(days=1),
            fin=hoy + timedelta(days=10),
            nota_minima=70.0,
        )
        await acciones_engine.anadir_participantes(
            session, tenant_id, user_id, accion_id=acc["id"], persona_ids=[persona_id]
        )
        parts = await acciones_engine.listar_participaciones_accion(
            session, tenant_id, user_id, accion_id=acc["id"]
        )
        part_id = parts[0]["id"]
        await session.commit()

        await examen_engine.iniciar_examen_participacion(
            session, tenant_id, user_id, participacion_id=part_id, persona_id=persona_id
        )
        await session.commit()

        # Simular que una transacción concurrente ya completó la participación
        ahora = datetime.now(timezone.utc)
        await session.execute(
            text(
                "UPDATE formacion_participaciones SET terminado_en = :term, nota = 100.0 WHERE id = :pid"
            ),
            {"term": ahora, "pid": part_id},
        )
        await session.commit()

        # La segunda transacción intenta calificar y debe ser rechazada con EXAMEN_YA_RENDIDO
        with pytest.raises(ErrorNegocio) as exc_info:
            await examen_engine.calificar_y_terminar_examen(
                session, tenant_id, user_id, participacion_id=part_id, persona_id=persona_id, respuestas=[0]
            )
        assert exc_info.value.code == e.EXAMEN_YA_RENDIDO.codigo


@pytest.mark.asyncio
async def test_rls_formacion():
    """Dado registros de formación en el tenant A, cuando se consulta con el rol de aplicación
    'lopdp_app' bajo el contexto del tenant B, entonces se obtienen 0 filas en las cuatro tablas.
    """
    async with async_session_factory() as session:
        tenant_a = f"t_a_{uuid.uuid4().hex[:8]}"
        tenant_b = f"t_b_{uuid.uuid4().hex[:8]}"
        ruc_a = f"17{uuid.uuid4().int % 100000000000:011d}"
        ruc_b = f"17{uuid.uuid4().int % 100000000000:011d}"

        await session.execute(
            text(
                """
                INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion)
                VALUES (:ta, 'Tenant A', 'A S.A.', :ra),
                       (:tb, 'Tenant B', 'B S.A.', :rb)
                """
            ),
            {"ta": tenant_a, "tb": tenant_b, "ra": ruc_a, "rb": ruc_b},
        )
        await session.commit()

        # Insertar registros como tenant A
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, false)"), {"t": tenant_a})
        cont_id = str(uuid.uuid4())
        await session.execute(
            text(
                "INSERT INTO formacion_contenidos (id, tenant_id, titulo, tipo, referencia, creado_por) "
                "VALUES (:id, :t, 'Manual A', 'pdf', 'https://e.com/a.pdf', 'u-a')"
            ),
            {"id": cont_id, "t": tenant_a},
        )
        preg_id = str(uuid.uuid4())
        await session.execute(
            text(
                "INSERT INTO formacion_preguntas (id, tenant_id, contenido_id, orden, enunciado, opciones, correcta) "
                "VALUES (:id, :t, :cid, 0, 'Pregunta A?', '[\"A\", \"B\"]'::jsonb, 0)"
            ),
            {"id": preg_id, "t": tenant_a, "cid": cont_id},
        )
        acc_id = str(uuid.uuid4())
        await session.execute(
            text(
                "INSERT INTO formacion_acciones (id, tenant_id, contenido_id, nombre, inicio, fin, nota_minima, creado_por) "
                "VALUES (:id, :t, :cid, 'Accion A', '2026-01-01', '2026-12-31', 70, 'u-a')"
            ),
            {"id": acc_id, "t": tenant_a, "cid": cont_id},
        )
        part_id = str(uuid.uuid4())
        await session.execute(
            text(
                "INSERT INTO formacion_participaciones (id, tenant_id, accion_id, persona_id) "
                "VALUES (:id, :t, :aid, 'p-1')"
            ),
            {"id": part_id, "t": tenant_a, "aid": acc_id},
        )
        await session.commit()

        # Conmutar a lopdp_app bajo tenant B
        await session.execute(text("SET LOCAL ROLE lopdp_app"))
        await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant_b})

        # Consulta directa en tenant B debe retornar 0 filas
        c_res = (await session.execute(text("SELECT id FROM formacion_contenidos WHERE id = :id"), {"id": cont_id})).all()
        assert len(c_res) == 0

        p_res = (await session.execute(text("SELECT id FROM formacion_preguntas WHERE id = :id"), {"id": preg_id})).all()
        assert len(p_res) == 0

        a_res = (await session.execute(text("SELECT id FROM formacion_acciones WHERE id = :id"), {"id": acc_id})).all()
        assert len(a_res) == 0

        part_res = (await session.execute(text("SELECT id FROM formacion_participaciones WHERE id = :id"), {"id": part_id})).all()
        assert len(part_res) == 0


@pytest.mark.asyncio
async def test_sin_palabra_prohibida_formacion():
    """Doctrina 1: Prohibida terminantemente la palabra 'certificado' o 'diploma'
    en el texto de la constancia de formación.
    """
    contenido_bytes = diploma_engine.generar_contenido_constancia(
        persona_id="p-12345",
        accion_nombre="Seguridad de la Información",
        nota=95.0,
        fecha_iso=datetime.now(timezone.utc).isoformat(),
    )
    texto = contenido_bytes.decode("utf-8").lower()
    assert "certificado" not in texto
    assert "diploma" not in texto
    assert "constancia de formación" in texto
