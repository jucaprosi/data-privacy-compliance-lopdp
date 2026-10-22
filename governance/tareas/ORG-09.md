+++
id = "ORG-09"
titulo = "Operador de la plataforma: alta de organizaciones e invitación del administrador inicial, sin acceso a los datos de los clientes"
ola = "D"
estado = "pendiente"
sala = "plataforma"
depende_de = ["DEV-01", "SEC-03", "SEC-07", "ORG-00"]
propiedad = ["alembic/versions/*_plataforma_operadores.py", "features/plataforma/**", "api/routers/plataforma.py", "tests/test_plataforma_operador.py"]
arbitro = "pytest tests/test_plataforma_operador.py tests/test_matriz_permisos.py + suite completa contra una rama Neon propia; prueba de mutación documentada"
rastros = ["¤rbac-tenant", "¤seguridad"]
+++

# ORG-09 · Operador de la plataforma («superadmin»)

**Objetivo.** No existe forma de dar de alta una organización ni su primer administrador desde la aplicación: la de producción se creó por SQL a mano, y en modo `oidc` un usuario sin rol en la organización recibe 403. Hace falta un **operador de la plataforma** que gestione la «puerta de entrada» (crear la organización y a quién se invita a administrarla) **sin poder ver los datos que cada cliente trata**.

## Base legal y decisiones del propietario (2026-10-21)
- La plataforma trata los datos de cada cliente **por cuenta de él**: es *encargado del tratamiento* en el sentido del Art. 4 de la LOPDP (Registro Oficial Suplemento 459), y el cliente es el *responsable*. El operador no debe acceder a esos datos por iniciativa propia: solo gestiona el alta.
- **Modelo híbrido:** el operador crea la organización y emite una invitación; quien la acepta se convierte en su `admin_organizacion` y configura el resto.
- **Quién es operador:** la lista la define el propietario fuera del código (no se guardan correos reales en el repositorio).
- **Qué ve el operador:** solo el nombre, el RUC, el estado, la fecha de alta y el correo del administrador inicial de cada organización. Nada de lo que trata la organización.

## Entrega
- Sala nueva `features/plataforma/` con su compuerta `plataforma_service.py` (ADPA): el operador es una **identidad de plataforma**, no un rol de ningún tenant. Tabla `operadores_plataforma` (por `google_sub` o correo verificado) que se puebla con un comando de administración, no por la API.
- Migración `*_plataforma_operadores.py`: `operadores_plataforma`, `invitaciones_organizacion` (organización, correo invitado, *hash* del código —nunca el código en claro—, caducidad, estado: emitida, aceptada, caducada, revocada) y `auditoria_plataforma` (quién, qué, cuándo, sobre qué organización). Permisos a `lopdp_app` sin `DELETE`.
- Endpoints bajo `/api/v1/plataforma` (solo operadores, con identidad verificada de Google mediante `verificar_token_google` de `app_core/security.py`):
  - crear una organización (nombre, RUC, tamaño) y su invitación; listar organizaciones con los metadatos permitidos; revocar una invitación no aceptada.
- **Aceptar la invitación:** un endpoint que recibe el código y un token de Google verificado (sin exigir pertenecer a la organización). Solo se acepta si el **correo verificado de Google coincide** con el invitado, la invitación está vigente y no se ha usado: entonces se crea el usuario (vinculando `google_sub`) y su rol `admin_organizacion`, y se deja evento en `audit_events` y en `auditoria_plataforma`. **Un solo uso.**
- **El operador nunca fija un tenant:** ningún endpoint de plataforma establece `app.current_tenant_id`. Una prueba demuestra que, como `lopdp_app` y sin tenant, el operador no ve filas de tablas con RLS de ninguna organización.
- Pruebas con base real: un no operador recibe 403 en todo `/plataforma`; crear y listar; el listado no expone más que los metadatos permitidos; invitación con correo distinto, caducada, revocada o ya usada se rechaza; la aceptación crea exactamente un `admin_organizacion`; cada acción queda en `auditoria_plataforma`. Sin SQL interpolado.
- **Prueba de mutación documentada:** quitar a propósito la comprobación de que el correo coincide y comprobar que una prueba falla.

## Límites
- No crea pantallas: el panel del operador y la página de aceptación quedan para una tarea de frontend aparte.
- No da al operador ningún acceso de soporte a los datos de un cliente; si algún día hace falta, será otra tarea con autorización explícita del cliente y su rastro.
- No cambia las reglas de roles dentro de la organización (ORG-01, ORG-02, ORG-05).

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
