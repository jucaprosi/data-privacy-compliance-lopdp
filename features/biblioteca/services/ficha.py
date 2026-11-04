# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Ficha de una plantilla (BIB-103): metadatos, variables con su disponibilidad y vista previa demostrativa.

La disponibilidad de los datos de la organización la calcula el llamador (el router, que cruza a Organización
por su compuerta) y llega aquí como un conjunto de claves: esta sala no importa a otra. La vista previa usa
solo valores de ejemplo fijos: nunca datos de la organización ni de otra.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app_core.errors import ErrorNegocio
from features.biblioteca.domain.plantillas_md import TOKEN, metadatos_de, separar

AVISO_VISTA_PREVIA = ("Vista previa demostrativa: los datos son de ejemplo y no pertenecen a ninguna organización. "
                      "El documento real se genera con «Usar en esta organización».")
CONDICION_SI = "#si "
# Variables que no salen de los datos de la organización: se resuelven al crear, al aprobar o las captura la persona.
AL_CREAR = frozenset({"documento.codigo", "documento.nombre", "documento.version", "fecha_emision",
                      "documento.proxima_revision"})
AL_APROBAR = frozenset({"documento.aprobado_por", "documento.fecha_aprobacion"})
EJEMPLOS = {
    "organizacion.razon_social": "Empresa Ejemplo S.A.", "organizacion.nombre_comercial": "Ejemplo",
    "organizacion.ruc": "0000000000001", "organizacion.sector": "Comercio", "organizacion.tamano": "Pequeña",
    "organizacion.direccion": "Calle Ejemplo 123", "organizacion.ciudad": "Quito",
    "organizacion.telefono": "+593 2 000 0000", "organizacion.correo_contacto": "contacto@ejemplo.test",
    "organizacion.correo_privacidad": "privacidad@ejemplo.test", "organizacion.sitio_web": "https://ejemplo.test",
    "representante.nombre": "Nombre Apellido", "representante.identificacion": "0000000000",
    "representante.cargo": "Gerente general", "dpo.nombre": "Delegado de Ejemplo",
    "dpo.correo": "dpd@ejemplo.test", "dpo.fecha_designacion": "2026-01-01",
    "documento.proxima_revision": "2027-01-01", "documento.aprobado_por": "Persona aprobadora",
    "documento.fecha_aprobacion": "2026-01-01", "fecha_emision": "2026-01-01",
    "tratamiento.finalidades": "Finalidad de ejemplo", "tratamiento.categorias_datos": "Datos de identificación",
    "tratamiento.plazo_conservacion": "5 años", "tratamiento.destinatarios": "Destinatario de ejemplo",
}
ETIQUETAS = {
    "organizacion.razon_social": "Razón social", "organizacion.nombre_comercial": "Nombre comercial",
    "organizacion.ruc": "RUC", "organizacion.sector": "Sector", "organizacion.tamano": "Tamaño de empresa",
    "organizacion.direccion": "Domicilio principal", "organizacion.ciudad": "Ciudad",
    "organizacion.telefono": "Teléfono de contacto", "organizacion.correo_contacto": "Correo general de contacto",
    "organizacion.correo_privacidad": "Canal para solicitudes de titulares", "organizacion.sitio_web": "Sitio web",
    "representante.nombre": "Representante legal", "representante.identificacion": "Cédula del representante legal",
    "representante.cargo": "Cargo del representante legal", "dpo.nombre": "Delegado de protección de datos",
    "dpo.correo": "Correo del delegado", "dpo.fecha_designacion": "Fecha de designación del delegado",
    "documento.codigo": "Código del documento", "documento.nombre": "Nombre del documento",
    "documento.version": "Versión de la plantilla", "documento.proxima_revision": "Próxima revisión",
    "documento.aprobado_por": "Quien aprobó", "documento.fecha_aprobacion": "Fecha de aprobación",
    "fecha_emision": "Fecha de emisión", "tratamiento.finalidades": "Finalidades del tratamiento",
    "tratamiento.categorias_datos": "Categorías de datos tratados",
    "tratamiento.plazo_conservacion": "Plazo de conservación", "tratamiento.destinatarios": "Destinatarios o encargados",
}
SQL_COPIA = ("SELECT plantilla_id AS id, codigo, nombre, version, cuerpo_md, origen_plantilla_id, origen_version "
             "FROM biblioteca_mis_plantillas WHERE plantilla_id=:id ORDER BY version DESC LIMIT 1")
SQL_PUBLICADA = ("SELECT v.id, v.codigo, v.version, v.cuerpo_md, v.ficha, c.nombre FROM biblioteca_versiones v "
                 "LEFT JOIN biblioteca_catalogo c ON c.codigo=v.codigo "
                 "WHERE v.id=:id AND v.estado='publicada' AND v.formato='MD'")


# ¤adpa
async def fijar_contexto(session: AsyncSession, usuario_id: str, tenant_id: str) -> None:
    """Organización y persona ya verificadas por la API, para que la RLS decida qué filas existen."""
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true), "
                               "set_config('app.current_user_id', :u, true)"), {"t": tenant_id, "u": usuario_id})


# ¤adpa
def variables_de(meta: dict, cuerpo: str) -> list[dict]:
    """Variables del cuerpo, en orden de aparición, con su etiqueta, origen y obligatoriedad."""
    contexto = {v["clave"]: v for v in meta.get("variables_contexto") or []}
    vistas: dict[str, dict] = {}
    for crudo in TOKEN.findall(cuerpo):
        clave = crudo.strip()
        if clave.startswith(("#", "/")) or clave in vistas:
            continue
        declarada = contexto.get(clave)
        ambito = clave.split(".")[0] if "." in clave else "documento"
        origen = ("persona" if declarada or ambito in ("contexto", "tratamiento")
                  else "al_crear" if clave in AL_CREAR else "al_aprobar" if clave in AL_APROBAR
                  else "delegado" if ambito == "dpo" else "organizacion")
        vistas[clave] = {"clave": clave, "etiqueta": (declarada or {}).get("etiqueta") or ETIQUETAS.get(clave, clave),
                         "ambito": ambito, "origen": origen,
                         "obligatoria": str((declarada or {}).get("obligatoria", "true")).lower() != "false"}
    return list(vistas.values())


# ¤adpa
def vista_previa(cuerpo: str, meta: dict) -> str:
    """Cuerpo con valores de ejemplo fijos y la rama «sí» de cada parte condicional. No lee datos reales."""
    ejemplos = {**EJEMPLOS, "documento.codigo": str(meta.get("codigo", "")), "documento.nombre": str(meta.get("nombre", "")),
                "documento.version": str(meta.get("version", ""))}
    for variable in meta.get("variables_contexto") or []:
        ejemplos[variable["clave"]] = f"[ejemplo: {variable.get('etiqueta', variable['clave'])}]"
    salida, rama = [], "fuera"
    posicion = 0
    for coincidencia in TOKEN.finditer(cuerpo):
        if rama != "no":
            salida.append(cuerpo[posicion:coincidencia.start()])
        posicion = coincidencia.end()
        token = coincidencia.group(1).strip()
        if token.startswith(CONDICION_SI):
            rama = "si"
        elif token == "#sino":
            rama = "no"
        elif token == "/si":
            rama = "fuera"
        elif rama != "no":
            salida.append(ejemplos.get(token, f"[{token}]"))
    if rama != "no":
        salida.append(cuerpo[posicion:])
    return "".join(salida)


# ¤adpa
def clave_disponible(clave: str, origen: str, disponibles: frozenset[str]) -> bool:
    """«Disponible» responde si la organización ya tiene el dato; lo que se resuelve solo o se captura no cuenta como faltante."""
    if origen in ("al_crear", "al_aprobar"):
        return True
    return clave in disponibles if origen in ("organizacion", "delegado") else False


# ¤adpa
async def obtener_ficha(session: AsyncSession, usuario_id: str, tenant_id: str, plantilla_id: str,
                        disponibles: frozenset[str]) -> dict:
    """Ficha de una plantilla SMARTCIDI publicada o de «Mi plantilla» de la organización de la sesión.

    La RLS decide qué filas existen para esta organización: una copia de otra organización, o una versión
    que no está publicada, responde como inexistente.
    """
    await fijar_contexto(session, usuario_id, tenant_id)
    copia = (await session.execute(text(SQL_COPIA), {"id": plantilla_id})).mappings().first()
    if copia is not None:
        fuente, texto, base = "organizacion", copia["cuerpo_md"], dict(copia)
        ficha, origen_id, origen_version = None, copia["origen_plantilla_id"], copia["origen_version"]
    else:
        publicada = (await session.execute(text(SQL_PUBLICADA), {"id": plantilla_id})).mappings().first()
        if publicada is None:
            raise ErrorNegocio("BIB_PLANTILLA_NO_ENCONTRADA")
        fuente, texto, base = "smartcidi", publicada["cuerpo_md"], dict(publicada)
        ficha, origen_id, origen_version = publicada["ficha"], None, None
    meta, cuerpo = metadatos_de(texto), separar(texto)[1]
    variables = [{**v, "disponible": clave_disponible(v["clave"], v["origen"], disponibles)}
                 for v in variables_de(meta, cuerpo)]
    return {
        "id": base["id"], "codigo": base["codigo"], "nombre": base.get("nombre") or meta["nombre"],
        "tipo": meta["tipo"], "fuente": fuente, "version": meta["version"] if fuente == "smartcidi" else base["version"],
        "formato": "MD", "ola": int(meta["ola"]), "validacion_legal": meta["validacion_legal"],
        "estado_editorial": "publicada" if fuente == "smartcidi" else "mi_plantilla",
        "fecha_corte_normativo": str(meta["fecha_corte_normativo"]), "base_lopdp": meta["base_lopdp"],
        "revision_meses": int(meta["revision_meses"]), "ficha": ficha, "avisos": meta.get("avisos") or [],
        "origen_plantilla_id": origen_id, "origen_version": origen_version,
        "cuerpo_markdown": cuerpo, "variables": variables,
        "vista_previa": {"demostrativa": True, "aviso": AVISO_VISTA_PREVIA, "markdown": vista_previa(cuerpo, meta)},
        "acciones": {"usar": True, "copiar": fuente == "smartcidi"},
    }
