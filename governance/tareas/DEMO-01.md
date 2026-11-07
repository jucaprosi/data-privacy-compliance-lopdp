+++
id = "DEMO-01"
titulo = "Identidad demo: resolutor de persona, «Ver como» y barrera de arranque contra producción"
ola = "D"
estado = "pendiente"
sala = "demo, pasillo_central"
depende_de = ["DEMO-00", "SEC-03", "SEC-07", "SEC-15", "ENT-02"]
propiedad = ["app_core/security.py#DEMO-01", "features/demo/services/resolutor_engine.py", "features/demo/services/persona_engine.py", "api/routers/demo_persona.py", "tests/test_demo_identidad.py", "tests/test_demo_arranque.py"]
arbitro = "pytest tests/test_demo_identidad.py tests/test_demo_arranque.py + suite de seguridad y de segregación del DPO existente en verde + linter ADPA sin cruces; mutaciones documentadas"
rastros = ["¤demo", "¤seguridad", "¤rbac-tenant"]
+++

# DEMO-01 · Identidad demo: resolutor de persona, «Ver como» y barrera de arranque contra producción

**Por qué.** El vendedor no es un usuario de la base demo: `usuario_de_identidad` responde 403 a quien no está en `users`. En modo demo, después de verificar el token de Google, el servidor **traduce** la identidad del vendedor a la persona ficticia activa de su sesión (un `users.id` con un solo rol). A partir de ahí `roles_activos`, `X-Role`, la RLS, la segregación del DPO y el trigger `fn_utr_dpo_sod` funcionan sin cambios.

**Dueña única de `app_core/security.py`** para la demo. La barrera va en `exigir_arranque_seguro()` y no en un router, porque `registrar_routers` de `main.py` captura los errores de importación de los routers y la API seguiría arrancando.

## Entrega
- **`app_core/security.py#DEMO-01`:**
  - `registrar_resolutor_identidad(fn)`. `app_core` no importa `features/demo` (inversión de dependencia).
  - `usuario_verificado()` consulta el resolutor registrado, si lo hay, después de `verificar_token_google`.
  - En `exigir_arranque_seguro()`: `DEMO_MODE=1` con `apunta_a_produccion()` verdadero hace fallar el arranque. El resto de la función no cambia (el modo `headers` sigue prohibido en la nube).
- **`services/resolutor_engine.py`:** `sub` → persona activa, **solo** dentro del tenant `es_demo` de su sesión vigente; sesión vencida al usarla ⟹ 401 `DEMO_VENCIDA` y marca la sesión; renueva `ultima_actividad` como máximo una vez cada 60 segundos. Usa `repo/sesiones_repo.py` y `domain/sesion.py` de DEMO-00.
- **`services/persona_engine.py`:** «Ver como». Persona ajena ⟹ 403 `DEMO_PERSONA_AJENA`. Audita `DEMO_CAMBIO_PERSONA` con la persona y el **correo del vendedor real** por `app_core/audit.py`.
- **`api/routers/demo_persona.py`:** `POST /demo/persona`, que devuelve el `X-Role` que el frontend debe usar. `AUTO_REGISTRO = DEMO_MODE`; al importarse registra el resolutor. `main.py` no se toca.

## Controles de seguridad obligatorios (revisión de la Coordinadora, 2026-11-06)
1. `registrar_resolutor_identidad` lanza `RuntimeError` si `DEMO_MODE` no es `1`, si `apunta_a_produccion()` es verdadero o si ya hay un resolutor (condición a del CTO).
2. El resolutor solo devuelve personas cuyo `tenant_id` tiene `es_demo = true` y coincide con el de la sesión vigente del vendedor; lo comprueba la consulta, no solo el código (condición b).
3. La auditoría lleva siempre al vendedor real (condición c).
4. `DEMO_MODE=1` con la base de producción hace fallar el arranque (reutiliza `apunta_a_produccion()`, SEC-15).
5. Sin `DEMO_MODE`: `/demo/*` responde 404 y no hay resolutor.
6. `demo_sesiones` no sale en ninguna respuesta; los correos de los vendedores no salen del servidor.
7. CORS del backend demo: solo el origen del frontend demo (variable de despliegue, DEMO-07).

## Pruebas
- `test_demo_arranque.py` (aísla las variables de entorno para no romper las pruebas de arranque existentes): `DEMO_MODE=1` con el host de producción ⟹ error; sin `DEMO_MODE` ⟹ `registrar_resolutor_identidad` lanza error y `/demo/persona` 404; segundo registro ⟹ error.
- `test_demo_identidad.py`: persona de otra organización o de un tenant sin `es_demo` ⟹ 403 `DEMO_PERSONA_AJENA`; cambio de persona ⟹ devuelve el `X-Role` y la auditoría tiene el correo del vendedor; sesión vencida ⟹ 401 `DEMO_VENCIDA`.
- Las pruebas de segregación del DPO y de RLS siguen en verde.
- Mutaciones documentadas: quitar `es_demo` del resolutor rompe «persona ajena»; quitar la barrera de `exigir_arranque_seguro()` rompe su prueba.

## Límites
- **Contrato congelado (CTO, 2026-11-06):** rutas, cuerpos, códigos 401/403/409 y `X-Role` de `FLUJOS_DEMO_COMERCIAL.md` §3, y las firmas de `demo_service.py` que fija DEMO-00. Si hay que cambiarlos, se para y se consulta a la Coordinadora; las fichas afectadas se ajustan en la misma tanda.
- No toca `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod`, la RLS, `api/rbac.py` ni `main.py`.
- No edita la compuerta, el dominio ni el repositorio de DEMO-00: los usa.
- No crea organizaciones ni sesiones (DEMO-02) y no ejecuta DELETE.

## Fuentes
- PRD, Módulo 9 «Demo comercial» (`governance/artefactos/PRD.md`, PR #432, aprobado por el CTO el 2026-11-06).
- Flujos y contrato de la API: `governance/apoyo/FLUJOS_DEMO_COMERCIAL.md` (§3 congelado por el CTO).
- Corte ortogonal y matriz flujo × archivo del Arquitecto de soluciones ADPA (2026-11-06): ninguna ruta con dos dueños; lo compartido es una compuerta o el contrato de DEMO-00, que las demás solo leen.
- Especificación UX/UI: `governance/apoyo/UX_DEMO_COMERCIAL.md`.
- Decisiones del CTO: rol inicial Administrador; 60 minutos sin actividad; tope de 20 demos activas; `DEMO_VENDEDORES` en Vercel; una sola demo activa por vendedor (motivo `reemplazo`).
