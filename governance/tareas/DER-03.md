+++
id = "DER-03"
titulo = "derechos_arco: crear_solicitud_arco respeta el tenant recibido, sin uuid4 ni commit propio"
ola = "C"
estado = "hecha"
sala = "derechos_arco"
depende_de = ["ADPA-01", "ADPA-05", "RM-02", "SEC-09"]
propiedad = ["features/derechos_arco/derechos_arco_service.py", "alembic/versions/20261108_derechos_tenant_texto.py", "tests/test_der03_tenant_solicitud.py", "features/derechos_arco/domain/models.py", "api/routers/arco_router.py", "tests/test_derechos_arco_esquema.py", "tests/test_arco_seguro.py", "tests/test_e2e_flujo_completo.py"]
crea = ["alembic/versions/20261108_derechos_tenant_texto.py", "tests/test_der03_tenant_solicitud.py"]
siembra = ["features/derechos_arco/derechos_arco_service.py#DER-01", "features/derechos_arco/derechos_arco_service.py#DER-02"]
arbitro = "pytest tests/test_der03_tenant_solicitud.py + suite completa, con PostgreSQL real y RLS con lopdp_app; mutación documentada; FUSION_ALEMBIC antes de fusionar"
rastros = ["¤seguridad-tenant", "¤rbac-tenant"]
+++

# DER-03 · La solicitud ARCO queda en su organización

**Origen.** Hallazgo de EP-10 del 2026-11-08. En main, `crear_solicitud_arco`:
- fija `tenant_id=uuid4()` al azar e ignora el tenant que recibe (líneas 43-47), así que la solicitud queda huérfana, fuera de la organización y de su RLS;
- la columna `derechos_arco_solicitudes.tenant_id` es UUID, pero los tenants son texto (por ejemplo `ep-org-micro`);
- hace `session.commit()` por su cuenta (línea 56), y rompe la transacción de quien la llama.

## Entrega
- `crear_solicitud_arco` usa el tenant recibido o el de la sesión, nunca uno generado, y no hace commit: lo hace quien la llama.
- Migración `20261108_derechos_tenant_texto.py`: `tenant_id` pasa al mismo tipo que `tenants.id`, con su clave foránea y su política RLS. Revisa que no haya filas huérfanas; si las hay, la migración se detiene y las informa, sin borrarlas.

## Pruebas (`tests/test_der03_tenant_solicitud.py`)
1. La solicitud creada queda con el tenant recibido y se lee por la compuerta en ese tenant.
2. Desde otro tenant no se ve (RLS con `lopdp_app`).
3. La compuerta no hace commit: un rollback de quien la llama deja la tabla sin la fila.

**Mutación:** volver a `uuid4()` hace fallar la prueba 1.

**Orden.** Posee el archivo entero de la compuerta, así que DER-01 y DER-02, que tienen secciones en ese archivo, van después.

## No hagas
- No te conectes a producción ni a Cloud SQL.

## Ajustes del Arquitecto (2026-11-08)
1. `features/derechos_arco/domain/models.py`: la columna del ORM (`UUID(as_uuid=True)`, línea 29) pasa a `String`, igual que `tenants.id`.
2. DER-03 deja vacías las marcas `#DER-01` y `#DER-02` en la compuerta. Sus líneas de `_exenciones_propiedad.txt` se retiraron al declarar la siembra, porque el verificador lo exige.
3. RLS: la migración quita la política de 20261020 (que compara `tenant_id::text`) y la vuelve a crear sobre la columna de texto, sin cast y con FORCE. La prueba 2 corre con `lopdp_app` después de la migración.
4. FUSION_ALEMBIC: la migración va cuarta, sobre BIB-117 → DEMO-00; las de DER-01 y DER-02 van después. Ninguna llamada actual depende del commit que se quita.

**Validada por el Arquitecto ADPA (2026-11-08).**

**Ampliación (Tech Lead, 2026-11-08, a pedido de nube-backend).** La migración pasa `tenant_id` a texto con FK a `tenants`, así que la ficha asume tres archivos de fichas hechas (SEC-08, SEC-09, ADPA-01, RM-02): `arco_router.py` (`tenant_id` como `str` en el esquema y en el alta, que pasa por la compuerta `crear_solicitud_arco`), `test_derechos_arco_esquema.py` (`varchar` y tenants sembrados) y `test_arco_seguro.py` (compara con el tenant en texto).

**Riesgos de la migración (CTO, 2026-11-08). Obligatorios antes de escribir código.**
1. **Huérfanos.** Producción puede tener solicitudes con un `tenant_id` inventado por `uuid4`, que es justo el defecto que corrige esta ficha. Antes de crear la FK, la migración cuenta las filas cuyo `tenant_id` no existe en `tenants`. Si hay alguna, aborta con un mensaje claro que diga cuántas son, sin borrar, reasignar ni modificar ninguna. Qué hacer con ellas lo deciden el propietario y el DPO, porque son solicitudes de titulares con plazo legal. Prueba: con un huérfano sembrado, la migración falla con ese mensaje y la tabla no cambia.
2. **Expand/contract (GCP-07).** `alter_column(type_=...)` rompe la revisión anterior y `verificar_migracion_compatible.py` lo rechaza. La ficha lo resuelve en dos fases:
   - **Expandir:** columna nueva de texto, copia de los datos y FK `NOT VALID` con `VALIDATE CONSTRAINT` aparte.
   - **Contraer:** retirar la columna vieja en una migración posterior marcada con `CONTRACCION = True`.
   - Si una sola migración resulta imposible, documentar el motivo en el PR y llevarle al CTO la excepción justificada antes de fusionar.
   - El verificador de migraciones debe quedar en 0 o con la excepción aceptada.

**Segunda ampliación (Tech Lead, 2026-11-08).** `tests/test_e2e_flujo_completo.py` (de SEC-07 y SEC-08, hechas) hace POST /arco con un tenant que no existe y confirma la transacción, así que deja una solicitud huérfana en cada corrida y, con la FK, recibe un 500. La ficha lo asume: siembra dos tenants de texto y al final borra lo que creó. La contracción (retirar la columna uuid y el trigger) queda para DER-04.
