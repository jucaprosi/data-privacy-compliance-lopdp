+++
id = "CAPA-03"
titulo = "La evidencia vencida reabre el control periódico y produce un hallazgo"
ola = "D"
estado = "en_curso"
sala = "auditoria_capa"
depende_de = ["CAPA-02", "EVI-02", "RM-21", "ADPA-05", "ADPA-06"]
propiedad = ["features/auditoria_capa/services/reapertura_engine.py", "features/auditoria_capa/auditoria_capa_service.py#CAPA-03", "tests/test_controles_reapertura.py", "features/auditoria_capa/domain/errores.py#CAPA-03", "app_core/pasillo/auditoria_capa.py#CAPA-03", "app_core/pasillo/evidencias.py#CAPA-03", "app_core/pasillo/roadmap.py#CAPA-03", "app_core/pasillo/notificaciones.py#CAPA-03", "app_core/pasillo/dpo_cockpit.py#CAPA-03"]
arbitro = "pytest tests/test_controles_reapertura.py contra un PostgreSQL 16 local en contenedor con lopdp_app + suite completa + vigilantes; prueba de mutación documentada"
rastros = ["¤controles-periodicos", "¤evidencias-vigencia", "¤hallazgos"]
+++

# CAPA-03 · La evidencia vencida reabre el control periódico y produce un hallazgo

**Origen.** Optimización O-8 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`, segunda mitad: se separa de CAPA-02 porque necesita la vigencia de evidencias (EVI-02).

## Entrega
- Un control periódico cuya última verificación se apoya en una evidencia **vencida** pasa a `vencido` y produce un hallazgo por la compuerta de `roadmap` (`registrar_hallazgo`, RM-21, origen `control_periodico`).
- La vigencia se lee **solo** por la compuerta de `evidencias` (EVI-02); `auditoria_capa` no guarda ninguna vigencia propia (fuente única, `INV_LOPDP_COMPLIANCE_GRAPH_SSOT`).
- Lo que necesite de otra sala, por su compuerta; errores con `ErrorNegocio`; pruebas contra un PostgreSQL 16 local en contenedor, nunca producción.

## Pruebas
- Al vencer la evidencia, el control se reabre y aparece exactamente un hallazgo; una evidencia nueva vigente lo devuelve a vigente.
- Mutación documentada: leer una fecha guardada en `auditoria_capa` en lugar de la de `evidencias` y comprobar que la prueba falla.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#CAPA-03` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#CAPA-03` sin modificar `app_core/errors.py`.
