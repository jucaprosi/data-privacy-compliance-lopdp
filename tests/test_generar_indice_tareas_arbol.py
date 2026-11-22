"""ADPA-10 · R-PROP-EXISTE: la propiedad de cada ficha se comprueba contra el árbol (¤arbitro).

GOB-05: el generador es el del molde de ZERAG (governance/molde/generar_indice_tareas.py) con las
diferencias que LOPDP conserva; estas pruebas usan las funciones del molde (códigos de Hallazgo,
Exencion, tramitar_exenciones, leer_arbol_git) y suman las de los TICKETS 292 a 295 y 300.

Árbol sintético inyectado: salvo §7 y los repositorios temporales de §5, ninguna prueba toca el disco
ni git. Diseño en governance/apoyo/DISENO_PROPIEDAD_CONTRA_ARBOL.md (§2, reglas 1 a 4; §7).

Mutaciones que estas pruebas matan:
- M1: si validar_contra_arbol ignora las entradas con «#», falla test_m1_ruta_equivocada_con_seccion_sugiere_la_real.
- M2: si acepta como creadora a una ficha que no es ancestro, falla la prueba 2c.
- M3: si compara la marca solo por el nombre de archivo, falla la prueba 1a.
- CI-35 m1/m2: dar error con 0 fichas no hechas, o aceptar 0 fichas cargadas, hace fallar test_7a.
- GOB-05: tratar una exención caducada como aviso en modo árbitro, o no leer ZERAG_ARBITRO, hace
  fallar test_5e; comparar claves de configuración por archivo hace fallar test_8a.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_RUTA = Path(__file__).resolve().parent.parent / "scripts" / "generar_indice_tareas.py"
if "generar_indice_tareas" in sys.modules:
    git = sys.modules["generar_indice_tareas"]
else:
    _spec = importlib.util.spec_from_file_location("generar_indice_tareas", _RUTA)
    git = importlib.util.module_from_spec(_spec)
    sys.modules["generar_indice_tareas"] = git
    _spec.loader.exec_module(git)


def _t(tid, propiedad, depende=(), crea=(), siembra=(), estado="pendiente"):
    return git.Tarea(id=tid, titulo=tid, ola="A", estado=estado, sala="s", depende_de=tuple(depende),
                     propiedad=tuple(propiedad), arbitro="pytest", crea=tuple(crea), siembra=tuple(siembra))


def _hallazgos(tareas, archivos):
    """archivos: {ruta: contenido}. Devuelve los hallazgos de validar_contra_arbol."""
    return git.validar_contra_arbol(tareas, set(archivos), archivos.get, "HEAD abc1234")


def _errores(tareas, archivos):
    return [h for h in _hallazgos(tareas, archivos) if h.bloquea]


# 1 · sección en un archivo que existe ---------------------------------------------------------

def test_1a_seccion_sin_marca_rechaza():
    # M3: «otro/y.py» tiene la marca, pero «x/y.py» no; comparar por nombre la daría por buena
    archivos = {"x/y.py": "codigo\n", "otro/y.py": "# === A ===\n# === fin A ===\n"}
    errores = _errores([_t("A", ["x/y.py#A"])], archivos)
    assert [h.codigo for h in errores] == ["PROP_SIN_MARCA"] and "x/y.py" in errores[0].mensaje


def test_1b_seccion_con_marca_acepta():
    assert _errores([_t("A", ["x/y.py#A"])], {"x/y.py": "# === A ===\n# === fin A ===\n"}) == []


def test_1c_ancestro_que_siembra_acepta():
    u = _t("U", ["x/y.py"], siembra=["x/y.py#A"])
    a = _t("A", ["x/y.py#A"], depende=["U"])
    assert _errores([u, a], {"x/y.py": "codigo\n"}) == []


def test_1d_siembra_de_ficha_sin_relacion_rechaza():
    u = _t("U", ["x/y.py"], siembra=["x/y.py#A"])
    a = _t("A", ["x/y.py#A"])
    errores = {(h.ficha, h.codigo) for h in _errores([u, a], {"x/y.py": "codigo\n"})}
    assert ("A", "PROP_SIN_MARCA") in errores and ("U", "SIEMBRA_INCOHERENTE") in errores


# 2 · sección en un archivo que no existe --------------------------------------------------------

def test_2a_sin_creadora_rechaza():
    errores = _errores([_t("A", ["nuevo/z.py#A"])], {"otro.py": ""})
    assert [(h.codigo, h.ficha, h.entrada) for h in errores] == [("PROP_SIN_CREADORA", "A", "nuevo/z.py#A")]


def test_2b_ancestro_que_crea_y_siembra_acepta():
    u = _t("U", ["nuevo/z.py"], crea=["nuevo/z.py"], siembra=["nuevo/z.py#A"])
    a = _t("A", ["nuevo/z.py#A"], depende=["U"])
    assert _errores([u, a], {"otro.py": ""}) == []


def test_2c_creadora_sin_relacion_rechaza():  # M2
    u = _t("U", ["nuevo/z.py"], crea=["nuevo/z.py"], siembra=["nuevo/z.py#A"])
    a = _t("A", ["nuevo/z.py#A"])
    errores = _errores([u, a], {"otro.py": ""})
    assert any(h.ficha == "A" and h.codigo == "PROP_SIN_CREADORA" for h in errores)


# 3 · ruta equivocada con sugerencia (TICKET-293) ------------------------------------------------

def test_3_ruta_equivocada_sugiere_la_real():
    errores = _errores([_t("A", ["a/pantallas/i.tsx"])], {"a/layout/pantallas/i.tsx": ""})
    assert [h.codigo for h in errores] == ["PROP_RUTA_INEXISTENTE"]
    assert "¿quiso decir a/layout/pantallas/i.tsx?" in errores[0].mensaje


def test_m1_ruta_equivocada_con_seccion_sugiere_la_real():
    real = "frontend/src/components/layout/pantallas/index.tsx"
    archivos = {real: "// === MUT-01 ===\n// === fin MUT-01 ===\n"}
    errores = _errores([_t("MUT-01", ["frontend/src/components/pantallas/index.tsx#MUT-01"])], archivos)
    assert len(errores) == 1 and f"¿quiso decir {real}?" in errores[0].mensaje


def test_sala_nueva_sin_carpeta_padre_no_es_error():
    # ADPA-09: «formacion/domain/errores.py» no es una ruta equivocada de «organizacion/domain/errores.py»
    archivos = {"features/organizacion/domain/errores.py": ""}
    hallazgos = _hallazgos([_t("A", ["features/formacion/domain/errores.py"])], archivos)
    assert hallazgos and all(not h.bloquea for h in hallazgos)


def test_3b_la_ruta_que_crea_otra_tarea_abierta_no_se_sugiere():
    # TICKET-293: B declara «features/x/a.py» en su «crea»; A no recibe una sugerencia de otra sala
    archivos = {"features/y/a.py": ""}
    a = _t("A", ["features/x/a.py"])
    b = _t("B", ["features/x/a.py"], crea=["features/x/a.py"])
    hallazgos = [h for h in _hallazgos([a, b], archivos) if "A:" in h.mensaje]
    assert hallazgos and all(not h.bloquea and "la declara B" in h.mensaje for h in hallazgos)
    assert "features/y/a.py" not in " ".join(h.mensaje for h in hallazgos)


def test_3c_la_busqueda_por_nombre_base_se_limita_a_la_sala():
    rutas = {"features/y/a.py": "features/y/a.py", "features/x/b.py": "features/x/b.py"}
    assert git.sugerir_ruta("features/x/a.py", rutas) == ([], False)
    # sin carpeta base común (ruta en la raíz, que ya tiene archivos): el nombre base suelto no sale de su sala
    raiz = {"x.py": "x.py", "features/y/a.py": "features/y/a.py"}
    assert git.sugerir_ruta("a.py", raiz) == ([], False)


def test_creacion_implicita_solo_avisa_en_fase_1():
    hallazgos = git.validar_contra_arbol([_t("A", ["sala_nueva/x.py", "sala_nueva/**"])], {"otro.py"},
                                         lambda r: "")
    assert hallazgos and all(not h.bloquea for h in hallazgos)


# 4 · coherencia de «crea» ----------------------------------------------------------------------

def test_4a_crea_de_ruta_existente_rechaza():
    errores = _errores([_t("A", ["x.py"], crea=["x.py"])], {"x.py": ""})
    assert any(h.codigo == "CREA_YA_EXISTE" for h in errores)


def test_4a_bis_en_curso_su_propio_pr_ya_trae_el_archivo():
    # LOPDP conserva (diferencia con el molde): la ficha en curso que creó el archivo en su PR no falla
    assert _errores([_t("A", ["x.py"], crea=["x.py"], estado="en_curso")], {"x.py": ""}) == []


def test_4b_dos_creadoras_rechaza():
    errores = _errores([_t("A", ["n.py"], crea=["n.py"]), _t("B", ["n.py"], crea=["n.py"], depende=["A"])],
                       {"otro.py": ""})
    assert any(h.codigo == "CREA_DOBLE" for h in errores)


# 5 · exenciones con caducidad (TICKETS 294 y 300) ------------------------------------------------

def _ex(ficha, entrada, motivo="m", linea=1):
    return git.Exencion(ficha, entrada, motivo, linea)


def test_5a_exencion_nueva_frente_a_la_publicada():
    previas = [_ex("A", "x/y.py#A")]
    despues = previas + [_ex("B", "z.py#B", linea=2)]
    assert [e.clave for e in git.exenciones_nuevas(despues, previas)] == [("B", "z.py#B")]
    assert git.exenciones_nuevas(previas, despues) == []


def test_5b_vigente_se_conserva_y_resuelta_caduca():
    archivos = {"x/y.py": "codigo\n"}
    siguen, vigentes, caducadas = git.aplicar_exenciones(_hallazgos([_t("A", ["x/y.py#A"])], archivos),
                                                         [_ex("A", "x/y.py#A")])
    assert [h for h in siguen if h.bloquea] == [] and len(vigentes) == 1 and caducadas == []
    resuelto = {"x/y.py": "# === A ===\n"}
    siguen, vigentes, caducadas = git.aplicar_exenciones(_hallazgos([_t("A", ["x/y.py#A"])], resuelto),
                                                         [_ex("A", "x/y.py#A")])
    assert vigentes == [] and [e.clave for e in caducadas] == [("A", "x/y.py#A")]


def test_5c_formato_de_la_lista():
    exenciones, errores = git.leer_exenciones("# comentario\n\nA|x.py#A|motivo con | barra\nmala\n")
    assert [(e.ficha, e.entrada, e.motivo, e.linea) for e in exenciones] == [("A", "x.py#A", "motivo con | barra", 3)]
    assert errores and "l.4" in errores[0]  # una línea mal formada es un error


def _repo(tmp_path: Path, publicada: str, actual: str) -> Path:
    """Repositorio temporal: «publicada» en HEAD (la referencia) y «actual» en el disco, sin commit."""
    archivo = tmp_path / "governance" / "tareas" / git.ARCHIVO_EXENCIONES
    archivo.parent.mkdir(parents=True)
    archivo.write_text(publicada, encoding="utf-8", newline="\n")
    for orden in (["init", "-q"], ["add", "-A"],
                  ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "publicada"]):
        subprocess.run(["git", "-C", str(tmp_path), *orden], check=True, capture_output=True)
    archivo.write_text(actual, encoding="utf-8", newline="\n")
    return archivo


def _informe():
    return git.Informe(tareas=[], indice="", conflictos=[], base=git.Base(), errores=[], avisos=[], medidas={})


def _error_de(ficha, entrada):
    return git.Hallazgo("PROP_SIN_MARCA", f"{ficha}: sin marca", ficha=ficha, entrada=entrada)


LINEA = "A|x.py#A|motivo\n"


def test_5d_vigente_se_conserva_sin_avisos(tmp_path):
    _repo(tmp_path, LINEA, LINEA)
    informe = _informe()
    siguen = git.tramitar_exenciones(tmp_path, informe, [_error_de("A", "x.py#A")], True, "HEAD")
    assert siguen == [] and informe.errores == [] and informe.avisos == []
    assert informe.medidas["exenciones"]["vigentes"] == ["A|x.py#A"]


def test_5e_caducada_informa_en_local_y_falla_en_arbitro_sin_escribir(tmp_path):
    archivo = _repo(tmp_path, LINEA, LINEA)
    antes = archivo.read_bytes()
    local = _informe()
    git.tramitar_exenciones(tmp_path, local, [], git.modo_arbitro(False, {}), "HEAD")
    assert local.errores == [] and any("A|x.py#A" in a and "retire la línea 1" in a for a in local.avisos)
    for arbitro in (git.modo_arbitro(True, {}), git.modo_arbitro(False, {"ZERAG_ARBITRO": "1"})):
        informe = _informe()
        git.tramitar_exenciones(tmp_path, informe, [], arbitro, "HEAD")
        assert any("A|x.py#A" in e and "retire la línea 1" in e for e in informe.errores)
    assert archivo.read_bytes() == antes  # TICKET-300: el generador no escribe la lista


def test_5f_exencion_nueva_frente_a_la_referencia_falla_en_arbitro(tmp_path):
    _repo(tmp_path, "# sin exenciones\n", LINEA)
    arbitro, local = _informe(), _informe()
    git.tramitar_exenciones(tmp_path, arbitro, [_error_de("A", "x.py#A")], True, "HEAD")
    git.tramitar_exenciones(tmp_path, local, [_error_de("A", "x.py#A")], False, "HEAD")
    assert any("no está en HEAD" in e for e in arbitro.errores)
    assert local.errores == [] and any("no está en HEAD" in a for a in local.avisos)


def test_5g_referencia_que_no_resuelve_falla_en_arbitro(tmp_path):
    _repo(tmp_path, LINEA, LINEA)
    informe = _informe()
    git.tramitar_exenciones(tmp_path, informe, [_error_de("A", "x.py#A")], True, "no/existe")
    assert any("no resuelve" in e for e in informe.errores)


# 6 · cero fichas -------------------------------------------------------------------------------

def test_6_cero_fichas_cargadas_falla_e_informa_la_base():
    # CI-35 R2: sin ninguna ficha es un fallo del lector, no un estado del proyecto
    errores = git.validar([], arbol={"x.py"}, leer=lambda r: "", base="HEAD abc1234")
    assert len(errores) == 1 and "Base: HEAD abc1234" in errores[0]
    # CI-35 R1: todas en «hecha» es un estado legítimo
    hechas = git.validar([_t("A", ["x.py"], estado="hecha")], arbol={"x.py"}, leer=lambda r: "", base="HEAD abc1234")
    assert hechas == []


def test_validar_sin_arbol_no_cambia():
    assert git.validar([_t("A", ["no/existe.py#A"])]) == []


# 7 · el repositorio real ------------------------------------------------------------------------
# Corre R-PROP-EXISTE sobre el árbol real (git ls-tree de HEAD) con la lista de exenciones real.
# No necesita .env ni base de datos.

def _real():
    tareas, errores = git.cargar_tareas()
    leido, motivo = git.leer_arbol_git(git.RAIZ)
    assert leido is not None, motivo
    sha, rutas = leido
    errores += git.validar(tareas, arbol=set(rutas), leer=lambda r: git.leer_archivo_git(git.RAIZ, r),
                           base=f"HEAD {sha}", raiz=git.RAIZ)
    return errores, f"HEAD {sha}", tareas, rutas


def test_7a_la_propiedad_real_cumple_contra_el_arbol():
    # CI-35 R3: muestra sintética fija, válida tenga main 0 o más fichas pendientes
    archivos = {"x.py": "", "y.py": ""}
    hechas = [_t("A", ["x.py"], estado="hecha"), _t("B", ["y.py"], depende=["A"], estado="hecha")]
    # m1: volver a dar error con 0 fichas no hechas
    assert git.validar_contra_arbol(hechas, set(archivos), archivos.get, "HEAD abc1234") == []
    # m2: aceptar una lista vacía (lector roto)
    vacia = git.validar_contra_arbol([], set(archivos), archivos.get, "HEAD abc1234")
    assert [h.bloquea for h in vacia] == [True] and "Base: HEAD abc1234" in vacia[0].mensaje
    # y con las fichas reales, sin fijar cuántas siguen pendientes
    errores, base, _, _ = _real()
    assert errores == [], f"Base: {base}\n" + "\n".join(errores)


def test_7b_una_exencion_obsoleta_en_la_lista_real_caduca():
    _, base, tareas, rutas = _real()
    hallazgos = git.validar_contra_arbol(tareas, rutas, lambda r: git.leer_archivo_git(git.RAIZ, r), base)
    _, _, caducadas = git.aplicar_exenciones(hallazgos, [_ex("ADPA-10", "no/existe.py#ADPA-10")])
    assert [e.texto() for e in caducadas] == ["ADPA-10|no/existe.py#ADPA-10"]


def test_7c_el_arnes_por_salas_elige_esta_prueba_aunque_solo_cambie_una_sala():
    # Árbitro de repositorio: un PR que solo toca features/diagnostico/** también la corre.
    spec = importlib.util.spec_from_file_location("seleccionar_pruebas", _RUTA.parent / "seleccionar_pruebas.py")
    sel = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("seleccionar_pruebas", sel)
    spec.loader.exec_module(sel)
    eleccion = sel.seleccionar(["features/diagnostico/diagnostico_service.py"])
    assert eleccion.modo == "salas"
    assert "tests/test_generar_indice_tareas_arbol.py" in eleccion.pruebas
    assert "tests/test_indice_tareas.py" in eleccion.pruebas


# 8 · claves de configuración (TICKET-295) -------------------------------------------------------

def test_8a_claves_distintas_de_un_archivo_de_configuracion_no_chocan():
    a, b = _t("A", ["config.yml#cache"]), _t("B", ["config.yml#db"])
    conflictos, _ = git.encontrar_conflictos([a, b], git._ancestros([a, b]))
    assert conflictos == []
    c = _t("C", ["config.yml#cache"])
    conflictos, _ = git.encontrar_conflictos([a, c], git._ancestros([a, c]))
    assert [(x.a, x.b) for x in conflictos] == [("A", "C")]


def test_8b_un_archivo_que_no_se_analiza_se_posee_entero():
    assert git.claves_de_configuracion("c.yml", "cache: 1\ndb:\n  x: 2\n") == frozenset({"cache", "db"})
    assert git.claves_de_configuracion("c.yml", "- a\n- b\n") is None
    assert git.se_pisan("c.yml#cache", "c.yml#db", frozenset({"c.yml"}))
    assert not git.se_pisan("c.yml#cache", "c.yml#db")


def test_8c_la_clave_de_configuracion_no_necesita_marca():
    assert _errores([_t("A", ["config.yml#cache"])], {"config.yml": "cache: 1\n"}) == []


# 9 · cabecera de imports compartida (TICKET-292) -------------------------------------------------

DOS_SECCIONES = ('"""Módulo con dos secciones."""\nimport os\n\n\n'
                 "# === A ===\ndef a():\n    return os.sep\n# === fin A ===\n\n\n"
                 "# === B ===\ndef b():\n    return a()\n# === fin B ===\n")


def test_9a_los_imports_en_la_cabecera_no_avisan():
    assert git.imports_dentro_de_secciones(DOS_SECCIONES) == []
    mal = DOS_SECCIONES.replace("# === B ===\n", "# === B ===\nimport sys  # noqa: E402\n")
    linea = mal.split("\n").index("import sys  # noqa: E402") + 1
    assert git.imports_dentro_de_secciones(mal) == [linea]
    avisos = _hallazgos([_t("A", ["m.py#A"]), _t("B", ["m.py#B"])], {"m.py": mal})
    assert [h.codigo for h in avisos] == ["IMPORT_EN_SECCION"] and not avisos[0].bloquea


def _ruff():
    if shutil.which("ruff"):
        return ["ruff"]
    if importlib.util.find_spec("ruff") is not None:
        return [sys.executable, "-m", "ruff"]
    return None


def test_9b_dos_secciones_con_imports_en_la_cabecera_pasan_ruff_sin_noqa(tmp_path):
    ruff = _ruff()
    if ruff is None:
        pytest.skip("ruff no está instalado en este entorno")
    archivo = tmp_path / "m.py"
    archivo.write_text(DOS_SECCIONES, encoding="utf-8", newline="\n")
    assert "noqa" not in DOS_SECCIONES
    r = subprocess.run([*ruff, "check", "--no-cache", "--isolated", "--select", "E402,F401,F821", str(archivo)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
