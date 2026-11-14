# ¤arbitro ¤seguridad
"""RET-00 · Analizadores y catálogos del árbitro de plataforma única.

Todo es estructural: lee el árbol rastreado por git y analiza el código por AST. No lee `governance/`
ni comentarios. No importa de ninguna sala (R-ADPA). Cada analizador es una función pura sobre texto,
para que las mutaciones de `tests/test_plataforma_unica.py` la ejerciten con árboles simulados.

Formato de las listas (una línea por elemento, `#` comenta):
- catálogos (`dependencias.txt`, `servicios_externos.txt`, `variables.txt`, `despliegue.txt`):
  `elemento|motivo`; el motivo es obligatorio (R6).
- `pendientes/<ficha>.txt`: `regla|archivo|elemento`, lo que hoy incumple y la ficha que lo retira (R7).

Convivencia con el árbitro de menciones vigente (R9): hasta RET-07 ningún archivo de esta carpeta puede
escribir el nombre de la base gestionada anterior. `enmascarar` lo sustituye por `§1§` en toda clave y
mensaje; el mismo paso se aplica al medir y al leer, así que la comparación es idéntica.

Generar o regenerar las listas midiendo el árbol (solo al crear el árbitro):
    python tests/plataforma_unica/catalogos.py --generar
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIR = Path(__file__).resolve().parent
DIR_PENDIENTES = DIR / "pendientes"
CATALOGOS = {
    "dependencias": DIR / "dependencias.txt",
    "servicios_externos": DIR / "servicios_externos.txt",
    "variables": DIR / "variables.txt",
    "despliegue": DIR / "despliegue.txt",
}
FICHAS_DUENAS = ("RET-01", "RET-02", "RET-03", "RET-05", "RET-06", "IA-04", "IA-06", "IA-08")

CODIGO_DIRS = ("app_core", "features", "api", "jobs", "scripts")
CODIGO_SUELTOS = ("main.py", "alembic/env.py")
ENTRADA_UNICA = "main:app"

# ---- enmascarado del nombre de la base gestionada anterior (R9) ---------------------------------
_NOMBRE_PROHIBIDO = "ne" + "on"
_MASCARA = "§1§"


def enmascarar(texto: str) -> str:
    return re.sub(_NOMBRE_PROHIBIDO, _MASCARA, texto, flags=re.IGNORECASE)


def clave(regla: str, archivo: str, elemento: str) -> str:
    return enmascarar(f"{regla}|{archivo}|{elemento}")


# ---- archivos del árbol ------------------------------------------------------------------------

def archivos_rastreados() -> list[str]:
    r = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files"], cwd=RAIZ, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stderr
    return [f for f in r.stdout.split("\n") if f and (RAIZ / f).is_file()]


def leer(ruta: str) -> str:
    return (RAIZ / ruta).read_text(encoding="utf-8", errors="replace")


def es_codigo_de_producto(ruta: str) -> bool:
    if not ruta.endswith(".py"):
        return False
    if ruta in CODIGO_SUELTOS:
        return True
    return ruta.split("/", 1)[0] in CODIGO_DIRS


def es_prueba(ruta: str) -> bool:
    return (ruta.startswith("tests/") and ruta.endswith(".py") and not ruta.startswith("tests/plataforma_unica/")
            and ruta != "tests/test_plataforma_unica.py")


# ---- lectura de listas -------------------------------------------------------------------------

def leer_lista(texto: str) -> list[tuple[str, str]]:
    """`elemento|motivo`; ignora comentarios y vacías. El separador es la primera barra vertical."""
    filas = []
    for crudo in texto.replace("\r", "").split("\n"):
        crudo = crudo.strip()
        if not crudo or crudo.startswith("#"):
            continue
        elemento, _, motivo = crudo.partition("|")
        filas.append((elemento.strip(), motivo.strip()))
    return filas


def leer_pendientes(texto: str) -> set[str]:
    claves = set()
    for crudo in texto.replace("\r", "").split("\n"):
        crudo = crudo.strip()
        if crudo and not crudo.startswith("#"):
            claves.add(crudo)
    return claves


def cargar_catalogo(nombre: str) -> list[tuple[str, str]]:
    return leer_lista(CATALOGOS[nombre].read_text(encoding="utf-8"))


def cargar_pendientes() -> dict[str, set[str]]:
    return {p.stem: leer_pendientes(p.read_text(encoding="utf-8")) for p in sorted(DIR_PENDIENTES.glob("*.txt"))}


# ---- R1 · dependencias -------------------------------------------------------------------------

def normalizar_paquete(nombre: str) -> str:
    return re.sub(r"[-_.]+", "-", nombre).lower()


def paquetes_de_requirements(texto: str) -> list[str]:
    nombres = []
    for linea in texto.replace("\r", "").split("\n"):
        linea = linea.split("#", 1)[0].strip()
        if not linea or linea.startswith("-"):
            continue
        m = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", linea)
        if m:
            nombres.append(normalizar_paquete(m.group(0)))
    return nombres


def paquetes_de_package_json(texto: str) -> list[str]:
    datos = json.loads(texto)
    nombres = []
    for seccion in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        nombres += list(datos.get(seccion, {}))
    return nombres


# Módulo importado -> paquete que lo instala, cuando el nombre no coincide.
MODULO_A_PAQUETE = {
    "jwt": "pyjwt", "dotenv": "python-dotenv", "multipart": "python-multipart", "yaml": "pyyaml",
    "google.genai": "google-genai", "google.cloud.storage": "google-cloud-storage",
    "fpdf": "fpdf2", "pydantic_settings": "pydantic-settings", "pytest_asyncio": "pytest-asyncio",
    "PIL": "pillow", "bs4": "beautifulsoup4", "dateutil": "python-dateutil",
}
# Módulos que llegan como dependencia de un paquete declarado (extras o dependencias directas de su metadata).
TRANSITIVAS = {
    "starlette": {"fastapi"}, "cryptography": {"pyjwt"}, "coverage": {"pytest-cov"},
    "google.auth": {"google-cloud-storage", "google-genai"}, "google.oauth2": {"google-cloud-storage", "google-genai"},
    "google.api_core": {"google-cloud-storage"}, "google.cloud": {"google-cloud-storage"},
    "google.protobuf": {"google-cloud-storage", "google-genai"}, "pydantic_core": {"pydantic"}, "anyio": {"httpx"},
}
_STDLIB = set(sys.stdlib_module_names)


def modulos_locales(archivos: list[str]) -> set[str]:
    locales = set()
    for f in archivos:
        if f.endswith(".py"):
            primero = f.split("/", 1)[0]
            locales.add(primero[:-3] if primero.endswith(".py") else primero)
            if primero in ("scripts", "verificadores", "tests") and f.count("/") == 1:
                locales.add(f.rsplit("/", 1)[1][:-3])  # módulos que esos directorios importan entre sí
    return locales


def paquete_de_modulo(modulo: str) -> str:
    partes = modulo.split(".")
    for n in range(len(partes), 0, -1):
        previo = ".".join(partes[:n])
        if previo in MODULO_A_PAQUETE:
            return MODULO_A_PAQUETE[previo]
    return normalizar_paquete(partes[0])


def modulos_importados(fuente: str) -> list[str]:
    """Nombres punteados importados (absolutos) por un módulo, por AST."""
    try:
        arbol = ast.parse(fuente)
    except SyntaxError:
        return []
    salida = []
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            salida += [a.name for a in nodo.names]
        elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and nodo.module:
            salida.append(nodo.module)
            salida += [f"{nodo.module}.{a.name}" for a in nodo.names if a.name != "*"]
    return salida


def imports_sin_dependencia(fuente: str, declaradas: set[str], locales: set[str]) -> list[str]:
    """Módulos de terceros importados cuyo paquete no está declarado (R1)."""
    sin = set()
    for modulo in modulos_importados(fuente):
        top = modulo.split(".")[0]
        if top in _STDLIB or top in locales:
            continue
        partes = modulo.split(".")
        if top == "google" and len(partes) == 1:
            continue  # espacio de nombres: lo resuelve el submódulo importado
        resueltos = {paquete_de_modulo(".".join(partes[:n])) for n in range(1, len(partes) + 1)}
        for n in range(1, len(partes) + 1):
            resueltos |= TRANSITIVAS.get(".".join(partes[:n]), set())
        if resueltos & declaradas:
            continue
        sin.add(".".join(partes[:2]) if top == "google" and len(partes) > 1 else top)
    return sorted(sin)


# ---- R2 · configuración solo por el proceso ----------------------------------------------------

_ENV_ARCHIVO = re.compile(r"(^|[\\/])\.env(\.[A-Za-z0-9_-]+)?$")


def _texto_de(nodo: ast.AST) -> str | None:
    return nodo.value if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str) else None


def _es_environ(nodo: ast.AST) -> bool:
    return (isinstance(nodo, ast.Attribute) and nodo.attr == "environ") or (isinstance(nodo, ast.Name) and nodo.id == "environ")


def _docstrings(arbol: ast.AST) -> set[int]:
    ids = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            cuerpo = nodo.body
            if cuerpo and isinstance(cuerpo[0], ast.Expr) and isinstance(cuerpo[0].value, ast.Constant) \
                    and isinstance(cuerpo[0].value.value, str):
                ids.add(id(cuerpo[0].value))
    return ids


def configuracion_del_modulo(fuente: str) -> tuple[set[str], set[str]]:
    """(variables leídas, usos prohibidos) de un módulo de producto.

    Usos prohibidos: `env_file`, `load_dotenv`/`dotenv_values` y un archivo `.env` escrito como cadena.
    """
    try:
        arbol = ast.parse(fuente)
    except SyntaxError:
        return set(), set()
    docs = _docstrings(arbol)
    variables: set[str] = set()
    usos: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Subscript) and _es_environ(nodo.value):
            v = _texto_de(nodo.slice)
            if v:
                variables.add(v)
        elif isinstance(nodo, ast.Call):
            f = nodo.func
            nombre = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
            if nodo.args and _texto_de(nodo.args[0]):
                if nombre == "getenv" or (isinstance(f, ast.Attribute) and _es_environ(f.value)
                                          and nombre in ("get", "pop", "setdefault")):
                    variables.add(_texto_de(nodo.args[0]))
            if nombre in ("load_dotenv", "dotenv_values", "find_dotenv"):
                usos.add("load_dotenv")
            for kw in nodo.keywords:
                if kw.arg == "env_file":
                    usos.add("env_file")
        elif isinstance(nodo, ast.Compare):
            if any(isinstance(o, (ast.In, ast.NotIn)) for o in nodo.ops) and any(_es_environ(c) for c in nodo.comparators):
                v = _texto_de(nodo.left)
                if v:
                    variables.add(v)
        elif isinstance(nodo, (ast.Import, ast.ImportFrom)):
            nombres = [a.name for a in nodo.names] + ([nodo.module] if isinstance(nodo, ast.ImportFrom) and nodo.module else [])
            if any(n and n.split(".")[0] == "dotenv" for n in nombres):
                usos.add("load_dotenv")
        elif isinstance(nodo, ast.Constant) and isinstance(nodo.value, str) and id(nodo) not in docs:
            if _ENV_ARCHIVO.search(nodo.value):
                usos.add("archivo_env")
        elif isinstance(nodo, ast.ClassDef) and any(
                (isinstance(b, ast.Name) and b.id == "BaseSettings") or (isinstance(b, ast.Attribute) and b.attr == "BaseSettings")
                for b in nodo.bases):
            for item in nodo.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    campo = item.target.id
                    alias = [_texto_de(k.value) for k in item.value.keywords if k.arg in ("alias", "validation_alias")]                         if isinstance(item.value, ast.Call) else []
                    if alias:
                        variables.update(a for a in alias if a)
                    elif not campo.startswith("_") and campo != "model_config":
                        variables.add(campo.upper())
    return {v for v in variables if v}, usos


# ---- R3 · servicios externos -------------------------------------------------------------------

_URL = re.compile(r"https?://([A-Za-z0-9*][A-Za-z0-9.*-]*)", re.IGNORECASE)
_HOST_SIN_ESQUEMA = re.compile(r"(?<![\w.@/-])(\*\.[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")
_RESERVADOS = ("localhost", "127.0.0.1", "0.0.0.0", "::1", "example.com", "example.org", "example.net")


def dominios_en_texto(texto: str) -> set[str]:
    encontrados = set()
    for host in [m.group(1) for m in _URL.finditer(texto)] + [m.group(1) for m in _HOST_SIN_ESQUEMA.finditer(texto)]:
        host = host.lower().strip(".")
        if "." not in host or host in _RESERVADOS or host.endswith((".invalid", ".test", ".localhost", ".local")):
            continue
        if re.fullmatch(r"[\d.]+", host):
            continue
        encontrados.add(host)
    return encontrados


def dominios_del_modulo(fuente: str) -> set[str]:
    """Dominios escritos como cadena (no docstring) en un módulo Python."""
    try:
        arbol = ast.parse(fuente)
    except SyntaxError:
        return set()
    docs = _docstrings(arbol)
    dominios: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str) and id(nodo) not in docs:
            dominios |= dominios_en_texto(nodo.value)
    return dominios


def dominio_catalogado(dominio: str, catalogo: list[str]) -> bool:
    for c in catalogo:
        if c == dominio:
            return True
        if c.startswith("*.") and (dominio == c[2:] or dominio.endswith(c[1:])):
            return True
    return False


def es_manifiesto_de_dominios(ruta: str) -> bool:
    return (ruta.startswith("frontend/next.config") and ruta.endswith(".ts")) \
        or (ruta.startswith("governance/operaciones/") and ruta.endswith((".yaml", ".yml")))


# ---- R4 · despliegue ---------------------------------------------------------------------------

_NOMBRES_DESPLIEGUE = {"vercel.json", "procfile", "app.yaml", "render.yaml", "netlify.toml", "fly.toml",
                       "docker-compose.yml", "docker-compose.yaml", "compose.yaml", "compose.yml", "serverless.yml"}


def es_archivo_de_despliegue(ruta: str) -> bool:
    bajo = ruta.rsplit("/", 1)[-1].lower()
    return (bajo in _NOMBRES_DESPLIEGUE or bajo.startswith("dockerfile") or bajo.endswith(".dockerfile")
            or bajo.startswith("cloudbuild") or ruta.startswith(".github/workflows/")
            or ruta.startswith(".vercel/") or ruta == "api/index.py"
            or (ruta.startswith("governance/operaciones/") and ruta.endswith((".yaml", ".yml"))))


_UVICORN = re.compile(r"uvicorn[\s\"',\[]+([\w.]+:\w+)")


def entradas_en_texto(texto: str) -> set[str]:
    return set(_UVICORN.findall(texto))


def entradas_importadas(fuente: str) -> set[str]:
    """`api.index` (otra entrada de la API distinta de `main`) importado por un módulo."""
    return {"api.index"} if any(m == "api.index" or m.startswith("api.index.") for m in modulos_importados(fuente)) else set()


# ---- R5 · guardia común de base en las pruebas --------------------------------------------------

_LITERAL_DE_HOST = re.compile(r"\bep-[a-z0-9]+-[a-z0-9]+")
_VARIABLES_DE_BASE = {"TEST_DATABASE_URL", "DATABASE_URL", "MIGRATION_DATABASE_URL"}


def guardia_de_base(fuente: str) -> tuple[set[str], bool, bool]:
    """(literales de host, usa la base, llama a la guardia común) de un archivo de pruebas."""
    try:
        arbol = ast.parse(fuente)
    except SyntaxError:
        return set(), False, False
    docs = _docstrings(arbol)
    literales: set[str] = set()
    usa = llama = False
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str) and id(nodo) not in docs:
            literales |= {m.group(0) for m in _LITERAL_DE_HOST.finditer(nodo.value.lower())}
            if nodo.value in _VARIABLES_DE_BASE:
                usa = True
        elif isinstance(nodo, ast.Call):
            f = nodo.func
            nombre = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
            if nombre in ("create_engine", "create_async_engine"):
                usa = True
            if nombre == "exigir_base_de_pruebas":
                llama = True
    return literales, usa, llama


# ---- ficha dueña de cada incumplimiento --------------------------------------------------------

_P_R2 = re.compile(r"cloudflare|\br2[_.-]|^r2$|boto", re.I)
_P_UPSTASH = re.compile(r"upstash", re.I)
_P_VERCEL = re.compile(r"vercel", re.I)
_P_IA = re.compile(r"deepseek|openai", re.I)
_P_BASE = re.compile(_NOMBRE_PROHIBIDO + r"|ep-[a-z0-9]+-[a-z0-9]+|dotenv", re.I)
_GUARDIAS = ("tests/conftest.py", "tests/test_conftest_guardias.py", "tests/test_hook_pre_push.py",
             "tests/test_crear_organizacion_dev.py", "tests/test_sec20_huella_cloudsql.py")


def ficha_de_ia(archivo: str) -> str:
    if archivo.startswith("features/preanalisis"):
        return "IA-04"
    if archivo.startswith("features/roadmap"):
        return "IA-06"
    return "IA-08"


def ficha_duena(regla: str, archivo: str, elemento: str) -> str | None:
    """Ficha que retira el incumplimiento, o `None` si el elemento es legítimo y va a un catálogo."""
    if regla == "R4" and ("vercel" in archivo.lower() or archivo == "api/index.py" or elemento == "entrada:api.index"):
        return "RET-05"
    if regla == "R5":
        if archivo in _GUARDIAS or archivo.startswith(("scripts/", "alembic/", "app_core/")):
            return "RET-01"
        return "RET-06"
    if regla == "R2" and elemento in ("env_file", "load_dotenv", "archivo_env"):
        return "RET-01"
    for ficha, patron in (("RET-02", _P_R2), ("RET-03", _P_UPSTASH), ("RET-05", _P_VERCEL)):
        if patron.search(elemento):
            return ficha
    if _P_IA.search(elemento):
        return ficha_de_ia(archivo)
    if _P_BASE.search(elemento):
        return "RET-01"
    return None


# ---- medición del árbol ------------------------------------------------------------------------

class Medicion:
    """Lo que hoy hay en el árbol: incumplimientos (clave -> ficha) y elementos catalogables."""

    def __init__(self) -> None:
        self.incumplimientos: dict[str, str] = {}
        self.catalogables: dict[str, set[str]] = {n: set() for n in CATALOGOS}

    def anotar(self, regla: str, archivo: str, elemento: str) -> None:
        ficha = ficha_duena(regla, archivo, elemento) or "RET-01"
        self.incumplimientos[clave(regla, archivo, elemento)] = ficha


def medir() -> Medicion:
    """Mide el árbol rastreado con las reglas R1 a R5 sobre los catálogos aún vacíos (para generar)."""
    return evaluar_arbol(None)


def evaluar_arbol(catalogos: dict[str, list[str]] | None, arbol: dict[str, str] | None = None) -> Medicion:
    """Mide el árbol. Con `catalogos`, solo es incumplimiento lo que no está en ellos; con `None`, todo
    elemento sin ficha dueña se anota como catalogable (modo generación). Con `arbol` ({ruta: texto}) mide
    ese árbol simulado en lugar del rastreado (mutaciones)."""
    m = Medicion()
    archivos = list(arbol) if arbol is not None else archivos_rastreados()
    lee = arbol.__getitem__ if arbol is not None else leer
    locales = modulos_locales(archivos)
    py = paquetes_de_requirements(lee("requirements.txt")) if "requirements.txt" in archivos else []
    npm = paquetes_de_package_json(lee("frontend/package.json")) if "frontend/package.json" in archivos else []
    declaradas = set(py)

    def elemento(nombre: str, regla: str, archivo: str, valor: str, catalogado) -> None:
        if catalogos is None:
            if ficha_duena(regla, archivo, valor):
                m.anotar(regla, archivo, valor)
            else:
                m.catalogables[nombre].add(valor.split(":", 1)[1] if nombre == "variables" else valor)
        elif not catalogado:
            m.anotar(regla, archivo, valor)

    cat_dep = set(catalogos["dependencias"]) if catalogos else set()
    for p in py:
        elemento("dependencias", "R1", "requirements.txt", f"python:{p}", f"python:{p}" in cat_dep)
    for p in npm:
        elemento("dependencias", "R1", "frontend/package.json", f"npm:{p}", f"npm:{p}" in cat_dep)

    cat_var = set(catalogos["variables"]) if catalogos else set()
    cat_srv = list(catalogos["servicios_externos"]) if catalogos else []
    cat_dsp = set(catalogos["despliegue"]) if catalogos else set()
    dominios_por_archivo: dict[str, set[str]] = {}
    for ruta in archivos:
        if es_codigo_de_producto(ruta):
            fuente = lee(ruta)
            for mod in imports_sin_dependencia(fuente, declaradas, locales):
                m.anotar("R1", ruta, f"import:{mod}")
            variables, usos = configuracion_del_modulo(fuente)
            for v in variables:
                elemento("variables", "R2", ruta, f"var:{v}", v in cat_var)
            for u in usos:
                m.anotar("R2", ruta, u)
            dominios_por_archivo[ruta] = dominios_del_modulo(fuente)
            for entrada in entradas_importadas(fuente):
                m.anotar("R4", ruta, f"entrada:{entrada}")
        elif es_manifiesto_de_dominios(ruta):
            dominios_por_archivo[ruta] = dominios_en_texto(lee(ruta))
        if es_archivo_de_despliegue(ruta):
            if catalogos is None:
                if ficha_duena("R4", ruta, "archivo"):
                    m.anotar("R4", ruta, "archivo")
                else:
                    m.catalogables["despliegue"].add(ruta)
            elif ruta not in cat_dsp:
                m.anotar("R4", ruta, "archivo")
        if es_archivo_de_despliegue(ruta) or ruta.endswith(".bat"):
            for entrada in entradas_en_texto(lee(ruta)):
                if entrada != ENTRADA_UNICA:
                    m.anotar("R4", ruta, f"entrada:{entrada}")
        if es_prueba(ruta):
            fuente = lee(ruta)
            for entrada in entradas_importadas(fuente):
                m.anotar("R4", ruta, f"entrada:{entrada}")
            literales, usa, llama = guardia_de_base(fuente)
            for lit in literales:
                m.anotar("R5", ruta, f"literal:{lit}")
            if usa and not llama:
                m.anotar("R5", ruta, "sin_guardia")
    for ruta, dominios in dominios_por_archivo.items():
        for d in dominios:
            elemento("servicios_externos", "R3", ruta, d, dominio_catalogado(d, cat_srv))
    if catalogos is None:
        m.catalogables["despliegue"].add(f"entrada:{ENTRADA_UNICA}")
    return m


_MOTIVOS = {
    "dependencias": "paquete que usa EVYDENTIA en Google Cloud o su cadena de pruebas",
    "servicios_externos": "dominio de Google Cloud, propio de EVYDENTIA o sitio oficial que el producto consulta",
    "variables": "variable de entorno que lee el código; se documenta en governance/operaciones/ENTORNO_LOCAL.md",
    "despliegue": "archivo de despliegue o de plataforma de Google Cloud, o de pruebas",
}


def generar() -> None:
    m = medir()
    DIR_PENDIENTES.mkdir(exist_ok=True)
    for nombre, ruta in CATALOGOS.items():
        cuerpo = "".join(f"{e}|{_MOTIVOS[nombre]}\n" for e in sorted(m.catalogables[nombre]))
        ruta.write_text(f"# RET-00 · catálogo cerrado de {nombre}. Formato elemento|motivo. Línea nueva: solo con "
                        f"motivo y fuera de un PR RET-.\n{cuerpo}", encoding="utf-8", newline="\n")
    por_ficha: dict[str, list[str]] = {f: [] for f in FICHAS_DUENAS}
    for k, ficha in sorted(m.incumplimientos.items()):
        por_ficha[ficha].append(k)
    for ficha, claves in por_ficha.items():
        (DIR_PENDIENTES / f"{ficha}.txt").write_text(
            f"# Pendientes de {ficha}. Formato regla|archivo|elemento; solo pueden decrecer contra origin/main.\n"
            + "".join(f"{c}\n" for c in claves), encoding="utf-8", newline="\n")
    print({n: len(v) for n, v in m.catalogables.items()}, {f: len(c) for f, c in por_ficha.items()})


if __name__ == "__main__":
    if "--generar" in sys.argv:
        generar()
