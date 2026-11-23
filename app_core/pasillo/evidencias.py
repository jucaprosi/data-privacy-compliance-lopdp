# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
"""Capacidades de la sala Evidencias para otras salas."""
from typing import Optional


def huella_registrada(tenant_id: str, sha256: str) -> Optional[str]:
    """Devuelve la huella normalizada si es válida y existe en la organización; si no, None."""
    from features.evidencias import evidencias_service

    try:
        huella = evidencias_service.normalizar_sha256(sha256)
    except evidencias_service.HashInvalido:
        return None
    return huella if evidencias_service.verificar_hash(tenant_id, huella) is not None else None


# === ADPA-06 ===
# ¤adpa Sección reservada del andamiaje ADPA-06 en este pasillo.
# === fin ADPA-06 ===

# === DIAG-04 ===
# Sección reservada para DIAG-04.
# === fin DIAG-04 ===

# === DEMO-03e ===
# ¤demo Copia y siembra de la sala para la demo «Cooperativa Demo»; la lógica vive en el motor de la sala.
async def clonar_desde_plantilla(session, origen: str, destino: str, mapa_ids: dict) -> dict:
    from features.evidencias import evidencias_service

    return await evidencias_service.clonar_desde_plantilla(session, origen, destino, mapa_ids)


async def sembrar_en_plantilla(session, plantilla_id: str, datos: dict) -> None:
    from features.evidencias import evidencias_service

    await evidencias_service.sembrar_en_plantilla(session, plantilla_id, datos)
# === fin DEMO-03e ===


# === CAPA-04 ===
async def custodiar_acta_auditoria(
    session,
    tenant_id: str,
    user_id: str,
    *,
    contenido: bytes,
    control_refs: list[str],
    nombre: str,
) -> dict:
    """Custodia el acta de auditoría como evidencia tipo 'acta_auditoria' (R4)."""
    from features.evidencias import evidencias_service

    return await evidencias_service.custodiar_documento_generado(
        session,
        tenant_id,
        user_id,
        contenido=contenido,
        tipo_mime="text/plain",
        tipo_evidencia="acta_auditoria",
        control_refs=control_refs,
        nombre=nombre,
    )


async def leer_contenido_acta(
    session,
    tenant_id: str,
    user_id: str,
    sha256: str,
) -> str:
    """Lee el texto del acta custodiada desde el almacén de evidencias (R4)."""
    from features.evidencias import evidencias_service

    almacen = evidencias_service.almacen_de_evidencias()
    clave = f"{tenant_id}/{sha256}"
    datos = almacen.descargar(clave, evidencias_service.TAMANO_MAXIMO_BYTES)
    if datos is None:
        raise ValueError("Acta no encontrada en el almacén de evidencias.")
    return datos.decode("utf-8")
# === fin CAPA-04 ===


# === FOR-01 ===
async def custodiar_constancia_formacion(
    session,
    tenant_id: str,
    user_id: str,
    *,
    contenido: bytes,
    nombre: str,
) -> dict:
    """R2: Custodia la constancia de formación vinculada al control P73."""
    from features.evidencias import evidencias_service

    return await evidencias_service.custodiar_documento_generado(
        session,
        tenant_id,
        user_id,
        contenido=contenido,
        tipo_mime="text/plain",
        tipo_evidencia="capacitacion",
        control_refs=["P73"],
        nombre=nombre,
    )
# === fin FOR-01 ===


# === EVI-04 ===
# ¤evidencias Custodia de documentos generados: el llamador ya autorizó; no exponer por router.
async def custodiar_documento_generado(session, tenant_id: str, user_id: str, **datos) -> dict:
    from features.evidencias import evidencias_service

    return await evidencias_service.custodiar_documento_generado(session, tenant_id, user_id, **datos)
# === fin EVI-04 ===

# === INC-02 ===
# ¤evidencias Huella de un documento custodiado de la organización, con la misma fuente que
# GET /evidencias/documentos (evidencias_documentos); None si no es válida o no está custodiada.
async def huella_custodiada(session, tenant_id: str, user_id: str, sha256: str) -> Optional[str]:
    from features.evidencias import evidencias_service

    try:
        huella = evidencias_service.normalizar_sha256(sha256)
    except evidencias_service.HashInvalido:
        return None
    documentos = await evidencias_service.listar_documentos(session, tenant_id, user_id)
    return huella if any(d.sha256 == huella for d in documentos) else None
# === fin INC-02 ===

# === MTGE-03 ===
# Sección reservada para MTGE-03.
# === fin MTGE-03 ===


# === TER-02 ===
async def custodiar_informe_garantias(
    session,
    tenant_id: str,
    user_id: str,
    *,
    contenido: bytes,
    nombre: str,
) -> dict:
    """Custodia el informe de revisión de garantías de un encargado."""
    from features.evidencias import evidencias_service

    return await evidencias_service.custodiar_documento_generado(
        session,
        tenant_id,
        user_id,
        contenido=contenido,
        tipo_mime="text/plain",
        tipo_evidencia="acta_auditoria",
        control_refs=["P73"],
        nombre=nombre,
    )


async def custodiar_archivo_proveedor(
    session,
    tenant_id: str,
    *,
    contenido: bytes,
    nombre: str,
    tipo_mime: str = "application/octet-stream",
) -> dict:
    """Custodia un archivo de evidencia adjuntado por el proveedor."""
    from features.evidencias import evidencias_service

    return await evidencias_service.custodiar_documento_generado(
        session,
        tenant_id,
        "portal_proveedor",
        contenido=contenido,
        tipo_mime=tipo_mime,
        tipo_evidencia="acuse",
        control_refs=["P73"],
        nombre=nombre,
    )
# === fin TER-02 ===

# === CAPA-03 ===
# ¤evidencias-vigencia ¤controles-periodicos Vigencia de las huellas, leída solo de la sala Evidencias (EVI-02).
async def vigencia_por_huella(session, tenant_id: str, user_id: str, huellas: list[str]) -> dict:
    """Por cada huella con documento registrado: la fecha de vencimiento más tardía (None = sin vencimiento).

    Las huellas sin documento registrado no aparecen: la sala Evidencias no les conoce vigencia.
    Se lista con el rol `dpo` porque la base exige que el DPO vea todo documento (ck_evidencias_atributos_dpo).
    """
    from features.evidencias import evidencias_service

    buscadas = set(huellas)
    vigencias: dict = {}
    if not buscadas:
        return vigencias
    documentos = await evidencias_service.listar_atributos(session, tenant_id, user_id, "dpo")
    for d in documentos:
        if d.sha256 not in buscadas:
            continue
        previa = vigencias.get(d.sha256, d.vence_en)
        vigencias[d.sha256] = None if previa is None or d.vence_en is None else max(previa, d.vence_en)
    return vigencias
# === fin CAPA-03 ===
