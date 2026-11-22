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

Propuesta para UX/UI, que la cierra antes de lanzar la ficha:
- Pestañas del panel: «Documento» (lo de hoy: documento, historial y revisión del operador) e «Impacto».
- «Impacto» muestra `PestanaImpacto` tal como la dejó NORM-03, con sus textos.
- Quien no tiene un rol de lectura no ve la pestaña.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un DPO con rutas simuladas, **entonces** ve la pestaña «Impacto», pide el análisis, ve el aviso de IA y puede aceptar con nota. Mutación m1: no montar la pestaña hace fallar la prueba. | `impacto.spec.ts` |
| **Dado** un administrador, **entonces** ve «Impacto» y «Pedir», pero no «Aceptar» ni «Rechazar». | `impacto.spec.ts` |
| **Dado** el operador de la plataforma o un rol sin lectura, **entonces** no ve la pestaña. | `impacto.spec.ts` |
| **Dado** las pestañas, **entonces** se recorren con las flechas y la pestaña activa tiene `aria-selected`. | `impacto.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/NORM-03b.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Cierra el pendiente 1 de #831 (NORM-03). Depende de NORM-02 y NORM-03, hechas. Pasa por UX/UI (§4).
