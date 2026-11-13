+++
id = "DEMO-01"
titulo = "Persona activa y «Ver como»: resolver, 403 si es ajena y auditoría con el vendedor real"
ola = "D"
estado = "en_curso"
sala = "demo"
depende_de = ["DEMO-00", "DEMO-08", "EP-01"]
propiedad = ["features/demo/services/resolutor_engine.py", "features/demo/services/persona_engine.py", "api/routers/demo_persona.py", "tests/test_demo_persona.py"]
arbitro = "pytest tests/test_demo_persona.py + suite de seguridad y de segregación del DPO existente en verde + linter ADPA sin cruces; mutaciones documentadas"
rastros = ["¤demo", "¤seguridad"]
+++

# DEMO-01 · Persona activa y «Ver como»: resolver, 403 si es ajena y auditoría con el vendedor real

**Proyecto:** EVYDENTIA (Google Cloud). **Sala dueña:** `demo`. Tanda 55.

**Por qué.** Es lo que permite enseñar el ciclo completo con una sola persona. El servidor decide la persona; el navegador solo la pide (invariante 61).

## Entrega
- `resolutor_engine.py`: `sub` → persona activa, solo dentro del tenant `es_demo` de la sesión vigente, comprobado en la consulta; vencida → 401; comprueba en **cada petición** que el vendedor sigue en `DEMO_VENDEDORES` (si no, 401 `DEMO_VENCIDA` y sesión vencida); renueva la actividad como mucho cada 60 s.
- `persona_engine.py`: `listar_personas` (lee con las funciones existentes de `app_core/pasillo/organizacion.py`) y `cambiar_persona`; 403 `DEMO_PERSONA_AJENA` si no es de su tenant; `audit_events` con persona y vendedor real.
- `api/routers/demo_persona.py`: `POST /api/v1/demo/persona`, que devuelve el `X-Role` de la persona; registra el resolutor con el gancho de DEMO-08 solo si `entorno_actual()` es `demo` (nada de registrar al importar en cualquier entorno); `AUTO_REGISTRO` solo en `demo`.

## Pruebas
- Pedir una persona de otra organización demo responde 403 (condición b).
- Persona de un tenant que no es `es_demo` ⟹ 403 (invariante 61).
- Sesión vencida ⟹ 401.
- Vendedor retirado de `DEMO_VENDEDORES` con sesión activa ⟹ 401 `DEMO_VENCIDA` y sesión vencida.
- El `X-Role` devuelto coincide con el único rol de la persona en `user_tenant_roles`, y `require_role` sigue autorizando contra la base.
- La auditoría registra persona y vendedor real (condición c).
- Fuera de `APP_ENV=demo`, `/api/v1/demo/*` responde 404.
- Mutación: quitar el filtro por tenant hace fallar la prueba.

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
