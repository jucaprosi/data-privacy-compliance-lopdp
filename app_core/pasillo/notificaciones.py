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
