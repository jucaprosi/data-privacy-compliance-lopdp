# RET-08 · El notificador como puerto
`¤sdd` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones.

| Elemento | Estado final |
| :--- | :--- |
| `Notificador` (puerto) | interfaz de `features/notificaciones`: `enviar_correo(correo) -> ResultadoDespacho` |
| `NotificadorFalso` | doble de pruebas; registra lo enviado y devuelve `ENVIADO` |
| `NotificadorEntornoPermitido` | decorador que filtra destinatarios por entorno (EP-08); se conserva |
| `NotificadorNoConfigurado` | en `services/adaptadores.py`; implementación de producción mientras no hay proveedor: no envía y devuelve `EstadoEnvio.PENDIENTE` con un `error_detalle` neutro («proveedor de correo no configurado») |
| `notificador_configurado()` | devuelve `NotificadorEntornoPermitido(NotificadorNoConfigurado())` |
| boceto del proveedor anterior en `services/adaptadores.py` y sus variables | se borran |

## 2. API

Sin rutas nuevas. `POST` de recordatorios (`api/routers/roadmaps_recordatorios.py`) sigue recibiendo el notificador por `Depends(notificador_configurado)`. Sin proveedor responde como hoy cuando el envío no se confirma: las tareas no se marcan como notificadas.

## 3. Reglas

- **R1 · Puerto.** Todo envío pasa por `Notificador`. Los llamadores (`roadmaps_recordatorios.py` y `app_core/pasillo/notificaciones.py`) no conocen ninguna implementación concreta.
- **R2 · Falla cerrado.** `notificador_configurado()` nunca devuelve `NotificadorFalso`. Sin proveedor, el resultado es `PENDIENTE` y nada se marca como notificado. Es el comportamiento actual de la fábrica, que se conserva.
- **R3 · Proveedor pendiente.** El adaptador real lo añade una ficha posterior, cuando el propietario elija proveedor (recomendado: la Gmail API de Google Workspace, con la credencial en Secret Manager; mapa §3). Esta ficha no crea ningún adaptador.
- **R4 · Borrado completo.** El boceto, su exportación en `services/__init__.py` y en `notificaciones_service.py`, y sus variables de entorno desaparecen. No queda un alias ni una prueba que compruebe el borrado.
- **R-ADPA · Ortogonalidad ZERAG (`RET-08`).** Solo `features/notificaciones/` y su prueba. Otras salas llegan por `app_core/pasillo/notificaciones.py`, sin cambios.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** `NotificadorFalso`, **cuando** se envían recordatorios, **entonces** registra el correo y `enviar_recordatorios` devuelve verdadero. | `tests/test_notificaciones.py` |
| **Dado** `notificador_configurado()` sin proveedor, **cuando** se envía un correo, **entonces** el resultado es `PENDIENTE` y `enviar_recordatorios` devuelve falso. Mutación: devolver el falso desde la fábrica hace fallar la prueba. | `tests/test_notificaciones.py` |
| **Dado** un entorno con lista de destinatarios permitidos, **entonces** el decorador deja fuera los destinatarios que no están en la lista. | las pruebas existentes de EP-08 |
| **Dado** el árbol con la ficha fusionada, **entonces** la suite completa pasa. | la suite existente |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-08.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Decisión pendiente del propietario: proveedor de correo (mapa del programa §3; brief `governance/operaciones/BRIEF_PROPIETARIO_RET_ARNESES_Y_CI.md`).
- Depende de NOTIF-01, dueña del diseño del notificador.
