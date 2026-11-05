# ADPA-06 · Andamiaje de secciones `#ID` en `app_core/pasillo/`
`¤sdd` `¤adpa` `¤pasillo`

## 1. Datos

Sin tablas nuevas. Contratos tipados en `app_core/pasillo/<sala>.py`.

## 2. API

Sin rutas nuevas.

## 3. Reglas

- **R1 · Secciones `#<ID>` pre-sembradas.** Cada módulo `app_core/pasillo/<sala>.py` incluye las secciones `# --- INICIO <ID> ---` / `# --- FIN <ID> ---` declaradas por las tareas pendientes.
- **R2 · Delegación perezosa.** Ningún módulo de `app_core/pasillo/` importa de `features/` en el nivel superior del módulo.

## 4. Interfaz

Sin interfaz propia.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** cada entrada `app_core/pasillo/<sala>.py#<ID>` en las tareas pendientes, **cuando** corre `test_adpa06_pasillos_secciones.py`, **entonces** el archivo y la sección `#<ID>` existen y delegan perezosamente a la compuerta de la sala. | `test_pasillos_tienen_secciones_reservadas` |

## 6. Trazabilidad

- ADR 0001 (`docs/adr/0001-pasillo-central-entre-salas.md`).
