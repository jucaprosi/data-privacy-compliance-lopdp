# ¤arbitro ¤seguridad
"""RET-00 · Árbitro de plataforma única: `main` solo depende de Google Cloud.

No busca nombres: comprueba la estructura por AST (de qué paquetes depende `main`, de dónde saca su
configuración, con qué dominios habla, cómo se despliega y cómo guardan la base las pruebas).
Reglas R1 a R9 de `governance/especificaciones/RET-00.md`; analizadores en
`tests/plataforma_unica/catalogos.py`; catálogos y pendientes en `tests/plataforma_unica/`.

Un fallo dice la regla, el archivo y el elemento, y qué catálogo se amplía si el cambio es legítimo.
No lee `governance/` ni comentarios. Sin `import yaml`; no toca la red ni la base.
"""
from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

_RUTA = Path(__file__).resolve().parent / "plataforma_unica" / "catalogos.py"
_spec = importlib.util.spec_from_file_location("catalogos_plataforma_unica", _RUTA)
cat = importlib.util.module_from_spec(_spec)
sys.modules["catalogos_plataforma_unica"] = cat
_spec.loader.exec_module(cat)

RAIZ = cat.RAIZ

# ---- utilidades de comparación con origin/main -------------------------------------------------

def _de_main(ruta: Path) -> str | None:
    rel = ruta.relative_to(RAIZ).as_posix()
    r = subprocess.run(["git", "show", f"origin/main:{rel}"], cwd=RAIZ, capture_output=True,
                       text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else None


def _rama_del_pr() -> str:
    rama = os.environ.get("GITHUB_HEAD_REF", "")
    if not rama:
        r = subprocess.run(["git", "branch", "--show-current"], cwd=RAIZ, capture_output=True, text=True)
        rama = r.stdout.strip()
    return rama


def es_pr_de_retiro(rama: str) -> bool:
    return re.search(r"(^|/)ret-\d+", rama, re.IGNORECASE) is not None


def _fichas_hechas() -> set[str]:
    spec = importlib.util.spec_from_file_location("_indice_tareas_ret00", RAIZ / "scripts" / "generar_indice_tareas.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_indice_tareas_ret00"] = mod
    spec.loader.exec_module(mod)
    tareas, _ = mod.cargar_tareas()
    return {t.id for t in tareas if t.estado == "hecha"}


def lineas_de_catalogo(texto: str) -> set[str]:
    return {f"{e}|{m}" for e, m in cat.leer_lista(texto)}


def errores_de_catalogos(actuales: dict[str, str], bases: dict[str, str | None], rama: str) -> list[str]:
    """R6: cada línea lleva motivo; una línea nueva no entra en un PR de ficha RET-."""
    errores = []
    for nombre, texto in actuales.items():
        for elemento, motivo in cat.leer_lista(texto):
            if not motivo:
                errores.append(f"R6|{nombre}.txt|{elemento}: falta el motivo")
        base = bases.get(nombre)
        if base is None or not es_pr_de_retiro(rama):
            continue
        viejos = {e for e, _ in cat.leer_lista(base)}
        for elemento, _ in cat.leer_lista(texto):
            if elemento not in viejos:
                errores.append(f"R6|{nombre}.txt|{elemento}: un PR de una ficha RET- no amplía catálogos")
    return errores


def errores_de_pendientes(actuales: dict[str, set[str]], bases: dict[str, set[str]], hechas: set[str]) -> list[str]:
    """R7: ids válidos, ninguno a nombre de una ficha hecha y ninguna entrada nueva contra origin/main."""
    errores = []
    for ficha, claves in actuales.items():
        if ficha not in cat.FICHAS_DUENAS:
            errores.append(f"pendientes/{ficha}.txt: ID desconocido (válidos: {', '.join(cat.FICHAS_DUENAS)})")
        if claves and ficha in hechas:
            errores.append(f"pendientes/{ficha}.txt: la ficha está hecha y aún tiene {len(claves)} pendientes")
        if ficha in bases:
            for k in sorted(claves - bases[ficha]):
                errores.append(f"pendientes/{ficha}.txt gana la entrada {k}")
    return errores


# ---- el árbol real ----------------------------------------------------------------------------

def _catalogos_reales() -> dict[str, list[str]]:
    return {n: [e for e, _ in cat.cargar_catalogo(n)] for n in cat.CATALOGOS}


def test_plataforma_unica_sin_incumplimientos_nuevos():
    medicion = cat.evaluar_arbol(_catalogos_reales())
    permitido = set().union(*cat.cargar_pendientes().values())
    nuevos = [k for k in medicion.incumplimientos if k not in permitido]
    assert not nuevos, (
        "Incumplimientos de plataforma única fuera de los pendientes (regla|archivo|elemento). Si el cambio es "
        "legítimo, amplíe el catálogo de su regla (R1 dependencias.txt, R2 variables.txt, R3 servicios_externos.txt, "
        "R4 despliegue.txt) con su motivo, en un PR que no sea de una ficha RET-; R5: llame a "
        "exigir_base_de_pruebas() y no compare el host con un literal:\n" + "\n".join(nuevos[:40]))


def test_pendientes_ya_cumplidos_se_retiran():
    medicion = cat.evaluar_arbol(_catalogos_reales())
    sobrantes = [f"{f}: {k}" for f, claves in cat.cargar_pendientes().items() for k in sorted(claves)
                 if k not in medicion.incumplimientos]
    assert not sobrantes, "Pendientes que ya no incumplen; retírelos en el mismo PR (R7):\n" + "\n".join(sobrantes[:40])


def test_catalogos_y_pendientes_cerrados():
    actuales = {n: p.read_text(encoding="utf-8") for n, p in cat.CATALOGOS.items()}
    bases = {n: _de_main(p) for n, p in cat.CATALOGOS.items()}
    pendientes = cat.cargar_pendientes()
    bases_pend = {}
    for f in sorted(cat.DIR_PENDIENTES.glob("*.txt")):
        v = _de_main(f)
        if v is not None:
            bases_pend[f.stem] = cat.leer_pendientes(v)
    errores = errores_de_catalogos(actuales, bases, _rama_del_pr())
    errores += errores_de_pendientes(pendientes, bases_pend, _fichas_hechas())
    assert not errores, "\n".join(errores)


def test_los_catalogos_no_nombran_la_base_gestionada_anterior():
    """R9: mientras viva el árbitro de menciones, esta carpeta no escribe el nombre que él vigila."""
    for ruta in [*cat.CATALOGOS.values(), *cat.DIR_PENDIENTES.glob("*.txt"), _RUTA, Path(__file__)]:
        assert not re.search("ne" + "on", ruta.read_text(encoding="utf-8"), re.IGNORECASE), ruta.name


# ---- mutaciones sobre árboles simulados --------------------------------------------------------

REQUIREMENTS = "fastapi>=0.1\nsqlalchemy[asyncio]>=2\npydantic-settings>=2\n"
CONFIG = (
    "import os\nfrom pydantic_settings import BaseSettings\n\n"
    "class AppConfig(BaseSettings):\n    database_url: str = Field(..., alias=\"DATABASE_URL\")\n\n"
    "URL = os.environ.get(\"APP_ENV\", \"x\")\n"
)
ARBOL_BASE = {
    "requirements.txt": REQUIREMENTS,
    "frontend/package.json": '{"dependencies": {"next": "1"}}',
    "frontend/next.config.ts": "const csp = \"connect-src 'self' https://*.googleapis.com\";\n",
    "main.py": "from fastapi import FastAPI\nfrom app_core.config import config\napp = FastAPI()\n",
    "app_core/__init__.py": "",
    "app_core/config.py": CONFIG,
    "Dockerfile": "FROM python:3.12\nCMD [\"uvicorn\", \"main:app\"]\n",
    "tests/test_a.py": "from app_core.config import config\n\ndef test_a():\n    assert config\n",
}
CATALOGOS_BASE = {
    "dependencias": ["python:fastapi", "python:sqlalchemy", "python:pydantic-settings", "npm:next"],
    "servicios_externos": ["*.googleapis.com"],
    "variables": ["DATABASE_URL", "APP_ENV"],
    "despliegue": ["Dockerfile", "entrada:main:app"],
}


def _medir_arbol(cambios: dict[str, str | None]) -> set[str]:
    arbol = dict(ARBOL_BASE)
    for ruta, texto in cambios.items():
        if texto is None:
            arbol.pop(ruta, None)
        else:
            arbol[ruta] = texto
    return set(cat.evaluar_arbol(CATALOGOS_BASE, arbol).incumplimientos)


def test_el_arbol_simulado_de_base_cumple():
    assert _medir_arbol({}) == set()


def test_dependencia_no_catalogada():
    """R1. Mutación: añadir el cliente de otro proveedor de nube hace fallar la prueba."""
    rojo = _medir_arbol({"requirements.txt": REQUIREMENTS + "boto3>=1.35\n"})
    assert rojo == {"R1|requirements.txt|python:boto3"}
    rojo = _medir_arbol({"frontend/package.json": '{"dependencies": {"next": "1", "@aws-sdk/client-s3": "3"}}'})
    assert rojo == {"R1|frontend/package.json|npm:@aws-sdk/client-s3"}


def test_import_sin_dependencia_declarada():
    """R1. Un módulo de terceros importado sin paquete declarado; los de la biblioteca estándar y locales no cuentan."""
    assert _medir_arbol({"features/a.py": "import requests\nimport json\nfrom app_core import config\n"}) \
        == {"R1|features/a.py|import:requests"}
    assert _medir_arbol({"features/a.py": "from starlette.requests import Request\n"}) == set()


def test_configuracion_solo_del_proceso():
    """R2. Mutación: volver a leer un archivo de entorno hace fallar la prueba."""
    con_archivo = CONFIG.replace("class AppConfig(BaseSettings):\n",
                                 "class AppConfig(BaseSettings):\n    model_config = SettingsConfigDict(env_file=\".env\")\n")
    assert _medir_arbol({"app_core/config.py": con_archivo}) == {
        "R2|app_core/config.py|env_file", "R2|app_core/config.py|archivo_env"}
    assert _medir_arbol({"app_core/otro.py": "from dotenv import load_dotenv\nload_dotenv()\n"}) >= {
        "R2|app_core/otro.py|load_dotenv"}
    assert _medir_arbol({"scripts/x.py": "import os\nos.getenv('VARIABLE_NUEVA')\n"}) == {
        "R2|scripts/x.py|var:VARIABLE_NUEVA"}
    assert _medir_arbol({"scripts/x.py": "import os\nx = os.environ['OTRA_NUEVA']\n"}) == {
        "R2|scripts/x.py|var:OTRA_NUEVA"}
    assert _medir_arbol({"scripts/x.py": "import os\nx = 'Z' in os.environ\nopen('.env')\n"}) == {
        "R2|scripts/x.py|var:Z", "R2|scripts/x.py|archivo_env"}
    assert _medir_arbol({"scripts/x.py": "import os\nx = os.environ.get('APP_ENV')\n"}) == set()
    # Un alias de cabecera HTTP no es una variable de entorno.
    assert _medir_arbol({"api/x.py": "def f(x=Header(alias='X-Role')):\n    pass\n"}) == set()


def test_servicio_externo_no_catalogado():
    """R3. Mutación: permitir en la política de contenido un almacén de otro proveedor hace fallar la prueba."""
    csp = "const csp = \"connect-src 'self' https://*.googleapis.com https://bucket.s3.amazonaws.com\";\n"
    assert _medir_arbol({"frontend/next.config.ts": csp}) == {"R3|frontend/next.config.ts|bucket.s3.amazonaws.com"}
    assert _medir_arbol({"features/x.py": "URL = 'https://api.otro-proveedor.com/v1'\n"}) == {
        "R3|features/x.py|api.otro-proveedor.com"}
    assert _medir_arbol({"governance/operaciones/m.yaml": "origen: https://registro.otro.io/img\n"}) == {
        "R3|governance/operaciones/m.yaml|registro.otro.io", "R4|governance/operaciones/m.yaml|archivo"}
    # Docstrings, comentarios y hosts locales no cuentan; un subdominio del comodín catalogado sí pasa.
    texto = '"""Ver https://docs.otro.io."""\n# https://comentario.otro.io\nA = "http://localhost:8000"\nB = "https://x.storage.googleapis.com/o"\n'
    assert _medir_arbol({"features/x.py": texto}) == set()


def test_despliegue_unico():
    """R4. Un archivo de despliegue fuera del catálogo o una entrada de la API distinta de `main` hacen fallar."""
    assert _medir_arbol({"vercel.json": "{}"}) == {"R4|vercel.json|archivo"}
    assert _medir_arbol({"Procfile": "web: uvicorn main:app"}) == {"R4|Procfile|archivo"}
    assert _medir_arbol({"Dockerfile": "CMD uvicorn api.index:app"}) == {"R4|Dockerfile|entrada:api.index:app"}
    assert _medir_arbol({"tests/test_b.py": "from api.index import app\n"}) == {"R4|tests/test_b.py|entrada:api.index"}
    assert _medir_arbol({"governance/operaciones/cloudrun.yaml": "kind: Service\n"}) == {
        "R4|governance/operaciones/cloudrun.yaml|archivo"}


def test_guardia_de_base_unica():
    """R5. Una prueba que usa la base debe llamar a la guardia común y no comparar el host con un literal."""
    sin_guardia = "import os\n\ndef test_b():\n    url = os.environ['TEST_DATABASE_URL']\n"
    assert _medir_arbol({"tests/test_b.py": sin_guardia}) == {"R5|tests/test_b.py|sin_guardia"}
    con_guardia = "import os\nfrom conftest import exigir_base_de_pruebas\n\ndef test_b():\n    exigir_base_de_pruebas()\n    os.environ['TEST_DATABASE_URL']\n"
    assert _medir_arbol({"tests/test_b.py": con_guardia}) == set()
    con_literal = con_guardia + "\ndef test_c():\n    assert 'ep-aaa-bbb' not in os.environ['TEST_DATABASE_URL']\n"
    assert _medir_arbol({"tests/test_b.py": con_literal}) == {"R5|tests/test_b.py|literal:ep-aaa-bbb"}
    assert _medir_arbol({"tests/test_b.py": 'def test_d():\n    """Evita ep-aaa-bbb."""\n'}) == set()


def test_catalogos_y_pendientes_cerrados_mutaciones():
    """R6 y R7. Mutación: aceptar una línea nueva en un PR RET-, o dejar crecer un pendiente, hace fallar."""
    base = {"variables": "A|motivo\n"}
    actual = {"variables": "A|motivo\nB|motivo\n"}
    assert errores_de_catalogos(actual, base, "tarea/x/ret-03")
    assert not errores_de_catalogos(actual, base, "tarea/x/gob-01")
    assert not errores_de_catalogos(actual, {"variables": None}, "tarea/x/ret-03")
    assert errores_de_catalogos({"variables": "A|\n"}, base, "tarea/x/gob-01")
    assert es_pr_de_retiro("tarea/juan-carlos/ret-00") and not es_pr_de_retiro("tarea/juan-carlos/ia-08")
    bases = {"RET-02": {"R1|a|x"}}
    assert errores_de_pendientes({"RET-02": {"R1|a|x", "R1|a|y"}}, bases, set())
    assert not errores_de_pendientes({"RET-02": {"R1|a|x"}}, bases, set())
    assert errores_de_pendientes({"OTRA": {"R1|a|x"}}, {}, set())
    assert errores_de_pendientes({"RET-02": {"R1|a|x"}}, {}, {"RET-02"})
    assert not errores_de_pendientes({"RET-02": set()}, {}, {"RET-02"})


def test_el_nombre_prohibido_se_enmascara():
    assert cat.enmascarar("a." + "ne" + "on" + ".tech") == "a.§1§.tech"
    assert cat.clave("R3", "x.py", "ne" + "on" + ".io") == "R3|x.py|§1§.io"
