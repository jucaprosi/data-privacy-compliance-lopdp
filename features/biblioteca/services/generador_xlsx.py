# ¤adpa
# ¤¤developer-architect
"""Generador XLSX (BIB-205) con openpyxl como escritor, nunca como motor de cálculo.

- Cada tabla del documento va a su hoja como tabla de Excel, con fechas reales, validación «sí/no» donde
  la columna solo tiene esas respuestas y una fila de total con la única fórmula autorizada (CONTARA).
- El libro pide recálculo completo al abrirse (`fullCalcOnLoad`); `recalcular` reproduce las fórmulas
  autorizadas para comprobar en pruebas que el resultado es el esperado.
- Un dato que empieza por = + - @ se escribe como texto con prefijo de cita: nunca se evalúa.
"""
import re
import zipfile
from collections.abc import Mapping
from datetime import date, datetime, time
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo
from api.errores import ErrorNegocio
from features.biblioteca.services.salida import Bloque, es_formula, zip_determinista
import features.biblioteca.domain.errores  # noqa: F401  registra los códigos de Biblioteca al importarse

FORMULAS_AUTORIZADAS = frozenset({"COUNTA"})
FORMULA = re.compile(r"^=([A-Z]+)\(([A-Z]+)([0-9]+):([A-Z]+)([0-9]+)\)$")
FECHA = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
SI_NO = frozenset({"sí", "si", "no"})
FORMATO_FECHA = "yyyy-mm-dd"
ESTILO_TABLA = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)


# ¤adpa
def formula(nombre: str, columna: str, desde: int, hasta: int) -> str:
    """Única puerta para escribir una fórmula: solo las de la lista autorizada y sobre un rango."""
    if nombre not in FORMULAS_AUTORIZADAS:
        raise ErrorNegocio("BIB_GEN_FORMULA_NO_AUTORIZADA", f"Fórmula no autorizada: {nombre}")
    return f"={nombre}({columna}{desde}:{columna}{hasta})"


# ¤adpa
def _fecha(valor: str) -> date | None:
    if not FECHA.match(valor):
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        return None


# ¤adpa
def _escribir(hoja, fila: int, columna: int, valor: object, negrita: bool = False) -> None:
    celda = hoja.cell(row=fila, column=columna)
    texto = "; ".join(map(str, valor)) if isinstance(valor, (list, tuple)) else ("" if valor is None else str(valor))
    fecha = _fecha(texto)
    if fecha is not None:
        celda.value = fecha
        celda.number_format = FORMATO_FECHA
    else:
        celda.value = texto
        celda.data_type = "s"  # texto siempre: openpyxl no lo toma como fórmula
        if es_formula(texto):
            celda.quotePrefix = True
    if negrita:
        celda.font = Font(bold=True)


# ¤adpa
def _cabeceras(fila: list[str]) -> list[str]:
    vistas: dict[str, int] = {}
    salida = []
    for n, c in enumerate(fila, 1):
        base = (c.replace("**", "").strip() or f"Columna {n}")[:250]
        vistas[base] = vistas.get(base, 0) + 1
        salida.append(base if vistas[base] == 1 else f"{base} ({vistas[base]})")
    return salida


# ¤adpa
def _hoja_tabla(libro: Workbook, numero: int, filas: list[list[str]]) -> None:
    hoja = libro.create_sheet(f"Tabla {numero}")
    cabecera = _cabeceras(filas[0])
    ancho = len(cabecera)
    datos = [f + [""] * (ancho - len(f)) for f in (r[:ancho] for r in filas[1:])] or [[""] * ancho]
    for c, titulo in enumerate(cabecera, 1):
        _escribir(hoja, 1, c, titulo, negrita=True)
        hoja.column_dimensions[get_column_letter(c)].width = min(max(len(titulo), 12) + 2, 60)
    for f, fila in enumerate(datos, 2):
        for c, valor in enumerate(fila, 1):
            _escribir(hoja, f, c, valor)
    ultima = len(datos) + 1
    hoja.add_table(Table(displayName=f"Tabla{numero}", ref=f"A1:{get_column_letter(ancho)}{ultima}",
                         tableStyleInfo=ESTILO_TABLA))
    for c in range(1, ancho + 1):
        valores = {str(fila[c - 1]).strip().lower() for fila in datos if str(fila[c - 1]).strip()}
        if valores and valores <= SI_NO:
            letra = get_column_letter(c)
            validacion = DataValidation(type="list", formula1='"sí,no"', allow_blank=True)
            validacion.add(f"{letra}2:{letra}{ultima}")
            hoja.add_data_validation(validacion)
    _escribir(hoja, ultima + 1, 1, "Total de filas", negrita=True)
    if ancho > 1:
        hoja.cell(row=ultima + 1, column=2).value = formula("COUNTA", "A", 2, ultima)


# ¤adpa
def _core(fecha: date) -> bytes:
    marca = datetime.combine(fecha, time()).strftime("%Y-%m-%dT%H:%M:%SZ")
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.'
            'openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" '
            'xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            '<dc:creator>EVYDENTIA</dc:creator>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{marca}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{marca}</dcterms:modified>'
            '</cp:coreProperties>').encode()


# ¤adpa
def generar_xlsx(titulo: str, valores: Mapping[str, object], contenido: list[Bloque], fecha: date,
                 faltantes: list[str] | None = None) -> bytes:
    """Libro de uso: hoja «Documento» con los datos y una hoja por tabla. Borrador: marca y faltantes."""
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Documento"
    _escribir(hoja, 1, 1, titulo, negrita=True)
    _escribir(hoja, 2, 1, "BORRADOR — no apto para revisión" if faltantes is not None else "Para revisión",
              negrita=True)
    _escribir(hoja, 4, 1, "Dato", negrita=True)
    _escribir(hoja, 4, 2, "Valor", negrita=True)
    claves = sorted(k for k, v in valores.items() if v not in (None, "", []) and not isinstance(v, bool))
    for n, clave in enumerate(claves, 5):
        _escribir(hoja, n, 1, clave)
        _escribir(hoja, n, 2, valores[clave])
    if claves:
        hoja.add_table(Table(displayName="Datos", ref=f"A4:B{4 + len(claves)}", tableStyleInfo=ESTILO_TABLA))
    hoja.column_dimensions["A"].width, hoja.column_dimensions["B"].width = 36, 80
    for numero, tabla in enumerate((b for b in contenido if b.tipo == "tabla" and b.filas), 1):
        _hoja_tabla(libro, numero, tabla.filas)
    if faltantes:
        hoja_faltan = libro.create_sheet("Faltantes")
        _escribir(hoja_faltan, 1, 1, "Dato que falta", negrita=True)
        for n, f in enumerate(faltantes, 2):
            _escribir(hoja_faltan, n, 1, f)
    libro.calculation.fullCalcOnLoad = True
    crudo = BytesIO()
    libro.save(crudo)
    with zipfile.ZipFile(BytesIO(crudo.getvalue())) as archivo:
        entradas = [(n, _core(fecha) if n == "docProps/core.xml" else archivo.read(n))
                    for n in sorted(archivo.namelist())]
    return zip_determinista(entradas)


# ¤adpa
def recalcular(hoja, referencia: str) -> object:
    """Valor de una celda con fórmula autorizada, calculado sin evaluar nada más."""
    valor = hoja[referencia].value
    m = FORMULA.match(str(valor)) if isinstance(valor, str) else None
    if m is None:
        return valor
    nombre, col, desde, col2, hasta = m.group(1), m.group(2), int(m.group(3)), m.group(4), int(m.group(5))
    if nombre not in FORMULAS_AUTORIZADAS or col != col2:
        raise ErrorNegocio("BIB_GEN_FORMULA_NO_AUTORIZADA", f"Fórmula no autorizada: {valor}")
    return sum(1 for f in range(desde, hasta + 1) if hoja[f"{col}{f}"].value not in (None, ""))
