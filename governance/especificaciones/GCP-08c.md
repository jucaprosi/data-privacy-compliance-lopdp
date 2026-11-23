# GCP-08c · Datos de ICU completos en la imagen web para formatear en es-EC
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `frontend/Dockerfile.cloudrun` | el runner trae datos de ICU completos, con la opción que elija R2 |
| `tests/test_gcp08_proxy_e_imagen.py` | `test_08_intl_es_ec_en_la_imagen` (nuevo) y `PRESUPUESTO_BYTES` recalculado según R3 |
| `tests/test_ci36_version_node.py` | con (b), `test_runner_alpine_trae_la_misma_version` describe el runner elegido (R2b); con (a), no cambia |
| `tests/test_gcp03_frontend_cloudrun.py` | con (b), `test_dockerfile_multistage_non_root` describe el runner elegido (R2b); con (a), no cambia |

**Medida del Arquitecto**, el 2026-11-23, en `alpine:3.21` con `apk add nodejs` (el mismo runner de main), formateando el 2026-11-23 y 1.234.567,891 USD:

| Datos de ICU | Fecha `es-EC` (`dateStyle: "full"`) | Número `es-EC` | `resolvedOptions().locale` |
| :--- | :--- | :--- | :--- |
| `icu-data-en`, el de hoy (2.733 KiB) | «Monday, November 23, 2026» | «$1,234,567.89» | `en-US` |
| `icu-data-full` (29 MiB) | «lunes, 23 de noviembre de 2026» | «$1.234.567,89» | — |

- **El defecto se reproduce.** Sin los datos completos, Node cae a `en-US` en silencio.
- **Dónde importa.** Next también renderiza en el servidor los componentes `"use client"`. Los 45 archivos de `frontend/src` que usan `Intl` o `toLocale*` pintan en el servidor en inglés y en el navegador en español, lo que da un desajuste de hidratación.
- **Tamaño.** `icu-data-full` añade unos 26 MiB netos y deja la imagen por encima del presupuesto de 138 MB de GCP-08b.

## 2. API

No aplica.

## 3. Reglas

- **R1 · Comprobación en físico primero.** El ingeniero repite la medida de §1 con la imagen real de `frontend/Dockerfile.cloudrun` y pega la salida en el PR. Si sale en español sin cambios, la ficha se cierra sin tocar nada.
- **R2 · Opción más ligera que formatee bien.** El ingeniero construye y mide dos variantes del runner, y se queda con la que pese menos y pase `test_08`:
  - (a) `apk add --no-cache nodejs icu-data-full`, sustituyendo a `icu-data-en`;
  - (b) un runner sobre `node:22-alpine`, cuyo binario oficial lleva ICU completa, con el mismo usuario `nextjs` y el mismo `CMD`.

  Anota en §1 del PR la tabla con los bytes de las dos.
- **R2b · Pruebas del runner, solo si se elige (b).** Hoy dos pruebas fijan el runner de (a):
  - `tests/test_ci36_version_node.py:125-135` exige `alias == "runner"`, una base `alpine:` y el Node de apk de esa rama;
  - `tests/test_gcp03_frontend_cloudrun.py:160-163` exige `runner.base == "alpine:3.21"` y `apk add … nodejs`.

  Con (b) describen el estado final y no aceptan las dos formas:
  - la primera exige `node:<esperada>-alpine` como base del runner, con la misma versión mayor que `engines` (CI-36), y el caso sintético rechaza una base `node:` de otra versión mayor;
  - la segunda exige esa base, sin `apk add nodejs`, y mantiene el usuario `nextjs` no root.

  Con (a), ninguna de las dos cambia.
- **R3 · Presupuesto nuevo.** Aplica GCP-08b R2: la medida de la opción elegida + 15 %, redondeada a MB, en `PRESUPUESTO_BYTES`, con la tabla de capas en el PR.
- **R4 · Orden.** Depende de GCP-08b y va en una tanda posterior, porque las dos son dueñas de `tests/test_gcp08_proxy_e_imagen.py`. Con FE-29 no choca.
- **R-ADPA · Ortogonalidad ZERAG (`GCP-08c`).** Solo los cuatro archivos. Sin `import yaml`.

## 4. Interfaz

No cambia ningún texto. La fecha y los números que hoy se pintan en el servidor pasan a salir en español, igual que en el navegador.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** la imagen construida, **entonces** `node -e` con `Intl.DateTimeFormat("es-EC", {dateStyle: "full", timeZone: "UTC"})` da «lunes, 23 de noviembre de 2026» y `Intl.NumberFormat("es-EC", {style: "currency", currency: "USD"})` da «$1.234.567,89». Mutación m1: volver a `icu-data-en` da rojo. | `tests/test_gcp08_proxy_e_imagen.py::test_08_intl_es_ec_en_la_imagen` |
| **Dado** la imagen construida, **entonces** cabe en el `PRESUPUESTO_BYTES` nuevo. | `tests/test_gcp08_proxy_e_imagen.py::test_05_la_imagen_cabe_en_su_presupuesto` |
| **Dado** el runner elegido, **entonces** las dos pruebas de R2b lo describen; con (b), un runner `node:` de otra versión mayor da rojo. Mutación m2: dejar `alpine:3.21` en la prueba con un runner (b) da rojo. | `tests/test_ci36_version_node.py::test_runner_alpine_trae_la_misma_version`, `tests/test_gcp03_frontend_cloudrun.py::test_dockerfile_multistage_non_root` |

## 6. Trazabilidad

- Ficha: `governance/tareas/GCP-08c.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Hallazgo del Arquitecto al medir GCP-08b, aceptado por el CTO (2026-11-23).
- Depende de GCP-08b, por el presupuesto y la prueba, y de las fichas hechas que comparten estos archivos: CI-36, GCP-03, GCP-03b, GCP-08, QA-12 y RET-05.
