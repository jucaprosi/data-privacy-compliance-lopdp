# GEN-01 · Aplicación genérica: los artefactos, las especificaciones y las fichas en estado final, sin la marca del operador
`¤sdd` `¤arbitro`

## 0. Programa

Decisión del propietario (2026-11-24): la aplicación es genérica. La marca del operador sale de forma estructural, desde el PRD hacia las especificaciones, el código, las pruebas, los contratos y los nombres de archivo. Rige la regla de retiro: lo retirado se borra como si nunca hubiera existido, todo se escribe en estado final y **no se añade ningún invariante, árbitro ni prueba que busque la palabra retirada**.

Medido en `origin/main` ea6d26bf (brief del CTO, repetido por el Arquitecto con `git grep -i`): 90 archivos de texto y 7 nombres de archivo.

| Ficha | Tanda | Qué | Depende de |
| :--- | ---: | :--- | :--- |
| GEN-01 | 99 | artefactos, 5 especificaciones y 15 fichas | — |
| GEN-02 | 100 | escala de madurez: contrato, servidor, pantalla, pruebas y archivo de assessment | GEN-01; recuento del propietario (GEN-02 R1) |
| GEN-03 | 100 | Biblioteca: fuente `"catalogo"`, código de error y textos | GEN-01 |
| GEN-07 | 100 | firma electrónica, plantilla RAT, documentos de apoyo y binarios | GEN-01; decisiones del propietario (GEN-07 R1 a R3) |
| GEN-05 | 101 | contrato OpenAPI regenerado | GEN-02, GEN-03 |
| GEN-06 | 101 | Alembic: archivo y revisión de la escala | GEN-02; `alembic_version` del propietario (GEN-06 R1) |

**Fuera del programa** (decisión del propietario, 2026-11-24): la marca en la interfaz, es decir, el título de `frontend/src/app/page.tsx`, el texto alternativo de `DashboardHeader.tsx` y los logotipos de `frontend/public/brand/`. Ninguna ficha del programa los toca. Los ids GEN-05 a GEN-07 se conservan.

**Cambios sobre el reparto del brief, por ortogonalidad:**
- `governance/ESCALA_MADUREZ.md` y `INFORME_SEGURIDAD_PRESENTACION_LOPDP.md` nombran el archivo de assessment y pasan a GEN-02, que es la ficha que lo renombra. Si no, dos fichas tocarían el mismo nombre de archivo en tandas distintas y quedarían desalineadas entre medias.
- Alembic va en la tanda 101, detrás de GEN-02, porque la prueba renombrada por GEN-02 lee la ruta de la migración (`MIGRACION`). GEN-06 posee esa prueba después.
- GEN-05 no puede ir con GEN-02 ni con GEN-03: regenera el contrato desde la API final de las dos. `tests/test_contrato_hoja_ruta.py` no compara `enum` ni `description`, así que GEN-02 y GEN-03 no lo rompen entre medias.

## 1. Datos

Sin código. Estado final de la propiedad:

| Archivo | Cambio |
| :--- | :--- |
| `PRD.md` | líneas 23 (se elimina la frase del operador: el operador no tiene nombre de marca), 29, 66, 140-141, 208, 245, 310, 312, 635, 656 y 715 con el vocabulario de §3 |
| `INVARIANTS.md` | 9 (título de la sección), 15 (el invariante de la escala pasa a llamarse con el sufijo `MATURITY_SCALE_1_5` en lugar del que nombra la marca, dentro de la misma familia LOPDP; texto: «La madurez se mide exclusivamente en la escala de madurez de 1 a 5»), 143 y 156 |
| `VPA_MAP.md` | 24 |
| `governance/METODOLOGIAS.md` | 29 |
| `INFORME_CONOCIMIENTOS_EPISTEMICOS.md` | 2: «EVYDENTIA · LOPDP 360» |
| `FUENTES_Y_BIBLIOGRAFIA.md` | 45 y 143 (R5) |
| `APORTES_INEDITOS.md` | 166, 1136, 2276 y 2282 (R5) |
| especificaciones | CAPA-04, DIAG-08, DIAG-09, FE-24, FIRMA-06 |
| fichas | BIB-102, BIB-103, BIB-109, DIAG-02, DIAG-05, DIAG-07b, DIAG-08, DIAG-09, DIAG-10, DIAG-12, DIAG-13, PRD-02, RET-06, RM-19, RM-25a |

## 2. API

Sin rutas.

## 3. Reglas

- **R1 · Vocabulario final** (decisión del CTO; UX/UI confirma los textos visibles):

  | Concepto | Estado final |
  | :--- | :--- |
  | escala | «escala de madurez de 1 a 5» |
  | versión de escala sellada | `madurez_1_5` |
  | invariante de la escala | mismo prefijo de la familia LOPDP, sufijo `MATURITY_SCALE_1_5` (lo escribe GEN-01 en `INVARIANTS.md`) |
  | operador | «Operador de la plataforma» |
  | fuente de plantilla | `"catalogo"` |
  | código de error | `BIB_COPIA_SOLO_CATALOGO` |
  | plantilla de la fuente `"catalogo"` | «Plantilla de la plataforma» (UX/UI, GEN-03 §4) |
  | archivo de assessment | `Assessment_Madurez_SGPDP.xlsx` (GEN-02 R4) |
  | migración de la escala | `alembic/versions/20261031_diagnostico_escala_madurez.py`, revisión `20261031_diag_escala_madurez` (GEN-06) |
  | prueba de la escala | `tests/test_diagnostico_escala_1_5.py` (GEN-02) |
- **R2 · Estado final, no historia.** Las especificaciones y fichas hechas se reescriben como si la escala y la fuente se hubieran llamado siempre así. Las rutas de propiedad de las fichas hechas pasan a los nombres nuevos: el índice solo comprueba la existencia en las fichas no hechas. No se añade ninguna nota del tipo «antes se llamaba».
- **R3 · Sin prohibiciones.** Ningún invariante, árbitro ni prueba nueva busca la palabra retirada.
- **R4 · El servidor MCP.** `VPA_MAP.md` del repositorio manda. El propietario promueve la línea 24 al almacén del servidor si quiere que lo sepa (la nota del triaje).
- **R5 · Fuentes y aportes.** Las citas nombran la obra por su título y fecha, no por la marca:
  - «Matriz de Madurez del SGPDP (archivo de assessment, 2026)» con `Assessment_Madurez_SGPDP.xlsx`;
  - «Reporte Assessment SGPDP» (15-sep-2026);
  - el informe de entrega de STB de ANF AC (15-oct-2026), con el nombre que su emisor da al documento si el propietario lo conserva (GEN-07 R3).
  - **Supuesto que anoto:** la autoría de la matriz es del operador. Si el propietario quiere atribuirla a una persona o entidad, la escribe en el PR de esta ficha.
- **R6 · Registros de lo ocurrido.** El historial de git, `governance/operaciones/REGISTRO_MIGRACIONES_MANUALES.md` (filas 17 y 18) y `governance/partes/` son registro de hechos pasados y no cambian. Confirmo la propuesta del CTO: reescribirlos falsearía lo que ocurrió y ninguna ficha los lee como contrato.
- **R-ADPA · Ortogonalidad ZERAG (`GEN-01`).** Solo la propiedad.

## 4. Interfaz

No aplica (GEN-03).

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** la propiedad, **entonces** usa el vocabulario de R1 en todas las líneas de §1. | revisión del Tech Lead y del Arquitecto |
| **Dado** el índice, el reparto y las especificaciones, **entonces** dan código 0. | árbitro de la ficha |
| **Dado** `tests/test_escala_madurez.py`, **entonces** sigue en verde: `METODOLOGIAS.md` e `INVARIANTS.md` no vuelven a definir la escala (E5). | `tests/test_escala_madurez.py` |

## 6. Trazabilidad

- Brief del CTO `ARQUITECTO_APP_GENERICA_SIN_MARCA_OPERADOR.md` (2026-11-24) y decisión del propietario.
- Depende de las fichas hechas que fijaron lo que se reescribe: DIAG-08, DIAG-09, DIAG-10 y PRD-02.
