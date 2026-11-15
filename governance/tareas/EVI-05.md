+++
id = "EVI-05"
titulo = "Tipo de evidencia «acuse» en la custodia de documentos generados"
ola = "D"
estado = "en_curso"
sala = "evidencias"
depende_de = ["EVI-04", "RET-02"]
propiedad = ["features/evidencias/services/custodia_generados_engine.py", "tests/test_evi05_tipo_acuse.py"]
crea = ["tests/test_evi05_tipo_acuse.py"]
arbitro = "pytest tests/test_evi05_tipo_acuse.py tests/test_evi04_custodia_generados.py contra PostgreSQL 16 local + suite de evidencias; mutación documentada"
rastros = ["¤evidencias"]
+++

# EVI-05 · Tipo de evidencia «acuse» en la custodia de documentos generados

**Contrato:** `governance/especificaciones/EVI-05.md` (manda sobre esta ficha).

**Origen.** Decisión del CTO (2026-11-15) sobre FIRMA-02: el acuse de aceptación es un tipo de evidencia propio de la sala de evidencias. FIRMA-02 depende de esta ficha.

## Entrega
- `TIPOS_EVIDENCIA` incluye `acuse`, después de `exportacion`.
- Prueba de que la custodia admite un PDF de tipo `acuse` y devuelve su sha256.

## Límites
- Solo la tupla y su prueba; el resto de la custodia no cambia.
- Pruebas contra el PostgreSQL 16 local, con `exigir_base_de_pruebas()`.
