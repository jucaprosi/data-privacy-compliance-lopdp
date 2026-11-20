# ¤adpa
"""Capacidades de la sala notificaciones para otras salas (pasillo central, ADPA §3).

Cada función importa la compuerta en su cuerpo; aquí no hay lógica de negocio.
Cada tarea escribe solo dentro de su sección reservada.
"""

# === ADPA-06 ===
# Andamiaje del pasillo de esta sala: secciones reservadas abajo.
# === fin ADPA-06 ===

# === CAPA-03 ===
# === fin CAPA-03 ===

# === DER-01 ===
# === fin DER-01 ===

# === INC-02 ===
# === fin INC-02 ===

# === NORM-02 ===
async def avisar_corrida_normativa_fallida(*, correos: list[str], origen: str, codigos: list[str], app_base_url: str) -> int:
    """Aviso técnico al operador de la plataforma por una corrida de vigilancia normativa fallida.

    Devuelve cuántos correos confirmó el proveedor. Sin datos de resoluciones: solo origen y códigos de error.
    """
    from uuid import uuid4

    from features.notificaciones import notificaciones_service as svc

    notificador = svc.notificador_configurado()
    enlace = f"{app_base_url.rstrip('/')}/normativa?pestana=bitacora"
    texto = (
        f"La búsqueda de novedades normativas ({origen}) terminó con fallo. "
        f"Códigos: {', '.join(codigos) or 'sin códigos'}. Revisa la bitácora: {enlace}"
    )
    enviados = 0
    for correo in correos:
        destinatario = svc.Destinatario(user_id="operador-plataforma", email=correo, nombre="Operador", tenant_id="")
        mensaje = svc.CorreoLoteNotificacion(
            lote_id=str(uuid4()), destinatario=destinatario, canal=svc.CanalNotificacion.CORREO,
            asunto="Vigilancia normativa: la búsqueda de novedades falló", cuerpo_texto=texto,
            cuerpo_html=f"<p>{texto}</p>", tareas=(),
        )
        resultado = await notificador.enviar_correo(mensaje)
        if resultado.estado == svc.EstadoEnvio.ENVIADO:
            enviados += 1
    return enviados
# === fin NORM-02 ===

# === NORM-02b ===
def _texto_aviso_normativo(novedades: list[dict], app_base_url: str) -> tuple[str, str]:
    """Texto plano y HTML del aviso: número, título y enlace interno de cada novedad (corpus público)."""
    from html import escape

    base = app_base_url.rstrip("/")
    filas = [(n["numero_resolucion"], n["titulo"], f"{base}/normativa?resolucion={n['id']}") for n in novedades]
    texto = ("La vigilancia normativa encontró resoluciones nuevas o con una versión nueva de la SPDP:\n"
             + "\n".join(f"- {numero}: {titulo} ({enlace})" for numero, titulo, enlace in filas)
             + f"\nRevísalas en el centro de vigilancia: {base}/normativa")
    items = "".join(f'<li>{escape(numero)}: <a href="{escape(enlace)}">{escape(titulo)}</a></li>'
                    for numero, titulo, enlace in filas)
    html = ("<p>La vigilancia normativa encontró resoluciones nuevas o con una versión nueva de la SPDP:</p>"
            f'<ul>{items}</ul><p><a href="{escape(base)}/normativa">Centro de vigilancia</a></p>')
    return texto, html


async def avisar_novedades_normativas(*, destinatarios: list[dict], novedades: list[dict], app_base_url: str) -> dict:
    """Un aviso por organización (R3), con solo sus destinatarios, por el notificador configurado.

    El puerto de notificaciones lleva un destinatario por mensaje: el aviso de una organización es un lote propio
    (`lote_id`) con un sobre por cada correo de esa organización; nunca hay correos de dos organizaciones en un
    lote ni en un sobre. Cuenta organizaciones: enviada si el proveedor confirma todos sus sobres; fallida si no o
    si el notificador lanza (R6). Devuelve {"enviados", "fallidos"}, sin correos (R8).
    """
    from uuid import uuid4

    from features.notificaciones import notificaciones_service as svc

    notificador = svc.notificador_configurado()
    texto, html = _texto_aviso_normativo(novedades, app_base_url)
    enviados = fallidos = 0
    for organizacion in destinatarios:
        correos = sorted({c for c in [*organizacion["correos_admin"], *organizacion["correos_dpo"]] if c and c.strip()})
        if not correos:
            continue
        lote_id = str(uuid4())
        confirmados = 0
        try:
            for correo in correos:
                destinatario = svc.Destinatario(user_id="", email=correo, nombre="",
                                                tenant_id=organizacion["tenant_id"])
                mensaje = svc.CorreoLoteNotificacion(
                    lote_id=lote_id, destinatario=destinatario, canal=svc.CanalNotificacion.CORREO,
                    asunto="Vigilancia normativa: resoluciones nuevas o modificadas",
                    cuerpo_texto=texto, cuerpo_html=html, tareas=(),
                )
                resultado = await notificador.enviar_correo(mensaje)
                if resultado.estado == svc.EstadoEnvio.ENVIADO:
                    confirmados += 1
        except Exception:  # el fallo de una organización no detiene el aviso a las demás (R6)
            confirmados = -1
        if confirmados == len(correos):
            enviados += 1
        else:
            fallidos += 1
    return {"enviados": enviados, "fallidos": fallidos}
# === fin NORM-02b ===
