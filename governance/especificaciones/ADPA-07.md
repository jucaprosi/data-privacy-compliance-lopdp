# ADPA-07 · Secciones `#ID` en registros y componentes Frontend compartidos
`¤sdd` `¤adpa` `¤secciones`

## 1. Datos

Sin tablas nuevas.

## 2. API

Sin rutas nuevas.

## 3. Reglas

- **R1 · Registros de menú y pantallas sin contención.** `menus/index.ts` y `pantallas/index.tsx` poseen secciones `// --- INICIO <ID> ---` / `// --- FIN <ID> ---` para las 18 tareas con pantalla propia.
- **R2 · Desacoplamiento de `DiagnosticCanvas.tsx` y `EvidenciasModule.tsx`.** `DiagnosticCanvas.tsx` expone `#EVI-01`, `#DIAG-05` y `#DIAG-07`; `EvidenciasModule.tsx` expone `#EVI-01` y `#EVI-02`.
- **R3 · Secciones en `DashboardHeader.tsx` (`#FE-25`) y `useBibliotecaStore.ts` (`#BIB-110`).** Ambos archivos contienen sus delimitadores reservados.

## 4. Interfaz

Sin cambio visual hasta que cada tarea rellene su sección reservada.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el conjunto de archivos Frontend compartidos, **cuando** corre `test_adpa07_secciones_frontend.py`, **entonces** todas las secciones `#<ID>` reclamadas por tareas pendientes están delimitadas por `// --- INICIO <ID> ---` y `// --- FIN <ID> ---`. | `test_secciones_frontend_existen` |

## 6. Trazabilidad

- Patrón de secciones reservadas de `FE-22` y `BIB-112`.
