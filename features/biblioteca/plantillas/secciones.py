# ¤adpa
# ¤¤developer-architect
"""Asistentes por secciones de AVI-01, EIPD-00 y PRO-01 (BIB-208).

- AVI: finalidades como colección sin tope (los tokens «_1» y «_2» del maestro son ejemplo); el bloque
  del DPD y el de retiro del consentimiento se omiten enteros cuando no corresponden; sin LEG-01 validada
  no se acepta.
- EIPD: un bloque por criterio (criterion_id, respuesta, evidencia); un disparador «Sí» sostiene
  «Requiere EIPD»; un «Desconocido» impide concluir que no hay obligación. Decide una persona.
- PRO: políticas por derecho y roles operativos; los campos de una solicitud concreta solo se nombran en
  el anexo y se rechazan como valores.
"""
from features.biblioteca.plantillas.captura import (
    Bloque, ContextoServidor, EntradaFicha, Pendiente, ResultadoFicha, Valor, es_servidor, exigir_conocidos,
    fecha_real, rechazar_servidor, revisar_valor, texto, vacio,
)
from api.errores import ErrorNegocio
from features.biblioteca.plantillas.mapas import MapaFicha

AVI_FINALIDADES = ("finalidad_1", "base_1_y_sustento", "obligatoriedad_y_consecuencias_1", "finalidad_2_si_aplica",
                   "base_2_y_sustento", "opcionalidad_y_consecuencias_2")
AVI_DPD = ("nombre_dpd", "direccion_dpd", "telefono_dpd", "correo_dpd")
AVI_RETIRO = ("canal_retiro", "efectos_retiro")
AVI_AUTOMATIZADAS = ("logica_comprensible", "datos_utilizados", "efectos_previstos", "canal_revision_humana")
EIPD_POR_CRITERIO = ("si_no", "si_no_desconocido")
PRO_POR_DERECHO = ("derecho", "articulo", "evento_inicial", "plazo_unidad_calendario", "motivo_y_fundamento_o_no_aplica")
PRO_ANEXO = ("solicitud_id", "fecha_hora_recepcion", "fecha_limite_validada")
FUNCIONES_PRO = ("recepción", "búsqueda", "ejecución", "revisión", "aprobación")
CONSENTIMIENTO = "CONSENTIMIENTO"
SI, NO, DESCONOCIDO = "Sí", "No", "Desconocido"
REQUIERE, SIN_OBLIGACION, INSUFICIENTE = (
    "Requiere EIPD", "No se identifica obligación con la evidencia actual", "Información insuficiente")


def _pendiente(campo: str, motivo: str, fila: int | None = None) -> Pendiente:
    return Pendiente(campo=campo, motivo=motivo, fila=fila)


def _coleccion(entrada: EntradaFicha, nombre: str, obligatorios: tuple[str, ...], etiqueta: str):
    filas = entrada.colecciones.get(nombre, [])
    pendientes = [] if filas else [_pendiente(nombre, f"Registre al menos una {etiqueta}.")]
    for numero, fila in enumerate(filas, start=1):
        pendientes += [_pendiente(f"{nombre}.{c}", "Obligatorio en cada elemento.", numero)
                       for c in obligatorios if vacio(fila.get(c))]
    return filas, pendientes


def _bloques_coleccion(seccion: str, filas: list[dict[str, Valor]]) -> list[Bloque]:
    return [Bloque(seccion=seccion, clave=clave, valor=texto(valor), indice=numero)
            for numero, fila in enumerate(filas, start=1) for clave, valor in fila.items() if not vacio(valor)]


def _condicion(entrada: EntradaFicha, nombre: str, pregunta: str, pendientes: list[Pendiente]) -> bool | None:
    if nombre not in entrada.condiciones:
        pendientes.append(_pendiente(f"condiciones.{nombre}", pregunta))
        return None
    return entrada.condiciones[nombre]


def _control(campo_clave: str, contexto: ContextoServidor, version: int) -> str | None:
    return {"elabora": contexto.actor_id, "fecha": contexto.fecha.isoformat(),
            "organizacion_id": contexto.organizacion_id, "version_cliente": str(version)}.get(campo_clave)


def _reglas_avi(entrada: EntradaFicha, pendientes: list[Pendiente]):
    finalidades, faltan = _coleccion(entrada, "purposes", (
        "description", "legal_basis_id", "legal_basis_rationale", "data_delivery_requirement",
        "delivery_consequences"), "finalidad")
    pendientes += faltan
    exigibles: set[str] = set()
    omitir: dict[str, tuple[str, ...]] = {}
    if entrada.condiciones.get("leg_validada") is not True:
        pendientes.append(_pendiente("condiciones.leg_validada",
                                     "Las bases deben estar validadas en LEG-01 antes de emitir el aviso."))
    dpd = _condicion(entrada, "tiene_dpd", "Confirme si la organización tiene DPD.", pendientes)
    if dpd:
        exigibles.update(AVI_DPD)
    elif dpd is False:
        omitir["Delegado de protección de datos"] = AVI_DPD
    if any(texto(f.get("legal_basis_id")).upper() == CONSENTIMIENTO for f in finalidades):
        exigibles.update(AVI_RETIRO)
    else:
        omitir["Retiro del consentimiento"] = AVI_RETIRO
    indirecta = _condicion(entrada, "recoleccion_indirecta", "Indique si hay recolección indirecta.", pendientes)
    if indirecta:
        exigibles.add("fuente_y_contexto")
    elif indirecta is False:
        omitir["Fuente de recolección indirecta"] = ("fuente_y_contexto",)
    automatizadas = texto(entrada.valores.get("existencia_o_ausencia_verificada"))
    if automatizadas == SI:
        exigibles.update(AVI_AUTOMATIZADAS)
    elif automatizadas == NO:
        omitir["Decisiones automatizadas"] = AVI_AUTOMATIZADAS
    return AVI_FINALIDADES, exigibles, omitir, _bloques_coleccion("Finalidades repetibles", finalidades), None


def recomendacion_eipd(criterios: list[dict[str, Valor]]) -> str:
    respuestas = {texto(c.get("answer")) for c in criterios}
    if SI in respuestas:
        return REQUIERE
    if DESCONOCIDO in respuestas or not criterios:
        return INSUFICIENTE
    return SIN_OBLIGACION


def _reglas_eipd(entrada: EntradaFicha, pendientes: list[Pendiente]):
    criterios, faltan = _coleccion(entrada, "criteria", ("criterion_id", "answer", "legal_source_version_id"), "criterio")
    pendientes += faltan
    vistos: set[str] = set()
    for numero, criterio in enumerate(criterios, start=1):
        respuesta, ident = texto(criterio.get("answer")), texto(criterio.get("criterion_id"))
        if ident in vistos:
            pendientes.append(_pendiente("criteria.criterion_id", "Criterio repetido.", numero))
        vistos.add(ident)
        if respuesta and respuesta not in (SI, NO, DESCONOCIDO):
            pendientes.append(_pendiente("criteria.answer", "Responda Sí, No o Desconocido.", numero))
        if respuesta in (SI, NO) and vacio(criterio.get("evidence_ids")):
            pendientes.append(_pendiente("criteria.evidence_ids", "Una respuesta firme necesita evidencia.", numero))
    sugerida = recomendacion_eipd(criterios)
    decidido = texto(entrada.valores.get("resultado_eipd"))
    if decidido and sugerida == REQUIERE and decidido != REQUIERE:
        pendientes.append(_pendiente("resultado_eipd", "Hay un disparador confirmado: la recomendación es Requiere EIPD."))
    if decidido == SIN_OBLIGACION and sugerida == INSUFICIENTE:
        pendientes.append(_pendiente("resultado_eipd", "Resuelva los hechos desconocidos antes de concluir."))
    exigibles = {"datos_faltantes", "responsable_obtenerlos"} if decidido == INSUFICIENTE else set()
    if decidido == SIN_OBLIGACION:
        exigibles.add("evento_revision")
    return EIPD_POR_CRITERIO, exigibles, {}, _bloques_coleccion("Criterios y evidencia", criterios), sugerida


def _reglas_pro(entrada: EntradaFicha, pendientes: list[Pendiente]):
    for clave in PRO_ANEXO:
        if not vacio(entrada.valores.get(clave)):
            raise ErrorNegocio("BIB_FICHA_INICIAL_CASO_INDIVIDUAL", detail=f"«{clave}» pertenece al registro operativo.")
    politicas, faltan = _coleccion(entrada, "right_policies", ("right_code", "start_event"), "política por derecho")
    pendientes += faltan
    for numero, politica in enumerate(politicas, start=1):
        regla = ("legal_source_version_id", "duration", "count_unit", "validated_by", "validated_at")
        if any(vacio(politica.get(c)) for c in regla) or not fecha_real(politica.get("validated_at")):
            pendientes.append(_pendiente("right_policies", "Configuración pendiente: falta la regla de cómputo validada.",
                                         numero))
    roles, faltan = _coleccion(entrada, "operational_roles", ("function_code",), "asignación de rol")
    pendientes += faltan
    cubiertas = {texto(r.get("function_code")) for r in roles if not vacio(r.get("role_id")) or not vacio(r.get("group_id"))}
    pendientes += [_pendiente("operational_roles", f"Asigne un cargo o grupo a la función «{f}».")
                   for f in FUNCIONES_PRO if f not in cubiertas]
    bloques = (_bloques_coleccion("Política de gestión de solicitudes", politicas)
               + _bloques_coleccion("Roles operativos", roles))
    return PRO_POR_DERECHO + PRO_ANEXO, set(), {}, bloques, None


REGLAS = {"AVI-01": _reglas_avi, "EIPD-00": _reglas_eipd, "PRO-01": _reglas_pro}


# ¤adpa
def evaluar_secciones(mapa: MapaFicha, entrada: EntradaFicha, contexto: ContextoServidor,
                      tratamientos: frozenset[str] | None) -> ResultadoFicha:
    exigir_conocidos(mapa, entrada.valores)
    pendientes: list[Pendiente] = []
    version = (entrada.version_anterior or 0) + 1
    sustituidos, exigibles, omitir, bloques, sugerida = REGLAS[mapa.codigo](entrada, pendientes)
    omitidas = {clave for claves in omitir.values() for clave in claves}
    for campo in mapa.campos:
        valor = entrada.valores.get(campo.clave)
        if es_servidor(campo):
            rechazar_servidor(campo, valor)
            valor = _control(campo.clave, contexto, version)
        elif campo.clave in sustituidos:
            if campo.clave not in PRO_ANEXO and not vacio(valor):
                raise ErrorNegocio("BIB_FICHA_INICIAL_CAMPO_DESCONOCIDO",
                                   detail=f"«{campo.clave}» se captura en la colección de la ficha.")
            continue
        elif campo.clave in omitidas:
            continue
        else:
            pendientes += revisar_valor(campo, valor, None, campo.clave in exigibles, tratamientos)
        if not vacio(valor):
            bloques.append(Bloque(seccion=campo.seccion or "", clave=campo.clave, valor=texto(valor)))
    return ResultadoFicha(
        codigo=mapa.codigo, modo="secciones", version_esquema=mapa.version_esquema, version=version,
        aceptada=not pendientes, pendientes=pendientes, bloques=bloques, omitidos=sorted(omitir),
        anexo=list(PRO_ANEXO) if mapa.codigo == "PRO-01" else [], recomendacion=sugerida,
        estado_generacion=mapa.estado_generacion,
    )
