+++
id = "RAT-01"
titulo = "El RAT se guarda en el servidor por organización y con los campos de un RAT completo"
ola = "D"
estado = "pendiente"
sala = "rat"
depende_de = ["QA-04", "ORG-00", "RM-00", "RM-13"]
propiedad = ["features/rat/domain/models.py", "features/rat/services/rat_engine.py", "features/rat/rat_service.py#RAT-01", "api/routers/rat.py", "alembic/versions/20261024_rat_actividades.py", "tests/test_rat_persistencia.py", "tests/test_api_gateway.py", "tests/test_sod_dpo.py", "tests/test_compliance_graph.py", "governance/contratos/hoja_de_ruta.openapi.json"]
arbitro = "pytest tests/test_rat_persistencia.py contra una rama Neon de revisión (incluido el aislamiento RLS) + suite completa; prueba de mutación documentada"
rastros = ["¤rat", "¤rbac-tenant"]
+++

# RAT-01 · RAT persistido

**Hallazgo (2026-10-23).** El Registro de Actividades de Tratamiento vive en la memoria del proceso (`InMemoryRATRepository` en `rat_engine.py`): se pierde al reiniciar el backend y en Vercel cada instancia tiene el suyo. Además le faltan campos que las matrices RAT de trabajo del equipo consultor (carpeta compartida SALUDATA, 2026-06) registran por actividad.

## Entrega
- Tabla `rat_actividades` con **RLS** por `tenant_id` (migración Alembic, id de revisión de 32 caracteres como máximo). Campos actuales de `ActividadRAT` más: medio o soporte, encargados, destinatarios, transferencia internacional (país), plazo de conservación, medidas de seguridad, nivel de riesgo, decisiones automatizadas, volumen de titulares en 12 meses, observaciones del DPO y `origen` (`manual` o `plantilla:<sector>`).
- El repositorio en memoria se sustituye por uno sobre PostgreSQL; los endpoints de `api/routers/rat.py` conservan su contrato y añaden editar y dar de baja (baja lógica, con evento en `audit_events`).
- Escribe el `coordinador`; leen además `implementador`, `dpo` y `admin_organizacion`. El DPO no modifica el RAT (SoD, independencia del DPO, art. 48 LOPDP): 403 «Violación SoD».
- Pruebas: crear, listar, editar y dar de baja; otra organización no ve las actividades (RLS); los datos sobreviven a una sesión nueva de base; rol sin permiso (403).
- **Prueba de mutación documentada:** volver al repositorio en memoria y comprobar que la prueba de persistencia falla.

## Límites
- No cambia el cálculo de gran escala (MTGE-01) ni la EIPD (RAT-03).

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.

## Implementación y correcciones del coordinador (2026-10-24)
- **Implementación:** la de PR #152 (equipo), con repositorio PostgreSQL, RLS probada con `lopdp_app`, auditoría atómica y validación de ediciones. Una versión paralela hecha por un agente se descartó.
- **SoD:** la versión inicial de esta ficha dejaba escribir al `dpo`, lo que contradice `ACCIONES_INCOMPATIBLES_DPO` (aprobar la finalidad del RAT) y `tests/test_sod_dpo.py`. Escribe el `coordinador`; el DPO consulta y recibe 403 «Violación SoD» al escribir.
- **Pruebas anteriores adaptadas** (fuera de la propiedad inicial, señaladas por la implementación): `test_api_gateway.py::test_rat_endpoints` (sin identidad no se escribe; se omite sin PostgreSQL), `test_sod_dpo.py` (la SoD con un DPO real está en `test_rat_persistencia.py`), `test_compliance_graph.py` (compuerta asíncrona contra la base; los riesgos siguen simulados hasta RAT-03).
- **Contrato:** regenerado con `scripts/exportar_contrato_hoja_ruta.py`; recoge además endpoints añadidos por tareas anteriores sin regenerar.
