# LEG-08b · Citas de las plantillas que LEG-08 no leyó
`¤sdd` `¤regulation-code` `¤arbitro` `¤cita-verificada`

## 1. Datos

Salen de la salida del árbitro de BIB-403 (`scripts/verificar_citas_plantillas.py`), recogida por el Tech Lead el 2026-11-24. Las claves usan el mismo patrón que LEG-08.

| Fuente (`fuente_id`) | Claves | Situación hoy | Plantillas |
| :--- | :--- | :--- | :--- |
| Reglamento General (`RGLOPDP-RO435`) | `RLOPDP-art-18`, `RLOPDP-art-53` | sin fila | 001, 007 |
| LOPDP (`LOPDP-RO459`) | `LOPDP-art-7-num-2`, `LOPDP-art-7-num-5` | sin fila | 010, 012 |
| Res. SPDP-SPD-2026-0040-R (`RES-2026-0040`) | `RES-2026-0040-art-3`, `-art-3-num-1`, `-art-4`, `-art-5`, `-art-8`, `-art-9`, `-art-9-num-4`, `-art-12` | sin fila | 009 |
| Res. SPDP-SPD-2025-0041-R (`RES-2025-0041`) | `RES-2025-0041-art-4` | sin fila | 010, 011, 012 |
| Res. SPDP-SPD-2025-0041-R (`RES-2025-0041`) | `RES-2025-0041-art-4-num-4`, `-art-5`, `-art-11`, `-art-11-num-2`, `-art-11-num-4`, `-art-15`, `-art-15-num-1`, `-art-16`, `-art-17` | `no_leida` | 010, 011, 012 |
| Res. SPDP-SPD-2025-0028-R (`RES-2025-0028`) | `RES-2025-0028-art-10` | `no_leida` | 001, 002, 006, 010 |
| Ley de Ciberseguridad, RO 5S 290 (`LEY-CIBER-RO290`) | `LOPDP-art-43-reforma-RO-5S-290` | `no_leida`; fuente no localizada | 001, 009 |

El artefacto tiene hoy las fuentes `RES-2025-0028` y `RES-2025-0041` sin PDF, porque el portal dio 404, y `LEY-CIBER-RO290` no localizada. La lectura empieza por obtener el PDF oficial de cada una.

## 2. API

Sin cambios.

## 3. Reglas

- **R1 · El método de LEG-08.** Rigen LEG-08 R1 a R5 sin cambios: solo fuente oficial, lectura literal sin completar de memoria, `sha256` del PDF tal como se descargó, y lo no leído no es verificado.
- **R2 · Lectura.** Un PDF con capa de texto se lee de su texto. Un escaneo se lee por OCR con confianza media de al menos 0,85 en la página citada, o por lectura visual de la imagen; la columna de forma de lectura de la fuente dice cuál se usó.
- **R3 · Estados.** Son los mismos de LEG-08: `verificada`, `no_encontrada` o `no_leida`. Lo que el pedido llama «no_verificada» es cualquiera de los dos últimos. Una clave que ya tenía fila cambia su fila, no se duplica.
- **R4 · Fuente nueva o actualizada.** Si se obtiene el PDF de `RES-2025-0028`, `RES-2025-0041` o `LEY-CIBER-RO290`, su fila de Fuentes gana la URL oficial y el `sha256`. Si no se obtiene, sus claves quedan `no_leida`.
- **R5 · Lo que queda sin verificar.** BIB-403 quita de las plantillas la cita que no quede `verificada`, o declara su sección informativa (BIB-403 R1). Esta ficha no toca las plantillas.
- **R-ADPA · Ortogonalidad ZERAG (`LEG-08b`).** Solo `CITAS_PLANTILLAS_VERIFICADAS.md`.

## 4. Interfaz

Sin cambios.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** las claves de §1, **entonces** cada una tiene una sola fila con su estado, y cada fuente leída tiene su URL oficial y su `sha256`. | revisión del CTO |
| **Dado** el artefacto ampliado y las plantillas de BIB-403, **entonces** el árbitro de los dos sentidos no informa ninguna cita «sin fila». | `scripts/verificar_citas_plantillas.py` (lo corre BIB-403) |

## 6. Trazabilidad

- **PRD:** §4, Módulo 7, «Publicación con cita verificada»; ley fundacional 6.
- **Rastro:** `¤cita-verificada`.
- Amplía LEG-08 con su mismo método; BIB-403 depende de esta ficha.
- Pedido del CTO (2026-11-24), base `origin/main` 6c5726e9.
