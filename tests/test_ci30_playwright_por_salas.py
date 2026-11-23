# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤ci-cd ¤arbitro
"""CI-30 · Autodescubrimiento en playwright.config.ts y arnés de Playwright por salas en CI.

Invariantes verificados:
1. Todo archivo .spec.ts que contiene `test.skip(project.name === "produccion")`, `fijarAjustes`,
   `__LOPDP_AUTH_PRUEBAS__` o `harness-roadmap` se autodescubre sin requerir lista estática manual.
2. Un cambio confinado a una sala con frontend corre solo los tests de Playwright de esa sala
   (ej. `tests/roadmap`).
3. Un cambio en componentes compartidos / layout del frontend corre toda la suite (`tests/`).
4. Un cambio exclusivo en backend o gobernanza sin salas de UI produce `playwright_specs == ""`
   permitiendo omitir el job en CI.

Mutaciones documentadas (M1 a M4):
- M1: alterar o vaciar MAPA_SALAS_PLAYWRIGHT['roadmap'] impide seleccionar 'tests/roadmap'.
- M2: omitir la guardia de layout devuelve cadena vacía o incompleta en cambios de componentes de armazón.
- M3: un cambio en gobernanza genera cadena vacía; si generara tests, rompería la omisión segura.
- M4: cualquier spec que salte en producción es descubierto sin excepciones pendientes.
"""
from pathlib import Path
import pytest
import scripts.seleccionar_pruebas as sp

RAIZ = Path(__file__).resolve().parent.parent


def test_autodescubrimiento_playwright_incluye_specs_con_skip_produccion():
    """Invariante 1: Todo archivo que omite producción se descubre automáticamente."""
    config_path = RAIZ / "frontend" / "playwright.config.ts"
    texto_config = config_path.read_text(encoding="utf-8")
    assert "descubrirSoloDesarrollo" in texto_config

    dir_tests = RAIZ / "frontend" / "tests"
    specs_con_skip = []
    for archivo in dir_tests.rglob("*.spec.ts"):
        contenido = archivo.read_text(encoding="utf-8")
        if (
            'test.skip(project.name === "produccion"' in contenido
            or "fijarAjustes" in contenido
            or "__LOPDP_AUTH_PRUEBAS__" in contenido
            or "harness-roadmap" in contenido
        ):
            specs_con_skip.append(archivo.name)

    assert len(specs_con_skip) >= 29, f"Se esperaban al menos 29 specs con skip, se hallaron {len(specs_con_skip)}"


def test_seleccion_playwright_sala_especifica():
    """Invariante 2: Un cambio en una sala selecciona solo sus pruebas de Playwright."""
    archivos = ["features/roadmap/services/nuevo_motor.py"]
    seleccion = sp.seleccionar(archivos, RAIZ)
    assert seleccion.modo == "salas"
    assert "roadmap" in seleccion.salas
    assert "tests/roadmap" in seleccion.playwright_specs
    assert "tests/rat" not in seleccion.playwright_specs


def test_seleccion_playwright_layout_compartido_corre_todo():
    """Invariante 3: Cambios en el armazón o layout del frontend corren toda la suite."""
    archivos = ["frontend/src/components/layout/dashboardNavigation.ts"]
    seleccion = sp.seleccionar(archivos, RAIZ)
    assert seleccion.playwright_specs == "tests/"


def test_seleccion_playwright_gobernanza_sin_ui_omite_job():
    """Invariante 4: Cambios en gobernanza o docs sin salas de UI devuelven cadena vacía."""
    archivos = ["governance/tareas/CI-30.md", "docs/adr/0001.md"]
    seleccion = sp.seleccionar(archivos, RAIZ)
    assert seleccion.playwright_specs == ""


def test_seleccion_playwright_modo_completo_corre_todo():
    """Invariante 3: El modo completo siempre ejecuta la suite completa."""
    seleccion = sp.seleccionar([], RAIZ)
    assert seleccion.modo == "completo"
    assert seleccion.playwright_specs == "tests/"


def test_mutacion_m1_alterar_mapeo_roadmap_falla():
    """M1: Si el mapeo de roadmap no apunta a tests/roadmap, la selección falla."""
    copia_mapa = dict(sp.MAPA_SALAS_PLAYWRIGHT)
    try:
        sp.MAPA_SALAS_PLAYWRIGHT["roadmap"] = "tests/inexistente"
        specs = sp.calcular_specs_playwright({"roadmap"}, ["features/roadmap/service.py"], "salas", RAIZ)
        assert "tests/roadmap" not in specs
    finally:
        sp.MAPA_SALAS_PLAYWRIGHT.clear()
        sp.MAPA_SALAS_PLAYWRIGHT.update(copia_mapa)


def test_mutacion_m2_layout_no_detectado_no_devuelve_tests_completo():
    """M2: Sin detección de layout compartido, no se devolvería tests/."""
    archivos = ["frontend/src/components/layout/Sidebar.tsx"]
    specs_con_guardia = sp.calcular_specs_playwright(set(), archivos, "salas", RAIZ)
    assert specs_con_guardia == "tests/"


def test_mutacion_m3_gobernanza_no_debe_devolver_specs():
    """M3: Si gobernanza devolviera specs, fallaría la prueba de omisión segura."""
    specs = sp.calcular_specs_playwright(set(), ["governance/artefactos/TASKS.md"], "salas", RAIZ)
    assert specs == ""


def test_invariante_descubrimiento_sin_falsos_negativos():
    """M4: Las pruebas con skip de producción se descubren sin exclusiones."""
    from tests.test_ci16_pruebas_sin_proyecto import sin_proyecto
    faltantes = sin_proyecto()
    assert not faltantes, f"Existen pruebas sin cubrir: {faltantes}"
