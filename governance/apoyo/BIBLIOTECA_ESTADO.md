# Estado del módulo Biblioteca EVYDENTIA

> **Sin seguimiento Git**; su propietaria propuesta es GOB-03. Corte: 2026-10-26, leído de `feat/bib-105` en 8805f5c, con cambios sin commit de otro chat en `alembic/versions/20261025_biblioteca_base.py` y `tests/test_bib_105_editorial.py`.
> Este archivo resume y enlaza. No sustituye a las fuentes de verdad del repo: el estado de cada tarea solo vive en la cabecera de `governance/tareas/BIB-*.md`; el alcance, en el PRD Módulo 7; el orden, en `governance/apoyo/BIBLIOTECA_PLAN.md`. Si hay contradicción, mandan ellas.
> Las citas normativas aparecen tal como las traen las plantillas y están **POR VERIFICAR**; este documento no afirma su contenido.

## 0. Reglas de trabajo para los chats (documentación, backend y frontend)

- **Estado del CI:** no se informa "en verde" hasta que **todos** los checks hayan terminado. Mientras alguno siga en ejecución se informa así: "X de Y terminados, N en curso", indicando además los que fallan. (Propietaria, 2026-10-26)

## 1. Objetivo

Administrar maestros documentales de protección de datos (Word y Excel) y los documentos de cada organización, sin confundir existencia, descarga, aprobación, implementación y eficacia. El catálogo maestro es global y solo lo escriben personas con capacidad editorial explícita; los documentos de empresa quedan aislados por tenant.

Tres entregas acumulativas (PRD Módulo 7 A):

| Entrega | Resultado | Fichas |
| :--- | :--- | :--- |
| 1. Biblioteca descargable | Catálogo, ficha, descarga controlada, administración editorial, documentos externos por empresa | BIB-101…108 |
| 2. Creación guiada | Formularios versionados, datos reutilizables, reglas explicables, generación DOCX/XLSX | BIB-201…208 |
| 3. Gestión e integración | Revisión, aprobación, acciones, evidencias, conservación, indicadores | BIB-301…307 |

## 2. Estado actual

- **Fichas:** las 23 en `pendiente` (ninguna cerrada; solo el coordinador cierra).
- **En curso:** BIB-105 (administración editorial) en `feat/bib-105`, [PR #158](https://github.com/jucaprosi/data-privacy-compliance-lopdp/pull/158) en borrador. Implementado en la rama:
  - Backend: tablas `biblioteca_capacidades`, `biblioteca_auditoria_capacidades`, `biblioteca_catalogo`, `biblioteca_versiones`, `biblioteca_revisiones`, `biblioteca_auditoria`, con RLS y grants de solo lectura más políticas por capacidad.
  - API `/biblioteca/editorial` (ver §6) y compuerta `features/biblioteca/biblioteca_service.py`.
  - Validación OOXML sin macros, hasta 10 MB, con SHA-256; separación autor/revisor/publicador; una sola versión publicada por código.
  - Frontend: harness `frontend/src/app/harness-biblioteca/editorial/` con `AdministracionEditorial` y `FichaEditorial`.
- **Kit v1:** `data/biblioteca/kit_v1/` con ocho maestros v0.1 **en revisión**, no publicados. Manifiesto SHA-256 válido (15/15).
- **Reparto:** `verificar_reparto.py --bloque BL-83` sale con 1 por los 21 archivos del commit 061fccb (kit y documentos). Se resolverá con la opción B (§3).

## 3. Decisiones tomadas

| Fecha | Decisión | Fuente |
| :--- | :--- | :--- |
| 2026-10-25 | 23 fichas, sin IDs artificiales; BL-83 secuencial: BIB-105 y después BIB-108 | BIBLIOTECA_PLAN.md, PR #157 |
| 2026-10-25 | Publicación denegada por defecto; exige ficha, archivo, responsable y dictamen técnico y jurídico independientes de la misma generación | BIB-105, `domain/editorial.py` |
| 2026-10-25 | Administrador de empresa o plataforma no concede capacidades editoriales | PRD Módulo 7 C |
| 2026-10-26 | Una sola versión publicada por código; la nueva sustituye explícitamente | commit 8805f5c |
| 2026-10-26 | Opción B: revertir 061fccb en `feat/bib-105` y llevar el kit a un PR propio | propietaria |
| 2026-10-26 | Nueva ficha GOB-03 dueña del kit y documentos de Biblioteca (incluido `PRD.md`, con `depende_de = ["ORG-01"]`) | propuesta aceptada |
| 2026-10-26 | BL-84 se registra en el PR de gobernanza de la tanda, después de fusionar #158 | propietaria |
| 2026-10-26 | README del módulo en `governance/apoyo/BIBLIOTECA_README.md`; GOB-03 posee este archivo y el README, depende de ORG-01, ORG-08, SEC-02 y BIB-105, en la rama `chore/gob-03-biblioteca` (fuera de #158) | propietaria |
| — | Las ocho v0.1 no se publican hasta aprobación una por una de la propietaria | propietaria |

## 4. Pendientes

### Pendientes para otros chats

El chat de documentación no escribe código; registra aquí lo que requiere cambios de código.

#### Backend
- [ ] Revertir 061fccb en `feat/bib-105` (chat de cierre) y volver a ejecutar `verificar_reparto.py --bloque BL-83` hasta 0.
- [ ] BIB-108: importador idempotente con `--verificar`, `data/biblioteca/manifiesto_inicial.json` y 50 códigos; espera a #158 y al kit (GOB-03).
- [ ] BIB-102/103/104: lectura pública del catálogo, ficha y descarga controlada (no existen endpoints aún).
- [ ] BIB-106: análisis antivirus y cuarentena de archivos externos; `validar_archivo` no acredita antivirus.
- [ ] Decisión humana: límite 10 MB actual frente a 20 MB del kit (`proposal_limits.max_file_megabytes`).

#### Frontend
- [ ] BIB-101: `BibliotecaWorkspace` con secciones reservadas; espera FE-17, FE-10, FE-19 y ORG-09.
- [ ] Catálogo, ficha y descarga (BIB-102…104) sobre el cliente `frontend/src/lib/biblioteca/http.ts`.
- [ ] El harness editorial es solo para editores; la vista de usuario final de empresa no existe todavía (BIB-101…104).

### Documentación y gobernanza (este chat)
- [x] Redactar `governance/tareas/GOB-03.md` y abrir el PR #174 en borrador.
- [ ] Registrar BL-84 tras fusionar #158.
- [x] EIPD-00: cotejo jurídico E1–E5 contra fuentes oficiales (§9.2).
- [x] EIPD-00: la propietaria resolvió los puntos PENDIENTE VALIDACIÓN de §9.2 (§9.3).
- [ ] EIPD-00 v0.3: revisar la norma de transferencias (SPDP-SPD-2026-0004-R) y la de IA con su reforma (0037-R); añadir un disparador de EIPD solo si se cita el artículo que la exige.
- [ ] Verificar si los datos de condenas e infracciones penales del art. 42 b) se solapan con el "pasado judicial" del art. 4 LOPDP (§9.3, P4).
- [ ] Validar la ausencia de reformas al art. 42 LOPDP con un texto consolidado (§9.3, P3).
- [ ] EIPD-00: redactar v0.2 como archivo nuevo con E1–E12 (el original v0.1 no se edita).
- [ ] Actualizar la línea 51 de BIB-108 ("sin seguimiento Git") en el PR del kit y añadir `GOB-03` a su `depende_de`.
- [ ] Decidir si `README.md` del kit entra en el manifiesto o se declara "no original".
- [ ] Revisión jurídica de las citas de las ocho plantillas (§5, columna "Fuentes que cita"): todas **POR VERIFICAR**.
- [ ] Revisión editorial: `{{FECHA}}` con tres usos en EIPD-00; `{{EVIDENCIA_ID}}` con significado distinto en AVI-01 y EIPD-00; columnas de fecha de INV-01 S, INV-02 Q, RAT-01 V, PLA-01 H y O sin validación de fecha en Excel.

## 5. Catálogo de las ocho plantillas iniciales

Datos de `catalogo/catalogo_maestro.xlsx` y de las propias plantillas. "Aprueba" es el campo del catálogo; en todas figura "Responsable del tratamiento o autoridad delegada". La aplicación a **encargados** no está definida por el kit salvo como dato capturado (rol `Responsable / Encargado / Por evaluar` en RAT-01 y LEG-01): **POR VERIFICAR**.

| Código | Nombre | Formato | Naturaleza (kit) | Aplica a (kit) | Fuentes que cita (POR VERIFICAR) | Variables / campos |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| INV-01 | Inventario de datos personales | XLSX | Medida demostrativa | Procesos que tratan datos personales | N01 | Columnas A–T, ficha INV-01 |
| INV-02 | Inventario de activos y sistemas | XLSX | Medida demostrativa | Activos que soportan tratamientos | N01 | Columnas A–R, ficha INV-02 |
| RAT-01 | Registro de actividades de tratamiento | XLSX | Obligación condicional o buena práctica | Responsable según umbral de trabajadores y gran escala | N01, N02 (art. 38 RGLOPDP), N09 (art. 6), N12 | Columnas A–X, ficha RAT-01 |
| LEG-01 | Matriz de bases legitimadoras por finalidad | XLSX | Medida demostrativa | Cada finalidad y cada rol | N01, N07 | Columnas A–S, ficha LEG-01 |
| PLA-01 | Plan de acción de implementación | XLSX | Buena práctica | Brechas y riesgos que requieren acción | N01 | Columnas A–S; R y S calculadas; hoja `Parametros` |
| EIPD-00 | Análisis de necesidad de EIPD | DOCX | Medida demostrativa | Antes de un tratamiento o cambio relevante | N01 (art. 42), N03, N09, N11 (art. 15 y transitoria) | 32 variables `{{…}}` (incluye 10 de control comunes) |
| AVI-01 | Aviso de privacidad por tratamiento | DOCX | Obligación expresa | Deber de información por actividad y audiencia | N01, N08 | 57 variables `{{…}}` (incluye 10 de control comunes) |
| PRO-01 | Procedimiento de atención de derechos | DOCX | Medida demostrativa | Organización sujeta a deberes de atención | N01 (art. 13), N02 (art. 38) | 23 variables `{{…}}` (incluye 10 de control comunes) |

- N01 en las ocho plantillas: "LOPDP. Arts. 7 a 10, 12 a 24, 25 a 30, 37 a 43, 46 a 50 y 55 a 61", con estado "texto consultado; verificar reformas". Ninguna de estas citas ha sido cotejada en este repositorio.
- El detalle de cada campo (requisito O/C/D, tipo, regla, columna de salida) está en `governance/apoyo/BIBLIOTECA_FICHAS_OCHO_PLANTILLAS.md`; no se copia aquí.
- Políticas, consentimientos, notificación de brechas, contratos con encargados y el resto del alcance documental pertenecen a los 40 códigos planificados: no tienen maestro redactado ni se ofrecen como archivo.
- El catálogo completo tiene 50 códigos: estos ocho, dos salidas existentes por mapear (DIA-01, DIA-02) y 40 planificadas que nunca se muestran como descargables.

## 6. Contrato backend ↔ frontend

### 6.1 Implementado en BIB-105 (rama, no integrado)

Prefijo `/biblioteca/editorial`. Identidad por `get_usuario_autenticado`; capacidades desde `biblioteca_capacidades`, nunca desde cabeceras.

| Método y ruta | Capacidad | Entrada | Salida |
| :--- | :--- | :--- | :--- |
| `GET ""` | cualquiera | — | `VistaEditorial` |
| `POST /versiones` | editor | `CrearVersion` | `VersionMaestra` (201) |
| `PUT /versiones/{id}/ficha` | editor | `EditarFicha` | `VersionMaestra` |
| `PUT /versiones/{id}/archivo` | editor | `ArchivoMaestro` (base64, ≤10 MB) | `VersionMaestra` |
| `POST /versiones/{id}/revisiones` | revisor_tecnico o revisor_juridico | `Dictamen` | `VersionMaestra` (201) |
| `POST /versiones/{id}/publicar` | publicador | `Transicion` | `VersionMaestra` |
| `POST /versiones/{id}/retirar` | publicador | `Transicion` | `VersionMaestra` |
| `GET /versiones/{id}/historial` | cualquiera | — | `EventoEditorial[]` |

Modelo `VersionMaestra` (espejo TS en `frontend/src/lib/biblioteca/editorial.ts`): `id, codigo, version, formato (DOCX|XLSX), ficha, responsable_id, autores[], estado, generacion, nombre_archivo, sha256, sustituye_id, creada_en`.
`Ficha`: `nombre, objetivo, fuentes, fecha_revision, instrucciones, dependencias, restricciones`, todos obligatorios para publicar.
Concurrencia: cada escritura envía `generacion`; si no coincide, `BIB_CONFLICTO_VERSION` (409).

Errores (`app_core/errors.py`): `BIB_SIN_CAPACIDAD` 403, `BIB_AUTOR_NO_INDEPENDIENTE` 403, `BIB_VERSION_INMUTABLE` 409, `BIB_PUBLICACION_INCOMPLETA` 409, `BIB_REVISION_PENDIENTE` 409, `BIB_NO_ENCONTRADA` 404, `BIB_CONFLICTO_VERSION` 409, `BIB_ARCHIVO_INVALIDO` 415, `BIB_SUSTITUCION_REQUERIDA` 409.

### 6.2 Estados

Versión maestra (implementado):

```
en_revision ──publicar──▶ publicada ──retirar──▶ retirada
                              │
        nueva versión con sustituye_id ──publicar──▶ anterior pasa a sustituida
```

- No existe un estado `borrador` separado: `en_revision` es el único editable (ficha y archivo) y cada edición incrementa `generacion`, lo que invalida los dictámenes previos.
- `publicada`, `retirada` y `sustituida` son inmutables.
- "Versión" es el campo `version` (`N.N` o `N.N.N`), único por código.

Documento de empresa (PRD Módulo 7 D, **no implementado**): borrador, generado para revisión, en revisión, devuelto, aprobado, implementado, verificado eficaz, sustituido, archivado.

### 6.3 Esperado y aún no definido en código

Propuestas del kit (`backlog_y_esquemas.json`); son contrato propuesto, no API instalada. Cada ficha fija las rutas reales al implementarse.

| Necesidad | Ficha |
| :--- | :--- |
| Catálogo y búsqueda para usuarios de empresa (solo publicadas) | BIB-102 |
| Ficha pública de plantilla | BIB-103 |
| Descarga controlada con registro | BIB-104 |
| Documentos externos y revisiones por empresa (`DocumentoEmpresa`, `RevisionDocumento` en `domain/base.py`) | BIB-106, BIB-107 |
| Formulario por versión con `schema_version` | BIB-201 |
| Generación: petición `organization_id, document_id, document_revision_id, template_version_id, schema_version, format, idempotency_key`; trabajo `queued / running / succeeded / failed` | BIB-205, BIB-207 |

## 7. Historial de PRs

| PR | Rama | Estado | Contenido |
| :--- | :--- | :--- | :--- |
| [#32](https://github.com/jucaprosi/data-privacy-compliance-lopdp/pull/32) | `docs/prd-tasks-hoja-de-ruta` | fusionado 2026-10-10 | PRD y hoja de ruta base (anterior a Biblioteca) |
| [#157](https://github.com/jucaprosi/data-privacy-compliance-lopdp/pull/157) | `chore/biblioteca-gobernanza` | fusionado 2026-10-25 | Plan de Biblioteca y 23 fichas BIB |
| [#158](https://github.com/jucaprosi/data-privacy-compliance-lopdp/pull/158) | `feat/bib-105` | borrador | BIB-105 administración editorial (+ kit, pendiente de separar) |
| [#174](https://github.com/jucaprosi/data-privacy-compliance-lopdp/pull/174) | `chore/gob-03-biblioteca` | borrador, CI 3/3 verde; no fusionar antes del #158 | Ficha GOB-03, este archivo y el README; después, kit v1 (BL-84) |

## 8. Registro de sesiones de documentación

| Fecha | Qué se hizo | Decisiones | Pendientes abiertos |
| :--- | :--- | :--- | :--- |
| 2026-10-26 | Diagnóstico del reparto BL-83, revisión de las ocho v0.1 y del manifiesto; creación de este archivo y borrador del README | Opción B, GOB-03, BL-84 tras #158 | Ficha GOB-03; revisión jurídica de citas |
| 2026-10-26 | README movido a `governance/apoyo/`; ficha GOB-03 creada y comprometida en `chore/gob-03-biblioteca` con este archivo y el README | GOB-03 depende de ORG-01, ORG-08 y BIB-105 | Push/PR de GOB-03; revisión de EIPD-00 |
| 2026-10-26 | Push y PR #174 en borrador; revisión de contenido de EIPD-00 (§9) | v0.2 de EIPD-00 será un archivo nuevo | Decisiones de §9; aprobación de la propietaria |
| 2026-10-26 | Decisiones de la propietaria sobre P1–P5 y E4 (§9.3); copias del checkout de BIB-105 eliminadas | Trabajar solo en `wt-gob-03` | v0.2 de EIPD-00; tarea v0.3 (E4) |
| 2026-10-26 | CI del #174: `tests/test_reparto.py` fallaba (R1: GOB-03 no figuraba en «Sin agente»); corregido en 6492552 | GOB-03 listada en «Biblioteca pendiente de asignación posterior»; depende también de SEC-02 | — |
| 2026-10-26 | Cotejo jurídico E1–E5 de EIPD-00 contra LOPDP, RGLOPDP y resoluciones SPDP (§9.2) | Solo fuente oficial; lo no comprobado queda PENDIENTE VALIDACIÓN | 6 puntos PENDIENTE VALIDACIÓN |

## 9. Revisión de contenido de plantillas

### 9.1 EIPD-00 v0.1: hallazgos (2026-10-26)

Todas las referencias normativas siguen **POR VERIFICAR**; esta revisión no coteja textos legales.

| # | Tipo | Hallazgo |
| :--- | :--- | :--- |
| E1 | Fuentes | El catálogo declara fuentes N01; N09; N11, pero la plantilla cita también N03. Falta alinear ambos. |
| E2 | Fuentes | N02 (Reglamento General) describe "capítulos sobre … EIPD" en PRO-01, pero EIPD-00 no lo cita. Jurídico debe decidir si aplica. |
| E3 | Normativa | Afirmaciones sustantivas sin cotejo: "Supuestos del art 42 LOPDP"; "N11 art. 15"; "N11 dispone EIPD previa y revisión cada doce meses"; disposición transitoria de N11. |
| E4 | Normativa | "revisar transferencias sujetas a autorización e IA según norma consolidada" no tiene fuente identificada. |
| E5 | Fuentes | El enlace de N01 apunta a un portal no oficial de la SPDP ni del Registro Oficial; conviene una fuente oficial. |
| E6 | Variables | `{{FECHA}}` se usa tres veces con significados distintos: elaboración, plazo para obtener datos faltantes y fecha de versión. |
| E7 | Variables | `{{SI_NO}}` es una clave genérica para biometría; la ficha la reserva solo para ese criterio. |
| E8 | Ficha | La ficha exige por criterio respuesta Sí/No/Desconocido, evidencia, fundamento y evaluador; la plantilla solo trae ese formato para alto riesgo y no tiene campo "evaluador" en ningún criterio. |
| E9 | Ficha | `{{REQUERIMIENTO_O_NO_IDENTIFICADO}}` mezcla la respuesta y su valor en una sola variable. |
| E10 | Contenido | Las instrucciones comunes citan campos condicionales (DPD, representación, transferencias) que esta plantilla no tiene. |
| E11 | Contenido | Remite a EIPD-01, que es un código planificado (lote 2) sin maestro; debe mostrarse como planificado. Lo mismo ocurre con los insumos RIE-01 y ESC-01 del catálogo. |
| E12 | Formato | "Estado: Borrador" está fijo en el texto, no como variable de control. |
### 9.2 EIPD-00: cotejo jurídico E1–E5 (2026-10-26)

Solo se citan fuentes oficiales leídas en esta sesión. Lo que no se pudo comprobar con fuente oficial queda **PENDIENTE VALIDACIÓN** para la propietaria.

**Fuentes oficiales consultadas**

| ID | Instrumento | Publicación verificada | Enlace oficial |
| :--- | :--- | :--- | :--- |
| N01 | Ley Orgánica de Protección de Datos Personales (LOPDP) | Quinto Suplemento del Registro Oficial Nº 459, 26 de mayo de 2021 (portada de la edición) | [spdp.gob.ec · Marco normativo](https://www.spdp.gob.ec/wp-content/uploads/2026/10/02-Ley-Organica-de-Proteccion-de-Datos-Personales-2021_compressed.pdf) |
| N02 | Reglamento General de la LOPDP (RGLOPDP), Decreto Ejecutivo 904 | Tercer Suplemento del Registro Oficial Nº 435, 13 de noviembre de 2023 (portada de la edición) | [spdp.gob.ec · Marco normativo](https://www.spdp.gob.ec/wp-content/uploads/2026/09/03-Reglamento-General-de-la-Ley-Organica-de-Proteccion-de-Datos-Personales-2023.pdf) |
| N03 | Resolución SPDP-SPD-2025-0003-R, Guía de Gestión de Riesgos y Evaluación de Impacto | Firmada el 29 de abril de 2025; vigente desde su suscripción (disposición final). Cuarto Suplemento del RO Nº 41, 19 de mayo de 2025 (dato de la propietaria, §9.3) | [spdp.gob.ec · Resoluciones](https://www.spdp.gob.ec/wp-content/uploads/2025/12/03.01.01-SPDP-SPD-2025-0003-R-Guia-Gest-de-Riesg-y-Ev-Imp-signed_compressed.pdf) |
| N09 | Resolución SPDP-SPD-2026-0005-R, Norma general sobre tratamiento a gran escala | Firmada el 2 de febrero de 2026; vigente desde su publicación en el RO. Suplemento del RO Nº 231, 25 de febrero de 2026 (dato de la propietaria, §9.3) | [spdp.gob.ec · Resoluciones](https://www.spdp.gob.ec/wp-content/uploads/2026/08/Resolucion0005.pdf) |
| N11 | Resolución SPDP-SPD-2026-0039-R, Norma general para el tratamiento de datos biométricos | Firmada el 9 de septiembre de 2026; vigente desde su publicación en el RO. RO Año II Nº 376, 24 de septiembre de 2026 (dato de la propietaria, §9.3) | [spdp.gob.ec · Resoluciones](https://www.spdp.gob.ec/wp-content/uploads/2026/10/SPDP-SPD-2026-0039-R-Norma-General-para-el-Tratamiento-de-Datos-Biometricos-signed.pdf) |

**Correcciones**

| # | Corrección propuesta para v0.2 | Fuente oficial |
| :--- | :--- | :--- |
| E1 | Añadir N02 y N03 a las fuentes de EIPD-00 en el catálogo (hoy N01; N09; N11). N03 aprueba la guía de riesgos y EIPD, cuyo capítulo I es obligatorio. | N03 arts. 1 y 2 |
| E2 | Citar el RGLOPDP, capítulo VII "Evaluación de impacto": art. 29 (concepto), art. 30 (objeto), art. 31 (EIPD obligatoria, previa al tratamiento; consulta a la Autoridad con respuesta en 5 días) y art. 32 (contenido mínimo y presentación ante la Autoridad, que corresponde a EIPD-01). | N02 arts. 29–32 |
| E3a | Sustituir "Supuestos del art 42 LOPDP" por los tres supuestos del art. 42, segundo inciso: a) evaluación sistemática y exhaustiva con perfiles y efectos jurídicos; b) tratamiento a gran escala de categorías especiales **o de datos relativos a condenas e infracciones penales**; c) observación sistemática a gran escala de una zona de acceso público. La variable `CATEGORIAS_ESPECIALES_GRAN_ESCALA` omite hoy las condenas e infracciones penales. | N01 art. 42; N02 art. 31 |
| E3b | Añadir como disparadores el primer inciso del art. 42 (alto riesgo o requerimiento de la Autoridad) y su penúltimo inciso: la Autoridad establecerá otros tipos de operaciones que requieran EIPD. | N01 art. 42 |
| E3c | Precisar que la EIPD se efectúa antes del inicio del tratamiento. | N01 art. 42, último inciso; N02 art. 31 |
| E3d | Biometría: cambiar "N11 art. 15" por "N11 arts. 5 y 15". El art. 15 confirma la EIPD obligatoria antes de implementar el sistema y su revisión cada 12 meses y cuando cambie el nivel de riesgo. El art. 13 exige evaluar antes mecanismos menos invasivos. | N11 arts. 5, 13 y 15 |
| E3e | Transitoria de N11: quienes ya usen sistemas biométricos al entrar en vigencia deben adecuarse en 12 meses contados desde la publicación de la norma en el RO. Coincide con la plantilla. | N11, disposición transitoria |
| E3f | N09 debe citarse por su art. 12.1 (el resultado del MTGE determina la obligación de EIPD previa) y no solo por los arts. 4 a 6, que tratan criterios y actualización del RAT. | N09 arts. 4–6 y 12.1 |
| E5 | Sustituir el enlace de N01 (finanzaspopulares.gob.ec) por el de la SPDP (tabla anterior), que reproduce la edición del RO. Sustituir también el enlace de N03 de la plantilla, que devuelve 404, por el oficial de la tabla. | — |

**PENDIENTE VALIDACIÓN**

| # | Punto | Motivo |
| :--- | :--- | :--- |
| P1 | Datos de publicación en el RO de N11 ("RO 376 de 24 de septiembre de 2026", según la plantilla). Determina desde cuándo corren los 12 meses de la transitoria. | El PDF oficial de la resolución no trae datos del RO; no se localizó la edición. |
| P2 | Datos de publicación en el RO de N09 y de N03. | Sus PDF oficiales no traen datos del RO. |
| P3 | Si la LOPDP tiene reformas posteriores al RO 459 que afecten al art. 42. | Solo se leyó el texto publicado en 2021; no se verificó una codificación vigente. |
| E4 | "Revisar transferencias sujetas a autorización e IA según norma consolidada". | No se localizó una fuente oficial que establezca un disparador de EIPD por transferencias o por IA. No se infiere. |
| P4 | Si los "datos relativos a condenas e infracciones penales" del art. 42 b) forman parte de las categorías especiales o son un supuesto aparte. | El texto los enumera junto a ellas; su calificación es jurídica. |
| P5 | Enlace directo en registroficial.gob.ec de las ediciones 459 (2021) y 435 (2023). | Se usaron los PDF de la SPDP, que reproducen esas ediciones; no se obtuvo el enlace del propio RO. |

### 9.3 EIPD-00: decisiones de la propietaria (2026-10-26)

Los datos de publicación en el RO de esta sección los aportó la propietaria; este chat no localizó esas ediciones (ver §9.2).

| # | Decisión para v0.2 |
| :--- | :--- |
| P1 | N11 (SPDP-SPD-2026-0039-R): expedida el 9 de septiembre de 2026; RO Año II Nº 376, 24 de septiembre de 2026. La transitoria de 12 meses vence el **24 de septiembre de 2027**. Enlace: el PDF oficial de §9.2 (`spdp.gob.ec/r39` devolvió 404 el 2026-10-26). |
| P2 | Citar con los datos del RO: N09 (0005-R), Suplemento del RO Nº 231, 25 de febrero de 2026, vigente desde la publicación; N03 (0003-R), Cuarto Suplemento del RO Nº 41, 19 de mayo de 2025, vigente desde la suscripción. Las fechas de firma de §9.2 se comprobaron contra los PDF oficiales y no estaban invertidas. |
| P3 | Texto en v0.2: "texto según RO 459 (26 may 2021); sin reformas al art. 42 identificadas al 26 oct 2026". Nota: validar con un texto consolidado. |
| E4 | Se elimina de v0.2 la frase sobre transferencias e IA. Tarea abierta para v0.3 en §4. |
| P4 | Dos variables separadas: `cat_especial` y `penal`. Disparador: `gran_escala ∧ (cat_especial ∨ penal)`. Nota: posible solapamiento con "pasado judicial" del art. 4 LOPDP, **pendiente de verificar**. |
| P5 | Citar en el texto el número y la fecha del RO y enlazar los PDF de la SPDP. |
