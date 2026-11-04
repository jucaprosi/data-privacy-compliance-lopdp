+++
id = "ADPA-05"
titulo = "Andamiar domain/errores.py por sala y secciones #ID en compuertas y routers compartidos"
ola = "C"
estado = "pendiente"
sala = "auditoria_capa, derechos_arco, diagnostico, dpo_cockpit, evidencias, firma_electronica, incidentes, notificaciones, organizacion, rat, regulacion_rag, riesgos_mtge, roadmap, terceros, transferencias"
depende_de = ["ADPA-04", "NOTIF-01", "FIRMA-01", "INC-01"]
propiedad = ["features/auditoria_capa/domain/errores.py#ADPA-05", "features/derechos_arco/domain/errores.py#ADPA-05", "features/diagnostico/domain/errores.py#ADPA-05", "features/dpo_cockpit/domain/errores.py#ADPA-05", "features/evidencias/domain/errores.py#ADPA-05", "features/firma_electronica/domain/errores.py#ADPA-05", "features/incidentes/domain/errores.py#ADPA-05", "features/notificaciones/domain/errores.py#ADPA-05", "features/organizacion/domain/errores.py#ADPA-05", "features/rat/domain/errores.py#ADPA-05", "features/regulacion_rag/domain/errores.py#ADPA-05", "features/riesgos_mtge/domain/errores.py#ADPA-05", "features/roadmap/domain/errores.py#ADPA-05", "features/terceros/domain/errores.py#ADPA-05", "features/transferencias/domain/errores.py#ADPA-05", "features/auditoria_capa/auditoria_capa_service.py#ADPA-05", "features/derechos_arco/derechos_arco_service.py#ADPA-05", "features/diagnostico/diagnostico_service.py#ADPA-05", "api/routers/diagnostico_respuestas.py#ADPA-05", "api/routers/diagnostico_resultados.py#ADPA-05", "features/dpo_cockpit/dpo_cockpit_service.py#ADPA-05", "features/evidencias/evidencias_service.py#ADPA-05", "features/firma_electronica/firma_electronica_service.py#ADPA-05", "features/incidentes/incidentes_service.py#ADPA-05", "features/notificaciones/notificaciones_service.py#ADPA-05", "features/organizacion/organizacion_service.py#ADPA-05", "features/rat/rat_service.py#ADPA-05", "features/riesgos_mtge/riesgos_mtge_service.py#ADPA-05", "features/roadmap/roadmap_service.py#ADPA-05", "features/terceros/terceros_service.py#ADPA-05", "features/transferencias/transferencias_service.py#ADPA-05", "tests/test_adpa05_secciones_y_errores.py"]
arbitro = "pytest tests/test_adpa05_secciones_y_errores.py + python scripts/verificar_reparto.py"
rastros = ["¤adpa", "¤errores", "¤secciones"]
+++
# ADPA-05 · Andamiar `domain/errores.py` por sala y secciones `#ID` en compuertas y routers compartidos

## Entrega
- Crear `features/<sala>/domain/errores.py` con bloques `# --- INICIO <ID> ---` / `# --- FIN <ID> ---` para las 15 salas con tareas pendientes, registrando sus códigos en `CATALOGO_ERRORES` y `CodigoErrorNegocio` sin tocar `app_core/errors.py`.
- Sembrar las 26 secciones `# --- INICIO <ID> ---` / `# --- FIN <ID> ---` faltantes en las compuertas `<sala>_service.py` y en `diagnostico_respuestas.py` / `diagnostico_resultados.py`.

## Pruebas
- `pytest tests/test_adpa05_secciones_y_errores.py` comprueba que todas las secciones `#<ID>` declaradas por las tareas pendientes existen físicamente y están delimitadas.
