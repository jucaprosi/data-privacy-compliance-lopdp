# SEC-24 · La cabecera de organización sin valor por defecto en la dependencia común
`¤sdd` `¤seguridad-tenant`

## 1. Datos

Sin tablas ni migraciones. Cambia una firma y una instantánea de contrato:

- `api/dependencies.py`: `obtener_tenant_id_actual` deja de declarar `Header(default="tenant-default")` para `X-Tenant-ID`.
- `tests/snapshots/openapi_evidencias_antiguas.json`: esa instantánea guarda el OpenAPI de las tres rutas antiguas de `/evidencias` y contiene cuatro veces `"default": "tenant-default"`. Al quitar el valor por defecto, el OpenAPI de esas rutas cambia y la instantánea deja de coincidir.

## 2. API

Ninguna ruta cambia de camino ni de respuesta con credenciales válidas. Cambia la declaración de la cabecera `X-Tenant-ID` en las rutas que usan la dependencia común (medido en `origin/main`: `conocimiento`, `diagnostico`, `evidencias`, `preanalisis`, `rag_router` y `regulacion_rag`):

| Caso | Antes | Después |
| :--- | :--- | :--- |
| Modo `oidc`, sin cabecera | 400 | 400 (sin cambio) |
| Modo `oidc`, con cabecera y token | autentica y comprueba la membresía | sin cambio |
| Modo `headers` (solo local), sin cabecera | usa `tenant-default` | 400 |
| OpenAPI | la cabecera tiene `default` | la cabecera no tiene `default` |

## 3. Reglas

- **R1 · Sin valor por defecto.** La firma de `obtener_tenant_id_actual` no da ningún valor a `X-Tenant-ID`. Sin cabecera, en cualquier modo, responde 400 con el mensaje que ya existe.
- **R2 · Nada más cambia en la dependencia.** En modo `oidc` sigue verificando el token y la membresía por `autenticar_en_tenant`. SEC-15 sigue impidiendo el modo `headers` fuera de local.
- **R3 · La instantánea se regenera a propósito.** `test_evidencias_rutas_estables.py` la declara congelada y dice que se regenera «solo a propósito, desde una copia de `main`». Esta ficha la regenera una vez, y el único cambio admitido en su diff es la desaparición de las cuatro líneas `"default": "tenant-default"`. Cualquier otra diferencia detiene la ficha.
- **R4 · Alcance.** Solo la dependencia común. Otros routers declaran su propia cabecera con el mismo valor por defecto (`auditoria_capa.py`, `dpo_cockpit.py`, `rat.py` y `rat_eipd.py`): quedan fuera y se listan para una ficha posterior.
- **R5 · Las pruebas que dependían del valor por defecto.** Si alguna prueba llamaba a una de esas rutas sin cabecera en modo `headers`, pasa a enviarla. No se cambia lo que la prueba afirma.
- **R-ADPA · Ortogonalidad ZERAG (`SEC-24`).** Sin llamadas entre salas.

## 4. Interfaz

No aplica: no hay pantalla. El frontend ya envía la cabecera en todas sus llamadas autenticadas; la ficha lo comprueba antes de cambiar la firma y, si alguna llamada no la envía, se detiene y lo informa.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** la firma de `obtener_tenant_id_actual`, **entonces** el parámetro de la cabecera no tiene valor por defecto. Mutación: volver a poner `tenant-default` hace fallar la prueba. | `test_firma_sin_valor_por_defecto` |
| **Dado** el modo `headers` y una petición sin `X-Tenant-ID`, **entonces** 400. | `test_headers_sin_cabecera_400` |
| **Dado** el modo `oidc`, **entonces** sin cabecera 400, y con cabecera y un usuario sin membresía 403, igual que antes. | `test_oidc_sin_cambios` |
| **Dado** la instantánea regenerada, **entonces** difiere de la anterior solo en las cuatro líneas del valor por defecto, y `test_evidencias_rutas_estables.py` pasa. Mutación: cambiar otra línea de la instantánea hace fallar la prueba. | `test_instantanea_solo_pierde_el_valor_por_defecto` |

Las tres primeras y la cuarta van en `tests/test_sec24_sin_tenant_por_defecto.py`, sin base de datos y sin `import yaml`.

## 6. Trazabilidad

- Ficha: `governance/tareas/SEC-24.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Mejora menor del CTO (2026-11-13), de prioridad baja. Depende de SEC-03 y SEC-15 (hechas).
- **Propiedad que falta en la ficha**, medida en `origin/main` 4eca5af2: `tests/snapshots/openapi_evidencias_antiguas.json` y `tests/test_evidencias_rutas_estables.py`, los dos de EVI-01 (hecha) y sin dueña abierta. Sin ellos, quitar el valor por defecto deja la suite en rojo.
- Orden con RET-01, que toca `app_core/security.py` y la guardia de arranque: SEC-24 va antes.
- Decisión que queda al CTO: la instantánea es un contrato congelado de EVI-01. Si no se quiere regenerar por una mejora de legibilidad, SEC-24 no se hace.
