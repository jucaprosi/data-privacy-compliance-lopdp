# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""El reparto en tandas, leído de las fichas (GOB-06): las de una tanda no se pisan y van después de lo que necesitan."""
import importlib.util
import subprocess
import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("verificar_reparto", _RAIZ / "scripts" / "verificar_reparto.py")
vr = importlib.util.module_from_spec(_spec)
sys.modules["verificar_reparto"] = vr
_spec.loader.exec_module(vr)
indice = vr._cargar_indice()


def _t(tid, propiedad, depende=(), estado="pendiente", tanda=None):
    return indice.Tarea(id=tid, titulo=tid, ola="A", estado=estado, sala="s", depende_de=tuple(depende),
                        propiedad=tuple(propiedad), arbitro="pytest", tanda=tanda)


def test_el_reparto_real_es_valido():
    tareas, errores = indice.cargar_tareas()
    assert errores == []
    assert vr.revisar(tareas, indice) == []
    # GOB-06 R6: las fichas de las tandas 93 a 96 que siguen sin hacer llevan su tanda (FE-29, la 93, ya está hecha)
    esperadas = {"IA-13": 94, "IA-14": 95, "IA-15": 96, "GCP-08c": 95, "IA-16": 96, "IA-17": 95, "DEMO-09": 97, "GEN-01": 99, "GEN-02": 100, "GEN-03": 100, "GEN-07": 100, "GEN-05": 101, "GEN-06": 101, "LEG-08": 101, "BIB-403": 102, "DEMO-12": 106, "BIB-405": 107, "BIB-406": 108, "BIB-409": 108, "BIB-407": 109, "BIB-410": 109, "NORM-07": 110, "NOTIF-02": 112, "BIB-408": 110, "NOTIF-03": 113, "OPE-01": 112, "BIB-413": 112, "BIB-411": 113, "BIB-412": 114, "BIB-414": 115, "NOTIF-04": 115, "BIB-415": 111, "OPE-02": 112, "FE-31": 116, "NOTIF-05": 116, "QA-14": 115, "QA-15": 116, "QA-16": 116, "GOB-07": 113, "FE-32": 117, "FE-40": 117, "FE-33": 118, "FE-34": 118, "FE-35": 118, "FE-36": 118, "FE-37": 119, "FE-38": 119, "FE-39": 119, "ARR-01": 121, "ARR-02": 121, "ARR-03": 121, "ARR-04": 122}
    por_id = {t.id: t for t in tareas}
    vivas = [tid for tid in esperadas if por_id[tid].estado != "hecha"]
    assert {tid: por_id[tid].tanda for tid in vivas} == {tid: esperadas[tid] for tid in vivas}
    salida = subprocess.run([sys.executable, str(_RAIZ / "scripts" / "verificar_reparto.py"), "--tandas"],
                            cwd=_RAIZ, capture_output=True, text=True, encoding="utf-8")
    assert salida.returncode == 0, salida.stdout
    assert vr.vista_de_tandas(tareas) == [l for l in salida.stdout.splitlines() if l.startswith("Tanda ")]


def test_r3_misma_tanda_no_se_pisa():
    comun = [_t("A-1", ["f/**"], tanda=2), _t("B-1", ["f/x.py"], tanda=2)]
    assert vr.revisar(comun, indice) == ["R3 A-1 y B-1 (tanda 2) escriben «f/**» / «f/x.py»"]
    # m1: sin mirar la `tanda`, dos fichas de tandas distintas también chocarían
    assert vr.revisar([_t("A-1", ["f/**"], tanda=2), _t("B-1", ["f/x.py"], tanda=3, depende=["A-1"])], indice) == []
    secciones = [_t("C-1", ["g.py#C"], tanda=3), _t("D-1", ["g.py#D"], tanda=3)]
    assert vr.revisar(secciones, indice) == []
    # sin tanda, o hecha, no se planifica y no cuenta para R3
    assert vr.revisar([_t("A-1", ["f/**"], tanda=2), _t("B-1", ["f/x.py"])], indice) == []
    assert vr.revisar([_t("A-1", ["f/**"], tanda=2), _t("B-1", ["f/x.py"], tanda=2, estado="hecha")], indice) == []


def test_r4_dependencia_antes():
    def caso(tanda_dep, estado_dep="pendiente"):
        return vr.revisar([_t("A-1", ["a.py"], tanda=tanda_dep, estado=estado_dep),
                           _t("B-1", ["b.py"], depende=["A-1"], tanda=2)], indice)
    assert caso(3) == ["R4 B-1 (tanda 2) depende de A-1 (tanda 3), que no está hecha ni va antes"]
    assert caso(2) == ["R4 B-1 (tanda 2) depende de A-1 (tanda 2), que no está hecha ni va antes"]  # m2
    assert caso(None) == ["R4 B-1 (tanda 2) depende de A-1 (sin tanda), que no está hecha ni va antes"]
    assert caso(1) == []
    assert caso(None, "hecha") == []


def test_el_diff_de_una_rama_debe_caber_en_su_propiedad():
    bloque = vr.bloque_de_ficha(_t("A-1", ["f/**", "g.py#C"]))
    assert vr.revisar_diff(["f/dentro/x.py", "g.py"], bloque, indice) == []
    assert vr.revisar_diff(["f/x.py", "ajeno.py"], bloque, indice) == ["R5 A-1: «ajeno.py» está fuera de su «Escribe»"]


def test_ninguna_tanda_supera_cuatro_fichas():
    tareas, _ = indice.cargar_tareas()
    por_tanda: dict[int, list[str]] = {}
    for t in vr.planificadas(tareas):
        por_tanda.setdefault(t.tanda, []).append(t.id)
    excesos = {t: ids for t, ids in por_tanda.items() if len(ids) > 4}
    assert excesos == {}, f"Tandas con más de 4 fichas en paralelo: {excesos}"


def test_ci26_m2_reparto_rama_con_tilde_no_da_hallazgo_r5(tmp_path, monkeypatch):
    import os, subprocess
    env = dict(os.environ, GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@e.com',
               GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@e.com')
    subprocess.run(['git', 'init'], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(['git', 'checkout', '-b', 'main'], cwd=tmp_path, check=True, capture_output=True)
    f = tmp_path / 'governance' / 'Metodología de trabajo.md'
    f.parent.mkdir(parents=True)
    f.write_text('v1', encoding='utf-8')
    subprocess.run(['git', 'add', '.'], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(['git', 'commit', '-m', 'base'], cwd=tmp_path, env=env, check=True, capture_output=True)
    subprocess.run(['git', 'checkout', '-b', 'tarea/juan-carlos/ci-26'], cwd=tmp_path, check=True, capture_output=True)
    f.write_text('v2', encoding='utf-8')
    subprocess.run(['git', 'commit', '-am', 'mod'], cwd=tmp_path, env=env, check=True, capture_output=True)

    ruta_tilde = "governance/Metodología de trabajo.md"
    bloque = vr.Bloque("CI-26", 77, ["CI-26"], [ruta_tilde])
    monkeypatch.setattr(vr, "RAIZ", tmp_path)

    # Con el lector real, no da hallazgo
    archivos = vr._archivos_del_diff("tarea/juan-carlos/ci-26", "main")
    assert vr.revisar_diff(archivos, bloque, indice) == []

    # Mutación m2: lector sin core.quotepath=off deja la ruta entre comillas y R5 falla
    salida_sin_quotepath = subprocess.run(["git", "diff", "--name-only", "main...tarea/juan-carlos/ci-26"],
                                          cwd=tmp_path, capture_output=True, text=True, check=True).stdout
    archivos_mutados = [l.strip() for l in salida_sin_quotepath.splitlines() if l.strip()]
    hallazgos = vr.revisar_diff(archivos_mutados, bloque, indice)
    assert len(hallazgos) == 1
    assert "está fuera de su «Escribe»" in hallazgos[0]


# --------------------------------------------------------------------------- CI-33

def _ficha_ci33(tid, propiedad=(), estado="en_curso"):
    lista = ", ".join(f'"{p}"' for p in propiedad)
    return (f'+++\nid = "{tid}"\ntitulo = "t"\nola = "backlog"\nestado = "{estado}"\nsala = "s"\n'
            f'depende_de = []\npropiedad = [{lista}]\ncrea = []\narbitro = "pytest"\n+++\n\n# {tid}\n')


_SECCIONADO = "cabecera\n# === BL-01 ===\nx = 1\n# === fin BL-01 ===\npie 1\npie 2\n"


def _repo_ci33(tmp_path, base: dict, rama: dict):
    """Repositorio temporal con `main` (archivos `base`) y la rama `tarea/x` (`rama`; None borra el archivo)."""
    import os
    import subprocess
    env = dict(os.environ, GIT_AUTHOR_NAME="T", GIT_AUTHOR_EMAIL="t@e.com",
               GIT_COMMITTER_NAME="T", GIT_COMMITTER_EMAIL="t@e.com")

    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, env=env, check=True, capture_output=True)

    def escribir(archivos):
        for ruta, texto in archivos.items():
            f = tmp_path / ruta
            if texto is None:
                f.unlink()
                continue
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(texto.encode("utf-8"))

    tmp_path.mkdir(parents=True, exist_ok=True)
    git("init")
    git("checkout", "-b", "main")
    escribir({"LEEME.md": "repo\n", **base})
    git("add", "-A")
    git("commit", "-m", "base")
    git("checkout", "-b", "tarea/x")
    escribir(rama)
    git("add", "-A")
    git("commit", "-m", "rama")
    return tmp_path


def _r5_ci33(tmp_path, monkeypatch, bloque, base, rama):
    monkeypatch.setattr(vr, "RAIZ", _repo_ci33(tmp_path, base, rama))
    return vr.revisar_rama("tarea/x", "main", bloque, indice)


def test_ci33_ficha_propia(tmp_path, monkeypatch):
    bloque = vr.Bloque("BL-01", 0, ["BL-01"], ["a.py"])
    hallazgos = _r5_ci33(tmp_path, monkeypatch, bloque,
                         {"governance/tareas/BL-01.md": _ficha_ci33("BL-01", estado="pendiente")},
                         {"governance/tareas/BL-01.md": _ficha_ci33("BL-01"), "a.py": "x = 1\n"})
    assert hallazgos == []


def test_ci33_ficha_ajena(tmp_path, monkeypatch):
    bloque = vr.Bloque("BL-01", 0, ["BL-01"], ["a.py"])
    hallazgos = _r5_ci33(tmp_path, monkeypatch, bloque, {"governance/tareas/OT-01.md": _ficha_ci33("OT-01")},
                         {"governance/tareas/OT-01.md": _ficha_ci33("OT-01", estado="bloqueada")})
    assert hallazgos == ["R5 BL-01: «governance/tareas/OT-01.md» está fuera de su «Escribe»"]


def test_ci33_tasks_no_es_de_cierre(tmp_path, monkeypatch):
    bloque = vr.Bloque("BL-01", 0, ["BL-01"], ["a.py"])
    hallazgos = _r5_ci33(tmp_path, monkeypatch, bloque, {}, {"governance/artefactos/TASKS.md": "t\n"})
    assert hallazgos == ["R5 BL-01: «governance/artefactos/TASKS.md» está fuera de su «Escribe»"]


def test_ci33_seccion_por_sembrar(tmp_path, monkeypatch):
    bloque = vr.Bloque("BL-01", 0, ["BL-01"], ["a.py"])
    hallazgos = _r5_ci33(
        tmp_path, monkeypatch, bloque,
        {"governance/tareas/BL-01.md": _ficha_ci33("BL-01", ["a.py"]), "b.py": _SECCIONADO},
        {"governance/tareas/BL-01.md": _ficha_ci33("BL-01", ["a.py", "b.py#BL-01"]),
         "b.py": _SECCIONADO.replace("x = 1\n", "x = 2\ny = 3\n")})
    assert hallazgos == []


def test_ci33_linea_fuera_de_la_seccion(tmp_path, monkeypatch):
    bloque = vr.Bloque("BL-01", 0, ["BL-01"], ["a.py"])
    ficha = {"governance/tareas/BL-01.md": _ficha_ci33("BL-01", ["a.py", "b.py#BL-01"])}
    mensaje = ["R5 BL-01: «b.py» cambia líneas fuera de la sección BL-01"]
    cambiada = _r5_ci33(tmp_path / "cambia", monkeypatch, bloque, {"b.py": _SECCIONADO},
                        {**ficha, "b.py": _SECCIONADO.replace("pie 1", "pie cambiado")})
    borrada = _r5_ci33(tmp_path / "borra", monkeypatch, bloque, {"b.py": _SECCIONADO},
                       {**ficha, "b.py": _SECCIONADO.replace("pie 1\n", "")})
    assert cambiada == mensaje
    assert borrada == mensaje


def test_ci33_borrado_dentro_de_la_seccion_es_valido():
    """El borrado puro da la línea siguiente; dentro de la sección, esa línea es la de cierre como mucho."""
    assert vr.rango_de_seccion(_SECCIONADO, "BL-01") == (2, 4)
    assert vr.rango_de_seccion("--- INICIO X-1 ---\na\n--- FIN X-1 ---\n", "X-1") == (1, 3)
    assert vr.rango_de_seccion(_SECCIONADO, "OT-01") is None


def test_ci33_seccion_sin_marca(tmp_path, monkeypatch):
    bloque = vr.Bloque("BL-01", 0, ["BL-01"], ["a.py"])
    hallazgos = _r5_ci33(tmp_path, monkeypatch, bloque, {"b.py": "sin marcas\n"},
                         {"governance/tareas/BL-01.md": _ficha_ci33("BL-01", ["a.py", "b.py#BL-01"]),
                          "b.py": "sin marcas, cambiado\n"})
    assert hallazgos == ["R5 BL-01: «b.py» no tiene la sección BL-01"]


def test_ci33_ficha_propia_hecha(tmp_path, monkeypatch):
    bloque = vr.Bloque("BL-01", 0, ["BL-01"], ["a.py"])
    hallazgos = _r5_ci33(tmp_path, monkeypatch, bloque, {"governance/tareas/BL-01.md": _ficha_ci33("BL-01")},
                         {"governance/tareas/BL-01.md": _ficha_ci33("BL-01", estado="hecha")})
    assert hallazgos == ["R5 BL-01: «governance/tareas/BL-01.md» pasa a hecha; el cierre lo hace el coordinador"]


def test_ci33_bloque_con_dos_tareas(tmp_path, monkeypatch):
    bloque = vr.Bloque("BL-01", 0, ["BL-01", "BL-02"], ["a.py"])
    hallazgos = _r5_ci33(tmp_path, monkeypatch, bloque,
                         {"governance/tareas/BL-01.md": _ficha_ci33("BL-01", estado="pendiente"),
                          "governance/tareas/BL-02.md": _ficha_ci33("BL-02", estado="pendiente")},
                         {"governance/tareas/BL-01.md": _ficha_ci33("BL-01"),
                          "governance/tareas/BL-02.md": _ficha_ci33("BL-02")})
    assert hallazgos == []
