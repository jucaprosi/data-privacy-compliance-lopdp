# ¤adpa
# ¤¤developer-architect
"""Generador DOCX (BIB-205) sin dependencias nuevas: OOXML escrito con la biblioteca estándar.

Decisión de motor: python-docx no está en requirements.txt y la ficha prohíbe instalar fuera del proceso
autorizado; WordprocessingML mínimo (documento, estilos, relaciones) basta para títulos, párrafos, listas,
citas y tablas con estilo propio. Todo texto se escapa como XML: nada de lo que escriba el usuario se
interpreta. `resolver_runs` sustituye variables partidas entre varios runs de un párrafo (plantillas DOCX
del kit); la salida de las plantillas MD ya llega resuelta.
"""
import re
from collections.abc import Mapping
from xml.sax.saxutils import escape
from features.biblioteca.services.salida import Bloque, tramos, zip_determinista

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
TOKEN = re.compile(r"\{\{([A-Za-z][A-Za-z0-9_.]*)\}\}")
PARRAFO = re.compile(r"<w:p[ >].*?</w:p>", re.S)
TEXTO_RUN = re.compile(r"(<w:t(?: [^>]*)?>)(.*?)(</w:t>)", re.S)
ESTILOS_TITULO = {1: "Title", 2: "Heading1", 3: "Heading2"}

TIPOS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
         '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
         '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
         '<Default Extension="xml" ContentType="application/xml"/>'
         '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.'
         'wordprocessingml.document.main+xml"/>'
         '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.'
         'wordprocessingml.styles+xml"/></Types>')
RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        'officeDocument" Target="word/document.xml"/></Relationships>')
RELS_DOC = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
            'styles" Target="styles.xml"/></Relationships>')


# ¤adpa
def _estilo(identificador: str, nombre: str, tamano: int, negrita: bool = False, tipo: str = "paragraph",
            extra: str = "") -> str:
    b = "<w:b/>" if negrita else ""
    return (f'<w:style w:type="{tipo}" w:styleId="{identificador}"><w:name w:val="{nombre}"/>'
            f'<w:basedOn w:val="Normal"/><w:qFormat/>{extra}<w:rPr>{b}<w:sz w:val="{tamano}"/></w:rPr></w:style>')


BORDES = "".join(f'<w:{lado} w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
                 for lado in ("top", "left", "bottom", "right", "insideH", "insideV"))
ESTILOS = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="{W}">'
           '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/>'
           '<w:pPr><w:spacing w:after="120"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>'
           '<w:sz w:val="22"/></w:rPr></w:style>'
           + _estilo("Title", "Title", 36, True) + _estilo("Heading1", "heading 1", 28, True)
           + _estilo("Heading2", "heading 2", 24, True)
           + _estilo("ListBullet", "List Bullet", 22, extra='<w:pPr><w:ind w:left="360" w:hanging="360"/></w:pPr>')
           + _estilo("Quote", "Quote", 22, extra='<w:pPr><w:ind w:left="567"/></w:pPr>')
           + _estilo("Borrador", "Marca de borrador", 24, True)
           + '<w:style w:type="table" w:styleId="TablaDocumento"><w:name w:val="Tabla del documento"/>'
           f'<w:tblPr><w:tblBorders>{BORDES}</w:tblBorders></w:tblPr></w:style></w:styles>')


# ¤adpa
def _runs(texto: str) -> str:
    salida = []
    for tramo, negrita in tramos(texto):
        lineas = tramo.split("\n")
        contenido = '<w:br/>'.join(f'<w:t xml:space="preserve">{escape(linea)}</w:t>' for linea in lineas)
        salida.append(f"<w:r>{'<w:rPr><w:b/></w:rPr>' if negrita else ''}{contenido}</w:r>")
    return "".join(salida)


# ¤adpa
def _parrafo(texto: str, estilo: str | None = None) -> str:
    propiedades = f'<w:pPr><w:pStyle w:val="{estilo}"/></w:pPr>' if estilo else ""
    return f"<w:p>{propiedades}{_runs(texto)}</w:p>"


# ¤adpa
def _tabla(filas: list[list[str]]) -> str:
    columnas = max((len(f) for f in filas), default=1)
    rejilla = "".join('<w:gridCol w:w="2400"/>' for _ in range(columnas))
    cuerpo = []
    for numero, fila in enumerate(filas):
        celdas = "".join(f'<w:tc><w:tcPr><w:tcW w:w="2400" w:type="dxa"/></w:tcPr>'
                         f"{_parrafo(f'**{c}**' if numero == 0 and c else c)}</w:tc>"
                         for c in fila + [""] * (columnas - len(fila)))
        cabecera = "<w:trPr><w:tblHeader/></w:trPr>" if numero == 0 else ""
        cuerpo.append(f"<w:tr>{cabecera}{celdas}</w:tr>")
    return (f'<w:tbl><w:tblPr><w:tblStyle w:val="TablaDocumento"/><w:tblW w:w="0" w:type="auto"/></w:tblPr>'
            f"<w:tblGrid>{rejilla}</w:tblGrid>{''.join(cuerpo)}</w:tbl>")


# ¤adpa
def _bloque(b: Bloque) -> str:
    if b.tipo == "titulo":
        return _parrafo(b.texto, ESTILOS_TITULO.get(b.nivel, "Heading2"))
    if b.tipo == "lista":
        return _parrafo("• " + b.texto, "ListBullet")
    if b.tipo == "cita":
        return _parrafo(b.texto, "Quote")
    if b.tipo == "tabla":
        return _tabla(b.filas) + "<w:p/>"
    return _parrafo(b.texto)


# ¤adpa
def generar_docx(contenido: list[Bloque], faltantes: list[str] | None = None) -> bytes:
    """DOCX de uso. Con `faltantes` (modo borrador) abre con la marca BORRADOR y el listado."""
    partes = []
    if faltantes is not None:
        partes.append(_parrafo("BORRADOR — no apto para revisión", "Borrador"))
        if faltantes:
            partes.append(_parrafo("Datos que faltan:"))
            partes += [_parrafo("• " + f, "ListBullet") for f in faltantes]
    partes += [_bloque(b) for b in contenido]
    documento = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W}" '
                 f'xmlns:r="{REL}"><w:body>{"".join(partes)}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
                 '<w:pgMar w:top="1418" w:right="1418" w:bottom="1418" w:left="1418" w:header="709" '
                 'w:footer="709" w:gutter="0"/></w:sectPr></w:body></w:document>')
    return zip_determinista([("[Content_Types].xml", TIPOS.encode()), ("_rels/.rels", RELS.encode()),
                             ("word/_rels/document.xml.rels", RELS_DOC.encode()),
                             ("word/styles.xml", ESTILOS.encode()), ("word/document.xml", documento.encode())])


# ¤adpa
def resolver_runs(textos: list[str], valores: Mapping[str, str]) -> list[str]:
    """Sustituye `{{X}}` aunque Word lo haya partido entre runs; conserva el formato de cada run.

    El valor completo queda en el run donde empieza la variable y los demás tramos de esa variable se
    vacían. Una variable sin valor se deja intacta (la detecta la comprobación de residuos).
    """
    unido = "".join(textos)
    limites, acumulado = [], 0
    for t in textos:
        limites.append((acumulado, acumulado + len(t)))
        acumulado += len(t)
    resultado = list(textos)
    for m in reversed(list(TOKEN.finditer(unido))):
        if m.group(1) not in valores:
            continue
        inicio, fin = m.span()
        tocados = [i for i, (a, b) in enumerate(limites) if a < fin and b > inicio]
        primero = tocados[0]
        for i in tocados:
            a, b = limites[i]
            # Se recorre de atrás hacia delante: lo anterior a `fin` en este run sigue intacto.
            antes = resultado[i][: inicio - a] if i == primero else ""
            despues = resultado[i][fin - a:] if b > fin else ""
            resultado[i] = antes + (str(valores[m.group(1)]) if i == primero else "") + despues
    return resultado


# ¤adpa
def rellenar_document_xml(xml: str, valores: Mapping[str, str]) -> str:
    """Aplica `resolver_runs` a cada párrafo de un `word/document.xml`; los valores se escapan."""
    def parrafo(m: re.Match) -> str:
        trozos = TEXTO_RUN.findall(m.group(0))
        if not trozos:
            return m.group(0)
        nuevos = iter(resolver_runs([t[1] for t in trozos], {k: escape(str(v)) for k, v in valores.items()}))
        return TEXTO_RUN.sub(lambda r: r.group(1) + next(nuevos) + r.group(3), m.group(0))
    return PARRAFO.sub(parrafo, xml)
