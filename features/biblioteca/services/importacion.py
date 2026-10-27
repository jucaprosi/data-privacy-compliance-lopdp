# ¤adpa
# ¤¤developer-architect
"""Inventario inicial reproducible: manifiesto desde el kit, verificación sin escritura e importación idempotente.

Los ocho maestros entran En revisión; nunca se publican ni se reemplazan en silencio.
"""
import base64
import hashlib
import json
from pathlib import Path
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from api.errores import ErrorNegocio
from features.biblioteca.domain.editorial import MAX_BYTES, ArchivoMaestro, Capacidad, validar_archivo
from features.biblioteca.services.autorizacion import autorizar

KIT = "data/biblioteca/kit_v1"
ESPECIFICACION = f"{KIT}/especificacion/especificacion_biblioteca.json"
MANIFIESTO_KIT = f"{KIT}/MANIFIESTO.sha256"
MANIFIESTO_INICIAL = "data/biblioteca/manifiesto_inicial.json"
CLAVE_INICIAL = "kit_v1@2026-10-24"
# El kit cita rutas de su ZIP original; en el repositorio viven en plantillas/v0.1 sin modificar.
RUTAS_HEREDADAS = {"02_Plantillas/": "plantillas/v0.1/", "03_Plantillas_Referencia/": "plantillas/v0.1/"}
DISPONIBILIDAD = {"Creada para revisión": "con_archivo", "Salida existente por mapear": "salida_por_mapear",
                  "Planificada": "planificada"}
ESPERADO = {"con_archivo": 8, "salida_por_mapear": 2, "planificada": 40}
COLUMNAS = ("nombre", "familia", "tipo", "naturaleza", "etapa", "formato", "fuentes")
FUERA_DE_METADATOS = {"codigo", "version", "estado", "estado_cliente", "archivo", "template_id",
                      "template_version_id", *COLUMNAS}
# Versiones aprobadas después del kit: no entran en MANIFIESTO.sha256 (opción B, 2026-10-26);
# su huella aprobada consta aquí y en BIBLIOTECA_ESTADO.md §9.4. Entran En revisión con clave propia.
DERIVADOS = ({"codigo": "EIPD-00", "version": "0.2", "clave": "EIPD-00@0.2",
              "ruta": f"{KIT}/plantillas/v0.2/EIPD-00.docx",
              "sha256": "f9f1378f5fcaa434acefbae549cd61ab269615354fbe5b7a499273b9f960a77f",
              "aprobacion": "governance/apoyo/BIBLIOTECA_ESTADO.md §9.4"},)
# Desviaciones aprobadas frente a los originales del kit, que no se editan (BIBLIOTECA_ESTADO.md §10).
DESVIACIONES = {"EIPD-00": {
    "fuentes": "N01;N02;N03;N09;N11",
    "retirar": {"CATEGORIAS_ESPECIALES_GRAN_ESCALA", "REQUERIMIENTO_O_NO_IDENTIFICADO", "SI_NO"},
    "anadir": {"BIOMETRIA_NUEVO_O_EXISTENTE", "BIOMETRIA_SI_NO", "CAT_ESPECIAL", "CONSULTA_AUTORIDAD_REFERENCIA",
               "ESTADO_DOCUMENTO", "EVALUADOR_ALTO_RIESGO", "EVALUADOR_BIOMETRIA", "EVALUADOR_GRAN_ESCALA",
               "EVALUADOR_OBSERVACION_PUBLICA", "EVALUADOR_OTRO_SUPUESTO", "EVALUADOR_PERFILES",
               "EVALUADOR_REQUERIMIENTO", "EVIDENCIA_BIOMETRIA", "EVIDENCIA_GRAN_ESCALA",
               "EVIDENCIA_OBSERVACION_PUBLICA", "EVIDENCIA_PERFILES", "FECHA_LIMITE_DATOS", "FECHA_VERSION",
               "GRAN_ESCALA", "OTRO_SUPUESTO_RESPUESTA", "PENAL", "REQUERIMIENTO_AUTORIDAD",
               "REQUERIMIENTO_REFERENCIA"},
}}
REFERENCIA_DESVIACIONES = "governance/apoyo/BIBLIOTECA_ESTADO.md §10"


# ¤adpa
def _sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


# ¤adpa
def _hashes_kit(raiz: Path) -> dict[str, str]:
    hashes = {}
    for linea in (raiz / MANIFIESTO_KIT).read_text(encoding="utf-8").splitlines():
        if linea.strip():
            sha, ruta = linea.split(maxsplit=1)
            hashes[ruta.strip()] = sha
    return hashes


# ¤adpa
def resolver_ruta(ruta_kit: str) -> str:
    for antigua, actual in RUTAS_HEREDADAS.items():
        if ruta_kit.startswith(antigua):
            return actual + ruta_kit[len(antigua):]
    raise ErrorNegocio("BIB_ARCHIVO_INVALIDO")


# ¤adpa
def construir_manifiesto(raiz: Path) -> dict:
    """Determinista: mismo kit, mismo manifiesto. No contiene secretos ni datos de clientes."""
    especificacion = json.loads((raiz / ESPECIFICACION).read_text(encoding="utf-8"))
    hashes = _hashes_kit(raiz)
    entradas = []
    for plantilla in especificacion["templates"]:
        disponibilidad = DISPONIBILIDAD[plantilla["estado"]]
        archivo = None
        if disponibilidad == "con_archivo":
            relativa = resolver_ruta(plantilla["archivo"])
            archivo = {"ruta_kit": plantilla["archivo"], "ruta": f"{KIT}/{relativa}", "sha256": hashes[relativa]}
        entrada = {
            "codigo": plantilla["codigo"], "version": plantilla["version"], "disponibilidad": disponibilidad,
            **{campo: str(plantilla[campo]) for campo in COLUMNAS}, "archivo": archivo,
            "metadatos": {k: v for k, v in sorted(plantilla.items()) if k not in FUERA_DE_METADATOS},
        }
        desviacion = DESVIACIONES.get(entrada["codigo"])
        if desviacion:
            entrada["fuentes"] = desviacion["fuentes"]
            campos = set(entrada["metadatos"]["campos_template"]) - desviacion["retirar"] | desviacion["anadir"]
            entrada["metadatos"] = {**entrada["metadatos"], "campos_template": sorted(campos),
                                    "desviaciones": REFERENCIA_DESVIACIONES}
        entradas.append(entrada)
    derivados = [{"codigo": d["codigo"], "version": d["version"], "clave": d["clave"], "aprobacion": d["aprobacion"],
                  "archivo": {"ruta": d["ruta"], "sha256": d["sha256"]}} for d in DERIVADOS]
    return {"clave": CLAVE_INICIAL, "corte": especificacion["as_of"],
            "fuente": {"ruta": ESPECIFICACION, "sha256": _sha256(raiz / ESPECIFICACION)},
            "entradas": sorted(entradas, key=lambda e: e["codigo"]), "derivados": derivados}


# ¤adpa
def _verificar_archivo(raiz: Path, codigo: str, version: str, archivo: dict, formato: str,
                       huellas: dict[str, str]) -> tuple[dict | None, str | None]:
    """`huellas` es la referencia aprobada por ruta relativa al kit: MANIFIESTO.sha256 o DERIVADOS."""
    base = (raiz / KIT).resolve()
    ruta = (raiz / archivo["ruta"]).resolve()
    if base not in ruta.parents or not ruta.is_file():
        return None, f"{codigo}: archivo inexistente o fuera del kit"
    datos = ruta.read_bytes()
    sha = hashlib.sha256(datos).hexdigest()
    if sha != archivo["sha256"] or huellas.get(ruta.relative_to(base).as_posix()) != sha:
        return None, f"{codigo} {version}: SHA-256 no coincide con la huella aprobada"
    if len(datos) > MAX_BYTES:
        return None, f"{codigo}: supera 10 MiB"
    try:
        validar_archivo(ArchivoMaestro(nombre=ruta.name, contenido_base64=base64.b64encode(datos).decode(),
                                       generacion=1), formato)
    except ErrorNegocio:
        return None, f"{codigo}: no abre como {formato} válido"
    return {"codigo": codigo, "version": version, "ruta": archivo["ruta"], "sha256": sha, "tipo": formato,
            "tamano": len(datos), "apertura": "ok"}, None


# ¤adpa
def verificar_manifiesto(manifiesto: dict, raiz: Path) -> dict:
    """Sin escritura: comprueba conteos, reproducibilidad, hashes y apertura de cada archivo."""
    errores: list[str] = []
    entradas = manifiesto.get("entradas", [])
    codigos = [e["codigo"] for e in entradas]
    if len(codigos) != 50 or len(set(codigos)) != 50:
        errores.append(f"Se esperaban 50 códigos únicos; hay {len(set(codigos))} únicos de {len(codigos)}")
    conteo = {clave: sum(e["disponibilidad"] == clave for e in entradas) for clave in ESPERADO}
    if conteo != ESPERADO:
        errores.append(f"Conteo por disponibilidad {conteo}; se esperaba {ESPERADO}")
    if manifiesto != construir_manifiesto(raiz):
        errores.append("El manifiesto no coincide con el que se reconstruye desde el kit")
    hashes, archivos = _hashes_kit(raiz), []
    for entrada in entradas:
        if (entrada["disponibilidad"] == "con_archivo") != (entrada.get("archivo") is not None):
            errores.append(f"{entrada['codigo']}: solo las entradas con archivo llevan archivo")
            continue
        if entrada.get("archivo"):
            resultado, error = _verificar_archivo(raiz, entrada["codigo"], entrada["version"], entrada["archivo"],
                                                  entrada["formato"], hashes)
            if error:
                errores.append(error)
            else:
                archivos.append(resultado)
    con_archivo = {e["codigo"]: e for e in entradas if e.get("archivo")}
    aprobadas = {(d["codigo"], d["version"]): d for d in DERIVADOS}
    base, derivados = (raiz / KIT).resolve(), []
    for derivado in manifiesto.get("derivados", []):
        codigo, version = derivado["codigo"], derivado["version"]
        aprobado, inicial = aprobadas.get((codigo, version)), con_archivo.get(codigo)
        if aprobado is None or inicial is None or inicial["version"] == version:
            errores.append(f"{codigo} {version}: derivado sin aprobación registrada o sin versión inicial")
            continue
        relativa = (raiz / aprobado["ruta"]).resolve()
        huellas = {relativa.relative_to(base).as_posix(): aprobado["sha256"]} if base in relativa.parents else {}
        resultado, error = _verificar_archivo(raiz, codigo, version, derivado["archivo"], inicial["formato"], huellas)
        if error:
            errores.append(error)
        else:
            derivados.append(resultado)
    return {"clave": manifiesto.get("clave"), "entradas": len(entradas), **conteo,
            "archivos": archivos, "derivados": derivados, "errores": errores}


# ¤adpa
def cargar_manifiesto(raiz: Path) -> dict:
    return json.loads((raiz / MANIFIESTO_INICIAL).read_text(encoding="utf-8"))


# ¤adpa
def _fila_catalogo(entrada: dict) -> dict:
    return {**{campo: entrada[campo] for campo in COLUMNAS},
            "disponibilidad": entrada["disponibilidad"], "metadatos": entrada["metadatos"]}


# ¤adpa
async def _planificar(session: AsyncSession, manifiesto: dict, clave: str) -> list[dict]:
    """Primera pasada sin escritura: cualquier diferencia con lo existente es conflicto, no reemplazo."""
    plan, conflictos = [], []
    for entrada in manifiesto["entradas"]:
        codigo = entrada["codigo"]
        await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:codigo, 0))"), {"codigo": codigo})
        catalogo = (await session.execute(text(
            "SELECT nombre, familia, tipo, naturaleza, etapa, formato, fuentes, disponibilidad, metadatos "
            "FROM biblioteca_catalogo WHERE codigo=:c"
        ), {"c": codigo})).mappings().first()
        if catalogo is not None and dict(catalogo) != _fila_catalogo(entrada):
            conflictos.append(codigo)
        version = None
        if entrada["archivo"]:
            version = (await session.execute(text(
                "SELECT id, sha256 FROM biblioteca_versiones WHERE codigo=:c AND version=:v"
            ), {"c": codigo, "v": entrada["version"]})).mappings().first()
            if version is not None and version["sha256"] != entrada["archivo"]["sha256"]:
                conflictos.append(codigo)
        registrada = (await session.execute(text(
            "SELECT 1 FROM biblioteca_importaciones WHERE clave=:k AND codigo=:c"
        ), {"k": clave, "c": codigo})).first()
        plan.append({"entrada": entrada, "catalogo": catalogo is not None,
                     "version_id": version["id"] if version else None, "registrada": registrada is not None})
    for derivado in manifiesto.get("derivados", []):
        version = (await session.execute(text(
            "SELECT id, sha256 FROM biblioteca_versiones WHERE codigo=:c AND version=:v"
        ), {"c": derivado["codigo"], "v": derivado["version"]})).mappings().first()
        if version is not None and version["sha256"] != derivado["archivo"]["sha256"]:
            conflictos.append(derivado["codigo"])
        registrada = (await session.execute(text(
            "SELECT 1 FROM biblioteca_importaciones WHERE clave=:k AND codigo=:c"
        ), {"k": derivado["clave"], "c": derivado["codigo"]})).first()
        plan.append({"derivado": derivado, "version_id": version["id"] if version else None,
                     "registrada": registrada is not None})
    if conflictos:
        raise ErrorNegocio("BIB_CONFLICTO_VERSION")
    return plan


# ¤adpa
async def _crear_version(session: AsyncSession, actor: str, raiz: Path, codigo: str, version: str,
                         formato: str, archivo: dict) -> str:
    version_id, ruta = str(uuid4()), raiz / archivo["ruta"]
    await session.execute(text(
        "INSERT INTO biblioteca_versiones(id,codigo,version,formato,responsable_id,autores,archivo,nombre_archivo,sha256) "
        "VALUES (:id,:codigo,:version,:formato,:actor,CAST(:autores AS jsonb),:archivo,:nombre,:sha)"
    ), {"id": version_id, "codigo": codigo, "version": version, "formato": formato, "actor": actor,
        "autores": json.dumps([actor]), "archivo": ruta.read_bytes(), "nombre": ruta.name, "sha": archivo["sha256"]})
    return version_id


# ¤adpa
async def _registrar(session: AsyncSession, actor: str, clave: str, codigo: str, version_id: str | None,
                     archivo: dict | None) -> None:
    await session.execute(text(
        "INSERT INTO biblioteca_importaciones(clave,codigo,version_id,origen,tipo,tamano,sha256,apertura,ejecutada_por) "
        "VALUES (:clave,:codigo,:version_id,:origen,:tipo,:tamano,:sha,:apertura,:actor)"
    ), {"clave": clave, "codigo": codigo, "version_id": version_id if archivo else None,
        "origen": archivo["ruta"] if archivo else None, "tipo": archivo["tipo"] if archivo else None,
        "tamano": archivo["tamano"] if archivo else None, "sha": archivo["sha256"] if archivo else None,
        "apertura": "ok" if archivo else "sin_archivo", "actor": actor})


# ¤adpa
async def importar(session: AsyncSession, actor: str, manifiesto: dict, raiz: Path, clave: str = CLAVE_INICIAL) -> dict:
    """Importa en la transacción del llamador; el llamador confirma o revierte."""
    informe = verificar_manifiesto(manifiesto, raiz)
    if informe["errores"]:
        raise ErrorNegocio("BIB_ARCHIVO_INVALIDO")
    await autorizar(session, actor, Capacidad.EDITOR)
    await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:k, 108))"), {"k": clave})
    archivos = {a["codigo"]: a for a in informe["archivos"]}
    derivados = {(d["codigo"], d["version"]): d for d in informe["derivados"]}
    resultado = {"clave": clave, "catalogo_creadas": 0, "versiones_creadas": 0, "importaciones_creadas": 0}
    for paso in await _planificar(session, manifiesto, clave):
        if "derivado" in paso:
            derivado = paso["derivado"]
            archivo = derivados[(derivado["codigo"], derivado["version"])]
            version_id = paso["version_id"]
            if version_id is None:
                version_id = await _crear_version(session, actor, raiz, derivado["codigo"], derivado["version"],
                                                  archivo["tipo"], derivado["archivo"])
                resultado["versiones_creadas"] += 1
            if not paso["registrada"]:
                await _registrar(session, actor, derivado["clave"], derivado["codigo"], version_id, archivo)
                resultado["importaciones_creadas"] += 1
            continue
        entrada = paso["entrada"]
        if not paso["catalogo"]:
            fila = _fila_catalogo(entrada)
            await session.execute(text(
                "INSERT INTO biblioteca_catalogo(codigo, nombre, familia, tipo, naturaleza, etapa, formato, fuentes, "
                "disponibilidad, metadatos) VALUES (:codigo, :nombre, :familia, :tipo, :naturaleza, :etapa, :formato, "
                ":fuentes, :disponibilidad, CAST(:metadatos AS jsonb))"
            ), {**fila, "codigo": entrada["codigo"], "metadatos": json.dumps(fila["metadatos"], ensure_ascii=False)})
            resultado["catalogo_creadas"] += 1
        version_id = paso["version_id"]
        if entrada["archivo"] and version_id is None:
            version_id = await _crear_version(session, actor, raiz, entrada["codigo"], entrada["version"],
                                              entrada["formato"], entrada["archivo"])
            resultado["versiones_creadas"] += 1
        if not paso["registrada"]:
            await _registrar(session, actor, clave, entrada["codigo"], version_id, archivos.get(entrada["codigo"]))
            resultado["importaciones_creadas"] += 1
    return resultado
