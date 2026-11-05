# Aceptación de extremo a extremo de Biblioteca (BIB-307)

Registro de la aceptación. Lo que no se pudo verificar se dice; nada se da por cumplido con simulaciones.

## Perfiles ficticios

| Perfil | Tratamiento | Rasgo que se prueba |
|---|---|---|
| Microempresa de servicios | Nómina y clientes | Recorrido mínimo, severidad media |
| Centro médico | Historias clínicas (datos sensibles) | Severidad alta; aprobado inmutable |
| Entidad pública | Registro de trámites ciudadanos | Severidad alta; aislamiento frente a las otras dos |

## Recorrido (servicios reales, IDs devueltos por la base)

1. Empresa y tratamiento (`rat_actividades`): filas semilla en una transacción que se revierte (no pasan por el servicio RAT).
2. Brecha: `roadmap.registrar_hallazgo` con origen `rat` y el ID del tratamiento; requisito = `control_ref`.
3. Acción: `roadmap.crear_tareas_desde_hallazgos`.
4. Documento: plantilla publicada por el flujo editorial; `crear_documento` vinculado a la acción y completado.
5. Revisión: autoridad delegada, `enviar_a_revision`, `aprobar_revision` (cuatro ojos).
6. Enlace documento-acción: `crear_enlace`; muestra requisito y brecha.
7. Un documento aprobado no cierra la acción (`RM_CIERRE_SIN_EVIDENCIA`).
8. Evidencia y verificación conforme por otra persona; cierre `completada`; brecha cerrada.

## Criterios y estado

| Criterio | Prueba | Estado |
|---|---|---|
| Tres perfiles con resultados explicados | `test_db_recorrido_completo_por_perfil_con_ids_reales` | Bloqueado: ver limitación 1 |
| Recorrido completo con IDs reales | ídem | Bloqueado: ver limitación 1 |
| Cero accesos cruzados (servicio, RLS, API) | `test_db_cero_accesos_cruzados_entre_las_tres_empresas`, `test_api_...`, spec Playwright | Bloqueado en base (limitación 1); Playwright: ver limitación 2 |
| Cero cambios de aprobado sin nueva revisión | `test_db_aprobado_no_cambia_sin_nueva_revision` | Bloqueado: ver limitación 1 |

## Mutación decisiva

`features/biblioteca/services/documentos_consulta.py`, `obtener_documento`: `WHERE id=:id AND tenant_id=:t` → `WHERE id=:id`.
Debe fallar `test_db_cero_accesos_cruzados_entre_las_tres_empresas` (tramo con rol que omite la RLS). Resultado observado: ver informe de la sesión.

## Limitaciones

1. `enviar_a_revision` (BIB-301) falla con `lopdp_app`: la base no le permite cambiar `estado` de `biblioteca_documentos`. La coordinación lo corrige en un PR aparte con funciones acotadas; las pruebas no usan el rol propietario para rodearlo. Hasta esa corrección, las pruebas de base de BIB-307 fallan en ese paso.
2. Playwright exige backend real; se apunta al PostgreSQL local del arnés. Si no arranca, queda como no verificado.
3. BIB-106, BIB-110, BIB-206, BIB-207, BIB-208 y EVI-01 no forman parte del recorrido; no se acreditan aquí.
4. Los mocks de terceros no sustituyen la aceptación del servicio operativo.
