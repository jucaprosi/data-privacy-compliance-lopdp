# PLAT-01 · Alta idempotente de organizaciones sintéticas en plataforma_service
`¤sdd` `¤seguridad-tenant` `¤adpa`

## 1. Datos

Sin tablas ni migraciones. Usa `tenants` (con `UNIQUE (ruc_identificacion)`), `users` y `auditoria_plataforma`, que ya existen.

| Archivo | Estado final |
| :--- | :--- |
| `features/plataforma/services/organizacion_sintetica_engine.py` (nuevo) | la lógica de §2 |
| `features/plataforma/plataforma_service.py` | exporta `OrganizacionSintetica`, `asegurar_organizacion_sintetica` y `asegurar_persona_sintetica` |
| `scripts/datos_sinteticos/organizaciones.py` | `_asegurar_tenant` y `_asegurar_usuario` llaman a la compuerta; el módulo no contiene SQL sobre `tenants` ni `users` |
| `tests/test_plat01_organizacion_sintetica.py` (nuevo) | casos de §5 |
| `tests/test_ep03_sembrar_entorno.py` | `TABLAS_DIRECTAS` queda vacío y la prueba pasa a llamarse «la siembra no escribe directo en ninguna tabla» |

**Marca sintética.** Una organización es sintética cuando su `ruc_identificacion` empieza por `999999999` (`PREFIJO_RUC_SINTETICO`, en el engine). Es el prefijo de las tres organizaciones de EP-03 (`9999999990001` a `9999999990003`).

Hecho medido en `origin/main` 5e872a4a:
- `organizaciones.py` inserta en `tenants` con `ON CONFLICT (id) DO NOTHING` y en `users` con un `SELECT` seguido de `INSERT`;
- `plataforma_service.py` solo expone `crear_organizacion_e_invitacion`, que emite invitación y responde 409 si el RUC existe;
- `app_core/entorno/guardias.py` ofrece `entorno_actual()`, `validar_arranque()` y `ENTORNOS_FICTICIOS = ("pruebas", "demo")`;
- `DOMINIO_FICTICIO` vale `example.test` (`scripts/datos_sinteticos/__init__.py`).

## 2. API

Sin rutas HTTP. Interfaz Python de la compuerta:

```python
@dataclass(frozen=True)
class OrganizacionSintetica:
    id: str; nombre_comercial: str; razon_social: str; ruc: str; sector: str; tamano: str

async def asegurar_organizacion_sintetica(session: AsyncSession, datos: OrganizacionSintetica) -> bool:
    """Crea la organización o confirma la existente; devuelve True si la creó."""

async def asegurar_persona_sintetica(session: AsyncSession, tenant_id: str, correo: str, nombre: str) -> tuple[str, bool]:
    """Crea la persona o devuelve la existente; devuelve (user_id, creada)."""
```

Errores (`ErrorNegocio`, registrados en el engine):
- `ENTORNO_NO_SINTETICO`: el entorno no está en `ENTORNOS_FICTICIOS` o `validar_arranque()` falla;
- `RUC_NO_SINTETICO`: el RUC de `datos` no lleva la marca;
- `ORGANIZACION_NO_SINTETICA`: ya existe una fila con ese `id` o ese RUC sin la marca;
- `ORGANIZACION_NO_DISPONIBLE`: `asegurar_persona_sintetica` recibe un `tenant_id` sin la marca.

## 3. Reglas

- **R1 · Entorno primero.** Las dos funciones llaman a `validar_arranque()` y comprueban `entorno_actual() in ENTORNOS_FICTICIOS` antes de la primera consulta. Leen el entorno solo por `app_core/entorno/guardias.py`.
- **R2 · Idempotencia sin carrera.** Organización: `INSERT … ON CONFLICT DO NOTHING RETURNING id` y relectura de la fila por `id` y RUC. Persona: el id es `id_de_usuario(correo)` (sha256 del correo en minúsculas), con `INSERT … ON CONFLICT DO NOTHING` y relectura. Nunca un `SELECT` seguido de `INSERT`.
- **R3 · Solo organizaciones sintéticas.** Si la relectura encuentra una organización sin la marca, la compuerta lanza `ORGANIZACION_NO_SINTETICA` y no escribe nada.
- **R4 · Personas.** El correo se guarda en minúsculas y sin credenciales. Una persona solo se asegura para un `tenant_id` sintético (R3). Valen los correos ficticios de dominio reservado (`example.test`) y las cuentas de quienes prueban leídas del archivo que git ignora. Los roles se conceden después por `organizacion_service.grant_role`, con la lista cerrada `ROLES_VALIDOS`; la compuerta no concede roles de plataforma.
- **R5 · Sin invitación.** Ninguna de las dos funciones crea invitaciones ni envía correos.
- **R6 · Sin superficie HTTP.** Ningún módulo de `api/` ni de `features/*/routes/` importa las dos funciones.
- **R7 · Auditoría.** Cada alta efectiva registra un evento con `registrar_auditoria_plataforma`, con `actor_tipo = "sistema"`, `accion = "alta_sintetica"` (o `"persona_sintetica"`) y `payload = {"origen": "sintetica", "entorno": <APP_ENV>}`, sin correo ni nombre.
- **R8 · Orden con QA-12.** QA-12 depende de PLAT-01 y posee también `tests/test_ep03_sembrar_entorno.py`. PLAT-01 se fusiona primero; QA-12 parte del archivo ya cambiado.
- **R-ADPA · Ortogonalidad ZERAG (`PLAT-01`).** La lógica vive en el engine; `plataforma_service.py` solo la reexporta. `scripts/datos_sinteticos/organizaciones.py` entra por `features.plataforma.plataforma_service`.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** `APP_ENV=pruebas`, **cuando** se llama dos veces con la misma organización, **entonces** hay una fila en `tenants`, la segunda llamada devuelve False y no hay invitaciones. Mutación m1: emitir la invitación hace fallar la prueba. | `tests/test_plat01_organizacion_sintetica.py` |
| **Dado** dos llamadas concurrentes (`asyncio.gather`), **entonces** queda una sola fila. | `tests/test_plat01_organizacion_sintetica.py` |
| **Dado** cada `APP_ENV` fuera de `{pruebas, demo}`, o `demo` con la huella de producción en `DATABASE_URL`, y una sesión que falla en cualquier `execute()`, **entonces** sale `ENTORNO_NO_SINTETICO` antes de la primera consulta. | `tests/test_plat01_organizacion_sintetica.py` |
| **Dado** una organización existente con el mismo id o RUC sin la marca, **entonces** sale `ORGANIZACION_NO_SINTETICA` y la fila queda intacta. Mutación m2: quitar la comprobación de la marca hace fallar la prueba. | `tests/test_plat01_organizacion_sintetica.py` |
| **Dado** un `tenant_id` sin la marca, **cuando** se asegura una persona, **entonces** sale `ORGANIZACION_NO_DISPONIBLE` y no se escribe en `users`. | `tests/test_plat01_organizacion_sintetica.py` |
| **Dado** un alta efectiva, **entonces** `auditoria_plataforma` tiene el evento con origen «sintetica» y su `payload` no contiene el correo ni el nombre. | `tests/test_plat01_organizacion_sintetica.py` |
| **Dado** el árbol de `api/` y `features/*/routes/`, **entonces** ningún archivo importa la compuerta (recorrido AST). | `tests/test_plat01_organizacion_sintetica.py` |
| **Dado** la siembra de EP-03, **entonces** no escribe directo en ninguna tabla y dos corridas dejan los mismos conteos. | `tests/test_ep03_sembrar_entorno.py` |
| **Dado** el árbol con la ficha fusionada, **entonces** la suite completa pasa. | la suite existente |

## 6. Trazabilidad

- Ficha: `governance/tareas/PLAT-01.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Depende de EP-03, ORG-11 y ORG-20, hechas. QA-12 depende de PLAT-01 (R8).
- Pruebas contra el PostgreSQL 16 local, con `exigir_base_de_pruebas()`.
