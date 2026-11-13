# -*- coding: utf-8 -*-
# ¤diagnostico-scoring
"""Árbitro de la escala de madurez: un solo contrato, sin copias ni consumidores olvidados.

`governance/contratos/escala_madurez.json` es la fuente única. Este árbitro comprueba:
  E1  el contrato está completo: niveles 1 a 5, evidencia 0 a 4, rangos contiguos y pesos que suman 1.
  E2  el contrato coincide con el archivo de assessment SMARTCIDI (huella, hojas y fórmulas).
  E3  las tablas de `governance/ESCALA_MADUREZ.md` son las que genera este script.
  E4  ningún archivo usa vocabulario retirado salvo los anotados con la tarea que lo retira,
      y una anotación que ya no hace falta se borra: la lista solo puede encoger.
  E5  la doctrina no vuelve a definir la escala 0 a 3.

    python scripts/verificar_escala_madurez.py             # código 1 si hay hallazgos
    python scripts/verificar_escala_madurez.py --escribir  # regenera las tablas y quita anotaciones cumplidas
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONTRATO = RAIZ / "governance" / "contratos" / "escala_madurez.json"
DOCUMENTO = RAIZ / "governance" / "ESCALA_MADUREZ.md"
DOCTRINA = ("governance/METODOLOGIAS.md", "governance/DOCTRINAS.md", "governance/artefactos/INVARIANTS.md")
ESCANEADOS = ("features", "api", "frontend/src", "tests")
EXTENSIONES = {".py", ".ts", ".tsx"}
EXCLUIDOS = {"tests/test_escala_madurez.py"}
INICIO, FIN = "<!-- tablas-generadas:inicio -->", "<!-- tablas-generadas:fin -->"
_ESCALA_VIEJA = re.compile(r"\(0 a 3\)|Maduro Explícito|Temprano Explícito|Caótico")


# ¤diagnostico-scoring
def cargar() -> dict:
    return json.loads(CONTRATO.read_text(encoding="utf-8"))


# ¤diagnostico-scoring
def revisar_contrato(c: dict) -> list[str]:
    """E1: forma del contrato."""
    h: list[str] = []
    asignados, evidencia = c["nivel_asignado"], c["nivel_evidencia"]
    if [n["nivel"] for n in asignados] != [1, 2, 3, 4, 5]:
        h.append("E1: el nivel asignado debe ir de 1 a 5")
    if [n["nivel"] for n in evidencia] != [0, 1, 2, 3, 4]:
        h.append("E1: el nivel de evidencia debe ir de 0 a 4")
    if asignados[0]["rango"][0] != 0 or asignados[-1]["rango"][1] != 100:
        h.append("E1: los rangos deben cubrir de 0 a 100")
    for previo, siguiente in zip(asignados, asignados[1:]):
        if previo["rango"][1] + 1 != siguiente["rango"][0]:
            h.append(f"E1: rangos no contiguos entre los niveles {previo['nivel']} y {siguiente['nivel']}")
    if round(sum(d["peso"] for d in c["dimensiones"]), 6) != 1:
        h.append("E1: los pesos de las dimensiones deben sumar 1")
    return h


# ¤diagnostico-scoring
def archivo_fuente(c: dict) -> Path | None:
    """El assessment puede estar en la raíz o en data/; sin él no se puede ejecutar E2."""
    for ruta in (RAIZ / c["fuente"]["archivo"], RAIZ / "data" / c["fuente"]["archivo"]):
        if ruta.exists():
            return ruta
    return None


# ¤diagnostico-scoring
def revisar_fuente(c: dict, ruta: Path) -> list[str]:
    """E2: la huella del archivo y lo que dicen sus hojas. Si cambia el archivo, se revisa el contrato."""
    import openpyxl

    h: list[str] = []
    if hashlib.sha256(ruta.read_bytes()).hexdigest() != c["fuente"]["sha256"]:
        h.append("E2: el archivo de assessment cambió; revise el contrato y actualice su huella")
    libro = openpyxl.load_workbook(ruta)
    niveles, catalogos = libro["Niveles de Madurez"], libro["Catálogos"]
    for fila, n in zip(range(4, 9), c["nivel_asignado"]):
        if niveles[f"A{fila}"].value != n["nivel"] or niveles[f"B{fila}"].value != n["nombre"]:
            h.append(f"E2: el nivel {n['nivel']} no coincide con la hoja «Niveles de Madurez»")
        if niveles[f"F{fila}"].value != f"{n['rango'][0]}% - {n['rango'][1]}%":
            h.append(f"E2: el rango del nivel {n['nivel']} no coincide con la hoja «Niveles de Madurez»")
    if catalogos["A3"].value != "Nivel asignado (1-5)" or catalogos["A5"].value != "Nivel evidencia (0-4)":
        h.append("E2: la hoja «Catálogos» ya no declara las escalas 1-5 y 0-4")
    matriz, dimensiones = libro["ASSESSMENT"], libro["Dimensiones"]
    r = c["reglas"]
    if matriz["M7"].value != '=IF(I7="No","N/A",IF(OR(K7="",L7=""),"",MIN(K7,L7+1)))':
        h.append("E2: cambió la fórmula del nivel efectivo")
    riesgo = str(matriz["P7"].value)
    for umbral in (r["riesgo_critico_desde"], r["riesgo_alto_desde"], r["riesgo_medio_desde"]):
        if f">={umbral}," not in riesgo:
            h.append(f"E2: la fórmula de riesgo ya no usa el umbral {umbral}")
    if f"E4<{r['cobertura_minima'] / 100}" not in str(dimensiones["G4"].value):
        h.append("E2: cambió la cobertura mínima de la hoja «Dimensiones»")
    for fila, d in zip(range(4, 14), c["dimensiones"]):
        if dimensiones[f"B{fila}"].value != d["peso"]:
            h.append(f"E2: el peso de {d['id']} no coincide con la hoja «Dimensiones»")
    for fila in range(7, 87):
        bloqueante = matriz[f"Q{fila}"].value == "Sí"
        if bloqueante != (matriz[f"J{fila}"].value == r["criticidad_bloqueante"]):
            h.append(f"E2: el control {matriz[f'A{fila}'].value} rompe la equivalencia bloqueante = criticidad máxima")
    return h


# ¤diagnostico-scoring
def tablas(c: dict) -> str:
    """Tablas del documento, siempre derivadas del contrato."""
    r = c["reglas"]
    lineas = ["### Nivel asignado", "", "| Nivel | Nombre | Criterio | Puntaje de dimensión |", "| :--- | :--- | :--- | :--- |"]
    lineas += [f"| {n['nivel']} | {n['nombre']} | {n['criterio']} | {n['rango'][0]} a {n['rango'][1]} |" for n in c["nivel_asignado"]]
    lineas += ["", "### Nivel de evidencia", "", "| Nivel | Nombre |", "| :--- | :--- |"]
    lineas += [f"| {n['nivel']} | {n['nombre']} |" for n in c["nivel_evidencia"]]
    lineas += ["", "### Umbrales", "", "| Regla | Valor |", "| :--- | :--- |"]
    lineas += [
        f"| Riesgo crítico desde | {r['riesgo_critico_desde']} |",
        f"| Riesgo alto desde | {r['riesgo_alto_desde']} |",
        f"| Riesgo medio desde | {r['riesgo_medio_desde']} |",
        f"| Criticidad de un control bloqueante | {r['criticidad_bloqueante']} |",
        f"| Control degradado con nivel efectivo menor que | {r['efectivo_degradado_bajo']} |",
        f"| Tope de la dimensión por control bloqueante degradado | {r['tope_por_bloqueante']} |",
        f"| Criticidad desde la que se exige evidencia | {r['criticidad_evidencia_exigible']} |",
        f"| Evidencia exigible | {r['evidencia_exigible']} |",
        f"| Tope de la dimensión por evidencia insuficiente | {r['tope_por_evidencia_insuficiente']} |",
        f"| Cobertura mínima para emitir nivel | {r['cobertura_minima']} % |",
    ]
    lineas += ["", "### Dimensiones", "", "| Id | Dimensión | Peso |", "| :--- | :--- | :--- |"]
    lineas += [f"| {d['id']} | {d['nombre']} | {d['peso']:.2f} |" for d in c["dimensiones"]]
    return "\n".join(lineas)


# ¤diagnostico-scoring
def bloque(texto: str) -> str | None:
    if INICIO not in texto or FIN not in texto:
        return None
    return texto.split(INICIO, 1)[1].split(FIN, 1)[0].strip()


# ¤diagnostico-scoring
def usos(raiz: Path, retirado: list[str]) -> dict[str, list[str]]:
    """Archivo relativo → términos retirados que contiene."""
    patron = re.compile("|".join(re.escape(t) for t in sorted(retirado, key=len, reverse=True)), re.IGNORECASE)
    canon = {t.lower(): t for t in retirado}
    hallados: dict[str, list[str]] = {}
    for carpeta in ESCANEADOS:
        for ruta in sorted((raiz / carpeta).rglob("*")):
            relativo = ruta.relative_to(raiz).as_posix()
            if ruta.suffix not in EXTENSIONES or "node_modules" in ruta.parts or relativo in EXCLUIDOS:
                continue
            terminos = {canon[m.group(0).lower()] for m in patron.finditer(ruta.read_text(encoding="utf-8", errors="ignore"))}
            if terminos:
                hallados[relativo] = sorted(terminos)
    return hallados


# ¤diagnostico-scoring
def revisar_vocabulario(c: dict, hallados: dict[str, list[str]]) -> list[str]:
    """E4: trinquete. Lo nuevo falla, lo anotado de más también."""
    h: list[str] = []
    pendientes, historicos = c["consumidores_pendientes"], c["lectura_historica"]
    for archivo, terminos in hallados.items():
        if archivo in historicos:
            continue
        anotados = set(pendientes.get(archivo, {}).get("terminos", []))
        for termino in terminos:
            if termino not in anotados:
                h.append(f"E4: {archivo} usa «{termino}», retirado de la escala; use el contrato vigente")
    for archivo, entrada in pendientes.items():
        sobran = set(entrada["terminos"]) - set(hallados.get(archivo, []))
        if sobran:
            h.append(f"E4: {archivo} ya no usa {sorted(sobran)}; ejecute --escribir para acortar la lista ({entrada['tarea']})")
    return h


# ¤diagnostico-scoring
def podar(c: dict, hallados: dict[str, list[str]]) -> dict:
    """Quita lo ya cumplido; nunca añade: un consumidor nuevo se corrige, no se anota aquí."""
    podados: dict[str, dict] = {}
    for archivo, entrada in c["consumidores_pendientes"].items():
        quedan = [t for t in entrada["terminos"] if t in hallados.get(archivo, [])]
        if quedan:
            podados[archivo] = {"tarea": entrada["tarea"], "terminos": quedan}
    return {**c, "consumidores_pendientes": podados}


# ¤diagnostico-scoring
def revisar_doctrina(raiz: Path) -> list[str]:
    """E5: la doctrina remite a la escala vigente; no conserva otra."""
    h: list[str] = []
    for relativo in DOCTRINA:
        for numero, linea in enumerate((raiz / relativo).read_text(encoding="utf-8").splitlines(), 1):
            if _ESCALA_VIEJA.search(linea):
                h.append(f"E5: {relativo}:{numero} conserva la escala 0 a 3")
    return h


# ¤diagnostico-scoring
def revisar(c: dict) -> list[str]:
    hallazgos = revisar_contrato(c)
    fuente = archivo_fuente(c)
    if fuente is not None:
        hallazgos += revisar_fuente(c, fuente)
    if bloque(DOCUMENTO.read_text(encoding="utf-8")) != tablas(c):
        hallazgos.append("E3: las tablas de governance/ESCALA_MADUREZ.md no son las del contrato; ejecute --escribir")
    hallazgos += revisar_vocabulario(c, usos(RAIZ, c["vocabulario_retirado"]))
    return hallazgos + revisar_doctrina(RAIZ)


# ¤diagnostico-scoring
def main() -> int:
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument("--escribir", action="store_true")
    c = cargar()
    if argumentos.parse_args().escribir:
        c = podar(c, usos(RAIZ, c["vocabulario_retirado"]))
        CONTRATO.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        texto = DOCUMENTO.read_text(encoding="utf-8")
        cabeza, resto = texto.split(INICIO, 1)
        DOCUMENTO.write_text(
            f"{cabeza}{INICIO}\n{tablas(c)}\n{FIN}{resto.split(FIN, 1)[1]}", encoding="utf-8", newline="\n"
        )
    hallazgos = revisar(c)
    for hallazgo in hallazgos:
        print(hallazgo)
    print(f"escala de madurez: {len(hallazgos)} hallazgos")
    return 1 if hallazgos else 0


if __name__ == "__main__":
    sys.exit(main())
