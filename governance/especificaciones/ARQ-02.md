# ARQ-02 · Mapa de capacidades
`¤sdd` `¤arbitro` `¤adpa`

## 1. Datos

Sin tablas ni migraciones. Un documento y una prueba:

- `governance/arquitectura/CAPACIDADES.md`: una tabla con las columnas `capacidad`, `artículos`, `estado legal`, `sala` y `fichas`.
  - `sala` es el nombre de una carpeta de `features/`, o `sin sala`.
  - `estado legal` es `verificado` o `sin verificar`.

Medido en `origin/main` 4eca5af2: `features/` tiene 26 salas, de `ai_copilot` a `transferencias`.

## 2. API

No aplica.

## 3. Reglas

- **R1 · Los artículos salen de las citas verificadas.** Un artículo de la LOPDP o de su reglamento solo entra como `verificado` si está en `governance/apoyo/CITAS_LEGALES_VERIFICADAS.md`, y lo cita tal como aparece allí.
- **R2 · Lo que no esté verificado.** Un artículo que no esté en ese archivo entra como `sin verificar`, con la pregunta para el banco del abogado. Nunca como interpretación propia.
- **R3 · Cobertura en los dos sentidos.**
  - Toda sala que nombra el mapa existe en `features/`.
  - Toda carpeta de `features/` aparece en el mapa, aunque sea en una fila de soporte sin capacidad legal (por ejemplo, `plataforma` o `demo`).
- **R4 · Capacidades sin sala o con dos.** Se marcan, no se resuelven: una capacidad `sin sala` o con dos salas va en una lista al final del documento para que el CTO decida.
- **R5 · Revisión normativa.** El DPO revisa las columnas `capacidad` y `artículos` antes de fusionar.
- **R6 · Sin duplicar.** El mapa enlaza las fichas y las especificaciones; no repite sus reglas.
- **R-ADPA · Ortogonalidad ZERAG (`ARQ-02`).** Solo gobernanza.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el mapa, **entonces** toda sala listada existe en `features/`. Mutación: añadir una sala inexistente hace fallar la prueba. | `test_salas_del_mapa_existen` |
| **Dado** `features/`, **entonces** toda carpeta aparece en el mapa. Mutación: crear una carpeta nueva sin fila hace fallar la prueba. | `test_toda_sala_en_el_mapa` |
| **Dado** una fila `verificado`, **entonces** cada artículo aparece en `CITAS_LEGALES_VERIFICADAS.md`. Mutación: marcar como verificado un artículo que no está hace fallar la prueba. | `test_articulos_verificados` |
| **Dado** una fila `sin verificar`, **entonces** lleva una pregunta para el banco del abogado. | `test_sin_verificar_con_pregunta` |

Todas en `tests/test_arq02_mapa_capacidades.py`, sin base de datos y sin `import yaml`.

## 6. Trazabilidad

- Ficha: `governance/tareas/ARQ-02.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Origen: propuesta TOGAF aprobada por el CTO (2026-11-13). TOGAF 10, fase B (mapa de capacidades).
- Propiedad: `governance/arquitectura/CAPACIDADES.md` y `tests/test_arq02_mapa_capacidades.py` (crea los dos). Lee `governance/apoyo/CITAS_LEGALES_VERIFICADAS.md`; no lo edita.
- Libre, en la tanda de gobernanza con ARQ-01 y ARQ-03.
