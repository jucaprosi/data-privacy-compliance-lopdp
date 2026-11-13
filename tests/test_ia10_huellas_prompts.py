# ¤gemini-vertex ¤arbitro
"""IA-10: huellas de prompts versionados (invariante 64). Editar un texto sin subir la versión da rojo."""
import importlib.util
import json
import os
from dataclasses import replace
from pathlib import Path

from features.inferencia.domain.prompts import (
    PromptVersionado,
    clave_huella,
    huella,
    huellas_distintas,
    huellas_faltantes,
)

RAIZ = Path(__file__).resolve().parent.parent
HUELLAS = RAIZ / "evaluacion" / "ia" / "huellas_prompts.json"


def _declarados(raiz: Path) -> list[tuple[str, PromptVersionado]]:
    """Recorre `<raiz>/features/<sala>/ai/prompts.py` y devuelve (carpeta de la sala, prompt) de cada `VERSIONES`."""
    encontrados = []
    for archivo in sorted((raiz / "features").glob("*/ai/prompts.py")):
        sala = archivo.parent.parent.name
        spec = importlib.util.spec_from_file_location(f"_prompts_{sala}_{abs(hash(str(raiz)))}", archivo)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        encontrados.extend((sala, p) for p in getattr(modulo, "VERSIONES", {}).values())
    return encontrados


def _prompts_del_repositorio() -> list[PromptVersionado]:
    return [p for _, p in _declarados(RAIZ)]


def _prefijos_incorrectos(raiz: Path) -> list[str]:
    """Ids cuyo prefijo no coincide con la carpeta de la sala donde se declaran."""
    return sorted(f"{p.id} en {sala}" for sala, p in _declarados(raiz) if p.sala != sala)


def _registradas() -> dict[str, str]:
    return json.loads(HUELLAS.read_text(encoding="utf-8"))


def test_todos_los_prompts_del_repositorio_tienen_huella_vigente():
    prompts = _prompts_del_repositorio()
    assert huellas_faltantes(prompts, _registradas()) == []
    assert huellas_distintas(prompts, _registradas()) == []


def test_no_hay_huellas_de_prompts_que_ya_no_existen():
    claves = {clave_huella(p) for p in _prompts_del_repositorio()}
    assert set(_registradas()) <= claves, "una versión anterior se borró: las versiones no se retiran"


def test_la_version_no_se_declara_dos_veces_con_texto_distinto():
    vistos: dict[str, str] = {}
    for p in _prompts_del_repositorio():
        assert vistos.setdefault(clave_huella(p), huella(p)) == huella(p)


BASE = PromptVersionado("roadmap.redaccion", 1, "Eres un redactor.", "Resume: {tema}")


def test_editar_el_texto_sin_subir_la_version_se_detecta():
    registradas = {clave_huella(BASE): huella(BASE)}
    editado = replace(BASE, plantilla="Resume brevemente: {tema}")
    assert huellas_distintas([BASE], registradas) == []
    assert huellas_distintas([editado], registradas) == ["roadmap.redaccion@1"]


def test_subir_la_version_deja_la_anterior_intacta_y_pide_su_propia_huella():
    registradas = {clave_huella(BASE): huella(BASE)}
    nueva = replace(BASE, version=2, plantilla="Resume brevemente: {tema}")
    assert huellas_distintas([BASE, nueva], registradas) == []
    assert huellas_faltantes([BASE, nueva], registradas) == ["roadmap.redaccion@2"]


def test_la_huella_cubre_el_texto_de_sistema():
    assert huella(BASE) != huella(replace(BASE, sistema="Eres otro redactor."))


def test_la_huella_es_sha256_estable():
    assert len(huella(BASE)) == 64 and huella(BASE) == huella(replace(BASE))


def test_el_prefijo_de_cada_id_coincide_con_la_sala_donde_se_declara():
    assert _prefijos_incorrectos(RAIZ) == []


def _sala_falsa(raiz: Path, sala: str, id_prompt: str) -> None:
    carpeta = raiz / "features" / sala / "ai"
    carpeta.mkdir(parents=True)
    codigo = [
        "from features.inferencia.domain.prompts import PromptVersionado",
        f"VERSIONES = {{1: PromptVersionado({id_prompt!r}, 1, 's', 't')}}",
    ]
    (carpeta / "prompts.py").write_text(os.linesep.join(codigo) + os.linesep, encoding="utf-8")


def test_un_prompt_con_prefijo_de_otra_sala_se_detecta(tmp_path):
    _sala_falsa(tmp_path, "roadmap", "ai_copilot.plan")
    assert _prefijos_incorrectos(tmp_path) == ["ai_copilot.plan en roadmap"]


def test_un_prompt_con_su_propio_prefijo_pasa(tmp_path):
    _sala_falsa(tmp_path, "roadmap", "roadmap.plan")
    assert _prefijos_incorrectos(tmp_path) == []
