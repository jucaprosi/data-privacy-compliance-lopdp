# GCP-08c · Datos de ICU completos en la imagen web para formatear en es-EC
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `frontend/Dockerfile.cloudrun` | el runner trae datos de ICU completos, con la opción que elija R2 |
| `tests/test_gcp08_proxy_e_imagen.py` | `test_08_intl_es_ec_en_la_imagen` (nuevo) y `PRESUPUESTO_BYTES` recalculado según R3 |

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
- **R3 · Presupuesto nuevo.** Aplica GCP-08b R2: la medida de la opción elegida + 15 %, redondeada a MB, en `PRESUPUESTO_BYTES`, con la tabla de capas en el PR.
- **R-ADPA · Ortogonalidad ZERAG (`GCP-08c`).** Solo los dos archivos. Sin `import yaml`.

## 4. Interfaz

No cambia ningún texto. La fecha y los números que hoy se pintan en el servidor pasan a salir en español, igual que en el navegador.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** la imagen construida, **entonces** `node -e` con `Intl.DateTimeFormat("es-EC", {dateStyle: "full", timeZone: "UTC"})` da «lunes, 23 de noviembre de 2026» y `Intl.NumberFormat("es-EC", {style: "currency", currency: "USD"})` da «$1.234.567,89». Mutación m1: volver a `icu-data-en` da rojo. | `tests/test_gcp08_proxy_e_imagen.py::test_08_intl_es_ec_en_la_imagen` |
| **Dado** la imagen construida, **entonces** cabe en el `PRESUPUESTO_BYTES` nuevo. | `tests/test_gcp08_proxy_e_imagen.py::test_05_la_imagen_cabe_en_su_presupuesto` |

## 6. Trazabilidad

- Ficha: `governance/tareas/GCP-08c.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Hallazgo del Arquitecto al medir GCP-08b, aceptado por el CTO (2026-11-23).
- Depende de GCP-08b, por el presupuesto y la prueba, y de las fichas hechas que comparten estos archivos: CI-36, GCP-03, GCP-03b, GCP-08 y QA-12.
