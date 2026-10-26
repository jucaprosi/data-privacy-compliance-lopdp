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
        entradas.append({
            "codigo": plantilla["codigo"], "version": plantilla["version"], "disponibilidad": disponibilidad,
            **{campo: str(plantilla[campo]) for campo in COLUMNAS}, "archivo": archivo,
            "metadatos": {k: v for k, v in sorted(plantilla.items()) if k not in FUERA_DE_METADATOS},
        })
    return {"clave": CLAVE_INICIAL, "corte": especificacion["as_of"],
            "fuente": {"ruta": ESPECIFICACION, "sha256": _sha256(raiz / ESPECIFICACION)},
            "entradas": sorted(entradas, key=lambda e: e["codigo"])}


# ¤adpa
def _verificar_archivo(raiz: Path, entrada: dict, hashes: dict[str, str]) -> tuple[dict | None, str | None]:
    archivo, codigo = entrada["archivo"], entrada["codigo"]
    base = (raiz / KIT).resolve()
    ruta = (raiz / archivo["ruta"]).resolve()
    if base not in ruta.parents or not ruta.is_file():
        return None, f"{codigo}: archivo inexistente o fuera del kit"
    datos = ruta.read_bytes()
    sha = hashlib.sha256(datos).hexdigest()
    if sha != archivo["sha256"] or hashes.get(ruta.relative_to(base).as_posix()) != sha:
        return None, f"{codigo}: SHA-256 no coincide con el manifiesto del kit"
    if len(datos) > MAX_BYTES:
        return None, f"{codigo}: supera 10 MiB"
    try:
        validar_archivo(ArchivoMaestro(nombre=ruta.name, contenido_base64=base64.b64encode(datos).decode(),
                                       generacion=1), entrada["formato"])
    except ErrorNegocio:
        return None, f"{codigo}: no abre como {entrada['formato']} válido"
    return {"codigo": codigo, "ruta": archivo["ruta"], "sha256": sha, "tipo": entrada["formato"],
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
            resultado, error = _verificar_archivo(raiz, entrada, hashes)
            if error:
                errores.append(error)
            else:
                archivos.append(resultado)
    return {"clave": manifiesto.get("clave"), "entradas": len(entradas), **conteo,
            "archivos": archivos, "errores": errores}


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
    if conflictos:
        raise ErrorNegocio("BIB_CONFLICTO_VERSION")
    return plan


# ¤adpa
async def importar(session: AsyncSession, actor: str, manifiesto: dict, raiz: Path, clave: str = CLAVE_INICIAL) -> dict:
    """Importa en la transacción del llamador; el llamador confirma o revierte."""
    informe = verificar_manifiesto(manifiesto, raiz)
    if informe["errores"]:
        raise ErrorNegocio("BIB_ARCHIVO_INVALIDO")
    await autorizar(session, actor, Capacidad.EDITOR)
    await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:k, 108))"), {"k": clave})
    archivos = {a["codigo"]: a for a in informe["archivos"]}
    resultado = {"clave": clave, "catalogo_creadas": 0, "versiones_creadas": 0, "importaciones_creadas": 0}
    for paso in await _planificar(session, manifiesto, clave):
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
            version_id = str(uuid4())
            ruta = raiz / entrada["archivo"]["ruta"]
            await session.execute(text(
                "INSERT INTO biblioteca_versiones(id,codigo,version,formato,responsable_id,autores,archivo,nombre_archivo,sha256) "
                "VALUES (:id,:codigo,:version,:formato,:actor,CAST(:autores AS jsonb),:archivo,:nombre,:sha)"
            ), {"id": version_id, "codigo": entrada["codigo"], "version": entrada["version"],
                "formato": entrada["formato"], "actor": actor, "autores": json.dumps([actor]),
                "archivo": ruta.read_bytes(), "nombre": ruta.name, "sha": entrada["archivo"]["sha256"]})
            resultado["versiones_creadas"] += 1
        if not paso["registrada"]:
            archivo = archivos.get(entrada["codigo"])
            await session.execute(text(
                "INSERT INTO biblioteca_importaciones(clave,codigo,version_id,origen,tipo,tamano,sha256,apertura,ejecutada_por) "
                "VALUES (:clave,:codigo,:version_id,:origen,:tipo,:tamano,:sha,:apertura,:actor)"
            ), {"clave": clave, "codigo": entrada["codigo"], "version_id": version_id if archivo else None,
                "origen": archivo["ruta"] if archivo else None, "tipo": archivo["tipo"] if archivo else None,
                "tamano": archivo["tamano"] if archivo else None, "sha": archivo["sha256"] if archivo else None,
                "apertura": "ok" if archivo else "sin_archivo", "actor": actor})
            resultado["importaciones_creadas"] += 1
    return resultado
