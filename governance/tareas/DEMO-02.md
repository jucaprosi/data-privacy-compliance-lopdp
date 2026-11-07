+++
id = "DEMO-02"
titulo = "Ciclo de sesión demo: entrar, tope, reemplazo, terminar, estado y prueba de punta a punta"
ola = "D"
estado = "pendiente"
sala = "demo"
depende_de = ["DEMO-00", "DEMO-01", "DEMO-03"]
propiedad = ["features/demo/domain/vendedores.py", "features/demo/services/entrada_engine.py", "features/demo/services/cierre_engine.py", "api/routers/demo_sesion.py", "tests/test_demo_ciclo.py", "tests/test_demo_punta_a_punta.py"]
arbitro = "pytest tests/test_demo_ciclo.py tests/test_demo_punta_a_punta.py contra una rama Neon de prueba + linter ADPA sin cruces; mutación documentada"
rastros = ["¤demo", "¤rbac-tenant"]
+++

# DEMO-02 · Ciclo de sesión demo: entrar, tope, reemplazo, terminar, estado y prueba de punta a punta

**Por qué.** Varios vendedores usan la demo a la vez sin verse: cada entrada recibe su propia organización, con tope y vencimiento. Va en la última tanda porque necesita `clonar_organizacion_plantilla` (DEMO-03) y el resolutor (DEMO-01) ya fusionados.

## Entrega
- **`domain/vendedores.py`:** lectura de `DEMO_VENDEDORES` (correos separados por comas, comparados en minúsculas y con correo verificado por Google).
- **`services/entrada_engine.py`** (`POST /demo/entrar`): vendedor fuera de la lista ⟹ 403 `DEMO_NO_AUTORIZADO` sin escribir nada ⟹ vence las demos inactivas por más de 60 minutos ⟹ vence la demo anterior del mismo vendedor (motivo `reemplazo`) ⟹ tope de 20 con bloqueo en la misma transacción que el INSERT (lleno ⟹ 409 `DEMO_OCUPADA`) ⟹ `organizacion_service.clonar_organizacion_plantilla` ⟹ sesión con la persona Administrador ⟹ devuelve el cuerpo de `GET /demo/estado`.
- **`services/cierre_engine.py`:** `POST /demo/terminar` marca la sesión y su organización como vencidas (motivo `terminar`); `GET /demo/estado` devuelve el cuerpo de §3 sin correos.
- **`api/routers/demo_sesion.py`:** las tres rutas, `AUTO_REGISTRO = DEMO_MODE`. `entrar` usa `app_core.security.verificar_token_google` (solo lectura).
- **Prueba de punta a punta:** entrar → «Ver como» → terminar → purga (llama al script de DEMO-05) en la rama Neon de prueba del agente.

## Pruebas
- `test_demo_ciclo.py`: dos entradas crean dos tenants y uno no ve los datos del otro; la entrada 21 ⟹ 409; segunda entrada del mismo vendedor vence la primera (401 `DEMO_VENCIDA`); «Terminar» y luego cualquier petición ⟹ 401; reloj simulado a 61 minutos ⟹ 401 y estado `vencida`; correo fuera de la lista ⟹ 403 y ninguna fila nueva.
- `test_demo_punta_a_punta.py`: el recorrido completo y, al final, ninguna fila del tenant purgado.
- Mutación documentada: quitar el bloqueo del tope deja pasar la entrada 21 en la prueba concurrente.

## Límites
- **Contrato congelado (CTO, 2026-11-06):** rutas, cuerpos, códigos 401/403/409 y `X-Role` de `FLUJOS_DEMO_COMERCIAL.md` §3, y las firmas de `demo_service.py` que fija DEMO-00. Si hay que cambiarlos, se para y se consulta a la Coordinadora; las fichas afectadas se ajustan en la misma tanda.
- No toca `features/organizacion/domain/roles.py`, el trigger `fn_utr_dpo_sod`, la RLS, `api/rbac.py` ni `main.py`.
- No edita la compuerta, el dominio común, el repositorio, `app_core/security.py` ni `organizacion_service.py`: los usa. No ejecuta DELETE.

## Fuentes
- PRD, Módulo 9 «Demo comercial» (`governance/artefactos/PRD.md`, PR #432, aprobado por el CTO el 2026-11-06).
- Flujos y contrato de la API: `governance/apoyo/FLUJOS_DEMO_COMERCIAL.md` (§3 congelado por el CTO).
- Corte ortogonal y matriz flujo × archivo del Arquitecto de soluciones ADPA (2026-11-06): ninguna ruta con dos dueños; lo compartido es una compuerta o el contrato de DEMO-00, que las demás solo leen.
- Especificación UX/UI: `governance/apoyo/UX_DEMO_COMERCIAL.md`.
- Decisiones del CTO: rol inicial Administrador; 60 minutos sin actividad; tope de 20 demos activas; `DEMO_VENDEDORES` en Vercel; una sola demo activa por vendedor (motivo `reemplazo`).
