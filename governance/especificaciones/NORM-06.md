# NORM-06 · El análisis de impacto lee los PDF escaneados
`¤sdd` `¤inteligencia-normativa` `¤copiloto-ia` `¤arbitro`

## 1. Datos

Hechos medidos en `origin/main` 38259fcb.

**El defecto.**
- `extraccion.py:66` (`extraer_texto`, con `pypdf` y `MAXIMO_PAGINAS = 400`) devuelve, en los escaneos de la LOPDP (RO 5S 459) y del Reglamento (Decreto 904), solo la capa del sello: unos 75 caracteres por página (medición del CTO).
- `impacto.py:148-151` solo falla con texto vacío, así que analiza las cabeceras sin avisar.

**La sala de inferencia.**
- `cliente_vertex.py` solo manda texto (`generar_json`, `vectorizar`, `crear_cache`).
- `inferencia_service._generar` hace tres cosas:
  - comprueba `MODELOS_PERMITIDOS`, que es solo `gemini-3.8-flash` (IA-13);
  - consume el tope de la organización;
  - reintenta una vez y falla cerrada con `InferenciaNoDisponible`.
- `generar_trazado` exige `model_version`.
- IA-12 R3 fija el precedente: el corpus normativo común, sin datos personales, **no consume tope**.

**Trazas.** `trazas_ia` (IA-10) es por organización, con RLS. Una transcripción es del corpus común y no es de ninguna organización, así que su traza va en su propia fila (abajo).

**Análisis.** `normativa_analisis_impacto` (`20261104_norm03_analisis_impacto.py`) guarda `modelo` y `corpus_sha256`, pero no el origen del texto.

**Ninguna ficha pendiente** comparte archivos con esta. Con NORM-05 (tanda 104) solo coincide en la rama de Alembic de la sala `inteligencia_normativa`, así que esta ficha va detrás.

**Migración** `alembic/versions/norm06_transcripciones.py`:
- `down_revision` = `inteligencia_normativa@head` después de NORM-05 (FUSION_ALEMBIC §2);
- tabla nueva `normativa_transcripciones`:
  - `archivo_sha256 varchar(64)`, PK, con `CHECK ~ '^[0-9a-f]{64}$'`;
  - `texto text NOT NULL`, con `CHECK length(texto) > 0`;
  - `paginas int NOT NULL` y `caracteres int NOT NULL`;
  - `modelo_solicitado varchar(40) NOT NULL` y `modelo_version varchar(80) NOT NULL`;
  - `prompt_id varchar(80) NOT NULL` y `prompt_version int NOT NULL`;
  - `creada_en timestamptz NOT NULL DEFAULT now()`;
- `GRANT SELECT, INSERT ON normativa_transcripciones TO lopdp_app`, sin `UPDATE` ni `DELETE`: es inmutable;
- columna `origen_texto varchar(14) NOT NULL DEFAULT 'capa_texto'` en `normativa_analisis_impacto`, con `CHECK IN ('capa_texto', 'transcripcion')`; las filas existentes quedan en `capa_texto`;
- `TABLAS_POR_SALA` de `alembic/salas.py` gana `normativa_transcripciones` → `inteligencia_normativa`.

## 2. API

Sin rutas nuevas. La respuesta del análisis de impacto gana `origen_texto` (`capa_texto` o `transcripcion`). GEN-05 o el siguiente regenerado lo recoge en OpenAPI.

## 3. Reglas

- **R1 · Detección del escaneo.** `domain/transcripcion.py` tiene la función pura `es_escaneo(paginas)`, sobre una lista con dos datos por página: `caracteres_utiles` (sin espacios) y `tiene_imagen` (un XObject `/Image`).
  - Una página es **escaneada** si `tiene_imagen` y `caracteres_utiles < 300`.
  - El documento es escaneado si al menos el **50 %** de sus páginas lo son.
  - **Por qué 300:** el sello de los dos escaneos da unos 75, cuatro veces menos. Una página del Registro Oficial con capa de texto da del orden de miles. Así hay margen amplio a los dos lados.
  - **Por qué el 50 %:** un PDF con texto puede tener portadas o anexos escaneados sueltos sin ser un escaneo.

  `extraccion.estadisticas(pdf)` calcula los dos datos con `pypdf`, dentro del mismo `MAXIMO_PAGINAS`.
- **R2 · Transcripción por el pasillo.** `inferencia_service.transcribir_pdf(pdf, prompt, *, modelo) -> (texto, TrazaTranscripcion)`, expuesta en `app_core/pasillo/inferencia.py`:
  - `cliente_vertex.transcribir` manda `types.Part.from_bytes(data=pdf, mime_type="application/pdf")` y la instrucción del prompt, con `temperature=0` y salida de texto plano;
  - comprueba `MODELOS_PERMITIDOS` y la región de IA-17 (`VERTEX_LOCATION`);
  - exige `model_version`;
  - **no consume tope**, por el precedente de IA-12 R3;
  - reintenta una vez y, si no, `InferenciaNoDisponible`.
- **R3 · Por tramos.** El engine parte el PDF en tramos de **10 páginas** con `pypdf.PdfWriter`, transcribe cada uno en orden y une el texto. Así cada salida queda muy por debajo del máximo de tokens de salida del modelo. Si un tramo da vacío o falla, falla todo el documento y no se guarda nada parcial.
- **R4 · Una sola vez por `sha256`.** `transcripcion_engine.texto_de(sesion, pdf, archivo_sha256)`:
  1. Si `es_escaneo` es falso, devuelve la capa de texto con `origen = "capa_texto"`.
  2. Si hay fila en `normativa_transcripciones`, la devuelve con `origen = "transcripcion"`, sin llamar al modelo.
  3. Si no, toma `pg_advisory_xact_lock(hashtextextended(sha256, 6))`, vuelve a mirar, transcribe e inserta la fila con su traza en la misma transacción. Dos análisis simultáneos del mismo documento transcriben una sola vez.
- **R5 · Falla cerrada de verdad.** En `impacto.solicitar`:
  - si el documento es escaneado y el pasillo lanza o devuelve vacío: `IaNoDisponible` o `ResolucionSinTexto`, y no se guarda el análisis;
  - con capa de texto, además del vacío actual, un documento con menos de 300 caracteres útiles por página de media también da `ResolucionSinTexto`, para no analizar casi nada en silencio;
  - la fila del análisis guarda `origen_texto`.
- **R6 · Trazabilidad.** La fila de `normativa_transcripciones` dice qué modelo (`modelo_version` devuelto por Vertex) y qué prompt (`normativa.transcripcion`, versión 1) la produjeron, y cuándo. La traza del análisis en `trazas_ia` sigue igual, y `origen_texto` enlaza las dos.
- **R7 · Prompt.** El prompt `normativa.transcripcion` v1, en `domain/transcripcion.py`, pide la transcripción literal, página a página, sin resumir, sin corregir y sin completar. Lo ilegible se marca `[ilegible]`. Se versiona como los demás (`prompt_versionado`).
- **R-ADPA · Ortogonalidad ZERAG (`NORM-06`).** Solo los archivos de la propiedad. La sala `inteligencia_normativa` llega a Vertex solo por el pasillo de inferencia, nunca importando `google.genai`.

## 4. Interfaz

Sin cambios de texto en esta ficha. Si UX/UI quiere mostrar «Texto obtenido por transcripción» en la propuesta, va en otra ficha.

## 5. Aceptación

Los PDF de prueba se generan dentro de la prueba: uno con una página que solo tiene una imagen y 40 caracteres de sello, y otro con texto. No se guarda ningún binario.

| Caso | Árbitro |
| :--- | :--- |
| **Dado** el PDF escaneado sintético, **entonces** `es_escaneo` es verdadero; con el de texto, falso. Mutación m1: umbral de 30 caracteres da rojo. Mutación m2: no exigir `tiene_imagen` da rojo. | `test_norm06_pdf_escaneados.py` |
| **Dado** un escaneo y un doble del pasillo, **entonces** el análisis usa el texto transcrito y guarda `origen_texto = transcripcion`. Mutación m3: analizar con la capa de texto da rojo. | ídem |
| **Dado** un escaneo con el pasillo caído o con texto vacío, **entonces** `IaNoDisponible` o `ResolucionSinTexto`, y no hay fila de análisis ni de transcripción. Mutación m4: seguir con las cabeceras da rojo. | ídem, PostgreSQL |
| **Dado** dos análisis del mismo `sha256`, **entonces** el doble del pasillo se llama una vez por tramo y hay una sola fila. Mutación m5: quitar la consulta previa da rojo. | ídem |
| **Dado** 25 páginas, **entonces** tres llamadas de 10, 10 y 5 páginas, en orden. Si falla la segunda, no se guarda nada. Mutación m6: guardar lo parcial da rojo. | ídem |
| **Dado** `transcribir_pdf`, **entonces** no consume tope, rechaza un modelo fuera de `MODELOS_PERMITIDOS` y exige `model_version`. Mutación m7: consumir tope da rojo. | ídem |
| **Dado** `lopdp_app`, **entonces** `UPDATE` y `DELETE` en `normativa_transcripciones` dan error. | ídem |
| **Dado** las suites de NORM-03 e IA-10, **entonces** siguen en verde. | existentes |

## 6. Trazabilidad

- **PRD:** §4, Módulo 6.3, «Transcripción de originales escaneados»; ley fundacional 7.
- Decisión del propietario (2026-11-24) y brief del CTO.
- Depende de NORM-03 (análisis), NORM-05 (cabeza de Alembic de la sala), IA-10 (trazas), IA-12 (precedente sin tope), IA-13 (modelo) e IA-17 (región).
- **Estimación de coste (para el CTO; no es una regla):**
  - Gemini cuenta cada página de un PDF como unos **258 tokens de entrada**.
  - Una página del Registro Oficial transcrita da unos 4.000 caracteres, es decir, unos **1.000 a 1.300 tokens de salida**.
  - **LOPDP (70 páginas), una vez:** unos 18.000 tokens de entrada y unos 80.000 a 90.000 de salida, más la instrucción de cada uno de los 7 tramos.
  - El coste es entrada × precio de entrada más salida × precio de salida del modelo de IA-13, según la página de precios de Vertex AI del día. Con precios de la gama Flash del orden de 0,30 USD por millón de tokens de entrada y 2,50 por millón de salida, queda en unos **0,25 USD por la LOPDP completa**.
  - El Reglamento (47 páginas) costaría unos dos tercios de eso.
  - Por R4 se paga una sola vez por versión del documento.
- **Sin brief del propietario:** no cambia cuenta, variable ni permiso. Usa los de IA-13 e IA-17.
