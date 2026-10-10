+++
id = "NOTIF-01"
titulo = "Notificaciones por correo (boceto)"
ola = "backlog"
estado = "pendiente"
sala = "notificaciones"
depende_de = ["RM-08"]
propiedad = ["features/notificaciones/**", "tests/test_notificaciones.py"]
arbitro = "boceto aprobado por el usuario"
rastros = ["¤roadmap"]
+++

# NOTIF-01 · Notificaciones por correo (boceto)

**Objetivo.** Avisos al usuario sobre sus tareas asignadas, solo por correo (PRD §5.8).

## Entrega
- Boceto (BBAP, paso 1): proveedor propuesto Resend (plan gratuito: 3 000 al mes y 100 al día), correo mínimo con enlace a la tarea y agrupado por usuario y lote.
- Requiere verificar un dominio remitente (acción del usuario). Eventos además de la asignación: por definir.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
