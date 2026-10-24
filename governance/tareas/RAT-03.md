+++
id = "RAT-03"
titulo = "EIPD persistida por actividad del RAT, con matriz de probabilidad e impacto 5x5"
ola = "D"
estado = "pendiente"
sala = "rat"
depende_de = ["RAT-01", "ENT-02", "RM-00"]
propiedad = ["features/rat/services/mtge_engine.py", "features/rat/services/eipd_engine.py", "features/rat/rat_service.py#RAT-03", "api/routers/rat_eipd.py", "main.py#RAT-03", "alembic/versions/20261024_rat_eipd.py", "tests/test_rat_eipd.py"]
arbitro = "pytest tests/test_rat_eipd.py contra una rama Neon de revisión + suite completa; prueba de mutación documentada"
rastros = ["¤riesgos-eipd", "¤rat"]
+++

# RAT-03 · EIPD persistida

**Origen.** Criterio 1 de la auditoría del MVP (persistir la EIPD). La matriz «RAT - EIPD» de la carpeta compartida SALUDATA da un formato de trabajo: por riesgo, tipo (seguridad, legal, privacidad), probabilidad 1-5, impacto 1-5, puntuación P x I, nivel, artículo de la LOPDP, responsable y plan de acción.

## Entrega
- Tablas `rat_eipd` y `rat_eipd_riesgos` con **RLS**; la EIPD en memoria actual (`mtge_engine.py`) pasa a la base, con su regla de deriva (más del 25 % de titulares la marca «requiere actualización»).
- Puntuación P x I y nivel calculados en el servidor. Los umbrales de nivel se fijan al implementar, contrastados con el texto vinculante (LOPDP art. 42 y su Reglamento), no con la matriz; cada constante cita su fuente.
- El DPO crea, edita y aprueba; el resto de roles lee. Cada aprobación queda en `audit_events`.
- Pruebas: cálculo en los bordes de cada nivel; persistencia; deriva; RLS; rol sin permiso (403).
- **Prueba de mutación documentada:** alterar un umbral y comprobar que una prueba de borde falla.

## Límites
- No incluye riesgo residual ni pérdida esperada en dólares (matriz de ciberseguridad): referencia fuera del MVP.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.
