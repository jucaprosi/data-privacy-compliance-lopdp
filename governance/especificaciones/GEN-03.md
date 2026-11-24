# GEN-03 · Biblioteca sin marca: la fuente de plantillas catalogo, el código BIB_COPIA_SOLO_CATALOGO y un solo término visible
`¤sdd` `¤biblioteca` `¤frontend-ide` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Programa: GEN-01 §0.

Hecho medido en `origin/main` ea6d26bf:
- `catalogo.py:19,30,67`: `FUENTES = ("smartcidi", "organizacion")`, el `Literal` del modelo de salida y la fuente que se asigna a las plantillas publicadas.
- `ficha.py:138-153`: la fuente se calcula al leer (publicada o «Mi plantilla») y decide `acciones.copiar`. **La fuente no se guarda en ninguna tabla**: `alembic/` no contiene el literal, así que no hay migración ni datos que convertir.
- `errores.py:37-38`: `BIB_COPIA_SOLO_SMARTCIDI` (422) y su mensaje. `mis_plantillas.py:30` lo lanza.
- Frontend: `catalogo.ts:16` (tipo `FuentePlantilla`), `:41` (opción del filtro «Modelos de plantillas»), `fichas.ts:18` y `FichaPlantilla.tsx:80,140`.
- `docs/biblioteca-pmv.md:16,19,149,151,240`.

## 2. API

| Ruta | Cambio |
| :--- | :--- |
| `GET /biblioteca/plantillas?fuente=` | `fuente` admite `catalogo` u `organizacion`; con otro valor, 422 como hoy |
| respuestas con `fuente` | `"catalogo"` u `"organizacion"` |
| `POST /plantillas/{id}/copias` sobre «Mi plantilla» | 422 `BIB_COPIA_SOLO_CATALOGO`: «Solo se copian las plantillas del catálogo; «Mi plantilla» se edita como versión nueva.» |

Cambia el contrato: backend y frontend van en el mismo PR. No hay clientes externos de esta API.

## 3. Reglas

- **R1 · Una sola fuente de la lista.** `FUENTES = ("catalogo", "organizacion")`. El `Literal` y el tipo del frontend usan los mismos dos valores.
- **R2 · Código de error.** `BIB_COPIA_SOLO_CATALOGO` sustituye al anterior, con el mismo estado 422.
- **R3 · Un solo término visible.**
  - La plantilla de la fuente `"catalogo"` se nombra con un único término, que elige UX/UI. «Modelos de plantillas» choca con el tipo «Modelo» del mismo filtro.
  - Lo usan la opción del filtro (`catalogo.ts:41`), la línea de la ficha (`FichaPlantilla.tsx:80`), el aviso de copia (`:140`) y `docs/biblioteca-pmv.md`.
  - **La ficha no se lanza sin el término anotado en §4.**
- **R4 · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`GEN-03`).** Solo la propiedad. Sin `import yaml`.

## 4. Interfaz

Pasa por UX/UI. Término de la fuente `"catalogo"`: **pendiente de UX/UI** (se pidió el 2026-11-24). Se anota aquí, en un PR de gobernanza, antes de lanzar la ficha.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el catálogo, **cuando** se filtra con `fuente=catalogo`, **entonces** devuelve las plantillas publicadas con `fuente = "catalogo"`. Mutación m1: dejar el valor anterior en `FUENTES` da rojo. | `tests/test_bib_102_catalogo.py`, `catalogo.spec.ts` |
| **Dado** «Mi plantilla», **cuando** se copia, **entonces** 422 `BIB_COPIA_SOLO_CATALOGO`. Mutación m2: lanzar otro código da rojo. | `tests/test_bib_103_ficha.py` |
| **Dado** la ficha de una plantilla del catálogo, **entonces** muestra el término de §4 y el aviso de copia con ese término. | `ficha.spec.ts`, `formularios.spec.ts` |

## 6. Trazabilidad

- Programa GEN-01 §0. Vocabulario de GEN-01 R1.
- Depende de las fichas hechas que comparten estos archivos: BIB-102, BIB-103 y BIB-109.
