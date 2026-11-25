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
- **R5 · Tarjeta duplicada.** El propietario corre, de solo lectura, un recuento por organización de sesión (`select tenant_id, titulo, count(*) from biblioteca_documentos group by 1, 2 having count(*) > 1`). Si da filas, la siembra o el clon duplican, y se corrige aquí. Si no da filas, la segunda tarjeta es el detalle, y no se cambia nada del frontend.
- **R6 · Procedimiento.** `docs/biblioteca-pmv.md` añade el bloque de la demo: `--entorno demo --confirmar-entorno`, desde `main` y tras fusionar, y la carga antes de la primera siembra.
- **R7 · Sin prohibiciones** (GEN-01 R3).
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
| **Dado** el script, **entonces** importa la sala solo por su servicio. | `tests/test_adpa_bulkhead.py` |

## 6. Trazabilidad

- **PRD:** Módulo 7, «Las mismas plantillas en producción y en la demo», y §5.6.
- Brief del CTO `ARQUITECTO_DEMO_PLANTILLAS_REALES` (2026-11-24), base `origin/main` 764c4a99. Decisión del propietario sobre BIB-404 (2026-11-24).
