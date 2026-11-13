+++
id = "EVI-03"
titulo = "Lectura de evidencias por el auditor: ve todas las de su tenant, sin escribir atributos"
ola = "backlog"
estado = "en_curso"
sala = "evidencias"
depende_de = ["EVI-02", "ORG-22"]
propiedad = ["features/evidencias/domain/models.py", "features/evidencias/domain/vigencia.py", "features/evidencias/evidencias_service.py#EVI-03", "api/routers/evidencias_inspeccion.py", "tests/matriz/roles/auditor.py#EVI-03", "tests/matriz/EVI-03.py", "tests/test_evi03_auditor_lee_evidencias.py"]
crea = ["tests/matriz/EVI-03.py", "tests/test_evi03_auditor_lee_evidencias.py"]
arbitro = "pytest tests/test_evi03_auditor_lee_evidencias.py + tests/test_evidencias_vigencia.py + tests/test_matriz_permisos.py contra PostgreSQL 16 local (RLS con lopdp_app); mutaciones m1 a m6"
rastros = ["¤evidencias", "¤rbac-tenant"]
+++

# EVI-03 · Lectura de evidencias por el auditor: ve todas las de su tenant, sin escribir atributos

Diseño del Arquitecto ADPA (2026-11-12), medido en el #678 (EVI-02), pedido del CTO: `ROLES_CONSULTA_DOCUMENTOS` y el CHECK `ck_evidencias_atributos_roles` dejan fuera al `auditor`, y un auditor que no ve las evidencias ni el paquete de inspección no puede auditar.

**Hallazgo de seguridad.** En `api/routers/evidencias_inspeccion.py`, `PUT /documentos/{id}/atributos` (`definir_atributos`, que fija `vence_en` y `visible_para`) usa el mismo `_consulta = require_role(*ROLES_CONSULTA_DOCUMENTOS)` que las lecturas. Si se agrega el auditor a `ROLES_CONSULTA_DOCUMENTOS` sin separar esto, el auditor podría escribir atributos. Esta ficha separa los roles de lectura de los de escritura.

**Criterio de `visible_para` (recomendado por el Arquitecto; lo confirma el CTO).** El auditor ve **todas** las evidencias de su tenant, igual que el DPO, sin importar `visible_para`: una auditoría independiente no puede depender de lo que el auditado decide mostrarle, y es la misma lógica que hoy obliga a que el DPO esté siempre (`ck_evidencias_atributos_dpo`). Con esto **no hace falta migración**: el CHECK `ck_evidencias_atributos_roles` no cambia, porque el auditor no se lista en `visible_para`. Alternativa no recomendada, si el CTO quisiera poder restringir al auditor por documento: migración `evi03_visibilidad_auditor.py` (sin fecha) que amplía el CHECK, cambia el DEFAULT y cuenta e informa las filas existentes; iría después de la de ORG-22 y en otra tanda.

## Entrega
- `features/evidencias/domain/models.py`: `ROLES_CONSULTA_DOCUMENTOS` suma `auditor`; nuevo `ROLES_DEFINIR_ATRIBUTOS` con los cuatro de hoy, sin auditor.
- `features/evidencias/domain/vigencia.py`: `ROLES_VISIBILIDAD_POSIBLES` deja de derivarse de `ROLES_CONSULTA_DOCUMENTOS` y queda con los cuatro explícitos (si no, el DEFAULT incluiría al auditor y el CHECK de la base rechazaría el INSERT); `puede_ver(rol, visibles)` devuelve `True` si `rol in ROLES_VEN_TODO = {"dpo", "auditor"}`.
- `api/routers/evidencias_inspeccion.py`: `definir_atributos` usa `require_role(*ROLES_DEFINIR_ATRIBUTOS)`; las lecturas (atributos, archivo, paquete-inspeccion) siguen con `_consulta`. `api/routers/evidencias.py` ya usa `ROLES_CONSULTA_DOCUMENTOS`, no cambia y no entra en la propiedad.
- `tests/matriz/EVI-03.py` (crea): hoy `tests/matriz` no tiene filas de evidencias, y `auditor.py` solo puede declarar `id_accion` que existan. Esta ficha crea las filas de las lecturas de evidencias (`/evidencias/atributos`, archivo, `paquete-inspeccion`) y de la `PUT` de atributos, con los roles de hoy; el auditor queda con las lecturas en `True` y la `PUT` en `False`.
- `tests/matriz/roles/auditor.py` (de ORG-22, que lo crea sin claves de evidencias): este PR le añade las claves de las filas nuevas (lecturas `True`, `PUT` `False`). Como las filas no existían, ORG-22 no puede dejarlas en `False`: corrige lo dicho antes (CTO, 2026-11-12). Sin choque: EVI-03 depende de ORG-22.
- **Fuera de alcance:** `responsable_area` va en otra ficha (su regla es de ámbito, `AREA_SCOPED_ROLES`, y exige un filtro nuevo documento → vínculo → área); el frontend (si el menú de evidencias se muestra al auditor): si cambia la pantalla, pasa por UX/UI.

## Pruebas (cada una con su mutación)
- **m1:** el auditor lista y descarga un documento con `visible_para = ['dpo']` → 200. Mutación: quitar `auditor` de `ROLES_VEN_TODO` → rojo.
- **m2:** el auditor hace la `PUT` de atributos → 403. Mutación: volver a usar `_consulta` en `definir_atributos` → rojo (la del hallazgo de seguridad).
- **m3:** atributos por defecto de un documento nuevo, sin auditor en `visible_para` → el `INSERT` pasa el CHECK. Mutación: volver a derivar `ROLES_VISIBILIDAD_POSIBLES` de `ROLES_CONSULTA_DOCUMENTOS` → el CHECK lo rechaza → rojo.
- **m4:** el auditor de A no ve evidencias de B (RLS). Mutación: quitar `fijar_contexto_rls` en la lectura → rojo.
- **m5:** `paquete-inspeccion` para el auditor → 200 y el mismo contenido que ve el DPO. Mutación: filtrar el paquete por `visible_para` para el auditor → rojo.

- **m6 (defensa en profundidad de la RLS, CTO 2026-11-12):** m4 sola no prueba la RLS, porque el `WHERE d.tenant_id` la tapa. Prueba aparte: con la sesión del tenant A (`lopdp_app`, contexto RLS fijado) un `SELECT` directo sobre `evidencias_atributos` **sin filtro de tenant** no devuelve filas del tenant B. Mutación: quitar `_fijar_rls` (o `fijar_contexto_rls`) de la lectura → rojo. Así la RLS y el filtro tienen cada uno su propia prueba.

## Límites
- Sin escritura para el auditor; sin migración (salvo la alternativa no recomendada). Pruebas contra PostgreSQL 16 local; nunca producción.
- Dueñas previas: `models.py` → EVI-01 (hecha); `vigencia.py` y `evidencias_inspeccion.py` → EVI-02; `tests/matriz/roles/auditor.py` → ORG-22, que lo crea. Las dos están en `depende_de`.
