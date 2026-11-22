# LEG-06 · Licencia propietaria y aviso de derechos de autor en todo archivo de código versionado
`¤sdd` `¤ip` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `LICENSE` (nuevo) | copia literal de `jucaprosi/evydentia@23b1d32:LICENSE`. Se lee con `gh api repos/jucaprosi/evydentia/contents/LICENSE` o desde `C:/Users/Juan Carlos/respaldo-evydentia/LICENSE`. Su SHA-256 es `f814709c25412c5863eec4c284303f790c04b6063356907468f964b73ee3a7db` |
| `frontend/package.json` | `"license": "UNLICENSED"` |
| `scripts/poner_aviso_de_autor.py` (nuevo) | pone la línea de aviso donde falte (R2); con `--verificar`, solo informa |
| `scripts/verificar_alcance_pr.py` | admite el diff transversal de R5 |
| `tests/test_verificar_alcance_pr.py` | casos de R5 |
| `tests/test_leg06_aviso_de_autor.py` (nuevo) | casos de §5 |
| cada archivo de R1 | su línea de aviso (diff transversal, R5) |

Hecho medido en `origin/main` 788666d7:
- No hay `LICENSE`, y `frontend/package.json` no declara `license`.
- `git ls-files` da 1.737 archivos con las extensiones de R1: 1.094 `.py`, 366 `.ts`, 218 `.tsx`, 26 `.yaml`, 9 `.css`, 6 `.bat`, 4 `.mjs`, 4 `.go`, 3 `.yml`, 3 `.ps1`, 2 `.ini`, 1 `.sql` y 1 `.js`. Dos de los `.yml` están en `.github/workflows/`.
- Ningún archivo versionado con esas extensiones sale de un generador: el índice de tareas se escribe en `governance/artefactos/_generado/`, que git ignora.
- `verificar_alcance_pr.py` (CI-23 y CI-25) da «ALCANCE NO VÁLIDO» por cada archivo fuera de la propiedad. Sin la regla R5, este PR sería imposible.

## 2. API

`scripts/poner_aviso_de_autor.py [--verificar]`:
- recorre `git ls-files` con las extensiones de R1, salvo las exclusiones de R1;
- inserta la línea según R2 y es idempotente: una segunda pasada no cambia nada;
- con `--verificar` lista los archivos sin aviso y sale con código 1 si hay alguno.

La prueba de §5 importa estas funciones; no lleva otra lista de extensiones.

## 3. Reglas

- **R1 · Qué archivos.** Todo archivo versionado con extensión `.py .ts .tsx .js .jsx .mjs .cjs .go .sql .css .yaml .yml .toml .ini .sh .ps1 .bat`, salvo los de `.github/` y los JSON. Un archivo vacío también lleva el aviso.
- **R2 · Dónde y cómo.** El aviso es la primera línea de contenido, con el comentario del lenguaje:
  - `#` en `.py .yaml .yml .toml .sh .ps1`;
  - `;` en `.ini`;
  - `//` en `.ts .tsx .js .jsx .mjs .cjs .go`;
  - `/* … */` en `.css`;
  - `--` en `.sql`;
  - `REM` en `.bat`.

  Va después de lo que tiene que ir primero, en este orden: el BOM, el shebang `#!`, la línea `coding` de Python (PEP 263) y `@echo off`. En TypeScript va antes de `"use client"` y `"use server"`: las directivas admiten comentarios antes. El texto es exactamente «© 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.».
- **R3 · Archivos nuevos.** La prueba de §5 falla si un archivo de R1 no tiene el aviso, y su mensaje da la línea exacta que hay que pegar. El molde de cada lenguaje está en la función `linea_de_aviso(extension)` del script.
- **R4 · Generadores.** Un generador que escriba un archivo versionado de R1 emite el aviso. Hoy no hay ninguno (§1).
- **R5 · Alcance transversal.** La ficha declara `transversal = "aviso-de-autor"`. Para ella, `verificar_alcance_pr.py` admite un archivo fuera de la propiedad solo si su diff contra la base:
  - (a) añade exactamente una línea igual a `linea_de_aviso` de su extensión;
  - (b) no borra ni modifica ninguna otra línea;
  - (c) la deja en la posición de R2.

  Si falla una de las tres, da rojo con el nombre del archivo. Ninguna otra ficha puede declarar `transversal`.
- **R6 · Sin choques.** El PR se lanza cuando no hay otra ficha en `en_curso`. `verificar_alcance_pr.py` lo comprueba en la base del PR y da rojo si hay alguna. El Tech Lead lo pone como último bloque de una tanda.
- **R-ADPA · Ortogonalidad ZERAG (`LEG-06`).** Los archivos de la propiedad y la línea de R5 en los demás. Sin `import yaml`.

## 4. Interfaz

No aplica: el aviso va en el código fuente y no se muestra en pantalla.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** `git ls-files` con las extensiones de R1, **entonces** todos llevan el aviso en la posición de R2. Mutación m1: quitarlo de un archivo da rojo con la línea que hay que pegar. | `test_todo_archivo_de_codigo_lleva_el_aviso` |
| **Dado** archivos sintéticos con BOM, shebang, línea `coding`, `@echo off`, `"use client"` y un archivo vacío, **entonces** el script deja el aviso en su sitio y una segunda pasada no cambia nada. Mutación m2: poner el aviso antes del shebang da rojo. | `test_posicion_y_idempotencia` |
| **Dado** `LICENSE`, **entonces** existe y su contenido es igual al del respaldo, comparado por hash: SHA-256 `f814709c25412c5863eec4c284303f790c04b6063356907468f964b73ee3a7db`. `frontend/package.json` lleva `"license": "UNLICENSED"`. Mutación m3: quitar el campo da rojo. | `test_licencia_y_package_json` |
| **Dado** un diff transversal sintético que añade el aviso, **entonces** el alcance da verde. Con una línea más cambiada en el mismo archivo da rojo. Mutación m4: quitar la condición (b) da verde y la prueba lo detecta. | `tests/test_verificar_alcance_pr.py::test_leg06_transversal` |
| **Dado** otra ficha en `en_curso` en la base, **entonces** el alcance de LEG-06 da rojo. Mutación m5: quitar R6 da verde y la prueba lo detecta. | `tests/test_verificar_alcance_pr.py::test_leg06_sin_fichas_en_curso` |

Además: `python -m compileall -q .`, `npx tsc --noEmit` y `npm run lint` en `frontend/`, y el arnés completo, todos en verde.

## 6. Trazabilidad

- Ficha: `governance/tareas/LEG-06.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Pedido del CTO (2026-11-22), aprobado por el propietario. Referencia: el mismo cambio en el respaldo `jucaprosi/evydentia`, con 1.645 archivos.
- Depende de las fichas hechas que comparten archivos de la propiedad: CI-19, CI-22, CI-23, CI-25, CI-26, CI-29, CI-31, CI-36, GCP-07, PRD-01, PRD-03, QA-11, RET-05, RET-09.
