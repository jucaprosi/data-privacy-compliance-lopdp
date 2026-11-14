# ARQ-01 · Registro de decisiones de arquitectura
`¤sdd` `¤arbitro` `¤adpa`

## 1. Datos

Sin tablas ni migraciones. Una carpeta de documentos y una prueba:

- `governance/arquitectura/decisiones/ADR-NNN.md`: un archivo por decisión, numerado desde `ADR-001` sin huecos.
- Cabecera obligatoria de cada ADR, en una tabla de dos columnas al inicio:

  | Campo | Valores |
  | :--- | :--- |
  | `estado` | `vigente` o `sustituida por ADR-NNN` |
  | `decidido_por` | `propietario`, `CTO` o `Arquitecto` |
  | `fecha` | AAAA-MM-DD |
  | `especificaciones` | lista de rutas a `governance/especificaciones/*.md`, o `ninguna` |

- Cuerpo obligatorio: tres encabezados `## Contexto`, `## Decisión` y `## Consecuencias`.

## 2. API

No aplica: no hay rutas ni código de producto.

## 3. Reglas

- **R1 · Precedencia sin cambios (decisión del CTO, 2026-11-13).** El orden sigue siendo INVARIANTS > PRD > especificación > ficha > código. Un ADR documenta y enlaza, pero no manda sobre la especificación. Si un ADR contradice una especificación, la especificación se corrige en el mismo PR. No queda ninguna contradicción abierta.
- **R2 · Sin duplicar.** Una especificación o un parte que cita una decisión enlaza su ADR y no vuelve a escribir la decisión. El ADR es el único lugar donde está el razonamiento.
- **R3 · Quién decide.** `decidido_por` dice quién tomó la decisión, no quién la escribe. Una decisión del propietario se copia tal como la dio, entre comillas y con su fecha, sin reinterpretarla. Si hace falta una interpretación técnica, va en `## Consecuencias` y la firma quien la hace.
- **R4 · Enlace obligatorio.** Toda especificación que contenga «decisión del CTO» o «decisión del propietario» enlaza al menos un `ADR-NNN.md` que existe. Ese ADR la lista a su vez en `especificaciones`.
- **R5 · Sustitución.** Un ADR no se borra ni se reescribe. Si cambia la decisión, se crea uno nuevo y el anterior pasa a `sustituida por ADR-NNN`, apuntando a un ADR que existe y está `vigente`. No hay ciclos.
- **R6 · ADR iniciales.** Uno por decisión, con su `decidido_por`:
  - Del propietario:
    - la plataforma única en Google Cloud (programa RET);
    - el PMV solo en la rama `pmv/consolidacion`;
    - el criterio legal de desarrollo;
    - GCP-06.
  - Del CTO:
    - la instantánea de SEC-24, que se regenera una sola vez;
    - las hojas anteriores de RM-27 con etiqueta y el CHECK `NOT VALID`;
    - `/cloudsql/` en RET-01;
    - los tres casos de la bibliografía de RET-07;
    - la regla de pruebas ajenas;
    - el binario en GB de BOV-01;
    - esta precedencia (R1).

  Para las decisiones del propietario, la ficha busca el texto original en los partes o en las fichas. Si no lo encuentra, el ADR no se crea y la decisión va a una lista para que el CTO la pida al propietario.
- **R7 · Las especificaciones que ya citan decisiones.** Las de `main` que contienen esas frases se corrigen en el mismo PR para enlazar su ADR (R4). Solo se añade el enlace; no cambia ninguna regla.
- **R-ADPA · Ortogonalidad ZERAG (`ARQ-01`).** Solo gobernanza.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** cada ADR, **entonces** tiene los cuatro campos con valores válidos y los tres encabezados. Mutación: quitar `decidido_por` o poner un valor fuera de los tres hace fallar la prueba. | `test_adr_campos_obligatorios` |
| **Dado** la numeración, **entonces** va de `ADR-001` sin huecos ni repetidos. | `test_adr_numeracion` |
| **Dado** una especificación con «decisión del CTO» o «decisión del propietario», **entonces** enlaza un ADR que existe y que la lista. Mutación: borrar el enlace de una especificación hace fallar la prueba. | `test_especificacion_enlaza_adr` |
| **Dado** un ADR `sustituida por ADR-n`, **entonces** ADR-n existe, está vigente y no hay ciclos. Mutación: apuntar a un ADR inexistente hace fallar la prueba. | `test_adr_sustitucion` |
| **Dado** un ADR con `decidido_por = propietario`, **entonces** su `## Decisión` contiene una cita entre comillas con fecha. | `test_adr_propietario_cita_literal` |

Todas en `tests/test_arq01_registro_adr.py`, sin base de datos y sin `import yaml`.

## 6. Trazabilidad

- Ficha: `governance/tareas/ARQ-01.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Origen: `governance/partes/arquitecto/2026-11-13_PROPUESTA_ADOPCION_TOGAF.md`, aprobada por el CTO el 2026-11-13 con condiciones. TOGAF 10, fase H y Architecture Repository; Nygard (2011).
- Propiedad, medida en `origin/main` 4eca5af2:
  - `governance/arquitectura/decisiones/` y sus `ADR-NNN.md` (crea);
  - `tests/test_arq01_registro_adr.py` (crea);
  - las especificaciones de `main` que citan una decisión, solo para añadir el enlace. Hoy son tres; la ficha las lista por nombre al empezar.
- Libre, en la tanda de gobernanza con ARQ-02 y ARQ-03. No desplaza a RET-00 ni a las fichas libres de la tanda de 20.
