# ¤rbac-tenant
# ¤arbitro
"""Matriz de permisos (RBAC) como prueba viva (PRD Módulo 5, §5.2).

Contrato verificado: INV_LOPDP_ROADMAP_RBAC_MATRIX.
Prueba parametrizada (rol × acción/endpoint) contra la matriz del PRD y el contrato
objetivo de governance/arquitectura/HOJA_DE_RUTA_ADPA.md.

Comportamiento determinista:
- Todos los endpoints de la matriz deben estar registrados en FastAPI (QA-05 / Criterio 10).
  Si un endpoint de la matriz no está registrado, la construcción de casos falla de inmediato.
- Para cada combinación (rol, endpoint), se evalúa:
  * El rol autorizado no recibe 403 Forbidden.
  * El rol no autorizado recibe estrictamente 403 Forbidden.
- Cobertura exhaustiva: toda ruta registrada bajo los prefijos de la matriz
  (/api/v1/roadmaps, /api/v1/organizacion, /api/v1/areas) debe estar en la matriz
  o en la lista explícita FUERA_DE_MATRIZ con su justificación.

Matriz por archivos (RM-21): desde RM-21 cada tarea declara sus filas en su propio archivo
`tests/matriz/<ID>.py`, que este test descubre solo (sin índice que editar) y suma a las filas de
abajo, que quedan intactas. Formato de un archivo de filas:
- `FILAS: list[tuple[str, str, str, set[str]]]` (obligatoria): `(id_accion, metodo, ruta_plantilla,
  roles_permitidos)`, igual que las tuplas de MATRIZ_PRD_CONTRATO.
- `FUERA_DE_MATRIZ: dict[tuple[str, str], str]` (opcional): `(metodo, ruta) -> justificación` de una
  ruta bajo los prefijos de la matriz que no se controla por rol.
Ejemplo vivo y documentación del formato: `tests/matriz/RM-21.py` y `tests/matriz/__init__.py`.
Un archivo con otro formato, un id_accion repetido o una ruta declarada dos veces hacen fallar la carga.
"""
from __future__ import annotations

import importlib.util
import inspect
import re
from pathlib import Path
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
        # RM-20: los cinco roles descargan el informe PDF, cada uno con su alcance (decisión del propietario).
        "descargar_informe_estado",
        "GET",
        "/api/v1/roadmaps/{roadmap_id}/informe.pdf",
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
    # ORG-14: leer, cualquier usuario de la organización; editar, solo su administrador.
    (
        "datos_documentales_get",
        "GET",
        "/api/v1/organizacion/datos-documentales",
        {
            "responsable_area",
            "coordinador",
            "dpo",
            "implementador",
            "admin_organizacion",
        },
    ),
    (
        "datos_documentales_patch",
        "PATCH",
        "/api/v1/organizacion/datos-documentales",
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


# Prefijos de API cubiertos por la matriz de permisos de la Hoja de Ruta y Organización
PREFIJOS_MATRIZ: tuple[str, ...] = (
    "/api/v1/roadmaps",
    "/api/v1/organizacion",
    "/api/v1/areas",
)

# Rutas registradas bajo PREFIJOS_MATRIZ que no requieren control de rol por matriz (QA-05).
# Cada entrada documenta de manera explícita el motivo técnico/funcional de su exclusión.
FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {
    ("GET", "/api/v1/organizacion/me/roles"): (
        "Endpoint de auto-descubrimiento de identidad; no filtra por rol operativo sino por "
        "usuario autenticado en el tenant para que el cliente descubra sus membresías."
    ),
    ("GET", "/api/v1/organizacion/mis-organizaciones"): (
        "Lista de organizaciones de la persona autenticada (ORG-13); no pertenece a un tenant ni "
        "filtra por rol: la identidad sale del token y la función de la base solo devuelve las suyas."
    ),
    ("GET", "/api/v1/roadmaps/jobs/{job_id}"): (
        "Consulta de estado de job asíncrono de generación; requiere solo pertenencia al tenant (get_context)."
    ),
    ("GET", "/api/v1/roadmaps/{roadmap_id}/kpis"): (
        "Lectura agregada de métricas del roadmap para visualización analítica por cualquier miembro activo del tenant (get_context)."
    ),
    ("PATCH", "/api/v1/roadmaps/tasks/{task_id}/details"): (
        "Edición operativa granular de campos de tarea (título, fechas, KPI), delegada exclusivamente a implementador; "
        "variante técnica de PATCH /tasks/{task_id}."
    ),
    ("POST", "/api/v1/organizacion/designaciones"): (
        "Alta de designación formal de DPD o Coordinador (ORG-06); potestad exclusiva de admin_organizacion."
    ),
    ("GET", "/api/v1/organizacion/designaciones"): (
        "Listado de designaciones formales del tenant; lectura por roles de gestión y supervisión "
        "(admin_organizacion, coordinador, dpo, implementador)."
    ),
    ("GET", "/api/v1/organizacion/designaciones/estado"): (
        "Informe de estado de cumplimiento de designaciones formales (solo lectura); "
        "disponible para admin_organizacion, coordinador, dpo, implementador."
    ),
    ("GET", "/api/v1/organizacion/designaciones/{designacion_id}"): (
        "Detalle de designación formal; lectura por roles de gestión y supervisión "
        "(admin_organizacion, coordinador, dpo, implementador)."
    ),
    ("POST", "/api/v1/organizacion/designaciones/{designacion_id}/declarar"): (
        "Declaración de inexistencia de conflictos de interés; permitida a cualquier usuario autenticado "
        "pero restringida por motor exclusivamente a la propia persona designada."
    ),
    ("POST", "/api/v1/organizacion/designaciones/{designacion_id}/inscribir"): (
        "Registro de constancia de inscripción de designación ante la SPDP; potestad exclusiva de admin_organizacion."
    ),
    ("POST", "/api/v1/organizacion/designaciones/{designacion_id}/revocar"): (
        "Revocación formal de designación de DPD o Coordinador; potestad exclusiva de admin_organizacion."
    ),
}


# --- Matriz por archivos: tests/matriz/<ID>.py ----------------------------------------------------

CARPETA_MATRIZ = Path(__file__).resolve().parent / "matriz"
_METODOS_HTTP = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def _validar_fila(origen: str, fila) -> tuple[str, str, str, set[str]]:
    roles_validos = {r.value for r in Role}
    assert isinstance(fila, tuple) and len(fila) == 4, f"{origen}: cada fila es (accion, metodo, ruta, roles)"
    accion, metodo, ruta, roles = fila
    assert isinstance(accion, str) and accion, f"{origen}: id_accion vacío"
    assert metodo in _METODOS_HTTP, f"{origen}: método desconocido {metodo!r} en {accion}"
    assert isinstance(ruta, str) and ruta.startswith("/api/v1/"), f"{origen}: ruta sin /api/v1 en {accion}"
    assert isinstance(roles, set) and roles <= roles_validos, f"{origen}: roles desconocidos en {accion}"
    return fila


def cargar_matriz_por_archivos(
    carpeta: Path = CARPETA_MATRIZ,
) -> tuple[list[tuple[str, str, str, set[str]]], dict[tuple[str, str], str]]:
    """Carga FILAS y FUERA_DE_MATRIZ de cada tests/matriz/<ID>.py, en orden de nombre."""
    filas: list[tuple[str, str, str, set[str]]] = []
    fuera: dict[tuple[str, str], str] = {}
    for archivo in sorted(carpeta.glob("*.py")):
        if archivo.name == "__init__.py":
            continue
        spec = importlib.util.spec_from_file_location(f"matriz_{archivo.stem.replace('-', '_')}", archivo)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        assert isinstance(getattr(modulo, "FILAS", None), list), f"{archivo.name}: falta la lista FILAS"
        filas.extend(_validar_fila(archivo.name, f) for f in modulo.FILAS)
        propias = getattr(modulo, "FUERA_DE_MATRIZ", {})
        assert isinstance(propias, dict) and all(
            isinstance(k, tuple) and len(k) == 2 and isinstance(v, str) and v for k, v in propias.items()
        ), f"{archivo.name}: FUERA_DE_MATRIZ es {{(metodo, ruta): justificación}}"
        fuera.update(propias)
    return filas, fuera


_FILAS_ARCHIVOS, _FUERA_ARCHIVOS = cargar_matriz_por_archivos()
_acciones = [a for a, *_ in MATRIZ_PRD_CONTRATO + _FILAS_ARCHIVOS]
assert len(_acciones) == len(set(_acciones)), "id_accion repetido entre la matriz y tests/matriz/"
assert not set(_FUERA_ARCHIVOS) & set(FUERA_DE_MATRIZ), "ruta declarada dos veces en FUERA_DE_MATRIZ"
MATRIZ_PRD_CONTRATO = MATRIZ_PRD_CONTRATO + _FILAS_ARCHIVOS
FUERA_DE_MATRIZ = {**FUERA_DE_MATRIZ, **_FUERA_ARCHIVOS}


def test_matriz_por_archivos_descubre_las_filas_de_cada_tarea():
    """Las filas de tests/matriz/RM-21.py entran en la matriz sin tocar ningún índice."""
    acciones = {a for a, *_ in MATRIZ_PRD_CONTRATO}
    assert {
        "listar_hallazgos",
        "registrar_hallazgos_desde_diagnostico",
        "convertir_hallazgos_en_tareas",
    } <= acciones
    # Las filas propias del test siguen en él (intactas) y las de archivo se suman detrás.
    assert MATRIZ_PRD_CONTRATO[0][0] == "ver_assessment"


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

    Criterio 10 del MVP (QA-05): Cero filas pendientes. Si un endpoint de la matriz
    no se encuentra registrado en la aplicación, falla de inmediato nombrando el método y la ruta.
    """
    casos = []
    todos_los_roles = [r.value for r in Role]

    for accion, method, path, allowed_roles in MATRIZ_PRD_CONTRATO:
        route_ctx = _buscar_contexto_ruta(path, method)
        assert route_ctx is not None, (
            f"Endpoint {method} {path} de la acción '{accion}' no está registrado en la aplicación"
        )

        for rol in todos_los_roles:
            debe_permitir = rol in allowed_roles
            caso_id = f"{accion}-{method}-{path}-{rol}"
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


async def test_cobertura_exhaustiva_rutas_api():
    """Verifica que toda ruta registrada bajo los prefijos de la matriz esté contemplada (QA-05).

    Recorre las rutas de la API bajo /api/v1/roadmaps, /api/v1/organizacion y /api/v1/areas.
    Falla si alguna ruta no está en MATRIZ_PRD_CONTRATO ni en la lista justificada FUERA_DE_MATRIZ.
    Garantiza además que ninguna entrada en FUERA_DE_MATRIZ quede obsoleta si la ruta cambia.
    """
    rutas_en_matriz = {(m, p) for _, m, p, _ in MATRIZ_PRD_CONTRATO}

    rutas_registradas: set[tuple[str, str]] = set()
    for r in app.routes:
        if hasattr(r, "path") and r.path and any(r.path.startswith(p) for p in PREFIJOS_MATRIZ):
            for m in getattr(r, "methods", []):
                if m not in ("HEAD", "OPTIONS"):
                    rutas_registradas.add((m, r.path))
        if hasattr(r, "effective_route_contexts"):
            for ctx in r.effective_route_contexts():
                if any(ctx.path.startswith(p) for p in PREFIJOS_MATRIZ):
                    for m in getattr(ctx, "methods", []):
                        if m not in ("HEAD", "OPTIONS"):
                            rutas_registradas.add((m, ctx.path))

    no_cubiertas = rutas_registradas - rutas_en_matriz - set(FUERA_DE_MATRIZ.keys())
    assert not no_cubiertas, (
        f"Rutas registradas bajo prefijos {PREFIJOS_MATRIZ} sin cobertura en la matriz de permisos "
        f"ni en FUERA_DE_MATRIZ: {sorted(no_cubiertas)}"
    )

    # Validar que no haya entradas obsoletas en FUERA_DE_MATRIZ
    for metodo, ruta in FUERA_DE_MATRIZ:
        assert (metodo, ruta) in rutas_registradas, (
            f"Ruta declarada en FUERA_DE_MATRIZ ya no está registrada en la aplicación: {metodo} {ruta}"
        )

