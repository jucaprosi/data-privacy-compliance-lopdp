+++
id = "ORG-24"
titulo = "Ficha de la organización activa: endpoint propio con RUC, naturaleza, nombres del DPO y del implementador y contadores"
ola = "backlog"
estado = "en_curso"
sala = "organizacion"
depende_de = ["ADPA-01", "ADPA-06", "CI-18", "DER-03", "DER-05", "DER-06a", "INC-01", "RM-01"]
propiedad = ["api/routers/organizacion_ficha.py", "features/organizacion/services/ficha_engine.py", "features/organizacion/organizacion_service.py#ORG-24", "app_core/pasillo/derechos_arco.py#ORG-24", "app_core/pasillo/incidentes.py#ORG-24", "features/derechos_arco/derechos_arco_service.py#ORG-24", "features/incidentes/incidentes_service.py#ORG-24", "tests/test_org24_ficha_organizacion.py", "tests/matriz/ORG-24.py", "tests/test_seleccionar_pruebas.py"]
crea = ["api/routers/organizacion_ficha.py", "features/organizacion/services/ficha_engine.py", "tests/test_org24_ficha_organizacion.py", "tests/matriz/ORG-24.py"]
arbitro = "pytest tests/test_org24_ficha_organizacion.py + tests/test_matriz_permisos.py contra PostgreSQL 16 local con lopdp_app (RLS); mutaciones m1 a m6"
rastros = ["¤rbac-tenant"]
+++

# ORG-24 · Ficha de la organización activa: endpoint propio con RUC, naturaleza, nombres del DPO y del implementador y contadores

Diseño del Arquitecto ADPA (2026-11-12), pedido del CTO para FE-25. **No se amplía `/organizacion/cartera`:** esa ruta lista varias organizaciones (una fila por cada tenant del que la persona es miembro) y su docstring (ORG-15) dice «ni datos personales»; `dpo_nombre` e `implementador_nombre` son datos personales y FE-25 muestra solo la organización activa. Meter nombres en la cartera los expondría para todas las organizaciones a la vez. Va en un endpoint propio de la organización activa.

## Datos (sin migración)
- **RUC:** `tenants.ruc_identificacion` (ya existe). **Naturaleza:** `tenants.naturaleza` (ORG-16, ya existe).
- **`nombres_visibles`, `dpo_nombre` e `implementadores`:** `users.nombre`, cruzado con `user_tenant_roles` vigente (`valid_from <= now()` si la tabla lo tiene, igual que la compuerta de roles) para `dpo` y para `implementador`. Contrato (CTO, 2026-11-12): `nombres_visibles: bool`, `dpo_nombre: Optional[str]` e `implementadores: list[str]` ordenada. Si el rol no ve los nombres: `nombres_visibles = false`, `dpo_nombre = null` e `implementadores = []`. La API no devuelve texto de presentación ni un campo que unas veces sea cadena y otras lista.
- **`solicitudes_abiertas` y `solicitudes_vencidas`:** `derechos_arco_solicitudes` con estado distinto de `CONTESTADA` y, para las vencidas, `fecha_vencimiento < now()`. Se lee la fecha guardada y **no se calcula ningún plazo** (LEG-03/REG-01); se devuelve también `plazo_estimado` (`derechos_arco_service.PLAZO_ESTIMADO`).
- **`vulneraciones_registradas`:** total de incidentes registrados del tenant. No se llama «abiertas» porque `incidentes` no tiene columna de estado y la ficha no puede afirmar que lo estén (CTO, 2026-11-12: sería un dato falso en una pantalla de cumplimiento). La ficha «Estado del incidente (abierto/cerrado) y contador de abiertas» (sala incidentes, por el Arquitecto) lo cambiará a `vulneraciones_abiertas`. **`vulneraciones_con_plazo`:** siempre `null` con «plazo_no_definido», porque `features/incidentes/domain/models.py` dice que los plazos de notificación siguen aplazados; cuando INC-02 o REG-01 los definan, otra ficha llena el campo.

## API
`GET /api/v1/organizacion/ficha`, con el tenant del token o de `X-Tenant-ID` (nunca del cuerpo) y cualquier rol vigente del tenant; un no miembro recibe 403. Router propio con `AUTO_REGISTRO = True` y sin tocar `main.py`. No hay OpenAPI publicado de organización (solo `hoja_de_ruta.openapi.json`): el contrato es el modelo Pydantic de respuesta del router.

## Visibilidad de los nombres (decisión del CTO, 2026-11-12; ESTIMADO)

Mientras el abogado no responda, ven los nombres del DPO y del implementador el `admin_organizacion`, el `implementador` y el propio DPO; **cualquier otro rol recibe `nombres_visibles = false`, `null` y `[]`; el texto «No disponible» lo pone el frontend (FE-25)**. **Minimización:** `_nombres` (la consulta de nombres) se llama solo cuando `nombres_visibles(rol)` da `True`; si no, no se consulta. Razón: minimización de datos; abrirlo más adelante es fácil, recoger un dato ya expuesto no. **Esta regla sustituye al ESTIMADO anterior del CTO** (parte del PRD único, l. 59: «cualquier miembro ve solo el nombre»). **Pregunta al abogado (ESTIMADO mientras no responda):** si el nombre del DPO y el del implementador pueden mostrarse a cualquier miembro de la organización. Se implementa en **una sola función** `nombres_visibles(rol)`; su prueba recorre **todos los roles de `ROLES`** (`auditor` y `responsable_area` incluidos) y comprueba que cualquier rol nuevo queda con `nombres_visibles = false` por omisión (lista cerrada de roles que ven, el resto cae al valor por defecto).

## Propiedad y siembra
Las secciones `ORG-24` de `organizacion_service.py`, los dos pasillos y los dos servicios de derechos e incidentes no existían: este PR de gobernanza las siembra (`# === ORG-24 ===` / `# === fin ORG-24 ===`, solo comentarios, precedente de IA-05 y FE-25). No hay archivos enteros ajenos, así que no choca con DER-01 ni con INC-02, que tienen sus propias secciones. `depende_de` vacío: ORG-15 y ORG-16 están hechas; DER-01 e INC-02 no hacen falta (se lee lo que ya existe). Puede ir en cualquier tanda. Después, FE-25 cambia su fuente de `/organizacion/cartera` a `/organizacion/ficha` y muestra «—» hasta que ORG-24 esté fusionada. La fila de la matriz es `tests/matriz/ORG-24.py` (nace aquí); el auditor lo decide `tests/matriz/roles/auditor.py` si ORG-22 ya está, o al llegar ORG-22.

## Pruebas (cada una con su mutación)
- **m1:** el miembro de A pide la ficha con `X-Tenant-ID` de B → 403 y nunca ve datos de B. Mutación: tomar el tenant del cuerpo o quitar `fijar_contexto_rls` → rojo.
- **m2:** la respuesta trae solo nombres; nunca email, cédula ni `user_id` del DPO o del implementador. Mutación: agregar email → rojo.
- **m3:** 2 abiertas, 1 vencida y 1 contestada → abiertas = 2 y vencidas = 1. Mutación: contar `CONTESTADA` como abierta → rojo.
- **m4:** `vulneraciones_con_plazo` es `null` con motivo. Mutación: calcular un plazo de 72 h → rojo.
- **m5:** si falla una compuerta (incidentes no disponible), solo ese campo es `null` con error; la ficha responde 200 con el resto. Mutación: dejar que la excepción tumbe la respuesta → rojo (mismo criterio que la cartera).
- **m6:** `nombres_visibles(rol)` recorre todos los roles de `ROLES`: `admin_organizacion`, `implementador` y `dpo` ven los nombres; `coordinador`, `responsable_area`, `auditor` y cualquier rol nuevo reciben `nombres_visibles = false`, `dpo_nombre = null` e `implementadores = []`. Mutación: invertir la regla o pasar a una lista abierta (por omisión ve) → rojo.

- **m7 (minimización):** con un rol que no ve los nombres, `_nombres` no se ejecuta (se espía la consulta). Mutación: llamarla siempre → rojo.

- **Prueba de `seleccionar_pruebas` (CTO, 2026-11-12):** `tests/test_seleccionar_pruebas.py:136` afirma que tocar `features/incidentes` no necesita node, un hecho del árbol real que ORG-24 vuelve falso (`ficha_engine` usa el pasillo de incidentes y organizacion invoca node). Esta ficha reescribe ese caso con un **MAPA sintético** (una sala sin dependientes que usen node → `False`; otra que sí → `True`), sin depender del grafo real; no vale cambiar «incidentes» por otra sala real. Mutación: que `necesita_node` devuelva siempre `True` → rojo. Dueña previa del archivo: CI-18 (hecha), por eso entra en `depende_de`.

## Límites
- Pruebas contra PostgreSQL 16 local; nunca producción ni el `.env` de la carpeta principal. Sin `import yaml` en pruebas. Sin frontend (FE-25 lo muestra).
