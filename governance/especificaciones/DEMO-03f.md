# DEMO-03f · Clonar desde plantilla en la sala videovigilancia
`¤sdd` `¤demo` `¤adpa`

## 1. Datos

Sin tablas ni migraciones. Copia filas de `cctv_camaras_inventario`, la tabla que crea CCTV-01 (su especificación §1).

| Archivo | Estado final |
| :--- | :--- |
| `features/videovigilancia/services/clon_plantilla_engine.py` (nuevo) | `clonar_desde_plantilla` y `sembrar_en_plantilla` |
| `features/videovigilancia/videovigilancia_service.py#DEMO-03f` | reexporta las dos funciones |
| `app_core/pasillo/videovigilancia.py#DEMO-03f` | `clonar_desde_plantilla`, que el orquestador de la demo descubre por nombre |
| `data/demo/cooperativa_demo.json` | bloque `salas.videovigilancia` con dos cámaras ficticias conformes |
| `tests/test_demo_clon_videovigilancia.py` (nuevo) | casos de §5 |

Bloque de la plantilla:

```json
"videovigilancia": {"camaras": [
  {"clave": "cam-recepcion", "nombre_ubicacion": "Recepción (ficticia)", "codec": "H265_PLUS"},
  {"clave": "cam-archivo", "nombre_ubicacion": "Archivo (ficticio)", "codec": "H265"}
]}
```

Las dos llevan `modo_grabacion = 'EVENTO_MOVIMIENTO'`, `audio_ambiental_activo = false`, `mascara_privacidad_activa = true`, `plazo_retencion_dias = 15` y `estado_conformidad = 'CONFORME'`.

Hecho medido en `origin/main` 5e872a4a:
- `features/demo/domain/plantilla.py` fija `PLANTILLA_TENANT_ID = "demo-plantilla-cooperativa"`, `MapaIds = dict[str, str]`, el protocolo `ClonadorDePlantilla` y `ORDEN_DE_SALAS`, que termina en `"videovigilancia"`;
- `features/demo/services/entrada_engine.py` busca `clonar_desde_plantilla` en `app_core.pasillo.<sala>` y omite la sala si no la encuentra;
- `features/videovigilancia` no existe: la crea CCTV-01, que siembra las secciones `DEMO-03f` de su compuerta y de su pasillo;
- `features/biblioteca/services/clon_plantilla_engine.py` (DEMO-03d) es el patrón de referencia.

## 2. API

Sin rutas HTTP. Firmas, las de `ClonadorDePlantilla`:

```python
async def clonar_desde_plantilla(session: AsyncSession, origen: str, destino: str, mapa_ids: MapaIds) -> MapaIds: ...
async def sembrar_en_plantilla(session: AsyncSession, plantilla_id: str, datos: dict) -> None: ...
```

## 3. Reglas

- **R1 · Solo lo suyo.** Lee las cámaras del tenant `origen` y las escribe en `destino`. No lee ni escribe tablas de otra sala.
- **R2 · Ids estables.** El id de cada cámara en el destino es `uuid5(NAMESPACE_URL, f"videovigilancia-demo/{destino}/{id_origen}")`. La inserción es `ON CONFLICT (id) DO NOTHING`, así que repetir la llamada no duplica ni cambia nada. El mapa devuelto amplía `mapa_ids` con `id_origen → id_destino`.
- **R3 · Sin clips.** Los clips (`cctv_clips_boveda` y los objetos de la bóveda) no se copian: son grabaciones con plazo de 15 días y pertenecen a cada organización. El clon muestra el inventario de cámaras y su conformidad.
- **R4 · Transacción del orquestador.** Ninguna de las dos funciones hace `commit`.
- **R5 · RLS.** Lee con el contexto del tenant `origen` y escribe con el de `destino` (`set_config('app.current_tenant_id', …, true)`). Al salir restaura el contexto que traía la sesión.
- **R6 · Siembra idempotente.** `sembrar_en_plantilla` escribe en `plantilla_id` las cámaras del bloque `salas.videovigilancia`, con id `uuid5(NAMESPACE_URL, f"videovigilancia-demo/{plantilla_id}/{clave}")` y `ON CONFLICT (id) DO NOTHING`.
- **R7 · Datos ficticios.** Los nombres de ubicación llevan «(ficticia)» o «(ficticio)». Las cámaras de la plantilla cumplen las reglas R1 y R2 de CCTV-01.
- **R-ADPA · Ortogonalidad ZERAG (`DEMO-03f`).** El orquestador llega por `app_core/pasillo/videovigilancia.py`. El engine no importa otras salas: recibe `origen`, `destino` y `plantilla_id` como argumentos y declara su propio alias `MapaIds = dict[str, str]`, como DEMO-03d.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** la plantilla sembrada, **cuando** se clona a un destino, **entonces** el destino tiene las mismas cámaras con otro `tenant_id` y otros ids, y la plantilla queda intacta. | `tests/test_demo_clon_videovigilancia.py` |
| **Dado** dos clonaciones seguidas al mismo destino, **entonces** el estado es el mismo. Mutación m1: un id aleatorio en lugar de `uuid5` duplica las filas y hace fallar la prueba. | `tests/test_demo_clon_videovigilancia.py` |
| **Dado** dos siembras seguidas, **entonces** la plantilla tiene dos cámaras. | `tests/test_demo_clon_videovigilancia.py` |
| **Dado** RLS forzada y el rol `lopdp_app` con el contexto del destino, **entonces** no ve las cámaras de la plantilla. | `tests/test_demo_clon_videovigilancia.py` |
| **Dado** una plantilla con clips, **entonces** el destino no tiene clips. | `tests/test_demo_clon_videovigilancia.py` |
| **Dado** `entrada_engine`, **entonces** encuentra `clonar_desde_plantilla` en el pasillo de videovigilancia. | `tests/test_demo_clon_videovigilancia.py` |
| **Dado** el árbol con la ficha fusionada, **entonces** la suite de videovigilancia, el linter ADPA y la suite completa pasan. | la suite existente |

## 6. Trazabilidad

- Ficha: `governance/tareas/DEMO-03f.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- **Orden con CCTV-01.** DEMO-03f depende de CCTV-01, que crea la sala completa y siembra `videovigilancia_service.py#DEMO-03f` y `app_core/pasillo/videovigilancia.py#DEMO-03f`. CCTV-01 se fusiona primero; DEMO-03f escribe solo dentro de esas dos secciones.
- `data/demo/cooperativa_demo.json` pasa de DEMO-03 y ORG-22, hechas, a esta ficha.
- PRD §5.6 y §5.6.8; `governance/apoyo/FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md`.
- Pruebas contra el PostgreSQL 16 local, con `exigir_base_de_pruebas()`.
