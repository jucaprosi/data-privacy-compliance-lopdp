"""Cero SQL interpolado y una sola fuente de sesión de BD (análisis AST, sin BD).

Habilita INV_LOPDP_SESSION_SINGLE_SOURCE. Una sentencia SQL llega a la BD solo como texto
literal con parámetros enlazados; un valor de petición nunca se concatena en ella.
"""
import ast
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETAS_EXCLUIDAS = {".venv", "venv", "node_modules", ".git", "__pycache__", "frontend", ".next"}
LLAMADAS_SQL = {"text", "execute", "exec_driver_sql"}

# Exenciones declaradas como datos, una por archivo y con su motivo. Un archivo exento que
# deja de tener hallazgos hace fallar la prueba: la exención caduca con el código que cubría.
EXENCIONES = {
    "alembic/versions/20261005_roadmaps.py": (
        "Migración DDL: el nombre de tabla sale de una tupla constante del módulo y PostgreSQL "
        "no admite parámetros enlazados en identificadores."
    ),
    "alembic/versions/20261008_app_role_rls.py": (
        "Migración DDL: tablas y rol salen de constantes del módulo; GRANT/POLICY no admiten "
        "parámetros enlazados en identificadores."
    ),
}


def _constantes_de_modulo(arbol: ast.Module) -> set[str]:
    """Nombres de módulo asignados a un literal de texto o a una colección de literales."""
    constantes = set()
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign) and len(nodo.targets) == 1 and isinstance(nodo.targets[0], ast.Name):
            valor = nodo.value
            es_literal = isinstance(valor, ast.Constant) and isinstance(valor.value, str)
            es_coleccion = isinstance(valor, (ast.Tuple, ast.List)) and all(
                isinstance(e, ast.Constant) for e in valor.elts
            )
            if es_literal or es_coleccion:
                constantes.add(nodo.targets[0].id)
    return constantes


def hallazgos_de(codigo: str, nombre: str = "<codigo>") -> list[str]:
    """Sentencias SQL construidas con valores que no son constantes de módulo."""
    arbol = ast.parse(codigo, filename=nombre)
    constantes = _constantes_de_modulo(arbol)
    encontrados = []
    for nodo in ast.walk(arbol):
        if not (isinstance(nodo, ast.Call) and nodo.args):
            continue
        funcion = nodo.func
        nombre_llamada = funcion.id if isinstance(funcion, ast.Name) else getattr(funcion, "attr", "")
        if nombre_llamada not in LLAMADAS_SQL:
            continue
        sentencia = nodo.args[0]
        motivo = None
        if isinstance(sentencia, ast.JoinedStr):
            sueltos = [
                ast.unparse(v.value)
                for v in sentencia.values
                if isinstance(v, ast.FormattedValue)
                and not (isinstance(v.value, ast.Name) and v.value.id in constantes)
            ]
            if sueltos:
                motivo = f"f-string con {', '.join(sueltos)}"
        elif isinstance(sentencia, ast.BinOp) and isinstance(sentencia.op, ast.Mod):
            motivo = "formato con %"
        elif isinstance(sentencia, ast.BinOp) and isinstance(sentencia.op, ast.Add):
            partes = [sentencia.left, sentencia.right]
            if not all(isinstance(p, ast.Constant) and isinstance(p.value, str) for p in partes):
                motivo = "concatenación con valores no literales"
        elif (
            isinstance(sentencia, ast.Call)
            and isinstance(sentencia.func, ast.Attribute)
            and sentencia.func.attr == "format"
        ):
            motivo = "str.format"
        if motivo:
            encontrados.append(f"{nombre}:{nodo.lineno} {nombre_llamada}(): {motivo}")
    return encontrados


def _archivos_py():
    for base, dirs, files in os.walk(RAIZ):
        dirs[:] = [d for d in dirs if d not in CARPETAS_EXCLUIDAS]
        for archivo in files:
            if archivo.endswith(".py"):
                yield os.path.join(base, archivo)


def _hallazgos_por_archivo() -> dict[str, list[str]]:
    resultado = {}
    for ruta in _archivos_py():
        rel = os.path.relpath(ruta, RAIZ).replace(os.sep, "/")
        with open(ruta, "r", encoding="utf-8") as f:
            encontrados = hallazgos_de(f.read(), rel)
        if encontrados:
            resultado[rel] = encontrados
    return resultado


# --- El detector detecta: sin estas pruebas, un detector que no ve nada daría un falso verde ---

def test_detector_marca_fstring_con_variable():
    assert hallazgos_de('def f(t):\n    return text(f"SET LOCAL x = \'{t}\'")\n')


def test_detector_marca_format_porcentaje_y_concatenacion():
    assert hallazgos_de('def f(t):\n    return text("SELECT %s" % t)\n')
    assert hallazgos_de('def f(t):\n    return text("SELECT " + t)\n')
    assert hallazgos_de('def f(t):\n    return text("SELECT {}".format(t))\n')


def test_detector_marca_execute_con_fstring():
    assert hallazgos_de('def f(c, t):\n    c.execute(f"DROP TABLE {t}")\n')


def test_detector_acepta_parametros_enlazados_y_constantes_de_modulo():
    assert not hallazgos_de('def f():\n    return text("SELECT set_config(\'a\', :v, true)")\n')
    assert not hallazgos_de('TABLA = "areas"\ndef f():\n    return text(f"TRUNCATE {TABLA}")\n')
    assert not hallazgos_de('def f():\n    return text("SELECT " "1")\n')


def test_detector_no_acepta_una_variable_local_que_se_llama_como_constante():
    assert hallazgos_de('def f():\n    TABLA = input()\n    return text(f"TRUNCATE {TABLA}")\n')


# --- Invariante real sobre el repositorio ---

def test_ninguna_sentencia_sql_se_construye_con_valores_dinamicos():
    por_archivo = _hallazgos_por_archivo()
    sin_exencion = {a: h for a, h in por_archivo.items() if a not in EXENCIONES}
    assert not sin_exencion, "SQL interpolado:\n" + "\n".join(
        linea for hs in sin_exencion.values() for linea in hs
    )


def test_cada_exencion_sigue_cubriendo_un_hallazgo():
    por_archivo = _hallazgos_por_archivo()
    caducadas = [a for a in EXENCIONES if a not in por_archivo]
    assert not caducadas, f"Exenciones sin hallazgo que cubrir (elimínalas): {caducadas}"
    assert all(EXENCIONES.values()), "Toda exención lleva su motivo"


def test_una_sola_fuente_de_sesion_de_bd():
    """INV_LOPDP_SESSION_SINGLE_SOURCE: un único módulo crea el motor y la fábrica de sesiones."""
    assert not os.path.exists(os.path.join(RAIZ, "app_core", "database.py")), "app_core/database.py debe estar eliminado"
    creadores = []
    for ruta in _archivos_py():
        rel = os.path.relpath(ruta, RAIZ).replace(os.sep, "/")
        if rel.startswith("tests/") or rel.startswith("alembic/"):
            continue
        with open(ruta, "r", encoding="utf-8") as f:
            arbol = ast.parse(f.read(), filename=rel)
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Call):
                f_ = nodo.func
                n = f_.id if isinstance(f_, ast.Name) else getattr(f_, "attr", "")
                if n in {"create_async_engine", "async_sessionmaker"}:
                    creadores.append(rel)
    assert set(creadores) == {"app_core/db/session.py"}, f"Fuentes de sesión: {sorted(set(creadores))}"
