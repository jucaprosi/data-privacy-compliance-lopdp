+++
id = "EVI-04"
titulo = "Subida de servidor en el almacén y custodia de documentos generados como evidencia"
ola = "backlog"
estado = "en_curso"
sala = "evidencias"
depende_de = ["EVI-01", "EVI-02", "SEC-05"]
propiedad = ["app_core/storage/gcs.py", "app_core/storage/r2.py", "features/evidencias/services/custodia_generados_engine.py", "features/evidencias/evidencias_service.py#EVI-04", "app_core/pasillo/evidencias.py#EVI-04", "tests/test_evi04_custodia_generados.py"]
crea = ["features/evidencias/services/custodia_generados_engine.py", "tests/test_evi04_custodia_generados.py"]
arbitro = "pytest tests/test_evi04_custodia_generados.py contra PostgreSQL 16 local (RLS con lopdp_app) + suite de evidencias; mutaciones m1 a m4"
rastros = ["¤evidencias"]
+++

# EVI-04 · Subida de servidor en el almacén y custodia de documentos generados como evidencia

Diseño del Arquitecto ADPA (2026-11-13, medido en main 08781173), aprobado por el CTO como ficha previa y compartida. Sin frontend: no pasa por UX/UI.

## Por qué
El `Almacen` de `app_core/storage` (`gcs.py`, `r2.py`) solo expone `firmar_subida`, `descargar` y `fijar_retencion`: el servidor no puede subir bytes propios. `registrar_evidencia_documental` (`evidencias_service.py:57`) calcula el hash pero no sube nada. La subida de servidor la necesita también NORM-01 (bucket normativo). La custodia la necesitan FOR-01 (constancia), CAPA-04 (acta), INC-02 (informes), DER-01 y FIRMA-02.

## Entrega
- Protocolo `Almacen`: `subir(clave, contenido: bytes, tipo_mime) -> None`, escritura única con `if_generation_match=0` y excepción `ObjetoYaExiste`. `gcs.py` lo implementa; el bucket viene del constructor, así que NORM-01 crea el suyo con `gs://evydentia-corpus-normativo`. `r2.py`: `subir` o `NotImplementedError` explícito si R2 está retirado.
- `custodiar_documento_generado(session, tenant_id, user_id, *, contenido: bytes, tipo_mime, tipo_evidencia, control_refs: list[str], nombre) -> {evidencia_id, sha256}` en `features/evidencias/services/custodia_generados_engine.py`, expuesta por la compuerta (`evidencias_service.py#EVI-04`) y el pasillo (`app_core/pasillo/evidencias.py#EVI-04`):
  - calcula el SHA-256, sube a la clave por hash y fija la retención según `domain/retencion.py`;
  - registra la evidencia y la vincula a los controles (`vincular_controles`);
  - todo en la transacción del llamador: si falla, no queda registro.

## Control de capacitación
La constancia de FOR-01 se vincula a `["P73"]` («Plan de capacitación en protección de datos», D10; `features/diagnostico/domain/banco_preguntas.json`, id 73; código `f"P{id}"`), con `tipo_evidencia = "capacitacion"`.

**Referencia normativa:** no se cita «LOPDP art. 47 num. 3» ni en esta ficha ni en la constancia. El Arquitecto contrastó el art. 47 con el texto oficial (5.º Suplemento R.O. 459, 26-V-2021): ninguno de sus 15 numerales trata de la capacitación del personal (el num. 3 es la verificación periódica de la eficacia de las medidas). La base defendible (art. 47 num. 2 como medida organizativa y art. 10, responsabilidad proactiva) queda ESTIMADA hasta la revisión del abogado; la corrección del banco va en `DIAG-16`.

## Mutaciones
m1 sobrescribir una clave existente → falla; m2 un hash distinto del contenido → falla; m3 registrar sin vincular el control → falla; m4 fuera de la nube, gcs falla cerrado.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#EVI-04` (ADR 0001).

## Decisiones del Tech Lead (2026-11-13)
- `tipo_evidencia` va en el evento de auditoría, sin columna propia; no se puede consultar por tipo.
