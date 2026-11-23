# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"""GOB-06 R5: los briefs de una tanda, en la carpeta local, coinciden con sus fichas (carpeta temporal)."""
import importlib.util
import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("verificar_briefs_locales", _RAIZ / "scripts" / "verificar_briefs_locales.py")
vbl = importlib.util.module_from_spec(_spec)
sys.modules["verificar_briefs_locales"] = vbl
_spec.loader.exec_module(vbl)
indice = vbl._cargar_indice()


def _t(tid, tanda=7, propiedad=("a.py", "b.py#X"), arbitro="pytest tests/test_a.py", estado="pendiente"):
    return indice.Tarea(id=tid, titulo=tid, ola="A", estado=estado, sala="s", depende_de=(),
                        propiedad=tuple(propiedad), arbitro=arbitro, tanda=tanda)


def _brief(tid, tanda=7, escribe=("a.py", "b.py#X"), hecho="pytest tests/test_a.py", eol="\n"):
    rutas = "".join(f"  - `{r}`\n" for r in escribe)
    texto = (f"### {tid} · titulo  (tanda {tanda})\n\n**Objetivo**\n\n1. `{tid}` — x\n\n"
             f"**Escribe** (lista exclusiva):\n\n{rutas}\n**No hagas:**\n\n- nada\n\n"
             f"**Hecho si** (árbitro exógeno):\n\n- `{tid}`: {hecho}\n- `python scripts/x.py` con código 0.\n")
    return texto.replace("\n", eol)


def _carpeta(tmp_path, briefs):
    (tmp_path / "briefs").mkdir()
    for nombre, texto in briefs.items():
        (tmp_path / "briefs" / nombre).write_bytes(texto.encode("utf-8"))
    return tmp_path


def test_r5_hecho_si_distinto_y_brief_que_falta(tmp_path):
    tareas = [_t("A-1"), _t("B-1"), _t("C-1"), _t("D-1", tanda=8), _t("E-1", estado="hecha")]
    carpeta = _carpeta(tmp_path, {"A-1.md": _brief("A-1", hecho="pytest otra cosa"),
                                  "C-1.md": _brief("C-1", eol="\r\n")})
    assert vbl.revisar_tanda(7, tareas, carpeta) == [
        "A-1: «Hecho si» difiere del `arbitro` de la ficha",
        "B-1: falta briefs/B-1.md",
    ]


def test_r5_m3_escribe_distinto_de_la_propiedad(tmp_path):
    # Mutación m3: no comparar «Escribe» con `propiedad` deja este brief sin hallazgo.
    carpeta = _carpeta(tmp_path, {"A-1.md": _brief("A-1", escribe=("a.py", "c.py"))})
    assert vbl.revisar_tanda(7, [_t("A-1")], carpeta) == [
        "A-1: «Escribe» difiere de la `propiedad` (faltan ['b.py#X'], sobran ['c.py'])"]


def test_r5_cabecera_con_otra_tanda(tmp_path):
    carpeta = _carpeta(tmp_path, {"A-1.md": _brief("A-1", tanda=6)})
    assert vbl.revisar_tanda(7, [_t("A-1")], carpeta) == [
        "A-1: la cabecera del brief no dice «### A-1 · … (tanda 7)»"]


def test_r8_manda_la_version_mas_alta(tmp_path):
    carpeta = _carpeta(tmp_path, {"A-1.md": _brief("A-1", hecho="vieja"), "A-1.v2.md": _brief("A-1"),
                                  "A-10.md": _brief("A-10", hecho="ajena")})
    assert vbl.brief_vigente(carpeta / "briefs", "A-1").name == "A-1.v2.md"
    assert vbl.revisar_tanda(7, [_t("A-1")], carpeta) == []


def test_main_sale_con_1_si_falta_un_brief(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(indice, "cargar_tareas", lambda: ([_t("A-1")], []))
    monkeypatch.setattr(vbl, "_cargar_indice", lambda: indice)
    assert vbl.main(["--tanda", "7", "--carpeta", str(_carpeta(tmp_path, {}))]) == 1
    assert "A-1: falta briefs/A-1.md" in capsys.readouterr().out
    assert vbl.main(["--tanda", "9", "--carpeta", str(tmp_path)]) == 0
