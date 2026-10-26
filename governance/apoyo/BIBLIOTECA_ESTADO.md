# Estado del módulo Biblioteca EVYDENTIA

> **Sin seguimiento Git**; su propietaria propuesta es GOB-03. Corte: 2026-10-26, leído de `feat/bib-105` en 8805f5c, con cambios sin commit de otro chat en `alembic/versions/20261025_biblioteca_base.py` y `tests/test_bib_105_editorial.py`.
> Este archivo resume y enlaza. No sustituye a las fuentes de verdad del repo: el estado de cada tarea solo vive en la cabecera de `governance/tareas/BIB-*.md`; el alcance, en el PRD Módulo 7; el orden, en `governance/apoyo/BIBLIOTECA_PLAN.md`. Si hay contradicción, mandan ellas.
> Las citas normativas aparecen tal como las traen las plantillas y están **POR VERIFICAR**; este documento no afirma su contenido.

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
| 2026-10-26 | README del módulo en `governance/apoyo/BIBLIOTECA_README.md`; GOB-03 posee este archivo y el README, depende de ORG-01, ORG-08 y BIB-105, en la rama `chore/gob-03-biblioteca` (fuera de #158) | propietaria |
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
- [x] Redactar `governance/tareas/GOB-03.md` (rama `chore/gob-03-biblioteca`, sin push).
- [ ] Registrar BL-84 tras fusionar #158; push y PR de GOB-03 cuando la propietaria lo autorice.
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
| — | `chore/gob-03-biblioteca` | local, sin push | Ficha GOB-03, este archivo y el README; después, kit v1 (BL-84) |

## 8. Registro de sesiones de documentación

| Fecha | Qué se hizo | Decisiones | Pendientes abiertos |
| :--- | :--- | :--- | :--- |
| 2026-10-26 | Diagnóstico del reparto BL-83, revisión de las ocho v0.1 y del manifiesto; creación de este archivo y borrador del README | Opción B, GOB-03, BL-84 tras #158 | Ficha GOB-03; revisión jurídica de citas |
| 2026-10-26 | README movido a `governance/apoyo/`; ficha GOB-03 creada y comprometida en `chore/gob-03-biblioteca` con este archivo y el README | GOB-03 depende de ORG-01, ORG-08 y BIB-105 | Push/PR de GOB-03; revisión de EIPD-00 |
