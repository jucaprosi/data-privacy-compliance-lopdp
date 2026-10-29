# ORG-16 · Alta de la organización en siete pasos
`¤sdd` `¤organizacion` `¤asistente`

## 1. Datos

Sin migración propia: cada paso escribe en tablas que ya existen por su compuerta. Una tabla de progreso es innecesaria: el estado del asistente se deriva (R2).

| Paso | Dónde se guarda | Compuerta |
| :--- | :--- | :--- |
| 1 Perfil | `tenants` (`nombre_comercial`, `tamano`, sector, naturaleza y columnas documentales de ORG-14) | `organizacion_service.update_tenant_config`, ORG-14 |
| 2 Sedes | columnas documentales de domicilio (ORG-14); sedes adicionales quedan fuera (ORG-17) | ORG-14 |
| 3 Áreas | `areas` | `organizacion_service.create_area` / `list_areas` |
| 4 Tratamientos sugeridos | `rat` (fichas marcadas `origen = 'sugerido'`) | `rat_service` |
| 5 Terceros típicos | `transferencias_terceros` | `terceros_service` |
| 6 Personas clave | `invitaciones_organizacion` (ORG-10) con rol propuesto | `organizacion_service` |
| 7 Resumen | nada; lanza el assessment | — |

Catálogos de sugerencias (paso 4 y 5): archivo estático `features/organizacion/data/sugerencias_por_sector.json` con `{sector: {tratamientos: [{nombre, finalidad, base_legal}], terceros: [{tipo, descripcion}]}}`. Solo estructura: ningún dato de otra organización (D-5).

## 2. API

Router `api/routers/organizacion_alta.py`, prefijo `/organizacion`, `AUTO_REGISTRO = True`.

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET /organizacion/alta` | `admin_organizacion`, `implementador`, `coordinador`, `dpo` | — | `200 {"pasos": [{"id": str, "completo": bool}], "completo": bool}` |
| `GET /organizacion/alta/sugerencias` | `admin_organizacion`, `implementador` | — | `200 {"tratamientos": [...], "terceros": [...]}` según el sector del paso 1; sin sector, listas vacías |
| `POST /organizacion/alta/paso/{id}` | `admin_organizacion`, `implementador` | cuerpo del paso (abajo) | `200 {"paso": id, "completo": true}` |

Cuerpos: `perfil {razon_social, ruc, sector, tamano ∈ {micro,pequena,mediana,corporativo}, naturaleza ∈ {publica,privada,mixta}, rol_datos ∈ {responsable,encargado,ambos}, actividades_riesgo: [str]}`; `sedes {domicilio, ciudad, provincia}`; `areas {areas: [{nombre, codigo?}]}`; `tratamientos {aceptados: [indice], ajustes: [{indice, nombre?, finalidad?}]}`; `terceros {aceptados: [indice]}`; `personas {personas: [{nombre, cargo, area_id?, email, rol ∈ {coordinador, responsable_area, dpo}}]}`; `resumen {}`.

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | `dpo`, `coordinador` o `responsable_area` al escribir |
| 409 | `TENANT_SIZE_NOT_CONFIGURED` | paso 6 con personas antes del paso 1 (reutiliza el código existente) |
| 409 | `DPO_INDEPENDENCE_VIOLATED` | paso 6 propone `dpo` para alguien con otro rol (reutiliza) |
| 422 | `PASO_DESCONOCIDO` | `id` fuera de los siete |
| 422 | (FastAPI) | campo faltante, valor fuera de los enumerados, `ruc` que no son 13 dígitos |

## 3. Reglas

- **R1 · Orden.** Los pasos 1 y 3 son obligatorios; 2, 4, 5 y 6 son opcionales (se pueden saltar con el patrón de FE-23). El paso 7 solo se completa si 1 y 3 están completos.
- **R2 · Estado derivado.** `completo(1) ⇔ tenants.tamano IS NOT NULL ∧ nombre_comercial no vacío`; `completo(3) ⇔ ∃ área`; `completo(2,4,5,6) ⇔` hay al menos un registro propio del paso; `completo(7) ⇔ completo(1) ∧ completo(3)`. No se guarda un `isConfigured`.
- **R3 · Idempotencia.** Repetir un paso actualiza, no duplica (áreas por `codigo` o `nombre`; tratamientos por índice de catálogo; invitaciones por `email`).
- **R4 · Personas.** Solo `nombre, cargo, area_id, email, rol`; ningún campo de identificación (D-6). Cada persona genera una invitación (ORG-10); el rol `dpo` pasa por `check_dpo_sod`.
- **R5 · Nada se crea aquí.** El tenant lo crea el operador (ORG-09); este asistente completa su perfil. Si el tenant no existe, 404 por RLS.
- **R6 · Auditoría.** `registrar_evento(entity_type='organizacion_alta', entity_id=tenant_id, action='paso_<id>')`.

## 4. Interfaz

`ProjectConfig.tsx` abre el asistente de FE-23 con los siete pasos; lee `GET /organizacion/alta` al montar y marca completos. Pantalla en Configuración (`menus/ORG-16.ts`, `pantallas/ORG-16.tsx`). Con los pasos 1 y 3 completos, el botón «Comenzar diagnóstico» se habilita; antes, dice qué falta. Los roles de solo lectura ven el estado sin botones.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un `admin_organizacion`, **cuando** completa los pasos 1 y 3, **entonces** `GET /organizacion/alta` responde `completo: true` desde otra sesión. Mutación: guardar solo en el navegador hace fallar la prueba. | `test_alta_persiste_en_servidor` |
| **Dado** un `dpo`, **cuando** envía el paso 1, **entonces** 403. | `test_alta_dpo_no_escribe` |
| **Dado** el paso 3 enviado dos veces con la misma área, **entonces** hay una sola área. | `test_alta_idempotente` |
| **Dado** el paso 6 con una persona `dpo` que ya es `coordinador`, **entonces** 409 `DPO_INDEPENDENCE_VIOLATED`. | `test_alta_dpo_exclusivo` |
| **Dado** sector `salud`, **cuando** se piden sugerencias, **entonces** vienen del catálogo y ninguna contiene datos de otra organización. | `test_alta_sugerencias_solo_estructura` |
| **Dado** el asistente, **cuando** se completa el paso 1 y se salta el 2, **entonces** el paso 3 queda activo y el progreso dice «Paso 3 de 7». | `frontend/tests/organizacion/alta.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/ORG-16.md`. PRD: Módulo 0 («Alta de organización en siete pasos»), Doctrina 9, §3.2 regla 4. Contraste: O-7, D-5, D-6.
- Decisiones abiertas: campos exactos de sector y naturaleza en `tenants` (hoy solo hay `tamano`); si faltan columnas, ORG-16 las añade en una migración propia y la ficha debe sumarla a su propiedad.
