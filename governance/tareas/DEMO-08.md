+++
id = "DEMO-08"
titulo = "Gancho de identidad demo en usuario_verificado()"
ola = "D"
estado = "en_curso"
sala = "pasillo_central"
depende_de = ["DEMO-00", "EP-01", "SEC-15"]
propiedad = ["app_core/security.py#DEMO-08", "tests/test_demo_gancho_identidad.py"]
arbitro = "pytest tests/test_demo_gancho_identidad.py + suite de seguridad existente en verde + linter ADPA sin cruces; mutaciones documentadas"
rastros = ["¤demo", "¤seguridad"]
+++

# DEMO-08 · Gancho de identidad demo en usuario_verificado()

**Proyecto:** EVYDENTIA (Google Cloud). **Sala dueña:** `pasillo_central`. Tanda 54.

**Por qué.** El vendedor no es usuario de la base demo. El servidor traduce su `sub` de Google a la persona activa con un resolutor que solo existe en el proyecto demo. Esta ficha es la única dueña de ese cambio en `app_core/security.py` (H2 del Arquitecto).

## Entrega
- `registrar_resolutor_identidad(fn)` en la sección `DEMO-08`: lanza error si `entorno_actual()` de EP-01 no es `demo` (nunca lee `APP_ENV` por su cuenta) y ante un segundo registro, venga de donde venga. Solo se registra desde `features/demo`, a través de su pasillo.
- En `usuario_verificado()`, tras verificar el token, si hay resolutor registrado devuelve lo que él resuelva; si no, el camino actual sin cambios.
- **Falla cerrado:** si el resolutor lanza una excepción o devuelve `None`, la respuesta es 401 `DEMO_VENCIDA`; nunca cae al camino normal de `usuario_de_identidad`.
- No toca `exigir_arranque_seguro()`: la barrera contra producción es de EP-01.

## Pruebas
- Fuera de `demo` según `entorno_actual()`, registrar el resolutor lanza error (condición a del CTO).
- Sin resolutor registrado, `usuario_verificado()` se comporta igual que antes.
- Un segundo registro lanza error, venga de donde venga.
- Resolutor que lanza una excepción ⟹ 401 `DEMO_VENCIDA`; resolutor que devuelve `None` ⟹ 401 `DEMO_VENCIDA`.
- Mutación: quitar la comprobación del entorno hace fallar la prueba.
- Mutación: quitar el «falla cerrado» pone en rojo la prueba de `None`.

## Límites
- Contrato congelado: rutas, cuerpos y códigos de `FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md` §1.7 y las firmas de `demo_service.py` que fija DEMO-00. Si hay que cambiarlos, para y consulta a Tech Lead.
- No toques `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod`, la RLS ni `main.py`.
- En archivos con secciones `#ID` escribe solo dentro de tus marcas `# --- INICIO <ID> --- … # --- FIN <ID> ---`.
- Nunca uses la base ni el proyecto de producción; solo datos ficticios con correos `.invalid`.

## Fuentes
- `governance/artefactos/PRD_EVYDENTIA_REVENTA_NUBE.md` §5.6 (demo comercial) y §5.6.8 (corte confirmado por el Arquitecto ADPA y el CTO, 2026-11-07).
- `governance/artefactos/INVARIANTS_EVYDENTIA_REVENTA_NUBE.md`, invariantes 60 a 63.
- Flujos y matriz: `governance/apoyo/FLUJOS_Y_MATRIZ_DEMO_EVYDENTIA.md`.
- Interfaz: `governance/apoyo/UX_DEMO_EVYDENTIA.md` (lo que cambia) sobre `governance/apoyo/UX_DEMO_COMERCIAL.md`.
