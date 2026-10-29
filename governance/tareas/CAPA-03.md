+++
id = "CAPA-03"
titulo = "La evidencia vencida reabre el control periódico y produce un hallazgo"
ola = "D"
estado = "pendiente"
sala = "auditoria_capa"
depende_de = ["CAPA-02", "EVI-02", "RM-21"]
propiedad = ["features/auditoria_capa/services/reapertura_engine.py", "features/auditoria_capa/auditoria_capa_service.py#CAPA-03", "tests/test_controles_reapertura.py"]
arbitro = "pytest tests/test_controles_reapertura.py contra una rama Neon de revisión con lopdp_app + suite completa + vigilantes; prueba de mutación documentada"
rastros = ["¤controles-periodicos", "¤evidencias-vigencia", "¤hallazgos"]
+++

# CAPA-03 · La evidencia vencida reabre el control periódico y produce un hallazgo

**Origen.** Optimización O-8 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`, segunda mitad: se separa de CAPA-02 porque necesita la vigencia de evidencias (EVI-02).

## Entrega
- Un control periódico cuya última verificación se apoya en una evidencia **vencida** pasa a `vencido` y produce un hallazgo por la compuerta de `roadmap` (`registrar_hallazgo`, RM-21, origen `control_periodico`).
- La vigencia se lee **solo** por la compuerta de `evidencias` (EVI-02); `auditoria_capa` no guarda ninguna vigencia propia (fuente única, `INV_LOPDP_COMPLIANCE_GRAPH_SSOT`).
- Lo que necesite de otra sala, por su compuerta; errores con `ErrorNegocio`; pruebas contra una rama Neon de revisión hija de `revision`, nunca producción.

## Pruebas
- Al vencer la evidencia, el control se reabre y aparece exactamente un hallazgo; una evidencia nueva vigente lo devuelve a vigente.
- Mutación documentada: leer una fecha guardada en `auditoria_capa` en lugar de la de `evidencias` y comprobar que la prueba falla.
