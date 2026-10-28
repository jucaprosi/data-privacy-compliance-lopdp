# RAT-06 · Exportación completa del RAT a XLSX y PDF con la versión vigente de cada ficha
`¤sdd` `¤rat`

## 1. Datos

Sin tablas nuevas. Lee las fichas vigentes y su última versión (RAT-05).

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET /rat/exportar?formato=xlsx\|pdf` | `implementador`, `coordinador`, `dpo`, `admin_organizacion` | — | `200` archivo, `Content-Disposition: attachment; filename="rat-<tenant>-<fecha>.<ext>"` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 409 | `RAT_VACIO` | ninguna ficha vigente |
| 422 | (FastAPI) | `formato` fuera de los dos |

## 3. Reglas

- **R1 · Contenido.** Una fila por tratamiento vigente (`baja_en IS NULL`), columnas fijas en el orden del RAT; `version` = número de la última versión.
- **R2 · Huella.** `huella = sha256(bytes del XLSX)`; el PDF la imprime en el pie y en los metadatos.
- **R3 · Sin datos personales de titulares.** Solo categorías; nunca registros.

## 4. Interfaz

Botón «Exportar» en el módulo RAT con dos opciones; muestra la huella tras descargar.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** 3 fichas vigentes y 1 dada de baja, **cuando** se exporta XLSX, **entonces** tiene 3 filas. Mutación: incluir la baja hace fallar la prueba. | `test_exportar_solo_vigentes` |
| **Dado** la exportación PDF, **entonces** el pie contiene la huella del XLSX generado en la misma llamada. | `test_exportar_huella` |
| **Dado** una organización sin fichas, **entonces** 409 `RAT_VACIO`. | `test_exportar_vacio` |
| **Dado** el módulo RAT, **cuando** se pulsa «Exportar XLSX», **entonces** se descarga un archivo `.xlsx`. | `frontend/tests/rat/exportacion.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RAT-06.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2 («Exportación completa a XLSX y PDF»).
