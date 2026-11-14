# RET-00 · Árbitro de plataforma única: `main` solo depende de Google Cloud
`¤sdd` `¤arbitro` `¤seguridad`

Corrección del CTO (2026-11-13): este árbitro **no busca nombres**. Comprueba la estructura: de qué paquetes depende `main`, de dónde saca su configuración, cómo se despliega y con qué servicios externos habla. Sustituye al árbitro vigente de menciones.

> **Convención transitoria.** «El árbitro vigente» es la prueba de menciones que hoy corre en cada fusión, y «BG» su serie de fichas (BG-00 a BG-04). Este documento no escribe el nombre que ese árbitro vigila porque todavía no admite menciones nuevas. La convención desaparece con RET-07 y no se copia a ninguna ficha.

## 1. Datos

Sin tablas ni migraciones. Los datos son cuatro catálogos cerrados y una carpeta de pendientes, en `tests/plataforma_unica/`:

- `dependencias.txt`: todos los paquetes que `requirements.txt` y `frontend/package.json` pueden declarar. Una dependencia nueva exige una línea nueva aquí, con su motivo.
- `servicios_externos.txt`: los dominios a los que el código y la política de contenido (`frontend/next.config.ts`) pueden apuntar. Hoy: los de Google Cloud, los propios de EVYDENTIA y los sitios oficiales que el producto consulta (por ejemplo, el de la autoridad de protección de datos).
- `variables.txt`: todas las variables de entorno que el código puede leer. Coincide con las que documenta `governance/operaciones/ENTORNO_LOCAL.md`.
- `despliegue.txt`: los archivos de despliegue y de configuración de plataforma que pueden existir en el árbol (`Dockerfile`, los manifiestos de `governance/operaciones/entornos/**` y los que el propietario mantiene en `.github/workflows/`), y la única entrada de la API, `main:app`.
- `pendientes/<ficha>.txt`: lo que hoy incumple un catálogo y qué ficha lo retira (`RET-01`, `RET-02`, `RET-03`, `RET-05`, `RET-06`, `IA-04`, `IA-06`, `IA-08`). Formato `regla|archivo|elemento`.

No hay lista de términos ni lista blanca de documentos: el árbitro no lee `governance/` ni comentarios.

## 2. API

No aplica: no hay rutas HTTP.

## 3. Reglas

- **R1 · Dependencias.** Todo paquete declarado en `requirements.txt` o en `frontend/package.json` está en `dependencias.txt`. Todo módulo de terceros que importa el código de producto (analizado por AST en `app_core/`, `features/`, `api/`, `jobs/`, `scripts/`, `main.py` y `alembic/env.py`) pertenece a un paquete declarado.
- **R2 · Configuración solo por el proceso.** El código lee su configuración de variables del proceso o de Secret Manager. El análisis por AST comprueba dos cosas:
  - toda variable leída (`os.environ`, `os.getenv` o un campo de la clase de configuración) está en `variables.txt`;
  - ninguna clase de configuración declara un archivo de entorno ni se abre un archivo de configuración local para leer credenciales.
- **R3 · Servicios externos.** Todo dominio escrito en una URL del código de producto, en la política de contenido del frontend o en un manifiesto está en `servicios_externos.txt`.
- **R4 · Despliegue.** No existe ningún archivo de despliegue o de plataforma fuera de `despliegue.txt`, y ningún módulo ni prueba importa otra entrada de la API que `main`.
- **R5 · Una sola guardia de base en las pruebas.** Un archivo de `tests/` que usa la base llama a `exigir_base_de_pruebas()` de `tests/conftest.py` y no compara por su cuenta el host de la base con un literal. Se comprueba por AST.
- **R6 · Los catálogos crecen a la vista.** Una línea nueva en cualquier catálogo solo entra con su motivo, y el PR que la añade no puede ser de una ficha `RET-`. El árbitro compara con `origin/main` y lo exige.
- **R7 · Los pendientes solo decrecen.** Ningún `pendientes/*.txt` gana entradas contra `origin/main`, salvo en el PR que crea el árbitro. Un pendiente cuyo incumplimiento ya no existe se retira en el mismo PR. Un pendiente a nombre de una ficha `hecha` es un error.
- **R8 · No toca código de producto.** Esta ficha crea el árbitro, sus catálogos y sus pendientes. No retira nada.
- **R9 · Convive con el árbitro vigente** hasta RET-07. Ese árbitro está entre los mínimos de cada fusión: RET-07 solo lo retira cuando este ya está en `main` y en esa lista.
- **R-ADPA · Ortogonalidad ZERAG (`RET-00`).** El árbitro no importa de ninguna sala; lee el árbol.

## 4. Interfaz

No aplica: no hay pantalla. Un fallo dice la regla, el archivo y el elemento (el paquete, la variable, el dominio o el archivo de despliegue), y qué catálogo habría que ampliar si el cambio es legítimo.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el árbol de `main`, **cuando** corre el árbitro, **entonces** todo incumplimiento está en los pendientes de una ficha abierta. | `test_plataforma_unica_sin_incumplimientos_nuevos` |
| **Dado** un paquete nuevo en `requirements.txt` que no está en `dependencias.txt`, **entonces** rojo con el paquete. Mutación: añadir un cliente de otro proveedor de nube hace fallar la prueba. | `test_dependencia_no_catalogada` |
| **Dado** un módulo que importa un paquete no declarado, **entonces** rojo con el archivo y el módulo. | `test_import_sin_dependencia_declarada` |
| **Dado** una clase de configuración que declara un archivo de entorno, o una variable leída que no está en `variables.txt`, **entonces** rojo. Mutación: volver a leer un archivo de entorno hace fallar la prueba. | `test_configuracion_solo_del_proceso` |
| **Dado** una URL del código o de la política de contenido con un dominio fuera de `servicios_externos.txt`, **entonces** rojo con el dominio. Mutación: permitir en la política de contenido un almacén de otro proveedor hace fallar la prueba. | `test_servicio_externo_no_catalogado` |
| **Dado** un archivo de despliegue fuera de `despliegue.txt`, o una prueba que importa otra entrada de la API, **entonces** rojo. | `test_despliegue_unico` |
| **Dado** una prueba que compara el host de la base con un literal en vez de llamar a la guardia común, **entonces** rojo. | `test_guardia_de_base_unica` |
| **Dado** una línea nueva en un catálogo dentro de un PR de una ficha `RET-`, o un pendiente que crece, **entonces** rojo. Mutación: aceptar la línea hace fallar la prueba. | `test_catalogos_y_pendientes_cerrados` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-00.md`.
- Programa: `governance/apoyo/RETIRO_PLATAFORMAS_PMV.md`, decisiones del propietario y corrección del CTO del 2026-11-13. RET-07 borra ese documento al cerrar.
- Especificación de referencia: `governance/especificaciones/README.md`.
- Sustituye al árbitro vigente (BG-00). Absorbe BG-02, cuyo trabajo pasa a RET-06.
- `.github/workflows/` y `verificadores/` son del propietario: si la lista de árbitros mínimos vive ahí, va un brief.
- Consecuencia que el CTO debe conocer: tras RET-07 **ningún árbitro permanente busca nombres** en documentos. Que los documentos no nombren lo retirado se comprueba una vez, en el PR de RET-07.
