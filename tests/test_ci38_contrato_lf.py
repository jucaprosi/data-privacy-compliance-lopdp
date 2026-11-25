# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤roadmap ¤arbitro
"""CI-38: el exportador del contrato escribe bytes con LF en cualquier sistema."""
import importlib.util
import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CR = bytes([13])
LF = bytes([10])


@pytest.fixture
def exportador():
    especificacion = importlib.util.spec_from_file_location(
        "exportar_contrato_hoja_ruta_ci38", RAIZ / "scripts" / "exportar_contrato_hoja_ruta.py"
    )
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


@pytest.fixture
def destino(exportador, tmp_path, monkeypatch):
    carpeta = tmp_path / "contratos"
    monkeypatch.setattr(exportador, "CONTRATOS_DIR", carpeta)
    monkeypatch.setattr(exportador, "CONTRATO_FILE", carpeta / "hoja_de_ruta.openapi.json")
    return carpeta / "hoja_de_ruta.openapi.json"


def test_el_archivo_exportado_no_tiene_cr_y_termina_en_lf(exportador, destino):
    assert exportador.exportar_contrato() == destino
    datos = destino.read_bytes()
    assert CR not in datos
    assert datos.endswith(LF)


def test_con_un_write_text_que_traduce_saltos_el_archivo_sigue_sin_cr(exportador, destino, monkeypatch):
    original = pathlib.Path.write_text

    def como_en_windows(self, data, encoding=None, errors=None, newline=None):
        return original(self, data.replace("\n", "\r\n"), encoding=encoding, errors=errors, newline="")

    monkeypatch.setattr(pathlib.Path, "write_text", como_en_windows)
    exportador.exportar_contrato()
    assert CR not in destino.read_bytes()
