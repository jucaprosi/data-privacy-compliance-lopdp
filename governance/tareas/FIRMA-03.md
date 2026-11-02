+++
id = "FIRMA-03"
titulo = "Persistencia de sesiones de firma (firma_sessions) y compuerta async"
ola = "backlog"
estado = "en_curso"
sala = "firma_electronica"
depende_de = ["FIRMA-01"]
propiedad = ["alembic/versions/20261103_firma_sessions.py", "features/firma_electronica/domain/entities.py", "features/firma_electronica/services/firma_session_engine.py", "features/firma_electronica/services/__init__.py", "features/firma_electronica/firma_electronica_service.py#FIRMA-03", "tests/test_firma_session_persistencia.py", "governance/especificaciones/FIRMA-03.md"]
arbitro = "pytest tests/test_firma_session_persistencia.py contra la rama Neon de la persona (incluido RLS con lopdp_app) + alembic heads con una sola cabeza + suite completa + scripts/verificar_especificaciones.py"
rastros = ["¤firma-electronica"]
+++

# FIRMA-03 · Persistencia de sesiones de firma (`firma_sessions`) y compuerta async

**Objetivo.** Llevar la sala `firma_electronica` al BBAP paso 2: persistencia real multi-organización de las sesiones de firma y compuerta `async`, conservando los bocetos de FIRMA-01 como aliases de compatibilidad.

**Contrato:** `governance/especificaciones/FIRMA-03.md` (manda sobre esta ficha en datos, funciones y aceptación).

## Entrega
- Migración `20261103_firma_sessions` con RLS (`ENABLE` y `FORCE`) y permisos mínimos de `lopdp_app`.
- Entidad `FirmaSession` y motor con `crear_sesion_firma`, `obtener_sesion`, `marcar_firmado` y `listar_sesiones`, con auditoría en `audit_events` al crear y al firmar.
- Compuerta que reexporta las funciones nuevas y conserva los `boceto_*`.
- Solo backend: sin frontend ni integración real con ANF o UniverselD.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad.
