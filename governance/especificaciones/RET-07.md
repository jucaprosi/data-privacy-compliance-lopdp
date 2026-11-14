# RET-07 · Historia del PMV fuera de `main`
`¤sdd` `¤arbitro` `¤gobernanza`

Segunda decisión del propietario (2026-11-13): el PMV queda solo en la rama `pmv/consolidacion`, y de `main` sale también su historia.

> **Convención.** «BG» es la serie de fichas del árbitro vigente de la base gestionada del PMV (BG-00 a BG-04), y «el árbitro vigente» es su prueba en `tests/`. Este documento no escribe el nombre del proveedor porque ese árbitro no admite menciones nuevas.

## 1. Datos

Sin tablas. Sala: gobernanza. Lo que cambia en el árbol de `main`:

- **Se retiran:**
  - `governance/historico/pmv/` (9 documentos);
  - el brief del propietario de la base gestionada del PMV (en `governance/apoyo/`);
  - las fichas BG-00 a BG-04, y sus especificaciones si las tienen;
  - el árbitro vigente y su carpeta de listas.
- **Se reescriben** las frases de fichas `hecha`, `governance/artefactos/APORTES_INEDITOS.md`, `governance/artefactos/FUENTES_Y_BIBLIOGRAFIA.md` e informes y partes fechados que describen las plataformas retiradas: quedan descritas sobre Cloud SQL, Cloud Storage, Vertex AI, Secret Manager y variables de entorno, o se quitan si solo hablaban de lo retirado.
- **Se borra** `governance/apoyo/RETIRO_PLATAFORMAS_PMV.md`, el documento de este programa.
- **Dependencias:** `requirements.txt` y `frontend/package.json` sin paquetes de las plataformas retiradas.
- **Índices:** el índice de tareas regenerado; `VPA_MAP.md` sin rastros huérfanos.
- **Árbitro:** `tests/plataforma_unica/pendientes/` vacío.

`alembic/versions/` no se toca.

## 2. API

No aplica.

## 3. Reglas

- **R1 · Primero se comprueba que existe en `pmv/consolidacion`.** Antes de retirar un archivo, se confirma que está en `origin/pmv/consolidacion` con el mismo contenido (mismo blob de git). Lo que falte o difiera se lleva allí con un PR a esa rama, y RET-07 espera a que se fusione. El PR de RET-07 incluye la tabla archivo → presente en `pmv/consolidacion`.
- **R2 · Reescribir no cambia el hecho.** No se deja un término de sustitución («proveedor anterior» o parecido): la frase se escribe sobre la plataforma actual o se quita. No cambian los números de aporte, las fechas, los identificadores de ficha, las cifras ni el sentido de la frase. No se borra ningún aporte ni se renumera.
- **R3 · Una cita no se falsea.** Una entrada de `FUENTES_Y_BIBLIOGRAFIA.md` cuyo título o URL nombra al proveedor no se puede reescribir sin alterar la fuente. No se cambia ni el título ni la URL. Esas entradas se listan en el PR y **las decide el CTO**: o salen de `main` junto con lo que solo se apoya en ellas (y quedan en `pmv/consolidacion`), o el propietario acepta una exclusión. La ficha no elige.
- **R4 · Las fichas BG salen con sus referencias.** Se quitan de `depende_de` de toda ficha que las cite y de cualquier lista de pendientes o exención. Ningún archivo queda con propiedad a nombre de una ficha que ya no existe.
- **R5 · el árbitro vigente no se retira sin su sustituto.** Solo se retira si `tests/test_plataforma_unica.py` (RET-00) ya está en `main` y ya figura entre los árbitros mínimos de cada fusión. Si esa lista vive en un workflow o en un verificador, el cambio es del propietario y va por brief antes de este PR.
- **R6 · Precondición.** RET-01, RET-02, RET-03, RET-05, RET-06, IA-04, IA-06 e IA-08 están `hecha` y sus pendientes, vacíos. RET-07 no retira código de producto: si queda una mención en producto, pertenece a su ficha dueña y RET-07 espera.
- **R7 · Los partes fechados.** La regla del proyecto es que un parte fusionado no se edita. Esta decisión del propietario la exceptúa solo para las frases sobre las plataformas retiradas. El PR lo declara y no cambia nada más en esos archivos.
- **R8 · Nada fuera de `main`.** No se toca `produccion` ni `dev/Aleczandra`, y no se crea ni se borra nada en las cuentas de los proveedores. Lo retirado sigue en la historia de git.
- **R9 · Comprobación única de los documentos.** El árbitro de RET-00 no lee documentos. Que los documentos ya no describen las plataformas retiradas se comprueba una vez, en este PR: el PR incluye el comando de búsqueda usado y su salida vacía. No queda una búsqueda permanente.
- **R-ADPA · Ortogonalidad ZERAG (`RET-07`).** Sin código de sala.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el árbol final, **entonces** `tests/plataforma_unica/pendientes/` está vacío y el árbitro de RET-00 pasa. Mutación: dejar un pendiente hace fallar la prueba. | `test_plataforma_unica_sin_incumplimientos_nuevos` |
| **Dado** el árbol final, **entonces** no existen `governance/historico/pmv/`, las fichas BG-00 a BG-04, la carpeta de listas del árbitro vigente ni el árbitro vigente, ni `governance/apoyo/RETIRO_PLATAFORMAS_PMV.md`. Mutación: dejar uno de ellos hace fallar la prueba. | `test_ret07_historia_retirada` |
| **Dado** las fichas de `governance/tareas/`, **entonces** ninguna cita una ficha inexistente en `depende_de` y el índice coincide con el generado. Mutación: dejar una cita a `BG-01` hace fallar la prueba. | `test_indice_tareas` |
| **Dado** `APORTES_INEDITOS.md` antes y después, **entonces** los números de aporte y las fechas son los mismos y no falta ninguno. Mutación: borrar o renumerar un aporte hace fallar la prueba. | `test_ret07_aportes_intactos` |
| **Dado** `requirements.txt` y `frontend/package.json`, **entonces** no declaran ninguna dependencia de las plataformas retiradas. | `test_sin_dependencias_de_plataformas` |
| **Dado** `VPA_MAP.md` y los invariantes citados, **entonces** no quedan rastros ni citas huérfanas. | `test_vpa_map` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-07.md`.
- Programa: `governance/apoyo/RETIRO_PLATAFORMAS_PMV.md` (PR #763, 39dbf4b5), segunda decisión del propietario del 2026-11-13.
- Especificación de referencia: `governance/especificaciones/README.md`.
- Última del programa: después de RET-06 y de IA-06 e IA-08. Árbitros de cierre: `test_plataforma_unica.py`, `test_indice_tareas`, `test_reparto`, `test_vpa_map` y `test_inv_citados_existen`.
- `.github/workflows/` y `verificadores/` son del propietario: si hacen falta, va un brief.
