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
| Tres perfiles con resultados explicados | `test_db_recorrido_completo_por_perfil_con_ids_reales` | Pasa (PG local, `lopdp_app`) |
| Recorrido completo con IDs reales | ídem | Pasa (PG local, `lopdp_app`) |
| Cero accesos cruzados (servicio, RLS, API) | `test_db_cero_accesos_cruzados_entre_las_tres_empresas`, `test_api_...`, spec Playwright | Pasa en base y API; Playwright pasa (1/1) con PG local |
| Cero cambios de aprobado sin nueva revisión | `test_db_aprobado_no_cambia_sin_nueva_revision` | Pasa (PG local, `lopdp_app`) |

## Mutación decisiva

`features/biblioteca/services/documentos_consulta.py`, `obtener_documento`: `WHERE id=:id AND tenant_id=:t` → `WHERE id=:id`.
Debe fallar `test_db_cero_accesos_cruzados_entre_las_tres_empresas` (tramo con rol que omite la RLS). Observado el 2026-11-04: «DID NOT RAISE ErrorNegocio» en `test_db_cero_accesos_cruzados_entre_las_tres_empresas` (1 falla, 6 pasan). Restaurado: 7 pasan.

## Limitaciones

1. Resuelta: `enviar_a_revision` (BIB-301) fallaba con `lopdp_app` por falta de permiso sobre `estado`. Lo corrigió #395 (`20261117_bib_estado_revision`, funciones acotadas). Las pruebas nunca usan el rol propietario para rodearlo.
2. Playwright corre contra el backend real con el PostgreSQL local del arnés; en Mac hace falta un alias `python` → `python3` en el PATH (la config no se toca). El helper de TEST-03 admite una sola empresa por prueba, así que la empresa ajena es un ID cualquiera.
3. BIB-106, BIB-110, BIB-206, BIB-207, BIB-208 y EVI-01 no forman parte del recorrido; no se acreditan aquí.
4. Los mocks de terceros no sustituyen la aceptación del servicio operativo.
