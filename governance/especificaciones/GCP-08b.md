# GCP-08b · Presupuesto de tamaño de la imagen web
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `tests/test_gcp08_proxy_e_imagen.py` | `PRESUPUESTO_BYTES = 138 * 1000 * 1000`, con un comentario que remite a esta §1; la prueba se llama `test_05_la_imagen_cabe_en_su_presupuesto` |

**Medida del Arquitecto en `origin/main` cec069b0**, el 2026-11-23, con `docker build -f frontend/Dockerfile.cloudrun` y `docker history --human=false`:

| Capa | Bytes |
| :--- | ---: |
| `apk add nodejs` (binario de Node 22 de 49 MiB, `icu-libs` y `icu-data-en`) | 68.591.616 |
| `.next/standalone` (`node_modules/next` ocupa 30 MB) | 39.661.568 |
| `alpine-minirootfs` 3.21 | 8.462.336 |
| `.next/static` | 3.186.688 |
| `public` y `WORKDIR` | 81.920 |
| **Total** | **119.984.128** |

- El total coincide al byte con el que midió el ingeniero de FE-29 en el CI del #972.
- **No hay recorte barato y seguro.**
  - No hay mapas de fuente: `find /app -name "*.map"` da 0.
  - La caché de npm no llega al runner, que solo copia `standalone`, `static` y `public`.
  - Lo que queda es el propio Node (el 57 %) y lo que Next traza para `standalone`. Recortar `node_modules/next` a mano, por ejemplo `dist/compiled/amphtml-validator` (4 MB), rompe con cualquier actualización de Next.
  - Por eso `frontend/Dockerfile.cloudrun` no cambia.
- **Presupuesto:** 119.984.128 × 1,15 = 137.981.747 bytes, que redondeado a MB da 138 MB (`138 * 1000 * 1000`).

## 2. API

No aplica.

## 3. Reglas

- **R1 · Una sola fuente.** El presupuesto vive solo en `PRESUPUESTO_BYTES` de la prueba. El mensaje de fallo da la medida y el presupuesto en MB.
- **R2 · Cambiar el presupuesto.** Subirlo exige una ficha nueva que mida de nuevo por capas y lo anote en su §1, con la misma regla: medida + 15 %, redondeado a MB.
- **R-ADPA · Ortogonalidad ZERAG (`GCP-08b`).** Solo la prueba. Sin `import yaml`.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** la imagen de main, **entonces** la suma de `docker history` es mayor que 0 y menor que `PRESUPUESTO_BYTES`. | `tests/test_gcp08_proxy_e_imagen.py::test_05_la_imagen_cabe_en_su_presupuesto` |
| **Dado** una imagen que supera el presupuesto, **entonces** la prueba da rojo, con la medida y el presupuesto en el mensaje. Mutación m1: comparar con un presupuesto de 1 MB da rojo. | `tests/test_gcp08_proxy_e_imagen.py::test_05_la_imagen_cabe_en_su_presupuesto` |

## 6. Trazabilidad

- Ficha: `governance/tareas/GCP-08b.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Pedido del CTO (2026-11-23), por el rojo de `test_05` en el CI del #972 (job 137470893838).
- Depende de las fichas hechas que comparten la prueba: CI-36, GCP-08 y QA-12.
