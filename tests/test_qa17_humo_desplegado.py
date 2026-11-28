# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤qa-engineer
# ¤arbitro
# ¤demo
"""QA-17 · El humo local y el desplegado, en escritorio y móvil y en los dos temas.

Contrato: governance/especificaciones/QA-17.md (R1 a R4, §5).

Las configuraciones se leen como texto (m1 y m2). El filtro de host (m3) se evalúa cargando la
configuración real con el cargador de TypeScript de Playwright, que ya está en frontend/node_modules:
`playwright test --list` lee la configuración y se para antes de globalSetup, webServer o cualquier petición.
"""
import os
import re
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
FRONTEND = RAIZ / "frontend"
HUMO = FRONTEND / "playwright.humo.config.ts"
DESPLEGADO = FRONTEND / "playwright.desplegado.config.ts"
CLI_PLAYWRIGHT = FRONTEND / "node_modules" / "@playwright" / "test" / "cli.js"

URL_DEMO = "https://evydentia-web-demo-517105327086.us-central1.run.app"

# R2: nombre, dispositivo y tema de cada proyecto.
PROYECTOS = {
    "escritorio-claro": ("Desktop Chrome", "light"),
    "escritorio-oscuro": ("Desktop Chrome", "dark"),
    "movil-claro": ("Pixel 7", "light"),
    "movil-oscuro": ("Pixel 7", "dark"),
}


def _leer(ruta: Path) -> str:
    return ruta.read_bytes().decode("utf-8")


def _bloque_projects(texto: str) -> str:
    """El arreglo `projects: [ … ]`, con sus corchetes equilibrados."""
    inicio = re.search(r"\bprojects\s*:\s*\[", texto)
    assert inicio, "la configuración no declara `projects: [`"
    nivel = 0
    for i in range(inicio.end() - 1, len(texto)):
        if texto[i] == "[":
            nivel += 1
        elif texto[i] == "]":
            nivel -= 1
            if nivel == 0:
                return texto[inicio.end() : i]
    raise AssertionError("`projects` sin cerrar")


def proyectos_declarados(texto: str) -> dict[str, tuple[str | None, str | None]]:
    """Cada proyecto con su dispositivo y el tema que deja en jubys-audit-storage (FE-41)."""
    bloque = _bloque_projects(texto)
    # El nombre del proyecto es el que va seguido de `use:`; el de localStorage no.
    partes = re.split(r'\bname\s*:\s*"([a-z0-9-]+)"\s*,\s*(?=use\s*:)', bloque)
    resultado = {}
    for nombre, cuerpo in zip(partes[1::2], partes[2::2]):
        dispositivo = re.search(r'devices\[\s*"([^"]+)"\s*\]', cuerpo)
        tema = re.search(r'\\?"theme\\?"\s*:\s*\\?"(light|dark)\\?"', cuerpo)
        resultado[nombre] = (dispositivo and dispositivo.group(1), tema and tema.group(1))
    return resultado


def _comprobar_proyectos(texto: str) -> None:
    assert proyectos_declarados(texto) == PROYECTOS


def _comprobar_sin_reintentos_ni_servidores(texto: str) -> None:
    assert re.findall(r"\bretries\s*:\s*([^,\n]+)", texto) == ["0"], "R1 y R4: `retries: 0` y nada más"
    servidores = re.findall(r"\bwebServer\s*:\s*(\[[^\]]*\]|[^,\n]+)", texto)
    assert all(re.fullmatch(r"\[\s*\]", s) for s in servidores), "R1: el desplegado no arranca servidores"


@pytest.mark.parametrize("config", [HUMO, DESPLEGADO], ids=["humo", "desplegado"])
def test_las_dos_configuraciones_declaran_los_cuatro_proyectos_con_su_tema(config: Path):
    _comprobar_proyectos(_leer(config))


def test_el_desplegado_no_reintenta_ni_arranca_servidores():
    _comprobar_sin_reintentos_ni_servidores(_leer(DESPLEGADO))


def test_el_desplegado_no_guarda_trazas_que_llevarian_el_token():
    """R5: la traza graba cabeceras y almacenamiento; con ella el token acabaría en un archivo."""
    assert re.search(r'\btrace\s*:\s*"off"', _leer(DESPLEGADO))


def test_el_desplegado_vive_fuera_del_humo_local():
    """R0."""
    assert (FRONTEND / "tests" / "desplegado" / "demo.spec.ts").is_file()
    assert re.search(r'testDir\s*:\s*"\./tests/desplegado"', _leer(DESPLEGADO))
    assert re.search(r'testDir\s*:\s*"\./tests/humo"', _leer(HUMO))


def test_la_cabecera_deja_el_comando_local():
    """R6: el comando de PowerShell, desde frontend/, con el token en la variable y sin guardarlo."""
    cabecera = _leer(DESPLEGADO).split("import ", 1)[0]
    assert "gcloud auth print-identity-token" in cabecera
    assert "--include-email" in cabecera
    assert "$env:HUMO_DEMO_TOKEN" in cabecera
    assert "npx playwright test -c playwright.desplegado.config.ts" in cabecera


# ---- Mutaciones de texto (m1 y m2) --------------------------------------------------------------------


def test_m1_quitar_movil_oscuro_da_rojo():
    texto = _leer(DESPLEGADO)
    mutado = texto.replace('name: "movil-oscuro"', 'name: "movil-oscuro-retirado"')
    assert mutado != texto
    with pytest.raises(AssertionError):
        _comprobar_proyectos(mutado)


def test_m1_un_proyecto_oscuro_sin_tema_da_rojo():
    texto = _leer(HUMO)
    mutado = texto.replace('\\"theme\\":\\"dark\\"', '\\"theme\\":\\"light\\"', 1)
    if mutado == texto:
        mutado = texto.replace('"theme":"dark"', '"theme":"light"', 1)
    assert mutado != texto
    with pytest.raises(AssertionError):
        _comprobar_proyectos(mutado)


def test_m2_retries_1_da_rojo():
    texto = _leer(DESPLEGADO)
    mutado = re.sub(r"\bretries\s*:\s*0", "retries: 1", texto)
    assert mutado != texto
    with pytest.raises(AssertionError):
        _comprobar_sin_reintentos_ni_servidores(mutado)


def test_m2_un_servidor_da_rojo():
    mutado = _leer(DESPLEGADO) + '\nconst x = { webServer: { command: "npx next start" } };\n'
    with pytest.raises(AssertionError):
        _comprobar_sin_reintentos_ni_servidores(mutado)


# ---- R1 · Filtro de host, con la configuración real (m3) ----------------------------------------------


def _listar(url: str | None, config: Path = DESPLEGADO) -> subprocess.CompletedProcess:
    if not CLI_PLAYWRIGHT.is_file():
        pytest.fail(f"falta {CLI_PLAYWRIGHT.relative_to(RAIZ)}: ejecute `npm ci` en frontend/")
    entorno = {k: v for k, v in os.environ.items() if k not in ("HUMO_DESPLEGADO_URL", "HUMO_DEMO_TOKEN")}
    if url is not None:
        entorno["HUMO_DESPLEGADO_URL"] = url
    return subprocess.run(
        ["node", str(CLI_PLAYWRIGHT), "test", "-c", str(config), "--list"],
        cwd=FRONTEND,
        env=entorno,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://app.evydentia.com",
        "http://localhost:3000",
        f"{URL_DEMO}.otro-dominio.com",
        URL_DEMO.replace("https://", "http://"),
        "https://evydentia-web-517105327086.us-central1.run.app",
        "no es una url",
    ],
)
def test_r1_fuera_de_la_demo_para_antes_de_pedir_nada(url: str):
    r = _listar(url)
    salida = r.stdout + r.stderr
    assert r.returncode != 0, salida
    assert "[PRECONDICION FALLIDA]" in salida, salida


@pytest.mark.parametrize("url", [None, URL_DEMO, "https://evydentia-api-demo-517105327086.us-central1.run.app"])
def test_r1_la_demo_carga_los_cuatro_proyectos(url: str | None):
    r = _listar(url)
    salida = r.stdout + r.stderr
    assert r.returncode == 0, salida
    for nombre in PROYECTOS:
        assert f"[{nombre}]" in salida, salida


def test_m3_aceptar_cualquier_host_da_rojo(tmp_path: Path):
    """La configuración mutada acepta app.evydentia.com: la comprobación de R1 tiene que detectarlo."""
    texto = _leer(DESPLEGADO)
    mutado = re.sub(r"function esHostDeDemo\(([^)]*)\)\s*:\s*boolean\s*\{", r"function esHostDeDemo(\1): boolean { return true;", texto)
    assert mutado != texto, "no se encontró esHostDeDemo para mutarla"
    copia = FRONTEND / "playwright.desplegado.m3.config.ts"
    copia.write_bytes(mutado.encode("utf-8"))
    try:
        r = _listar("https://app.evydentia.com", config=copia)
    finally:
        copia.unlink()
    assert "[PRECONDICION FALLIDA]" not in r.stdout + r.stderr
