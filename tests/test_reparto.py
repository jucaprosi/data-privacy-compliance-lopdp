# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""El reparto en bloques de los briefs coincide con las tasks y los bloques de una tanda no se pisan."""
import importlib.util
import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("verificar_reparto", _RAIZ / "scripts" / "verificar_reparto.py")
vr = importlib.util.module_from_spec(_spec)
sys.modules["verificar_reparto"] = vr
_spec.loader.exec_module(vr)
indice = vr._cargar_indice()


def _t(tid, propiedad, depende=(), estado="pendiente", agente="asignable"):
    return indice.Tarea(id=tid, titulo=tid, ola="A", estado=estado, sala="s", depende_de=tuple(depende),
                        propiedad=tuple(propiedad), arbitro="pytest", agente=agente)


def _bloque(bid, tanda, tareas, escribe):
    cuerpo = "".join(f"{i}. `{t}` — x\n" for i, t in enumerate(tareas, 1))
    rutas = "".join(f"  - `{e}`\n" for e in escribe)
    return f"### {bid} · nombre  (tanda {tanda})\n\n**Objetivo** (en este orden):\n\n{cuerpo}\n**Rastro ¤**\n\n**Escribe** (lista):\n\n{rutas}\n**No hagas:**\n\n"


def _briefs(*bloques):
    return "".join(bloques)


def test_el_reparto_real_es_valido():
    tareas, errores = indice.cargar_tareas()
    briefs = vr.BRIEFS.read_text(encoding="utf-8")
    assert errores == []
    assert vr.revisar(briefs, tareas, indice) == []


def test_una_task_hecha_o_repetida_o_sin_bloque_se_rechaza():
    tareas = [_t("A-1", ["a.py"]), _t("B-1", ["b.py"], agente="ninguno"), _t("C-1", ["c.py"]),
              _t("D-1", ["d.py"], estado="hecha")]
    briefs = _briefs(_bloque("BL-01", 0, ["A-1", "D-1"], ["a.py", "d.py"]),
                     _bloque("BL-02", 1, ["A-1", "Q-9"], ["a.py"]))
    hallazgos = vr.revisar(briefs, tareas, indice)
    assert "R1 D-1: está hecha y figura en BL-01" in hallazgos
    assert "R1 A-1: debe figurar en un solo bloque y figura en 2 (BL-01, BL-02)" in hallazgos
    assert "R1 Q-9: los briefs citan una task que no existe" in hallazgos
    assert "R1 C-1: debe figurar en un solo bloque y figura en 0" in hallazgos
    assert not [h for h in hallazgos if h.startswith("R1 B-1")]  # `agente = "ninguno"` cuenta como ubicación


def test_escribe_debe_ser_exactamente_la_propiedad_de_sus_tasks():
    tareas = [_t("A-1", ["a.py", "b.py"])]
    briefs = _briefs(_bloque("BL-01", 0, ["A-1"], ["a.py", "ajeno.py"]))
    assert vr.revisar(briefs, tareas, indice) == [
        "R2 BL-01: «b.py» es propiedad de sus tasks y no está en «Escribe»",
        "R2 BL-01: «ajeno.py» está en «Escribe» y no es propiedad de ninguna de sus tasks",
    ]


def test_dos_bloques_de_una_tanda_no_escriben_el_mismo_archivo_salvo_secciones_distintas():
    tareas = [_t("A-1", ["f/**"]), _t("B-1", ["f/x.py"]), _t("C-1", ["g.py#C"]), _t("D-1", ["g.py#D"])]
    mismo = _briefs(_bloque("BL-01", 2, ["A-1"], ["f/**"]), _bloque("BL-02", 2, ["B-1"], ["f/x.py"]),
                    _bloque("BL-03", 3, ["C-1"], ["g.py#C"]), _bloque("BL-04", 3, ["D-1"], ["g.py#D"]))
    assert vr.revisar(mismo, tareas, indice) == ["R3 BL-01 y BL-02 (tanda 2) escriben «f/**» / «f/x.py»"]
    distinta_tanda = _briefs(_bloque("BL-01", 2, ["A-1"], ["f/**"]), _bloque("BL-02", 3, ["B-1"], ["f/x.py"]),
                             _bloque("BL-03", 3, ["C-1"], ["g.py#C"]), _bloque("BL-04", 3, ["D-1"], ["g.py#D"]))
    assert vr.revisar(distinta_tanda, tareas, indice) == []


def test_una_dependencia_debe_ir_antes_o_estar_hecha():
    tareas = [_t("A-1", ["a.py"]), _t("B-1", ["b.py"], depende=["A-1"]), _t("C-1", ["c.py"], depende=["Z-1"]),
              _t("Z-1", ["z.py"], estado="hecha")]
    tarde = _briefs(_bloque("BL-01", 1, ["B-1"], ["b.py"]), _bloque("BL-02", 1, ["A-1"], ["a.py"]),
                    _bloque("BL-03", 2, ["C-1"], ["c.py"]))
    assert vr.revisar(tarde, tareas, indice) == [
        "R4 B-1 (BL-01, tanda 1) depende de A-1, que no va antes ni en una tanda anterior"]
    orden = _briefs(_bloque("BL-01", 1, ["B-1", "A-1"], ["a.py", "b.py"]), _bloque("BL-02", 2, ["C-1"], ["c.py"]))
    assert vr.revisar(orden, tareas, indice) == [
        "R4 B-1 (BL-01, tanda 1) depende de A-1, que no va antes ni en una tanda anterior"]
    bien = _briefs(_bloque("BL-01", 0, ["A-1"], ["a.py"]), _bloque("BL-02", 1, ["B-1"], ["b.py"]),
                   _bloque("BL-03", 2, ["C-1"], ["c.py"]))
    assert vr.revisar(bien, tareas, indice) == []


def test_el_diff_de_una_rama_debe_caber_en_su_escribe():
    bloque = vr.Bloque("BL-01", 0, ["A-1"], ["f/**", "g.py#C"])
    assert vr.revisar_diff(["f/dentro/x.py", "g.py"], bloque, indice) == []
    assert vr.revisar_diff(["f/x.py", "ajeno.py"], bloque, indice) == ["R5 BL-01: «ajeno.py» está fuera de su «Escribe»"]


def test_agente_ninguno_admite_ids_con_sufijo_de_letra():
    # DEMO-03f (PRD EVYDENTIA §5.6.8) no se asigna a un agente: lo dice su ficha, no la portada (CI-31).
    tareas = [_t("DEMO-03f", ["features/videovigilancia/x.py"], agente="ninguno")]
    assert vr.revisar(_briefs(), tareas, indice) == []

def test_ninguna_tanda_supera_cuatro_bloques():
    briefs = vr.BRIEFS.read_text(encoding="utf-8")
    bloques = vr.leer_bloques(briefs)
    por_tanda: dict[int, list[str]] = {}
    for b in bloques:
        por_tanda.setdefault(b.tanda, []).append(b.id)
    excesos = {t: bs for t, bs in por_tanda.items() if len(bs) > 4}
    assert excesos == {}, f"Tandas con más de 4 bloques en paralelo: {excesos}"

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


def test_ci33_brief_y_portada(tmp_path, monkeypatch):
    bloque = vr.Bloque("BL-01", 0, ["BL-01"], ["a.py"])
    hallazgos = _r5_ci33(tmp_path, monkeypatch, bloque, {},
                         {"governance/apoyo/briefs/BL-01.md": "brief\n", "governance/artefactos/TASKS.md": "t\n",
                          "governance/apoyo/BRIEFS_POR_BLOQUE.md": "portada\n"})
    assert hallazgos == [
        "R5 BL-01: «governance/apoyo/BRIEFS_POR_BLOQUE.md» está fuera de su «Escribe»",
        "R5 BL-01: «governance/apoyo/briefs/BL-01.md» está fuera de su «Escribe»",
        "R5 BL-01: «governance/artefactos/TASKS.md» está fuera de su «Escribe»",
    ]


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
