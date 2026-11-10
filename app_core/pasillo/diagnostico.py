# ¤adpa
"""Capacidades de la sala Diagnóstico para otras salas."""


def catalogo_de_controles() -> list[dict]:
    from features.diagnostico import diagnostico_service

    return diagnostico_service.obtener_catalogo_controles_p1_p80()


def sanitizar_textos(textos: list[str]) -> list[str]:
    """Anonimiza con un solo sanitizador, de modo que un mismo nombre recibe el mismo sustituto."""
    from features.diagnostico import diagnostico_service

    sanitizador = diagnostico_service.NERSanitizer()
    return [sanitizador.sanitize(texto) for texto in textos]


# --- INICIO ADPA-04 ---
def politica_evidencia() -> str:
    from features.diagnostico import diagnostico_service

    return diagnostico_service.politica_evidencia()


async def listar_respuestas(session, tenant_id: str, user_id: str) -> list:
    from features.diagnostico import diagnostico_service

    return await diagnostico_service.listar_respuestas(session, tenant_id, user_id)


async def listar_resultados(session, tenant_id: str, user_id: str) -> list:
    from features.diagnostico import diagnostico_service

    return await diagnostico_service.listar_resultados(session, tenant_id, user_id)


def respuesta_control_desde_fila(fila, **opciones):
    from features.diagnostico import diagnostico_service

    return diagnostico_service.respuesta_control_desde_fila(fila, **opciones)


def evaluar_assessment_por_dimension(respuestas: list):
    from features.diagnostico import diagnostico_service

    return diagnostico_service.evaluar_assessment_por_dimension(respuestas)


def es_resultado_anterior(indicadores) -> bool:
    from features.diagnostico import diagnostico_service

    return diagnostico_service.es_resultado_anterior(indicadores)


def estado_pendiente() -> str:
    from features.diagnostico import diagnostico_service

    return diagnostico_service.EstadoCumplimiento.PENDIENTE.value


def es_brecha_critica(brecha) -> bool:
    from features.diagnostico import diagnostico_service

    return brecha.severidad == diagnostico_service.SeveridadBrecha.CRITICO


def nuevo_sanitizador():
    """Un sanitizador por contexto: un mismo nombre recibe el mismo sustituto."""
    from features.diagnostico import diagnostico_service

    return diagnostico_service.NERSanitizer()
# --- FIN ADPA-04 ---


# === ADPA-06 ===
# ¤adpa Sección reservada del andamiaje ADPA-06 en este pasillo.
# === fin ADPA-06 ===

# === DIAG-11 ===
# ¤diagnostico Consulta para EVI-01 y DIAG-12: ¿la organización ya selló el diagnóstico real?
async def diagnostico_real_sellado(session, tenant_id: str, user_id: str | None = None) -> bool:
    from features.diagnostico import diagnostico_service

    return await diagnostico_service.diagnostico_real_sellado(session, tenant_id, user_id)
# === fin DIAG-11 ===

# === ORG-15 ===
# Sección reservada para ORG-15 (cartera por pertenencia).
# === fin ORG-15 ===

# === EVI-01 ===
# Sección reservada para EVI-01.
# === fin EVI-01 ===

# === DIAG-04 ===
# Sección reservada para DIAG-04.
# === fin DIAG-04 ===
