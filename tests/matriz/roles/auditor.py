# ¤rbac-tenant ¤arbitro
"""Matriz del rol auditor (ORG-22): para cada id_accion, si el auditor puede.

Lee las salas de su tenant (rutas sin require_role y GET de CAPA), registra y verifica solo en auditoria_capa,
no ejecuta ni cierra: todo lo demás espera 403. Una clave que falta rompe la carga («auditor sin decidir en <id>»).
"""
ROL = "auditor"

# === ORG-22 ===
PERMITIDO: dict[str, bool] = {
    "ver_assessment": True,
    "ficha_organizacion": True,  # ORG-24: ruta sin require_role, la lee cualquier rol vigente del tenant
    "cerrar_incidente": False,  # INC-03: cambia el estado; solo roles que registran incidentes
    "reabrir_incidente": False,
    "primera_validacion_evidencia": False,  # RM-25a: solo el coordinador
    "descargar_informe_estado": True,
    "ver_hoja_de_ruta": True,
    "generar_roadmap_ia": False,
    "editar_tareas_campos": False,
    "marcar_tarea_completada": False,
    "distribuir_tareas": False,
    "subir_evidencia_url": False,
    "subir_evidencia_reg": False,
    "validar_rechazar_evidencia": False,
    "ver_evidencia": True,
    "listar_atributos_evidencias": True,
    "definir_atributos_evidencia": False,
    "descargar_archivo_evidencia": True,
    "descargar_paquete_inspeccion": True,
    "ver_audit_log": False,
    "gestionar_usuarios_get": False,
    "gestionar_usuarios_post": False,
    "crear_areas": False,
    "editar_areas": False,
    "listar_areas": False,
    "asignar_roles": False,
    "listar_roles": False,
    "revocar_roles": False,
    "configurar_organizacion_get": True,
    "configurar_organizacion_patch": False,
    "datos_documentales_get": True,
    "datos_documentales_patch": False,
    "solicitar_alta_responsable": False,
    "listar_altas_responsable": False,
    "ver_alta_responsable": False,
    "cancelar_alta_responsable": False,
    "aprobar_alta_responsable": False,
    "rechazar_alta_responsable": False,
    "ejecutar_alta_responsable": False,
    "ver_arbol_estructura_organica": False,
    "ver_cobertura_estructura_organica": False,
    "crear_area_estructura_organica": False,
    "editar_area_estructura_organica": False,
    "crear_cargo_organico": False,
    "editar_cargo_organico": False,
    "asignar_titular_cargo_organico": False,
    "solicitar_excepcion_sod": False,
    "listar_excepciones_sod": False,
    "ver_excepcion_sod": False,
    "aprobar_excepcion_sod": False,
    "revocar_excepcion_sod": False,
    "observacion_dpo_excepcion_sod": False,
    "listar_plantillas_cuenta": False,
    "crear_plantilla_cuenta": False,
    "obtener_plantilla_cuenta": False,
    "actualizar_plantilla_cuenta": False,
    "diff_plantilla_cuenta": False,
    "aplicar_maestra_plantilla_cuenta": False,
    "listar_vinculos_documento": True,
    "reemplazar_vinculos_documento": False,
    "listar_documentos_de_tratamiento": True,
    "listar_controles_periodicos": True,
    "crear_control_periodico": False,
    "verificar_control_periodico": True,
    "retirar_control_periodico": False,
    "vencer_controles_periodicos": False,
    "listar_asignaciones_dominios": False,
    "asignar_dominio_diagnostico": False,
    "historial_asignaciones_dominios": False,
    "crear_enlaces_aceptacion": False,
    "listar_aceptaciones": True,
    "verificar_hash_documento": True,
    "ver_estado_alta": False,
    "ver_sugerencias_alta": False,
    "guardar_paso_alta": False,
    "listar_activos_inventario": False,
    "crear_activo_inventario": False,
    "editar_activo_inventario": False,
    "vincular_tratamientos_inventario": False,
    "listar_tratamientos_inventario": False,
    "listar_personas_inventario": False,
    "crear_persona_inventario": False,
    "editar_persona_inventario": False,
    "listar_sedes": False,
    "crear_sede": False,
    "editar_sede": False,
    "retirar_sede": False,
    "listar_clientes_encargo": False,
    "crear_cliente_encargo": False,
    "editar_cliente_encargo": False,
    "retirar_cliente_encargo": False,
    "consultar_validaciones_rat": False,
    "listar_versiones_rat": False,
    "leer_version_rat": False,
    "exportar_rat": False,
    "listar_hallazgos": False,
    "registrar_hallazgos_desde_diagnostico": False,
    "convertir_hallazgos_en_tareas": False,
    "ejecutar_recordatorios": False,
}
# === fin ORG-22 ===


_DUENO: dict[str, str] = {clave: "ORG-22" for clave in PERMITIDO}


def _seccion(ficha: str, claves: dict[str, bool]) -> None:
    """Suma las claves de una ficha; una clave declarada en dos secciones rompe la carga."""
    for clave, puede in claves.items():
        if clave in PERMITIDO:
            raise ValueError(f"auditor: «{clave}» declarada en {_DUENO[clave]} y en {ficha}")
        PERMITIDO[clave] = puede
        _DUENO[clave] = ficha


# === EVI-03 ===
_seccion("EVI-03", {})
# === fin EVI-03 ===

# === DPO-03 ===
_seccion("DPO-03", {"cerrar_consulta_dpo": False})
# === fin DPO-03 ===

# === NORM-02 ===
_seccion("NORM-02", {})
# === fin NORM-02 ===

# === MTGE-03 ===
_seccion("MTGE-03", {
    "eipd_catalogos": True, "eipd_listar": True, "eipd_obtener": True, "eipd_informe": True,
    "eipd_crear": False, "eipd_guardar_paso": False, "eipd_cerrar": False,
})
# === fin MTGE-03 ===

# === TER-01 ===
_seccion("TER-01", {})
# === fin TER-01 ===

# === ORG-20 ===
# Papelera (admin_organizacion e implementador) y exportación completa (solo admin_organizacion): el auditor no.
_seccion("ORG-20", {
    "listar_papelera": False,
    "restaurar_de_papelera": False,
    "solicitar_exportacion": False,
    "consultar_exportacion": False,
    "descargar_exportacion": False,
})
# === fin ORG-20 ===

# === REG-01 ===
_seccion("REG-01", {})
# === fin REG-01 ===

# === BOV-01 ===
_seccion("BOV-01", {})
# === fin BOV-01 ===

# === DLP-01 ===
# El auditor lee los escaneos de su organización (tipos y conteos); no lanza, vincula ni borra (CTO, 2026-11-13).
_seccion("DLP-01", {
    "escanear_muestra_dlp": False,
    "listar_escaneos_dlp": True,
    "vincular_escaneo_dlp_rat": False,
})
# === fin DLP-01 ===

# === INC-02 ===
_seccion("INC-02", {})
# === fin INC-02 ===

# === RAT-07 ===
_seccion("RAT-07", {
    "listar_colectivos_rat": False,  # _permiso_rat sin auditor: 403
    "crear_colectivo_rat": False,
    "editar_colectivo_rat": False,
    "registrar_consentimiento_rat": False,
    "consultar_consentimientos_rat": False,
})
# === fin RAT-07 ===
