# LEG-08 · Lectura oficial de las citas de las 12 plantillas
`¤sdd` `¤regulation-code` `¤arbitro`

## 1. Datos

Hechos medidos en `origin/main` a80da616.

**Lectura oficial que ya existe.**
- `governance/artefactos/CITAS_LEGALES_VERIFICADAS.md` (DIAG-16) leyó en el Registro Oficial:
  - LOPDP: arts. 6, 7 (núms. 1 y 8), 8, 10 (lits. a-m), 12-26, 30, 31, 34, 35, 37-44, 46-51, 56 y 57;
  - Reglamento General: solo los arts. 41, 42, 45, 46 y 47.
- `governance/apoyo/CITAS_LEGALES_VERIFICADAS.md` (LEG-03) leyó la LOPDP en una compilación privada, que no es fuente oficial.

**Citas de las 12 plantillas sin lectura oficial** (de `base_lopdp` y de los cuerpos):

| Norma | Citas sin lectura | Plantillas |
| :--- | :--- | :--- |
| LOPDP | arts. 9, 11, 55, 58, 59, 60, 62, 64 y 67-72; art. 18 num. 1; art. 7 num. 8 (el cuerpo de BIB-011 lo escribe «7.8») | 001, 002, 004, 005, 006, 007, 008, 011, 012 |
| Reforma del art. 43 | Ley Orgánica para el Fortalecimiento de la Ciberseguridad, RO 5S 290, 22-05-2026 | 001, 009 |
| Reglamento General | arts. 5-9, 12-16, 19, 20, 24-28, 31, 38-40, 43 y 44 | todas |
| Res. SPDP-SPD-2025-0006-R | arts. 1-4 y Anexo I | 004, 005, 012 |
| Res. SPDP-SPD-2025-0028-R | art. 10 (leída por LEG-01 fuera de los dos artefactos) | 001, 002, 006, 010 |
| Res. SPDP-SPD-2025-0041-R | arts. 4 (num. 4), 5, 11, 15, 16 y 17 | 010, 011, 012 |
| Res. SPDP-SPD-2026-0005-R | arts. 12, 14 (num. 3) y 15-18 | 011 |
| Res. SPDP-SPD-2026-0040-R | arts. 10 y 11 (leída por LEG-02 fuera de los dos artefactos) | 005, 009 |
| Res. SPDP-SPDP-2024-0019-R | la política de la SPDP, citada como modelo | 012 |

**Datos de las plantillas que hay que corregir o resolver.**
- BIB-010, BIB-011 y BIB-012 escriben «SPSP-SPD-2025-0041-R»: hay que comprobar en la fuente la identificación exacta de esa resolución.
- **Marcas «PENDIENTE VALIDACIÓN»:** hay 15, en nueve plantillas: BIB-001, 003, 005, 007, 009 y 010 (una cada una) y BIB-004, 011 y 012 (tres cada una). El brief del CTO hablaba de cuatro plantillas.
- **Citas fuera de la normativa de protección de datos:** el Código del Trabajo, que cita BIB-004 por la confidencialidad laboral.

**Artefacto nuevo.** Tiene el mismo formato que DIAG-16, con dos tablas:
- **Fuentes:** `fuente_id`, identificación oficial, URL oficial, `sha256` del PDF descargado, páginas leídas y fecha de lectura.
- **Citas:** `clave` (el mismo patrón que DIAG-16, por ejemplo `RLOPDP-art-14` o `RES-2025-0041-art-4-num-4`), `fuente_id`, epígrafe literal, texto literal breve, página, `estado` (`verificada`, `no_encontrada` o `no_leida`) y fecha.

La tabla de citas incluye también las que ya leyó DIAG-16, que se citan con su misma clave y su misma lectura, para que el artefacto sea la lista completa de las 12. Al final, una sección «Marcas resueltas» lleva una fila por cada marca «PENDIENTE VALIDACIÓN», con la plantilla, la fuente que la resuelve (o «sin fuente oficial») y el texto que propone.

## 2. API

Sin cambios.

## 3. Reglas

- **R1 · Solo fuente oficial.** Sirven el Registro Oficial, el portal de la SPDP (`spdp.gob.ec`) o el repositorio del Registro Oficial de la Corte Constitucional. Una compilación privada no sirve.
- **R2 · Lectura literal.** Los escaneos se transcriben palabra por palabra desde la imagen de la página, como en DIAG-16, sin completar nada de memoria.
- **R3 · Huella del documento.** Cada fuente lleva el `sha256` del PDF tal como se descargó. Es lo que ata la cita a una versión concreta de la norma (BIB-403 R2).
- **R4 · Lo no leído no es verificado.** Una cita que no se pudo leer queda `no_leida`, y una que no está en la fuente, `no_encontrada`. Las dos impiden publicar la plantilla (BIB-403 R1).
- **R5 · Marcas sin fuente.** Si una marca no tiene respuesta en la normativa de protección de datos, se registra como «sin fuente oficial» y se propone quitar la afirmación del texto. Esa decisión la toma el CTO al revisar.

## 4. Interfaz

Sin cambios.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** el artefacto, **entonces** cada cita de la tabla de §1 tiene una fila, y cada fuente, su URL oficial y su `sha256`. | revisión del CTO; el árbitro automático de los dos sentidos lo aporta BIB-403 |
| **Dado** las 15 marcas «PENDIENTE VALIDACIÓN», **entonces** cada una tiene su fila en «Marcas resueltas». | ídem |

## 6. Trazabilidad

- **PRD:** §4, Módulo 7, «Publicación con cita verificada»; ley fundacional 6.
- Brief del CTO v2 y DIAG-16, cuyo método y formato se reutilizan.
- BIB-403 depende de esta ficha.
