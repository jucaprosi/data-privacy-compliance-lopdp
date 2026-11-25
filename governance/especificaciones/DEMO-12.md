# DEMO-12 · La demo con las plantillas reales
`¤sdd` `¤demo` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Hechos medidos en `origin/main` 764c4a99:
- **Cargador sin demo.** `scripts/cargar_plantillas_pmv.py:25` tiene `ENTORNOS = ("local", "pruebas", "produccion")`. `entorno_de_url` no reconoce la base de la demo, así que hoy no se puede cargar el catálogo en `evydentia-demo-db` con la comprobación de entorno.
- **Documento inventado.** `data/demo/cooperativa_demo.json:104` siembra un único documento, «Política de protección de datos (borrador ficticio)», en estado `borrador`. `clon_plantilla_engine.sembrar_en_plantilla` (l. 135) lo inserta como `DEMO-DOC-01`, con origen `propio` y el contenido fijo «Documento ficticio de demostración. Sin datos reales.». `tests/test_demo_clon_biblioteca.py:244` fija ese título.
- **Camino real.** `documentos.crear_documento` (l. 55) crea un documento desde una versión publicada, con origen `plantilla`, `plantilla_id` y `plantilla_version`, rellenándola con `_rellenador`.
- **Catálogo real.** BIB-001 a BIB-012 en `plantillas/`. Por ejemplo, BIB-001 «Política de protección de datos personales», BIB-002 «Aviso de privacidad para clientes» y BIB-006 «Registro de actividades de tratamiento simple».
- **Tarjeta duplicada.** En `VistaDocumentos.tsx`, la lista pinta una `TarjetaDocumento` por documento (`key=doc.id`), y debajo va la ranura `documento:detalle` con el documento seleccionado. Con un solo documento sembrado, lo que se ve como segunda tarjeta es, con toda probabilidad, el detalle. Se confirma en R4.

## 2. API

Sin API nueva.

## 3. Reglas

- **R1 · Carga en la demo.** `ENTORNOS` gana `demo`. `entorno_de_url` devuelve `demo` cuando la URL nombra `evydentia-demo-db` o la base `evydentia_demo`, antes que las demás reglas. Con `--entorno demo`, sin `--confirmar-entorno` o con una URL que no sea la de la demo, sale con código 2 sin conectar, como los demás entornos. Carga las mismas plantillas BIB-001 a BIB-012 que producción, por el mismo flujo editorial (revisión técnica independiente y citas validadas, BIB-403). Lo ejecuta el propietario.
- **R2 · Documentos nacidos del catálogo.** Cada entrada de `biblioteca.documentos` en `cooperativa_demo.json` nombra un código de plantilla y un estado (`{"plantilla": "BIB-001", "estado": "borrador"}`), nunca un título ni un contenido. La siembra:
  - toma la última versión publicada de ese código;
  - crea el documento con su contenido, rellenado con los datos de la organización ficticia del mismo JSON por el mismo rellenador de `crear_documento`;
  - guarda origen `plantilla`, `plantilla_id` y `plantilla_version`;
  - conserva los identificadores deterministas (`_id_destino`) y la fila de historia.
  Se siembran al menos cuatro documentos, de plantillas distintas, que cubren los cuatro estados de `_ESTADOS_SEMBRABLES`. Al menos uno lleva origen `propio`, copia de una plantilla publicada, para que el filtro «Origen» tenga resultados en sus dos valores.
- **R3 · Falla cerrado.** Si un código no tiene versión publicada, la siembra lanza `ValueError` con el código, y no queda ningún documento sembrado: todo va en la misma transacción.
- **R4 · Títulos.** El título es el nombre de la plantilla, sin «(borrador ficticio)». La leyenda de la demo sigue siendo la de §5.6 del PRD. UX/UI confirma que no hace falta otra marca por documento.
- **R4b · Lo que sale de la pantalla** (condición de UX/UI, 2026-11-25). En pantalla, la única marca es la franja «Demostración · datos ficticios» de `AvisoEntorno.tsx` (EP-02, PRD §5.6 punto 6), fija en todas las pantallas, la Biblioteca y el detalle del documento incluidos. Al imprimir con Ctrl+P la franja sale, porque no tiene clase que la oculte en impresión. La demo sí exporta: `generacion.py` produce DOCX (`generador_docx.py`) y XLSX (`generador_xlsx.py`). Hoy no genera PDF con datos de la organización; si una ficha futura lo añade, lleva el mismo pie. Cuando `datos_ficticios()` de `app_core/entorno/guardias.py` es verdadero, cada DOCX lleva esa leyenda en el pie de página y cada XLSX en el pie de impresión de cada hoja, sin otro texto. Fuera de la demo la salida no cambia. La descarga de archivos maestros (`descarga.py`) entrega la plantilla del catálogo, sin datos de la organización, y no cambia.
- **R5 · Tarjeta duplicada.** El propietario corre, de solo lectura, un recuento por organización de sesión dentro de `BEGIN TRANSACTION READ ONLY`, por Antigravity o Cloud SQL Studio (sin psql, como en DEMO-11): `SELECT tenant_id, nombre, count(*) FROM biblioteca_documentos GROUP BY 1, 2 HAVING count(*) > 1;`. Si da filas, la siembra o el clon duplican, y se corrige aquí. Si no da filas, la segunda tarjeta es el detalle, y no se cambia nada del frontend.
- **R6 · Procedimiento.** `docs/biblioteca-pmv.md` añade el bloque de la demo, que ejecuta el propietario desde `main` y tras fusionar, en este orden:
  1. **Carga:** `--cargar --entorno demo --confirmar-entorno`. Deja cada plantilla «En revisión» y nunca publica (`cargar_plantillas_pmv.py:9`).
  2. **Revisión y publicación:** en la web de la demo, un usuario editor distinto del autor de la carga (BIB-403 R4) abre cada plantilla nombrada en `cooperativa_demo.json`, aprueba la revisión técnica en el expediente («Aprobar con autoridad vigente», `FlujoRevision.tsx`), valida sus citas y la publica. Como mínimo se publican esas plantillas.
  3. **Comprobación:** de solo lectura, como en R5: cada código nombrado en el JSON tiene una versión publicada. Si falta alguno, se para y no se siembra (R3 lo cubre de todos modos).
  4. **Retiro de lo ficticio** (R8) y, después, **siembra**.
- **R7 · Sin prohibiciones** (GEN-01 R3).
- **R8 · Retiro de lo ya sembrado.** Hoy la demo tiene `DEMO-DOC-01` ficticio en el tenant plantilla y en los tenants ya clonados.
  - **Sin colisión de ids:** el id de cada documento nuevo sale de `_id_destino(plantilla_id, "DEMO-" + código de plantilla)`, nunca de la posición, así que no puede coincidir con el viejo `DEMO-DOC-01`.
  - **Tenant plantilla.** El paso 4 de R6 lo ejecuta el propietario con el rol dueño de las tablas, el que migra (secreto `DATABASE_URL` de `evydentia-demo`, el mismo de `migrar-demo`), por Antigravity con `cloud-sql-proxy` o por Cloud SQL Studio, en una sola transacción. Nada va a `jobs/`: el rol `purga_demo` no es dueño (`politicas_purga.sql:15`), y `purga_demo_borrar_inmutables` rechaza la plantilla (l. 70-71). El id de la plantilla es `PLANTILLA_TENANT_ID = "demo-plantilla-cooperativa"` (`features/demo/domain/plantilla.py:17`).
  - **Dependencias medidas en `alembic/versions`.** Sobre `biblioteca_documentos` solo hay un disparador, `biblioteca_documento_validar` (BEFORE INSERT OR UPDATE), que no actúa en DELETE. Lo referencian sin cascada `biblioteca_documentos_historial` (inmutable), `biblioteca_conservacion`, `biblioteca_eventos_documento`, `biblioteca_evidencias` (RESTRICT), `biblioteca_cargas` y `biblioteca_revisiones_documento`; con cascada, los vínculos y enlaces. `biblioteca_descargas` no referencia documentos: apunta a `biblioteca_versiones` (`20261111_biblioteca_descargas.py:27`). El documento ficticio solo tiene su historial: si alguna de las otras tablas tiene filas suyas, el bloque para.
  - **Bloque** (va igual en `docs/biblioteca-pmv.md`):
    ```sql
    BEGIN;
    DO $$ BEGIN
      IF (SELECT count(*) FROM public.entorno_marcador) <> 1
         OR (SELECT valor FROM public.entorno_marcador) <> 'demo' THEN
        RAISE EXCEPTION 'No es la base de la demo';
      END IF;
    END $$;
    SELECT set_config('app.current_tenant_id', 'demo-plantilla-cooperativa', true);
    CREATE TEMP TABLE ficticios ON COMMIT DROP AS
      SELECT id FROM biblioteca_documentos
      WHERE tenant_id = 'demo-plantilla-cooperativa' AND codigo LIKE 'DEMO-DOC-%';
    -- Recuento antes: 1 documento y sus filas de historial.
    SELECT (SELECT count(*) FROM ficticios) AS documentos,
           (SELECT count(*) FROM biblioteca_documentos_historial WHERE documento_id IN (SELECT id FROM ficticios)) AS historial;
    DO $$ BEGIN
      IF (SELECT count(*) FROM ficticios) <> 1 THEN RAISE EXCEPTION 'Se esperaba 1 documento ficticio'; END IF;
      IF EXISTS (SELECT 1 FROM biblioteca_conservacion WHERE documento_id IN (SELECT id FROM ficticios))
         OR EXISTS (SELECT 1 FROM biblioteca_eventos_documento WHERE documento_id IN (SELECT id FROM ficticios))
         OR EXISTS (SELECT 1 FROM biblioteca_evidencias WHERE documento_id IN (SELECT id FROM ficticios))
         OR EXISTS (SELECT 1 FROM biblioteca_cargas WHERE documento_id IN (SELECT id FROM ficticios))
         OR EXISTS (SELECT 1 FROM biblioteca_revisiones_documento WHERE documento_id IN (SELECT id FROM ficticios)) THEN
        RAISE EXCEPTION 'El documento ficticio tiene dependencias: se para';
      END IF;
    END $$;
    ALTER TABLE biblioteca_documentos_historial DISABLE TRIGGER biblioteca_documento_historial_inmutable;
    DELETE FROM biblioteca_documentos_historial WHERE documento_id IN (SELECT id FROM ficticios);
    DELETE FROM biblioteca_documentos WHERE id IN (SELECT id FROM ficticios);
    ALTER TABLE biblioteca_documentos_historial ENABLE TRIGGER biblioteca_documento_historial_inmutable;
    -- Recuento después: 0.
    DO $$ BEGIN
      IF EXISTS (SELECT 1 FROM biblioteca_documentos WHERE tenant_id = 'demo-plantilla-cooperativa' AND codigo LIKE 'DEMO-DOC-%') THEN
        RAISE EXCEPTION 'Quedan documentos ficticios';
      END IF;
    END $$;
    COMMIT;
    ```
    Cualquier `RAISE` deja la transacción abortada: se ejecuta `ROLLBACK`, se para y se avisa al CTO.
  - **Tenants ya clonados:** no se tocan. Caducan y los borra la purga nocturna (DEMO-05). Las sesiones nuevas clonan ya el conjunto nuevo.
  - **Alcance:** solo la base de la demo. Sin migración y sin cambios en producción.
- **R-ADPA · Ortogonalidad ZERAG (`DEMO-12`).** Solo los archivos de la propiedad. El script importa la sala solo por `biblioteca_service.py` (`tests/test_adpa_bulkhead.py`). La prueba no usa `import yaml`.

## 4. Interfaz

Sin cambios de interfaz. La lista de documentos de la demo muestra los títulos de las plantillas (R4).

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** `entorno_de_url` con una URL de `evydentia-demo-db`, **entonces** da `demo`; con `--entorno demo` y una URL de pruebas, sale con código 2 sin conectar. Mutación m1: quitar `demo` de `ENTORNOS` da rojo. | `tests/test_demo12_plantillas_reales.py` |
| **Dado** el catálogo cargado y la siembra hecha, **entonces** la huella de cada documento sembrado coincide con la de su versión de plantilla rellenada, y su origen y versión son los de R2. Mutación m2: un contenido inventado en un documento da rojo. | ídem |
| **Dado** la siembra, **entonces** hay al menos cuatro documentos, de los cuatro estados y de los dos orígenes. Mutación m3: dejar un solo estado da rojo. | ídem |
| **Dado** un código sin versión publicada, **entonces** la siembra lanza `ValueError` y no queda ningún documento. Mutación m4: saltarse el código en silencio da rojo. | ídem |
| **Dado** el clon de la demo, **entonces** los nombres son los de las plantillas, sin «(borrador ficticio)». | `tests/test_demo_clon_biblioteca.py` |
| **Dado** `APP_ENV=demo`, **entonces** el DOCX y el XLSX generados llevan la leyenda en el pie; con `production`, la salida es idéntica a la de hoy. Mutación m5: quitar la leyenda del pie del DOCX da rojo. | `tests/test_demo12_plantillas_reales.py` |
| **Dado** un tenant plantilla con el viejo `DEMO-DOC-01`, **entonces** la siembra nueva no reutiliza su id y crea los documentos de R2. | `tests/test_demo12_plantillas_reales.py` |
| **Dado** el script, **entonces** importa la sala solo por su servicio. | `tests/test_adpa_bulkhead.py` |

## 6. Trazabilidad

- **PRD:** Módulo 7, «Las mismas plantillas en producción y en la demo», y §5.6.
- Brief del CTO `ARQUITECTO_DEMO_PLANTILLAS_REALES` (2026-11-24), base `origin/main` 764c4a99. Decisión del propietario sobre BIB-404 (2026-11-24).
