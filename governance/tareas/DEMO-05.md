+++
id = "DEMO-05"
titulo = "Cloud Run Job de purga nocturna: filas y objetos de las demos vencidas"
ola = "D"
estado = "en_curso"
sala = "operaciones"
depende_de = ["DEMO-00", "EP-01"]
propiedad = ["jobs/purga_demo/**", "tests/test_demo_purga.py"]
arbitro = "pytest tests/test_demo_purga.py contra una base de prueba; mutación documentada"
rastros = ["¤demo"]
+++

# DEMO-05 · Cloud Run Job de purga nocturna: filas y objetos de las demos vencidas

**Proyecto:** EVYDENTIA (Google Cloud). **Sala dueña:** `operaciones`. Tanda 54.

**Por qué.** La aplicación nunca borra (invariante 63). La purga física la hace un job aparte, con su propia cuenta de servicio y una credencial que la aplicación no tiene.

## Entrega
- `jobs/purga_demo/`: código del job y su Dockerfile.
- Se niega si el proyecto no es el de la demo o coincide con `HUELLA_PROYECTO_PRODUCCION`.
- Borra primero los objetos con prefijo `tenant_id` y después las filas de todas las tablas con `tenant_id`, auditoría incluida, de los tenants `es_demo` vencidos, nunca de la plantilla. **No** borra la fila de `demo_sesiones`: queda con `tenant_id` y persona en nulo y solo `sub`, correo, inicio, fin y motivo.
- Borra las filas de `demo_sesiones` vencidas hace más de 90 días (decisión del propietario, PRD §5.6.4).
- Comprueba que quedan 0 filas; si no, sale con error.
- La configuración de Cloud Scheduler y de la cuenta de servicio va en el informe para DEMO-07.

## Pruebas
- Tras la purga no queda ninguna fila del tenant vencido en ninguna tabla con `tenant_id`.
- La plantilla y las demos activas quedan intactas.
- La fila de `demo_sesiones` sigue el día 89 tras su vencimiento y ya no está el día 91.
- Tras la purga no queda ningún otro dato del vendedor fuera de esa fila.
- Contra la huella de producción el job sale con error.
- Mutación: saltar la comprobación de 0 filas hace fallar la prueba.

## Límites
- Contrato congelado: rutas, cuerpos y códigos de `FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md` §1.7 y las firmas de `demo_service.py` que fija DEMO-00. Si hay que cambiarlos, para y consulta a Tech Lead.
- No toques `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod`, la RLS ni `main.py`.
- En archivos con secciones `#ID` escribe solo dentro de tus marcas `# --- INICIO <ID> --- … # --- FIN <ID> ---`.
- Nunca uses la base ni el proyecto de producción; solo datos ficticios con correos `.invalid`.

## Fuentes
- `governance/artefactos/PRD.md` §5.6 (demo comercial) y §5.6.8 (corte confirmado por el Arquitecto ADPA y el CTO, 2026-11-07).
- `governance/artefactos/INVARIANTS.md`, invariantes 60 a 63.
- Flujos y matriz: `governance/apoyo/FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md`.
- Interfaz: `governance/apoyo/UX_DEMO_EVYDENTIA.md` (lo que cambia) sobre `governance/apoyo/UX_DEMO_COMERCIAL.md`.
