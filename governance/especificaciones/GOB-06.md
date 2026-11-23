# GOB-06 · Briefs y partes de relevo fuera del repositorio
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `scripts/verificar_reparto.py` | R3 y R4 calculados con las fichas (`tanda`, `propiedad`, `depende_de`); `--tandas` lee el campo `tanda` |
| `scripts/verificar_alcance_pr.py` | sin `PORTADA` ni el brief como archivo de cierre |
| `scripts/generar_indice_tareas.py` | `tanda` opcional (entero ≥ 1) en la cabecera; sin el campo `agente` ni `AGENTES` |
| `scripts/verificar_briefs_locales.py` (nuevo) | R5 |
| `tests/test_reparto.py` | casos de R3 y R4 con fichas sintéticas |
| `tests/test_ci29_sin_generados_compartidos.py` | sin los casos de briefs |
| `tests/test_verificar_alcance_pr.py` | sin los casos de briefs |
| `tests/test_indice_tareas.py` | casos de `tanda` y del campo `agente` retirado |
| `tests/test_verificar_briefs_locales.py` (nuevo) | casos de R5 con una carpeta temporal |
| `governance/apoyo/BRIEFS_POR_BLOQUE.md` | se borra |
| `governance/apoyo/BRIEFS_TAREAS_LIBRES.md` | se borra |
| `governance/apoyo/briefs/FE-29.md` | se borra |
| `governance/apoyo/briefs/IA-13.md` | se borra |
| `governance/apoyo/briefs/IA-14.md` | se borra |
| `governance/apoyo/briefs/IA-15.md` | se borra |
| `governance/apoyo/briefs/IA-16.md` | se borra |
| `scripts/migrar_reparto_ci31.py` | se borra |
| `tests/test_ci31_reparto_por_ficha.py` | se borra |
| `tests/test_reparto_copias.py` | se borra |
| `governance/tareas/FE-29.md` | `tanda = 93` en la cabecera |
| `governance/tareas/IA-13.md` | `tanda = 94` en la cabecera |
| `governance/tareas/IA-14.md` | `tanda = 95` en la cabecera |
| `governance/tareas/IA-15.md` | `tanda = 95` en la cabecera |
| `governance/tareas/IA-16.md` | `tanda = 96` en la cabecera |
| `governance/tareas/LEG-07.md` | `tanda` si sigue sin hacer y el Tech Lead le asignó una (R6); ya no tiene `agente` |
| `governance/tareas/GCP-08c.md` | sin `agente`; `tanda = 95`, posterior a la de GCP-08b (R6) |
| `governance/METODOLOGIAS.md` | remite a la carpeta local de R1 en lugar de a los briefs del repositorio |
| `governance/Metodología de trabajo en equipo.md` | remite a la carpeta local de R1 en lugar de a los briefs del repositorio |
| `governance/apoyo/DISENO_PORTALES_EXTERNOS.md` | remite a la carpeta local de R1 en lugar de a los briefs del repositorio |
| `governance/operaciones/CONFIGURACION_LOGIN_GOOGLE.md` | remite a la carpeta local de R1 en lugar de a los briefs del repositorio |
| `governance/apoyo/LANZAMIENTO_TANDA_ORTOGONAL.md` | remite a la carpeta local de R1 en lugar de a los briefs del repositorio |
| `governance/apoyo/LANZAMIENTO_TANDA_SECUENCIAL.md` | remite a la carpeta local de R1 en lugar de a los briefs del repositorio |
| `governance/partes/README.md` | una línea: los partes nuevos van a `relevos\<rol>\` de R1; los existentes se quedan como registro fechado |

Hecho medido en `origin/main` aa900e0d con `git grep -l -E "apoyo/briefs|BRIEFS_TAREAS_LIBRES|BRIEFS_POR_BLOQUE"`:
- **Código y pruebas:** `verificar_reparto.py`, `verificar_alcance_pr.py`, `migrar_reparto_ci31.py`, `test_ci29_sin_generados_compartidos.py`, `test_ci31_reparto_por_ficha.py`, `test_reparto.py` y `test_verificar_alcance_pr.py`. `test_reparto_copias.py` importa `verificar_reparto` y comprueba las copias de los briefs.
- **El campo `agente`:** lo define `generar_indice_tareas.py` (`AGENTES`, `Tarea.agente`) y en `origin/main` 5d4aa36d solo lo usan `GCP-08c.md` y la propia `GOB-06.md`; `LEG-07.md` lo quitó al cerrarse (#971).
- **Dónde vive hoy la tanda:** solo en la cabecera de cada brief, `### <ID> · título (tanda N)`. Sin briefs en el repositorio, hace falta un campo en la ficha.
- **Briefs vivos:** `governance/apoyo/briefs/` tiene FE-29 e IA-13 a IA-16, en las tandas 93 a 96.
- **Documentos vivos que remiten a los briefs:** los seis de la tabla.
- **Fuera de alcance**, por ser registros fechados de trabajo cerrado que ningún árbitro lee: las 22 fichas y especificaciones hechas que nombran los briefs, los 20 partes existentes de `governance/partes/` y `APORTES_INEDITOS.md`. El CTO lo confirmó el 2026-11-23. Los `BRIEF_PROPIETARIO_*.md` son pasos del propietario, no briefs de agente, y se quedan.
- `.github/workflows/` solo llama a `verificar_alcance_pr.py` con `--rama --base --cabeza`, y esa interfaz no cambia.

## 2. API

- `python scripts/verificar_reparto.py [--tandas]`: código 1 con hallazgos de R3 o R4.
- `python scripts/verificar_briefs_locales.py --tanda N [--carpeta RUTA]`: la carpeta por defecto es la de R1. Sale con código 1 si falta algún brief de la tanda o no coincide con su ficha. No va en el CI.

## 3. Reglas

- **R1 · Carpeta local.** `C:\Users\Juan Carlos\compartido\evydentia\` está fuera de todo worktree y sin git:
  - `briefs\<ID>.md`, uno por ficha;
  - `relevos\<rol>\AAAA-MM-DD_<tema>.md`, para los partes de sesión de cada rol, que antes iban a `governance/partes/<rol>/`;
  - `TAREAS_LIBRES.md`, que sustituye a la hoja del CTO.

  La escribe el Tech Lead, salvo `TAREAS_LIBRES.md`, que es del CTO.
- **R2 · Tanda en la ficha.** `tanda = N` es opcional y solo lo lleva una ficha no hecha que ya está planificada. Lo pone el Tech Lead en un PR de gobernanza.
- **R3 · Ortogonalidad en el CI.** Dos fichas no hechas con la misma `tanda` no comparten ningún archivo de su `propiedad`, salvo secciones reservadas distintas. Es la R3 de hoy, calculada con las fichas.
- **R4 · Orden en el CI.** Cada `depende_de` de una ficha con `tanda` está hecha o tiene una `tanda` menor.
- **R5 · Briefs locales.** `verificar_briefs_locales.py --tanda N` comprueba cada ficha no hecha con `tanda = N`:
  - existe `briefs\<ID>.md` y su cabecera dice `(tanda N)`;
  - su «Escribe» es igual a la `propiedad` de la ficha;
  - su «Hecho si» es igual al `arbitro` de la ficha.

  El Tech Lead lo corre antes de lanzar la tanda, y una ficha sin brief no se lanza.
- **R6 · Ningún brief en el repositorio.** Decisión del propietario, 2026-11-23: ni los briefs ni los archivos de briefs se versionan.
  - El CTO ya copió a la carpeta de R1 los briefs vivos (FE-29 e IA-13 a IA-16, más LEG-07 del Tech Lead) y la hoja. GOB-06 no copia ni sobrescribe nada.
  - Antes de borrar, el ingeniero compara el SHA-256 de cada `governance/apoyo/briefs/<ID>.md` y de `BRIEFS_TAREAS_LIBRES.md` con su copia en la carpeta (`briefs\<ID>.md` y `TAREAS_LIBRES.md`), y pega la tabla en el PR. Si alguno difiere, no borra y avisa al CTO.
  - Pone `tanda` en las fichas de §1 que sigan sin hacer al lanzar GOB-06; una ficha hecha no lleva `tanda` (R2). Quita `agente` de GCP-08c y de la propia GOB-06, que es su archivo de cierre.
  - Corre R5 para las tandas 93 a 96 contra la carpeta real y pega la salida en el PR.
  - Hasta que se fusione GOB-06, toda ficha nueva entra con `agente = "ninguno"` y su brief va solo a la carpeta.
- **R6b · Partes de sesión.** Desde GOB-06 no se versiona ningún parte nuevo: van a `relevos\<rol>\` de R1. Si un parte contiene una decisión de diseño que debe vincular, la decisión va a la especificación que corresponda. Es una indicación en `governance/partes/README.md`, no un árbitro.
- **R7 · Sin choques.** GOB-06 se lanza cuando ninguna ficha cuya cabecera edita (FE-29, IA-13 a IA-16, LEG-07 y GCP-08c) está en `en_curso`.
- **R8 · Riesgos asumidos.**
  - La carpeta no tiene historial: un brief sobrescrito se pierde. El Tech Lead no sobrescribe; añade una versión `<ID>.v2.md` y deja la anterior.
  - Una sesión en la nube, o Aleczandra y José en su equipo, no ven la carpeta. A ellos se les pega el brief en el chat.
  - Si se borra la carpeta, se pierden los briefs pendientes. Las fichas y especificaciones del repositorio bastan para reescribirlos.
- **R-ADPA · Ortogonalidad ZERAG (`GOB-06`).** Solo los archivos de la propiedad. Sin `import yaml`.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** dos fichas sintéticas con la misma `tanda` que comparten un archivo, **entonces** `verificar_reparto` da un hallazgo R3; con secciones distintas, o con tandas distintas, no da ninguno. Mutación m1: no mirar la `tanda` da rojo. | `tests/test_reparto.py::test_r3_misma_tanda_no_se_pisa` |
| **Dado** una ficha con `tanda = 2` que depende de otra pendiente con `tanda = 3`, **entonces** hay un hallazgo R4; con la dependencia hecha o en la tanda 1, no hay ninguno. Mutación m2: aceptar una tanda igual da rojo. | `tests/test_reparto.py::test_r4_dependencia_antes` |
| **Dado** el árbol real, **entonces** `verificar_reparto` da código 0 y `--tandas` lista 93 a 96 con las fichas de R6. | `tests/test_reparto.py::test_el_reparto_real_es_valido` |
| **Dado** una carpeta temporal con un brief con «Hecho si» distinto del `arbitro`, otro que falta y otro correcto, **entonces** R5 da exactamente los dos hallazgos. Mutación m3: no comparar «Escribe» con `propiedad` da rojo. | `tests/test_verificar_briefs_locales.py` |
| **Dado** una ficha con `agente`, o con una `tanda` que no es un entero positivo, **entonces** el índice da error. Mutación m4: aceptar `tanda = 0` da rojo. | `tests/test_indice_tareas.py` |
| **Dado** un PR que añade `governance/apoyo/briefs/X.md`, **entonces** `verificar_alcance_pr` lo trata como cualquier archivo sin dueña. Mutación m5: volver a admitirlo como archivo de cierre da rojo. | `tests/test_verificar_alcance_pr.py` |

## 6. Trazabilidad

- Ficha: `governance/tareas/GOB-06.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Pedido del CTO, aprobado por el propietario el 2026-11-23.
- Depende de las fichas hechas que comparten archivos de la propiedad: ADPA-10, BIB-105, CI-19, CI-22, CI-23, CI-25, CI-26, CI-29, CI-31, CI-33, CI-34, CI-35, GOB-02, GOB-03, GOB-05, LEG-06, MARCA-06, OPS-05, PRD-01, QA-11, REP-01, RET-09, SEC-02, SEC-12.
