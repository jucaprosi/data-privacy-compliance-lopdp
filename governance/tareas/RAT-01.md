+++
id = "RAT-01"
titulo = "El RAT se guarda en el servidor por organización y con los campos de un RAT completo"
ola = "D"
estado = "pendiente"
sala = "rat"
depende_de = ["QA-04"]
propiedad = ["features/rat/domain/models.py", "features/rat/services/rat_engine.py", "features/rat/rat_service.py#RAT-01", "api/routers/rat.py", "alembic/versions/20261024_rat_actividades.py", "tests/test_rat_persistencia.py"]
arbitro = "pytest tests/test_rat_persistencia.py contra una rama Neon de revisión (incluido el aislamiento RLS) + suite completa; prueba de mutación documentada"
rastros = ["¤rat", "¤rbac-tenant"]
+++

# RAT-01 · RAT persistido

**Hallazgo (2026-10-23).** El Registro de Actividades de Tratamiento vive en la memoria del proceso (`InMemoryRATRepository` en `rat_engine.py`): se pierde al reiniciar el backend y en Vercel cada instancia tiene el suyo. Además le faltan campos que las matrices RAT de trabajo del equipo consultor (carpeta compartida SALUDATA, 2026-06) registran por actividad.

## Entrega
- Tabla `rat_actividades` con **RLS** por `tenant_id` (migración Alembic, id de revisión de 32 caracteres como máximo). Campos actuales de `ActividadRAT` más: medio o soporte, encargados, destinatarios, transferencia internacional (país), plazo de conservación, medidas de seguridad, nivel de riesgo, decisiones automatizadas, volumen de titulares en 12 meses, observaciones del DPO y `origen` (`manual` o `plantilla:<sector>`).
- El repositorio en memoria se sustituye por uno sobre PostgreSQL; los endpoints de `api/routers/rat.py` conservan su contrato y añaden editar y dar de baja (baja lógica, con evento en `audit_events`).
- Escriben `coordinador` y `dpo`; leen además `implementador` y `admin_organizacion`.
- Pruebas: crear, listar, editar y dar de baja; otra organización no ve las actividades (RLS); los datos sobreviven a una sesión nueva de base; rol sin permiso (403).
- **Prueba de mutación documentada:** volver al repositorio en memoria y comprobar que la prueba de persistencia falla.

## Límites
- No cambia el cálculo de gran escala (MTGE-01) ni la EIPD (RAT-03).

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.
