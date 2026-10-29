# ¤adpa
# ¤¤developer-architect
"""Reglas puras de las plantillas Markdown del PMV (docs/biblioteca-pmv.md, apartados a y b).

Valida metadatos y cuerpo sin escribir nada. Los metadatos usan un subconjunto de YAML (escalares,
listas en línea y listas de objetos simples); se leen sin dependencias nuevas.
"""
import hashlib
import re
from api.errores import ErrorNegocio

COMUNES = frozenset({
    "organizacion.razon_social", "organizacion.nombre_comercial", "organizacion.ruc", "organizacion.sector",
    "organizacion.tamano", "organizacion.direccion", "organizacion.ciudad", "organizacion.telefono",
    "organizacion.correo_contacto", "organizacion.correo_privacidad", "organizacion.sitio_web",
    "representante.nombre", "representante.identificacion", "representante.cargo",
    "dpo.nombre", "dpo.correo", "dpo.fecha_designacion",
    "documento.codigo", "documento.nombre", "documento.version", "documento.proxima_revision",
    "documento.aprobado_por", "documento.fecha_aprobacion", "fecha_emision",
    "tratamiento.finalidades", "tratamiento.categorias_datos", "tratamiento.plazo_conservacion",
    "tratamiento.destinatarios",
})
OBLIGATORIOS = ("codigo", "nombre", "tipo", "ola", "sector", "naturaleza", "tamano_empresa", "version",
                "base_lopdp", "validacion_legal", "fecha_corte_normativo", "variables_contexto", "revision_meses")
TIPOS = frozenset({"politica", "aviso", "formulario", "acuerdo", "contrato", "registro", "procedimiento",
                   "protocolo", "modelo"})
NATURALEZAS = frozenset({"publica", "privada", "ambas"})
VALIDACIONES = frozenset({"pendiente", "en_revision", "validada", "con_observaciones"})
TIPOS_CONTEXTO = frozenset({"texto", "si_no", "lista"})
NIVELES_AVISO = frozenset({"info", "alto"})
CONDICION_DPO = "dpo.designado"
MARCAS_BORRADOR = ("<!-- VARIANTE", "POR VERIFICAR")
CODIGO = re.compile(r"^BIB-0[0-9]{2}$")
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
FECHA = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
CONTEXTO = re.compile(r"^contexto\.[a-z][a-z0-9_]*$")
TOKEN = re.compile(r"\{\{([^}]*)\}\}")
VARIABLE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)?$")


# ¤adpa
def _escalar(valor: str):
    valor = valor.strip()
    if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
        return valor[1:-1]
    if valor.startswith("[") and valor.endswith("]"):
        return [v.strip() for v in valor[1:-1].split(",") if v.strip()]
    return valor.split(" #", 1)[0].strip()


# ¤adpa
def leer_metadatos(cabecera: str) -> dict:
    """Claves de primer nivel y listas de objetos de un nivel. Lanza ValueError si no es legible."""
    meta: dict = {}
    lista: list | None = None
    actual: dict | None = None
    for numero, linea in enumerate(cabecera.splitlines(), 1):
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        if not linea.startswith(" "):
            clave, separador, valor = linea.partition(":")
            if not separador or not re.fullmatch(r"[a-z][a-z0-9_]*", clave.strip()):
                raise ValueError(f"línea {numero} sin clave válida")
            valor = _escalar(valor)
            meta[clave.strip()] = valor if valor != "" else []
            lista, actual = (meta[clave.strip()], None) if valor == "" else (None, None)
        elif linea.lstrip().startswith("- ") and lista is not None:
            actual = {}
            lista.append(actual)
            clave, separador, valor = linea.lstrip()[2:].partition(":")
            if not separador:
                raise ValueError(f"línea {numero}: elemento de lista sin clave")
            actual[clave.strip()] = _escalar(valor)
        elif actual is not None:
            clave, separador, valor = linea.strip().partition(":")
            if not separador:
                raise ValueError(f"línea {numero}: propiedad sin clave")
            actual[clave.strip()] = _escalar(valor)
        else:
            raise ValueError(f"línea {numero}: sangría inesperada")
    return meta


# ¤adpa
def separar(texto: str) -> tuple[str, str]:
    """Devuelve (cabecera YAML, cuerpo). Lanza ValueError si falta la cabecera."""
    if not texto.startswith("---\n"):
        raise ValueError("falta la cabecera de metadatos entre '---'")
    cierre = texto.find("\n---\n", 3)
    if cierre < 0:
        raise ValueError("cabecera de metadatos sin cerrar")
    return texto[4:cierre + 1], texto[cierre + 5:]


# ¤adpa
def huella(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# ¤adpa
def _validar_metadatos(meta: dict, codigo_esperado: str) -> tuple[list[str], dict[str, str]]:
    fallos = [f"falta metadato {k}" for k in OBLIGATORIOS if k not in meta]
    codigo = meta.get("codigo")
    if not isinstance(codigo, str) or not CODIGO.match(codigo) or codigo != codigo_esperado:
        fallos.append(f"codigo inválido o distinto del archivo: {codigo}")
    if "tipo" in meta and meta["tipo"] not in TIPOS:
        fallos.append(f"tipo no admitido: {meta['tipo']}")
    if "naturaleza" in meta and meta["naturaleza"] not in NATURALEZAS:
        fallos.append(f"naturaleza no admitida: {meta['naturaleza']}")
    if "validacion_legal" in meta and meta["validacion_legal"] not in VALIDACIONES:
        fallos.append(f"validacion_legal no admitida: {meta['validacion_legal']}")
    if "version" in meta and not (isinstance(meta["version"], str) and SEMVER.match(meta["version"])):
        fallos.append(f"version no es semver: {meta['version']}")
    if "fecha_corte_normativo" in meta and not FECHA.match(str(meta["fecha_corte_normativo"])):
        fallos.append("fecha_corte_normativo no es AAAA-MM-DD")
    for clave in ("ola", "revision_meses"):
        if clave in meta and not str(meta[clave]).isdigit():
            fallos.append(f"{clave} no es un entero")
    if "tamano_empresa" in meta and not isinstance(meta["tamano_empresa"], list):
        fallos.append("tamano_empresa no es una lista")
    contexto: dict[str, str] = {}
    declaradas = meta.get("variables_contexto")
    if declaradas is not None and not isinstance(declaradas, list):
        fallos.append("variables_contexto no es una lista")
        declaradas = []
    for variable in declaradas or []:
        clave, tipo = variable.get("clave", ""), variable.get("tipo", "texto")
        if not CONTEXTO.match(clave):
            fallos.append(f"variable de contexto con ámbito o nombre inválido: {clave}")
        elif clave in contexto:
            fallos.append(f"variable de contexto repetida: {clave}")
        if tipo not in TIPOS_CONTEXTO:
            fallos.append(f"{clave}: tipo de contexto no admitido: {tipo}")
        if not variable.get("etiqueta"):
            fallos.append(f"{clave}: falta etiqueta")
        contexto[clave] = tipo
    si_no = {k for k, tipo in contexto.items() if tipo == "si_no"}
    avisos = meta.get("avisos", [])
    if not isinstance(avisos, list):
        fallos.append("avisos no es una lista")
        avisos = []
    for aviso in avisos:
        if aviso.get("cuando") not in si_no:
            fallos.append(f"aviso con condición no declarada: {aviso.get('cuando')}")
        if aviso.get("nivel") not in NIVELES_AVISO or not aviso.get("texto"):
            fallos.append("aviso sin nivel válido (info|alto) o sin texto")
    return fallos, contexto


# ¤adpa
def _validar_cuerpo(cuerpo: str, contexto: dict[str, str]) -> list[str]:
    fallos: list[str] = []
    si_no = {k for k, tipo in contexto.items() if tipo == "si_no"}
    condiciones = {CONDICION_DPO} | si_no
    abierto: str | None = None
    for crudo in TOKEN.findall(cuerpo):
        if crudo != crudo.strip():
            fallos.append(f"espacios dentro de las llaves: {{{{{crudo}}}}}")
        token = crudo.strip()
        if token.startswith("#si "):
            if abierto is not None:
                fallos.append("bloque anidado")
            abierto = token[4:].strip()
            if abierto not in condiciones:
                fallos.append(f"condición no admitida: {abierto}")
        elif token == "#sino":
            if abierto is None:
                fallos.append("{{#sino}} fuera de bloque")
        elif token == "/si":
            if abierto is None:
                fallos.append("{{/si}} sin abrir")
            abierto = None
        else:
            if not VARIABLE.match(token) or (token not in COMUNES and token not in contexto):
                fallos.append(f"variable desconocida: {token}")
            elif token.startswith("dpo.") and abierto != CONDICION_DPO:
                fallos.append(f"{token} fuera de {{{{#si {CONDICION_DPO}}}}}")
    if abierto is not None:
        fallos.append("bloque sin cerrar")
    for clave in contexto:
        if clave not in si_no and "{{" + clave + "}}" not in cuerpo:
            fallos.append(f"variable de contexto declarada y no usada: {clave}")
    return fallos


# ¤adpa
def validar_plantilla_md(texto: str, codigo_esperado: str) -> list[str]:
    """Lista de incumplimientos de la convención; vacía si la plantilla es válida."""
    try:
        cabecera, cuerpo = separar(texto)
        meta = leer_metadatos(cabecera)
    except ValueError as error:
        return [f"cabecera ilegible: {error}"]
    fallos, contexto = _validar_metadatos(meta, codigo_esperado)
    fallos += _validar_cuerpo(cuerpo, contexto)
    if any(marca in texto for marca in MARCAS_BORRADOR):
        fallos.append("quedan marcas de borrador")
    return fallos


# ¤adpa
def metadatos_de(texto: str) -> dict:
    return leer_metadatos(separar(texto)[0])


# ¤adpa
def exigir_plantilla_cargable(texto: str, codigo_esperado: str) -> dict:
    """Valida para carga: solo entra sin dictamen jurídico, nunca como «validada»."""
    if validar_plantilla_md(texto, codigo_esperado):
        raise ErrorNegocio("BIB_ARCHIVO_INVALIDO")
    meta = metadatos_de(texto)
    # «validada» exige el dictamen de la revisión jurídica del flujo editorial; un archivo no lo acredita.
    if meta["validacion_legal"] == "validada":
        raise ErrorNegocio("BIB_ARCHIVO_INVALIDO")
    return meta
