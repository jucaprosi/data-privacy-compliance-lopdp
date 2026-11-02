# ¤arbitro
"""El arnés solo mira el árbol que rastrea git, no lo que haya en el disco."""
import importlib.util
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("arnes_cero_regresiones", RAIZ / "verificadores" / "arnes_cero_regresiones.py")
arnes = importlib.util.module_from_spec(_spec)
sys.modules["arnes_cero_regresiones"] = arnes
_spec.loader.exec_module(arnes)


def test_el_arnes_ignora_lo_que_git_no_rastrea(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "bueno.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "borrado.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "verificadores").mkdir()
    (tmp_path / "verificadores" / "v.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    (tmp_path / "borrado.py").unlink()
    otra = tmp_path / ".worktrees" / "otra"
    otra.mkdir(parents=True)
    (otra / "ajeno.py").write_bytes(b"\xef\xbb\xbfx = 1\n")
    monkeypatch.setattr(arnes, "PROJECT_ROOT", str(tmp_path))
    assert arnes.archivos_rastreados((".py",), excluir_carpetas=("verificadores",)) == ["bueno.py"]
    assert arnes.verificar_utf8_no_bom() is True
