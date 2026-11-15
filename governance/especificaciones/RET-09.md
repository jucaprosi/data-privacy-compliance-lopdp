# RET-09 · Documentación y artefactos vivos
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. La lista exacta de archivos es la `propiedad` de la ficha, medida en `origin/main`.

| Grupo | Estado final |
| :--- | :--- |
| documentos auxiliares depurados del ciclo previo fuera del stack activo de Google Cloud | fuera del árbol vivo |
| guías de operaciones, arquitectura y apoyo, fichas, briefs y especificaciones con menciones sueltas | se reescriben en términos de Google Cloud y del PostgreSQL 16 local; `PRUEBAS_EN_FISICO.md` §6 corre contra el PostgreSQL local |
| `APORTES_INEDITOS.md`, `FUENTES_Y_BIBLIOGRAFIA.md`, `data/CANDIDATOS_VPA.json` | se retira el aporte, la fuente o el candidato cuyo contenido es solo la plataforma; se reescribe en términos neutros el que enseña algo general |
| `governance/operaciones/entornos/pruebas/secretos.yaml` | solo los secretos de Google Cloud |
| fichas hechas que existían solo para una plataforma (la serie de la base anterior y las que solo la migraban) | se borran con su brief y su especificación |
| `governance/partes/` | registro fechado: no se toca |
| `governance/artefactos/data/` salvo `CANDIDATOS_VPA.json` | material del propietario: no se toca |

## 2. API

`governance/contratos/hoja_de_ruta.openapi.json` se reescribe solo en sus descripciones. Las rutas, los esquemas y los nombres de campo no cambian; los que cambian, cambian con la migración de RET-02.

## 3. Reglas

- **R1 · Borrado completo.** Lo que §1 manda borrar se borra entero. No queda un archivo índice, una lista ni una prueba que compruebe que se borró.
- **R2 · Reescritura en positivo.** El texto reescrito describe el estado final. No usa «ya no», «antes», «se retiró» ni un término de sustitución para la plataforma anterior.
- **R3 · Doctrina intacta.** En los `.md` y `.yaml` no cambian los encabezados normativos, los tokens, los roles ni los candados.
- **R4 · Números estables.** Los números de aporte o de fuente que se retiran no se reutilizan.
- **R5 · Fichas retiradas.** En el mismo PR:
  1. se quitan sus ids del `depende_de` de cada ficha que las cita (`CI-24`, `CI-28`, `CI-29`, `IA-08`, `RET-01`, `RET-05`, `RET-06`, `QA-10` y las demás que aparezcan);
  2. se borran la ficha, su brief en `governance/apoyo/briefs/` y su especificación;
  3. se corren `generar_indice_tareas.py --verificar` y `verificar_reparto.py`; una ficha que queda sin dependencias pasa a `depende_de = []`.
- **R6 · Exclusiones por choque.** Los archivos que posee otra ficha abierta quedan fuera de RET-09 y los limpia esa ficha al cerrarse, con la misma regla R2:
  - `tests/test_demo_purga.py`: DEMO-05;
  - los archivos de organización: ORG-17b y ORG-20;
  - los archivos de ADPA-12 y de CI-30.

  El Tech Lead anota la lista exacta en la ficha RET-09. Cada ficha dueña la recoge en su propio PR, y RET-09 no espera a ninguna de ellas.
- **R7 · TASKS.** `governance/artefactos/TASKS.md` lo actualiza el Tech Lead al fusionar cada ficha del programa.
- **R-ADPA · Ortogonalidad ZERAG (`RET-09`).** Solo los archivos de su `propiedad`. `verificadores/` y `.github/` son del propietario (`governance/operaciones/BRIEF_PROPIETARIO_RET_ARNESES_Y_CI.md`).

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** las fichas retiradas, **entonces** ninguna ficha las cita en `depende_de`, y el índice y el reparto pasan. | `tests/test_indice_tareas.py`, `tests/test_reparto.py`, `generar_indice_tareas.py --verificar` y `verificar_reparto.py` |
| **Dado** cada especificación reescrita, **entonces** conserva sus seis apartados y sus escenarios. | `tests/test_verificar_especificaciones.py` y `scripts/verificar_especificaciones.py` |
| **Dado** un `.md` o `.yaml` reescrito, **entonces** sus encabezados, tokens, roles y candados no cambian. | revisión del PR (R3) |
| **Dado** el árbol con la ficha fusionada, **entonces** la suite completa pasa. | la suite existente |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-09.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Mapa del programa: `governance/partes/arquitecto/2026-11-14_COBERTURA_PLATAFORMA_UNICA.md`, §2.
- Orden: va al final del programa, porque sus fichas y briefs citan las anteriores.
