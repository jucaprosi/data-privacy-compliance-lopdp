"""GCP-11 · El brief del propietario: la lectura no cambia recursos y ningún bloque imprime un secreto.

`¤versionado-despliegue` `¤arbitro`

Mutaciones documentadas: añadir `gcloud run deploy` a un bloque de lectura, o dejar
`gcloud secrets versions access ...` sin asignar a una variable, hace fallar su caso.
"""
import re
from pathlib import Path

BRIEF = Path(__file__).resolve().parents[1] / "governance/operaciones/BRIEF_PROPIETARIO_REVISION_00006.md"
VERBOS = re.compile(r"\b(deploy|update|delete|replace|update-traffic)\b|\bset-[\w-]+|\badd(-[\w-]+)?\b")


def bloques(texto: str):
    """(sección, código) de cada bloque powershell; la sección es el último «## » anterior."""
    seccion, resultado = "", []
    for parte in re.split(r"(?m)^(## .*)$", texto):
        if parte.startswith("## "):
            seccion = parte[3:].strip()
        else:
            resultado += [(seccion, b) for b in re.findall(r"```powershell\n(.*?)```", parte, re.S)]
    return resultado


def faltas_de_lectura(texto: str) -> list[str]:
    return [f"verbo de cambio «{m.group(0)}»" for s, b in bloques(texto) if s.startswith("Lectura")
            for m in VERBOS.finditer(b)]


def faltas_de_impresion(texto: str) -> list[str]:
    malas = []
    for _s, b in bloques(texto):
        for linea in b.splitlines():
            if "versions access" in linea and not re.match(r"\s*\$\w+\s*=", linea):
                malas.append(linea.strip())
    return malas


def test_el_brief_tiene_lectura_y_cambio():
    secciones = [s for s, _ in bloques(BRIEF.read_text(encoding="utf-8"))]
    assert any(s.startswith("Lectura") for s in secciones) and any(s.startswith("Cambio") for s in secciones)


def test_los_bloques_de_lectura_no_cambian_recursos():
    assert faltas_de_lectura(BRIEF.read_text(encoding="utf-8")) == []


def test_ningun_bloque_imprime_el_valor_de_un_secreto():
    assert faltas_de_impresion(BRIEF.read_text(encoding="utf-8")) == []


def test_cada_bloque_lleva_su_variable_de_proyecto_o_su_cd():
    for _s, b in bloques(BRIEF.read_text(encoding="utf-8")):
        assert "$Proyecto" in b or "Set-Location" in b


def test_mutacion_un_deploy_en_la_lectura_se_detecta():
    mutado = BRIEF.read_text(encoding="utf-8").replace("gcloud run revisions describe", "gcloud run deploy", 1)
    assert any("deploy" in f for f in faltas_de_lectura(mutado))


def test_mutacion_un_acceso_sin_asignar_se_detecta():
    mutado = BRIEF.read_text(encoding="utf-8").replace("$Valor = gcloud secrets versions access", "gcloud secrets versions access", 1)
    assert faltas_de_impresion(mutado)
