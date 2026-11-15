# EVI-05 · Tipo de evidencia «acuse» en la custodia de documentos generados
`¤sdd` `¤evidencias`

## 1. Datos

Sin tablas ni migraciones.

| Archivo | Estado final |
| :--- | :--- |
| `features/evidencias/services/custodia_generados_engine.py` | `TIPOS_EVIDENCIA = ("capacitacion", "acta_auditoria", "informe_incidente", "respuesta_derecho", "asesoria_dpo", "exportacion", "acuse")` |
| `tests/test_evi05_tipo_acuse.py` (nuevo) | casos de §5 |

Hecho medido en `origin/main` 1333d1a7: `TIPOS_EVIDENCIA` es una tupla cerrada de seis tipos (`custodia_generados_engine.py:37`), y `custodiar_documento_generado` rechaza cualquier otro con `CustodiaInvalida`. `evidencias_service.py` la reexporta.

## 2. API

Sin rutas nuevas. `app_core/pasillo/evidencias.py::custodiar_documento_generado` admite `tipo_evidencia="acuse"` y devuelve `{evidencia_id, sha256, tipo_evidencia}`, como para los demás tipos.

## 3. Reglas

- **R1 · Tipo propio.** `acuse` identifica el comprobante de una aceptación (FIRMA-02). Ningún otro tipo lo sustituye.
- **R2 · Misma custodia.** Un `acuse` sigue las reglas de la custodia de EVI-04: firma de formato, límites, sha256 calculado sobre los bytes, subida única, retención de `retencion_dias` y vínculo a controles.
- **R-ADPA · Ortogonalidad ZERAG (`EVI-05`).** Solo la tupla de la sala de evidencias. Otras salas la usan por `app_core/pasillo/evidencias.py`.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un PDF y `tipo_evidencia="acuse"`, **cuando** se custodia, **entonces** se registra la evidencia y el `sha256` devuelto es el de los bytes. Mutación m1: quitar `acuse` de la tupla hace fallar la prueba. | `tests/test_evi05_tipo_acuse.py` |
| **Dado** un tipo fuera de la tupla, **entonces** sigue saliendo `CustodiaInvalida`. | `tests/test_evi05_tipo_acuse.py` |
| **Dado** el árbol con la ficha fusionada, **entonces** la suite de evidencias y la suite completa pasan. | la suite existente |

## 6. Trazabilidad

- Ficha: `governance/tareas/EVI-05.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Depende de EVI-04 y RET-02, hechas, dueñas anteriores del archivo. FIRMA-02 depende de EVI-05.
