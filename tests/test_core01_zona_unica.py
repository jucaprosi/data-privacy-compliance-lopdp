"""CORE-01 · Una sola zona de negocio: solo app_core/zona_negocio.py define el desfase de Ecuador.

`¤arbitro`
"""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
UNICA = RAIZ / "app_core" / "zona_negocio.py"
PROHIBIDOS = (
    re.compile(r"\bZONA_GUAYAQUIL\s*="),
    re.compile(r"timedelta\(\s*hours\s*=\s*-\s*5\s*\)"),
)


def copias_de_la_zona(raiz: Path = RAIZ) -> list[str]:
    """Líneas de features/ y app_core/ que definen la zona fuera de su único lugar."""
    hallazgos = []
    for carpeta in ("features", "app_core"):
        for ruta in sorted((raiz / carpeta).rglob("*.py")):
            if ruta.resolve() == UNICA.resolve():
                continue
            for n, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
                if any(p.search(linea) for p in PROHIBIDOS):
                    hallazgos.append(f"{ruta.relative_to(raiz).as_posix()}:{n}: {linea.strip()}")
    return hallazgos


def test_la_zona_de_negocio_vive_solo_en_app_core():
    assert copias_de_la_zona() == []


def test_los_dos_consumidores_importan_zona_negocio():
    for relativa in ("features/auditoria_capa/domain/control_periodico.py",
                     "features/roadmap/services/recordatorios_engine.py"):
        texto = (RAIZ / relativa).read_text(encoding="utf-8")
        assert "from app_core.zona_negocio import ZONA_NEGOCIO" in texto, relativa


def test_la_guarda_detecta_una_copia_local(tmp_path):
    """Mutación en miniatura: una copia reintroducida aparece en el informe."""
    (tmp_path / "app_core").mkdir()
    (tmp_path / "features" / "sala").mkdir(parents=True)
    (tmp_path / "features" / "sala" / "m.py").write_text(
        'ZONA_GUAYAQUIL = timezone(timedelta(hours=-5), "America/Guayaquil")\n', encoding="utf-8")
    assert len(copias_de_la_zona(tmp_path)) == 1
