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


def _t(tid, propiedad, depende=(), estado="pendiente"):
    return indice.Tarea(id=tid, titulo=tid, ola="A", estado=estado, sala="s", depende_de=tuple(depende),
                        propiedad=tuple(propiedad), arbitro="pytest")


def _bloque(bid, tanda, tareas, escribe):
    cuerpo = "".join(f"{i}. `{t}` — x\n" for i, t in enumerate(tareas, 1))
    rutas = "".join(f"  - `{e}`\n" for e in escribe)
    return f"### {bid} · nombre  (tanda {tanda})\n\n**Objetivo** (en este orden):\n\n{cuerpo}\n**Rastro ¤**\n\n**Escribe** (lista):\n\n{rutas}\n**No hagas:**\n\n"


def _briefs(*bloques, sin_agente=()):
    pie = "## Sin agente (solo el propietario)\n\n" + "".join(f"- `{t}`\n" for t in sin_agente)
    return "".join(bloques) + pie


def test_el_reparto_real_es_valido():
    tareas, errores = indice.cargar_tareas()
    briefs = vr.BRIEFS.read_text(encoding="utf-8")
    assert errores == []
    assert vr.revisar(briefs, tareas, indice) == []


def test_una_task_hecha_o_repetida_o_sin_bloque_se_rechaza():
    tareas = [_t("A-1", ["a.py"]), _t("B-1", ["b.py"]), _t("C-1", ["c.py"]), _t("D-1", ["d.py"], estado="hecha")]
    briefs = _briefs(_bloque("BL-01", 0, ["A-1", "D-1"], ["a.py", "d.py"]),
                     _bloque("BL-02", 1, ["A-1", "Q-9"], ["a.py"]),
                     sin_agente=["B-1"])
    hallazgos = vr.revisar(briefs, tareas, indice)
    assert "R1 D-1: está hecha y figura en BL-01" in hallazgos
    assert "R1 A-1: debe figurar en un solo bloque y figura en 2 (BL-01, BL-02)" in hallazgos
    assert "R1 Q-9: los briefs citan una task que no existe" in hallazgos
    assert "R1 C-1: debe figurar en un solo bloque y figura en 0" in hallazgos
    assert not [h for h in hallazgos if h.startswith("R1 B-1")]  # «Sin agente» cuenta como ubicación


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
