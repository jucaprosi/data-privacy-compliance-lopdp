+++
id = "INC-04"
titulo = "La marca de notificación pendiente del cierre ya no se escribe falsa"
ola = "backlog"
estado = "pendiente"
sala = "incidentes"
depende_de = ["INC-02", "INC-03"]
propiedad = ["features/incidentes/services/estado_engine.py", "features/incidentes/domain/estado.py", "tests/test_inc03_estado_incidente.py", "tests/test_inc04_marca_notificacion.py"]
crea = ["tests/test_inc04_marca_notificacion.py"]
arbitro = "pytest tests/test_inc04_marca_notificacion.py tests/test_inc03_estado_incidente.py contra un PostgreSQL 16 local (incluido RLS con lopdp_app) + tests/test_incidentes_asistente.py; mutaciones documentadas por escenario"
rastros = ["¤incidentes"]
+++

# INC-04 · La marca de notificación pendiente ya no se escribe falsa

Pedido de la sesión de INC-02 (2026-11-13); decisión y especificación del Arquitecto en `governance/especificaciones/INC-04.md` (manda sobre esta ficha). Modelo sugerido: sonnet. Libre; debe entrar antes de INC-03f.

**Problema.** `estado_engine` escribe `decision_notificacion = 'pendiente'` en todo cierre con datos personales, estimando que se podía cerrar sin decisión. Desde INC-02 (#773) eso es imposible, así que la insignia «Cerrado, notificación pendiente» de INC-03f mentiría siempre.

**Entrega.** R1 a R5 de la especificación: no se escribe marca falsa, la lectura entrega una marca anterior solo si el incidente sigue sin sección 7, la constante se conserva solo para leer lo anterior, la auditoría deja de llevar la marca en los eventos nuevos y la mutación m9 de `test_inc03_estado_incidente.py` pasa a INC-04 con cesión explícita y su fila en la tabla de pruebas ajenas. Sin migración ni backfill.
