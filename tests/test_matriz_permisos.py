# ¤rbac-tenant
# ¤arbitro
"""Matriz de permisos (RBAC) como prueba viva (PRD Módulo 5, §5.2).

Contrato verificado: INV_LOPDP_ROADMAP_RBAC_MATRIX.
Prueba parametrizada (rol × acción/endpoint) contra la matriz del PRD y el contrato
objetivo de governance/arquitectura/HOJA_DE_RUTA_ADPA.md.

Comportamiento determinista:
- Si el endpoint está registrado en FastAPI, se evalúa contra la matriz del PRD:
  * El rol autorizado no recibe 403 Forbidden.
  * El rol no autorizado recibe estrictamente 403 Forbidden.
- Si el endpoint aún no está registrado en la aplicación, la fila se marca
  dinámicamente como xfail(strict=False, reason="Endpoint aún no registrado en la aplicación").
  Cuando la tarea correspondiente lo registre, la fila se evaluará automáticamente
  sin requerir modificaciones en este archivo de prueba.
"""
from __future__ import annotations

import inspect
import re
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app_core.db.session import get_session
from features.organizacion import organizacion_service
from features.organizacion.organizacion_service import Role
from main import app

pytestmark = pytest.mark.asyncio

# Definición normativa de la matriz de permisos: PRD §5.2 y HOJA_DE_RUTA_ADPA §5.
# Tupla: (id_accion, metodo, ruta_plantilla, conjunto_roles_permitidos)
MATRIZ_PRD_CONTRATO: list[tuple[str, str, str, set[str]]] = [
    (
        "ver_assessment",
        "GET",
        "/api/v1/diagnostico/{id}/exportar",
        {
            "responsable_area",
            "coordinador",
            "dpo",
            "implementador",
            "admin_organizacion",
        },
    ),
    (
        "ver_hoja_de_ruta",
        "GET",
        "/api/v1/roadmaps/{roadmap_id}",
        {
            "responsable_area",
            "coordinador",
            "dpo",
            "implementador",
            "admin_organizacion",
        },
    ),
    (
        "generar_roadmap_ia",
        "POST",
        "/api/v1/roadmaps/generate",
        {"implementador"},
    ),
    (
        "editar_tareas_campos",
        "PATCH",
        "/api/v1/roadmaps/tasks/{task_id}",
        {"implementador"},
    ),
    (
        "marcar_tarea_completada",
        "PATCH",
        "/api/v1/roadmaps/tasks/{task_id}",
        {"implementador"},
    ),
    (
        "distribuir_tareas",
        "POST",
        "/api/v1/roadmaps/tasks/{task_id}/assign",
        {"coordinador"},
    ),
    (
        "subir_evidencia_url",
        "POST",
        "/api/v1/roadmaps/tasks/{task_id}/evidence/upload-url",
        {"responsable_area", "coordinador"},
    ),
    (
        "subir_evidencia_reg",
        "POST",
        "/api/v1/roadmaps/tasks/{task_id}/evidence",
        {"responsable_area", "coordinador"},
    ),
    (
        "validar_rechazar_evidencia",
        "PATCH",
        "/api/v1/roadmaps/tasks/{task_id}/evidence/{evidence_id}",
        {"coordinador", "dpo", "implementador"},
    ),
    (
        "ver_evidencia",
        "GET",
        "/api/v1/roadmaps/tasks/{task_id}/evidence",
        {
            "responsable_area",
            "coordinador",
            "dpo",
            "implementador",
            "admin_organizacion",
        },
    ),
    (
        "ver_audit_log",
        "GET",
        "/api/v1/roadmaps/{roadmap_id}/audit-log",
        {"coordinador", "dpo", "implementador", "admin_organizacion"},
    ),
    (
        "gestionar_usuarios_get",
        "GET",
        "/api/v1/organizacion/usuarios",
        {"admin_organizacion"},
    ),
    (
        "gestionar_usuarios_post",
        "POST",
        "/api/v1/organizacion/usuarios",
        {"admin_organizacion"},
    ),
    (
        "crear_areas",
        "POST",
        "/api/v1/organizacion/areas",
        {"admin_organizacion"},
    ),
    (
        "editar_areas",
        "PATCH",
        "/api/v1/organizacion/areas/{area_id}",
        {"admin_organizacion"},
    ),
    (
        "listar_areas",
        "GET",
        "/api/v1/organizacion/areas",
        {"admin_organizacion"},
    ),
    (
        "asignar_roles",
        "POST",
        "/api/v1/organizacion/roles",
        {"admin_organizacion"},
    ),
    (
        "listar_roles",
        "GET",
        "/api/v1/organizacion/roles",
        {"admin_organizacion"},
    ),
    (
        "revocar_roles",
        "DELETE",
        "/api/v1/organizacion/roles/{assignment_id}",
        {"admin_organizacion"},
    ),
    (
        "configurar_organizacion_get",
        "GET",
        "/api/v1/organizacion/configuracion",
        {
            "responsable_area",
            "coordinador",
            "dpo",
            "implementador",
            "admin_organizacion",
        },
    ),
    (
        "configurar_organizacion_patch",
        "PATCH",
        "/api/v1/organizacion/configuracion",
        {"admin_organizacion"},
    ),
    (
        "solicitar_alta_responsable",
        "POST",
        "/api/v1/areas/responsable-requests",
        {"coordinador"},
    ),
    (
        "listar_altas_responsable",
        "GET",
        "/api/v1/areas/responsable-requests",
        {"coordinador", "implementador"},
    ),
    (
        "ver_alta_responsable",
        "GET",
        "/api/v1/areas/responsable-requests/{id}",
        {"coordinador", "implementador"},
    ),
    (
        "cancelar_alta_responsable",
        "PATCH",
        "/api/v1/areas/responsable-requests/{id}",
        {"coordinador"},
    ),
    (
        "aprobar_alta_responsable",
        "POST",
        "/api/v1/areas/responsable-requests/{id}/approve",
        {"implementador"},
    ),
    (
        "rechazar_alta_responsable",
        "POST",
        "/api/v1/areas/responsable-requests/{id}/reject",
        {"implementador"},
    ),
    (
        "ejecutar_alta_responsable",
        "POST",
        "/api/v1/areas/responsable-requests/{id}/execute",
        {"implementador"},
    ),
    (
        "ver_arbol_estructura_organica",
        "GET",
        "/api/v1/organizacion/estructura/arbol",
        {"coordinador", "implementador", "dpo", "admin_organizacion"},
    ),
    (
        "ver_cobertura_estructura_organica",
        "GET",
        "/api/v1/organizacion/estructura/cobertura",
        {"coordinador", "implementador", "dpo", "admin_organizacion"},
    ),
    (
        "crear_area_estructura_organica",
        "POST",
        "/api/v1/organizacion/estructura/areas",
        {"admin_organizacion"},
    ),
    (
        "editar_area_estructura_organica",
        "PATCH",
        "/api/v1/organizacion/estructura/areas/{area_id}",
        {"admin_organizacion"},
    ),
    (
        "crear_cargo_organico",
        "POST",
        "/api/v1/organizacion/estructura/cargos",
        {"admin_organizacion"},
    ),
    (
        "editar_cargo_organico",
        "PATCH",
        "/api/v1/organizacion/estructura/cargos/{cargo_id}",
        {"admin_organizacion"},
    ),
    (
        "asignar_titular_cargo_organico",
        "POST",
        "/api/v1/organizacion/estructura/cargos/{cargo_id}/titular",
        {"admin_organizacion"},
    ),
    (
        "solicitar_excepcion_sod",
        "POST",
        "/api/v1/organizacion/excepciones-sod",
        {"coordinador", "admin_organizacion"},
    ),
    (
        "listar_excepciones_sod",
        "GET",
        "/api/v1/organizacion/excepciones-sod",
        {"coordinador", "implementador", "dpo", "admin_organizacion"},
    ),
    (
        "ver_excepcion_sod",
        "GET",
        "/api/v1/organizacion/excepciones-sod/{id}",
        {"coordinador", "implementador", "dpo", "admin_organizacion"},
    ),
    (
        "aprobar_excepcion_sod",
        "POST",
        "/api/v1/organizacion/excepciones-sod/{id}/approve",
        {"admin_organizacion"},
    ),
    (
        "revocar_excepcion_sod",
        "POST",
        "/api/v1/organizacion/excepciones-sod/{id}/revoke",
        {"admin_organizacion"},
    ),
    (
        "observacion_dpo_excepcion_sod",
        "POST",
        "/api/v1/organizacion/excepciones-sod/{id}/observaciones-dpo",
        {"dpo"},
    ),
]


def _buscar_contexto_ruta(path: str, method: str):
    """Busca en la aplicación FastAPI si la ruta y método especificados están registrados."""
    for r in app.routes:
        if hasattr(r, "path") and r.path == path and method in getattr(r, "methods", []):
            return r
        if hasattr(r, "effective_route_contexts"):
            for ctx in r.effective_route_contexts():
                if ctx.path == path and method in getattr(ctx, "methods", []):
                    return ctx
    return None


def _construir_casos_prueba():
    """Genera las combinaciones parametrizadas (rol × acción/endpoint).

    Aplica xfail dinámico si el endpoint no se encuentra registrado aún.
    """
    casos = []
    todos_los_roles = [r.value for r in Role]

    for accion, method, path, allowed_roles in MATRIZ_PRD_CONTRATO:
        route_ctx = _buscar_contexto_ruta(path, method)
        registrado = route_ctx is not None

        for rol in todos_los_roles:
            debe_permitir = rol in allowed_roles
            caso_id = f"{accion}-{method}-{path}-{rol}"

            if not registrado:
                casos.append(
                    pytest.param(
                        accion,
                        method,
                        path,
                        rol,
                        debe_permitir,
                        marks=pytest.mark.xfail(
                            reason=f"Endpoint {method} {path} no registrado aún en la aplicación",
                            strict=False,
                        ),
                        id=caso_id,
                    )
                )
            else:
                casos.append(
                    pytest.param(
                        accion,
                        method,
                        path,
                        rol,
                        debe_permitir,
                        id=caso_id,
                    )
                )
    return casos


CASOS_MATRIZ = _construir_casos_prueba()


def _concretar_ruta(path: str) -> str:
    """Sustituye variables de ruta {param} por identificadores ficticios para la petición HTTP."""
    return re.sub(r"\{[^}]+\}", "dummy-resource-id", path)


def _extraer_roles_permitidos_estatico(route_ctx) -> set[str] | None:
    """Inspecciona el AST/dependencias de FastAPI para extraer los roles permitidos por require_role."""
    if not route_ctx:
        return None

    from api.rbac import get_context

    def _inspeccionar_dependant(dep):
        if dep.call is get_context:
            return "ALL"
        if dep.call is not None:
            closure = inspect.getclosurevars(dep.call)
            if "roles" in closure.nonlocals:
                return set(closure.nonlocals["roles"])
        for hijo in dep.dependencies:
            res = _inspeccionar_dependant(hijo)
            if res is not None:
                return res
        return None

    res = _inspeccionar_dependant(route_ctx.dependant)
    if res == "ALL" or res is None:
        return {r.value for r in Role}
    return res


@pytest.mark.parametrize(
    "accion,method,path,rol,debe_permitir",
    CASOS_MATRIZ,
)
async def test_matriz_permisos_rol_accion(
    accion: str,
    method: str,
    path: str,
    rol: str,
    debe_permitir: bool,
    monkeypatch: pytest.MonkeyPatch,
):
    """Verifica que cada combinación (rol, endpoint) cumpla la matriz del PRD §5.2.

    Si debe permitir: el endpoint no responde con 403 Forbidden.
    Si no debe permitir: el endpoint responde estrictamente con 403 Forbidden.
    """
    route_ctx = _buscar_contexto_ruta(path, method)
    assert route_ctx is not None, f"Endpoint {method} {path} no encontrado"

    # Verificación estática directa de la dependencia del endpoint contra el contrato
    roles_estaticos = _extraer_roles_permitidos_estatico(route_ctx)
    if roles_estaticos is not None:
        if debe_permitir:
            assert rol in roles_estaticos, (
                f"Contrato estático violado en {method} {path}: "
                f"rol '{rol}' no está en roles permitidos {roles_estaticos}"
            )
        else:
            assert rol not in roles_estaticos, (
                f"Contrato estático violado en {method} {path}: "
                f"rol '{rol}' está indebidamente en roles permitidos {roles_estaticos}"
            )

    # Interceptar la ejecución final del endpoint para aislar la verificación de autorización RBAC
    # respetando si la función del endpoint original es síncrona o asíncrona.
    if inspect.iscoroutinefunction(route_ctx.dependant.call):
        mock_handler = AsyncMock(return_value={"ok": True})
    else:
        mock_handler = MagicMock(return_value={"ok": True})

    monkeypatch.setattr(
        route_ctx.dependant,
        "call",
        mock_handler,
    )

    # Verificación dinámica vía cliente ASGI simulando membresía activa
    monkeypatch.setattr(
        organizacion_service,
        "has_active_role",
        AsyncMock(return_value=True),
    )
    app.dependency_overrides[get_session] = lambda: None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ruta_real = _concretar_ruta(path)
        cabeceras = {
            "X-User-ID": "usuario-test-matriz",
            "X-Tenant-ID": "tenant-test-matriz",
            "X-Role": rol,
        }
        respuesta = await client.request(method, ruta_real, headers=cabeceras)

        if debe_permitir:
            assert respuesta.status_code != 403, (
                f"Acceso denegado indebidamente (403): {method} {path} para rol '{rol}'. "
                f"Detalle: {respuesta.text}"
            )
        else:
            assert respuesta.status_code == 403, (
                f"Acceso permitido indebidamente: {method} {path} para rol '{rol}' "
                f"debió responder 403 pero respondió {respuesta.status_code}"
            )
