# NOTIF-05 · La bandeja nombra cada enlace por su destino
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas. Medido en `origin/main` f2636b8b:
- `frontend/src/components/avisos/BandejaAvisos.tsx:111` escribe «Revisar la versión» en todo aviso con `enlace`.
- `GET /avisos` devuelve `id`, `titulo`, `texto`, `enlace`, `leido`, `pendiente` y `creado_en`, pero no el `tipo` (`avisos_plataforma.py:102`).

La bandeja elige el texto del enlace por su ruta:

| Ruta del enlace | Texto |
| :--- | :--- |
| empieza por `/plataforma/capacidades` | «Ver capacidades editoriales» |
| cualquier otra | «Revisar la versión» |

## 2. API

Sin cambios.

## 3. Reglas

- **R1 · El enlace dice adónde lleva.** El texto nombra el destino (WCAG 2.2, 2.4.4). Los textos son los de NOTIF-02 y NOTIF-04 R2.
- **R2 · Un aviso nuevo con otro destino** añade su fila a la tabla de §1.
- **R-SP · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`NOTIF-05`).** Solo los archivos de la propiedad.

## 4. Interfaz

La bandeja de NOTIF-02; solo cambia el texto del enlace.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** un aviso con enlace a `/plataforma/capacidades`, **entonces** el enlace dice «Ver capacidades editoriales». Mutación m1: el texto fijo da rojo. | `frontend/tests/avisos/bandeja.spec.ts` |
| **Dado** un aviso de versión por revisar, **entonces** el enlace sigue diciendo «Revisar la versión». Mutación m2: usar el texto de capacidades para todos da rojo. | ídem |

## 6. Trazabilidad

- NOTIF-04 R2 y revisión del Tech Lead de #1104. Decisión del Arquitecto: el texto sale del destino, sin columna nueva ni `tipo` en la API, porque `avisos_plataforma.py` es de NOTIF-03, que está pendiente.
