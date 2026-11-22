# NORM-03b · Pestaña «Impacto» en el panel de una resolución de NORM-02
`¤sdd` `¤frontend-ide` `¤arbitro`

## 1. Datos

Sin backend nuevo. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `frontend/src/components/normativa/PanelResolucion.tsx` | pestañas «Documento» e «Impacto»; la segunda pinta `PestanaImpacto` con `resolucionId`, `esDpo` y `puedePedir` |
| `frontend/src/components/normativa/CentroVigilancia.tsx` | lee los roles de `/organizacion/me/roles` y se los pasa al panel |
| `frontend/tests/normativa_impacto/impacto.spec.ts` | corre contra rutas simuladas, sin `NORM03_BACKEND_REAL` |

Hecho medido en `origin/main` 60b8a5e0:
- `api/routers/inteligencia_normativa_impacto.py` declara `AUTO_REGISTRO = True`. El OpenAPI de `main.app` ya tiene `POST /api/v1/normativa/resoluciones/{id}/impacto`, `GET /api/v1/normativa/impacto` y `POST /api/v1/normativa/impacto/{id}/decision`. El router está montado.
- `PestanaImpacto({ resolucionId, esDpo, puedePedir })` no se importa fuera de `frontend/src/components/normativa_impacto/`.
- Roles del router: pide `dpo` y `admin_organizacion`; leen además `coordinador`, `implementador` y `auditor`; decide solo `dpo`. El operador de la plataforma (`esOperador()`) no es miembro de la organización.
- La prueba de Playwright se omite sin `NORM03_BACKEND_REAL=1`.

## 2. API

Sin rutas nuevas.

## 3. Reglas

- **R1 · Quién ve la pestaña.** La ven los roles de lectura del router. El operador de la plataforma no la ve. `esDpo` es verdadero solo con `dpo`, y `puedePedir` con `dpo` o `admin_organizacion`. El servidor vuelve a autorizar.
- **R2 · Roles de la sesión.** Se leen de `/organizacion/me/roles`, como en `AsistenteVulneraciones`. Si esa lectura falla, la pestaña no se pinta.
- **R3 · Accesibilidad.** Las pestañas siguen el patrón `tablist` de `CentroVigilancia` (`role="tab"`, `aria-selected`, `aria-controls`) y se recorren con las flechas.
- **R-ADPA · Ortogonalidad ZERAG (`NORM-03b`).** Solo los tres archivos; `normativa_impacto/**` no cambia.

## 4. Interfaz

UX/UI cerró esta sección el 2026-11-21.

**Pestañas.** Van en este orden: «Documento» e «Impacto».
- El `role="tablist"` lleva `aria-label` «Secciones de la resolución».
- Cada pestaña lleva `role="tab"`, `aria-selected` y `aria-controls`.
- Cada panel lleva `role="tabpanel"` y `aria-labelledby`.
- Al abrir una resolución, la pestaña activa es «Documento».

**Teclado.**
- Las flechas izquierda y derecha recorren las pestañas en ciclo; Inicio y Fin llevan a la primera y a la última.
- Solo la pestaña activa tiene `tabindex=0`.
- Las flechas mueven el foco y activan la pestaña a la vez, sin un paso extra. El foco se queda en la pestaña.

**Visibilidad.**
- El tablist solo se pinta para dpo, admin_organizacion, coordinador, implementador y auditor.
- Con cualquier otro rol, incluido el operador de la plataforma, no hay tablist y el panel se ve como hoy.
- Si falla la lectura de roles, el panel se ve como hoy y no aparece ningún aviso de error.
- Mientras se leen los roles, el tablist tampoco se pinta.

**Textos.** «Impacto» usa los textos de `PestanaImpacto` sin cambios. UX/UI los revisó en main.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** cada rol de lectura, **entonces** `getByRole("tab", { name: "Impacto" })` es visible. Un DPO pide el análisis y acepta con nota. Mutación m1: no montar la pestaña hace fallar la prueba. | `impacto.spec.ts` |
| **Dado** el operador de la plataforma, **entonces** esa pestaña tiene count 0 y se ve el documento. | `impacto.spec.ts` |
| **Dado** `/organizacion/me/roles` con 500, **entonces** no hay pestaña «Impacto» ni `role="alert"`. | `impacto.spec.ts` |
| **Dado** el foco en «Documento», **cuando** se pulsa ArrowRight, **entonces** «Impacto» queda con `aria-selected=true`; otro ArrowRight vuelve a «Documento». | `impacto.spec.ts` |
| **Dado** una pantalla de 375 px, **entonces** el panel tiene `scrollWidth <= clientWidth`. | `impacto.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/NORM-03b.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Cierra el pendiente 1 de #831 (NORM-03). Depende de NORM-02 y NORM-03, hechas. UX/UI cerró §4 el 2026-11-21.
