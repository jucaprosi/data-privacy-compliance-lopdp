# GOB-07 · El tema claro es el predeterminado y la referencia de diseño
`¤sdd` `¤frontend-ide` `¤arbitro`

## 1. Datos

Hechos medidos en `origin/main` 6efbb733 (brief del CTO):
- PRD §6 (`governance/artefactos/PRD.md:633`) pide los dos temas con variables semánticas, sin decir cuál es el predeterminado ni la referencia.
- El criterio 23 (`PRD.md:678`) pide «todas las pantallas legibles en ambos temas», y la prueba no cubría `/plataforma`.
- `METODOLOGIAS.md` §12 fija la base acromática en negros (`#0a0a0c`) y grises oscuros (`#141417`, `#26262b`), con el claro como añadido.
- FE-30 ya sirve el tema claro en la primera pintura.

Textos de estado final:
- **PRD §6:** «El tema claro es el predeterminado (primera pintura, sin preferencia guardada) y la referencia de diseño y de desarrollo: cada pantalla se diseña y se prueba primero en claro. El oscuro es la alternativa y sale de los mismos tokens `--ui-*`.»
- **Criterio 23:** «El contraste cumple WCAG 2.2 AA (4,5:1 en texto normal; 3:1 en texto grande y bordes de controles), medido primero en claro y después en oscuro, en todas las rutas de la aplicación y en cada vista del tablero, Plataforma incluida. Árbitro: `frontend/tests/contraste/rutas.spec.ts` (FE-32).»
- **METODOLOGIAS §12, base acromática:** blanco `#ffffff` de fondo y superficie, `#fafafa` de superficie secundaria, texto `#09090b`, texto suave `#52525b`, borde decorativo `#d4d4d8` y borde de control `#71717a`. Los valores oscuros (`#0a0a0c`, `#141417`, `#18181b`, `#f4f4f5`, `#a1a1aa`, `#34343b` y `#8a8a93`) describen el tema alternativo. Fuente: parte del UX/UI §7 (2026-11-27).
- **METODOLOGIAS §12, partes de pantalla:** todo parte de pantalla del UX/UI abre su sección de tokens con la columna del tema claro, después la del oscuro, y nombra solo tokens `--ui-*`.

## 2. API

No aplica.

## 3. Reglas

- **R1 · Claro primero.** El PRD y la metodología describen el claro como referencia y el oscuro como alternativa de los mismos tokens.
- **R2 · Medición en todas las rutas.** El criterio 23 nombra a FE-32 como árbitro.
- **R-SP · Sin prohibiciones** (GEN-01 R3): las reglas se miden por el contraste de lo que se ve.
- **R-ADPA · Ortogonalidad ZERAG (`GOB-07`).** Solo los archivos de la propiedad.

## 4. Interfaz

Sin pantalla.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** PRD §6, el criterio 23 y `METODOLOGIAS.md` §12, **entonces** dicen los textos de §1. | revisión del CTO |
| **Dado** el índice y el reparto, **entonces** siguen en verde. | `tests/test_reparto.py`, `tests/test_indice_tareas.py` |

## 6. Trazabilidad

- Orden del propietario del 2026-11-27, brief del CTO `ARQUITECTO_UXUI_TEMA_CLARO_PREDETERMINADO.md`, parte del UX/UI `UXUI_PARTE_PANTALLA_CONTRASTE_PLATAFORMA.md` §7.
