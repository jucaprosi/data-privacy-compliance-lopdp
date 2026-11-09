+++
id = "SEC-21"
titulo = "Límite por IP en la ruta pública GET /api/v1/entorno"
ola = "backlog"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["SEC-13", "SEC-13a"]
propiedad = ["app_core/limites/politicas.py", "api/middleware/limite_peticiones.py", "tests/test_limite_entorno_publico.py", "governance/apoyo/BRIEF_PROPIETARIO_SEC21_WORKFLOW.md"]
crea = ["tests/test_limite_entorno_publico.py", "governance/apoyo/BRIEF_PROPIETARIO_SEC21_WORKFLOW.md"]
arbitro = "pytest tests/test_limite_entorno_publico.py tests/test_sec13_limite_peticiones.py; mutaciones documentadas; revisión de Seguridad"
rastros = ["¤seguridad"]
+++

# SEC-21 · Límite por IP en /api/v1/entorno

Diseño del Arquitecto ADPA (2026-11-09). `GET /api/v1/entorno` es pública y no lleva token. Hoy cae en `api_general`, de ámbito «usuario». Sin token, la petición se resuelve con una Identidad anónima, así que todos los anónimos comparten una cubeta o quedan mal acotados. La prueba 1 lo confirma.

## Entrega
- **Política:** `Politica("entorno_publico", "ip", 60, MINUTO)`, ajustable con `LIMITE_ENTORNO_PUBLICO` como las demás.
- **Ruta:** en `politicas_de_ruta`, la constante `PREFIJOS_PUBLICOS_IP = ("/api/v1/entorno",)` devuelve `("entorno_publico",)` y se evalúa antes que `api_general`.
- **Clave:** la IP de `ip_cliente()`, corregida según «Saltos de proxy».
- **Fuera de alcance:** health (sigue en `RUTAS_LIBRES`), el router y tablas nuevas. `api/middleware/limite_peticiones.py` sí entra, solo por `ip_cliente()` y la lectura de la variable; sus dueñas, SEC-13 y SEC-13a, están hechas.

## Pruebas (cada una con su mutación)
1. `politicas_de_ruta("/api/v1/entorno", "GET") == ("entorno_publico",)`, también con «/» final. Mutación: quitar el prefijo.
2. Con el limitador en memoria o el PG16 del arnés, la petición 61 desde la misma IP en un minuto da 429 con `politica: "entorno_publico"`, y desde otra IP sigue en 200. Mutación: cambiar el ámbito a «usuario».
3. Con `LIMITE_ENTORNO_PUBLICO=5`, el tope cambia.
4. `/api/v1/health` sigue libre.

## Saltos de proxy (riesgo del CTO; regla del Arquitecto endurecida por Seguridad, 2026-11-09)
Detrás del balanceador externo de GCP, X-Forwarded-For llega como «<IP cliente>, <IP balanceador>». Hoy `ip_cliente()` toma la última entrada, así que todas las políticas de ámbito «ip» (también las de SEC-13) comparten una cubeta. El docstring de `ip_cliente` está mal y se corrige.
- **`PROXIES_CONFIABLES = n`** (propuesta del Tech Lead del 2026-11-09 para conciliar a Seguridad y al CTO; pendiente de su visto bueno). `n` es el número de proxies de confianza delante de la aplicación; cada uno añade una entrada por la derecha de XFF.
  - **n=0:** no hay proxy de confianza. Todo el XFF lo escribe el cliente, así que se ignora y se usa solo `scope["client"]`, o `"desconocida"` si no viene (Seguridad). Es el caso de local, el CI y el arnés, y es el valor por defecto fuera de la nube.
  - **n=1:** Cloud Run hoy, sin balanceador. La infraestructura de Google añade la IP real del cliente como última entrada; es el comportamiento que funciona hoy (CTO).
  - **Con balanceador:** el valor se fija con el XFF real que se vea en los logs, y no se supone de antemano.
  - **En la nube** (`K_SERVICE`) la variable es obligatoria: si falta o no es un entero ≥ 0, el arranque falla. Fuera de la nube vale 0.
- **Regla de `ip_cliente(scope)`:**
  1. Si hay varias cabeceras X-Forwarded-For, se unen en orden antes de dividir; hoy `_cabeceras()` se queda con la última.
  2. Se separa por comas y se quitan espacios y entradas vacías; queda E.
  3. Con n=0 se ignora E.
  4. Con n≥1, el candidato es E[len(E)-n], es decir, la entrada que añadió el proxy de confianza más externo. Lo que antepone el cliente queda a la izquierda y nunca se lee.
  5. Falla cerrada con n≥1: si len(E) < n o el candidato no valida con `ipaddress.ip_address`, se usa la clave común `"desconocida"`, nunca E[0] ni `scope["client"]`.
  6. Las IPv6 se agrupan por /64.
- **Requisito de despliegue, fuera de la propiedad de SEC-21:** el ingress de Cloud Run debe ser `internal-and-cloud-load-balancing`. Si `run.app` queda público con n=1, un atacante entra directo, antepone una IP falsa y rompe el límite. Va en el brief de GCP. El brief tiene que decir que con ingress `all` y el balanceador delante, el valor que cuenta el balanceador es falsificable, porque un atacante puede entrar directo a `run.app` (Seguridad). Lo aplica el propietario y lo confirma con un `gcloud run services describe` de lectura. Si hace falta un árbitro, será una ficha de nube aparte, sobre `deploy-gcp.yml` o la plantilla del servicio.
- **Pruebas** (cada una con su mutación):
  - con n=1 y XFF «1.2.3.4», la clave es 1.2.3.4, como hoy en Cloud Run;
  - con n=1, «falsa, 1.2.3.4» da 1.2.3.4;
  - con n=2, «falsa, cliente, balanceador» da «cliente»; dos clientes detrás del mismo balanceador tienen cubetas distintas, y el mismo cliente con distintas entradas falsas comparte cubeta (la petición 61 da 429);
  - con n=0, dos peticiones desde el mismo `scope["client"]` con XFF distintos comparten cubeta (mutación: leer XFF con n=0);
  - con n=0 y sin XFF, dos `scope["client"]` distintos dan cupos distintos (mutación: devolver `"desconocida"` siempre);
  - con n≥1 y menos entradas que n, o con una entrada inválida, se usa `"desconocida"`;
  - varias cabeceras XFF se unen en orden;
  - `2001:db8::1` y `2001:db8::2` comparten cupo y `2001:db9::1` no;
  - en la nube, sin la variable o con un valor inválido, el arranque falla.

  Mutaciones: contar desde la izquierda, usar `scope["client"]` o E[0] como respaldo con n≥1, quedarse solo con la última cabecera y aceptar un n inválido.
- **Evidencia, no árbitro:** cuando exista el balanceador, el propietario anota un XFF real visto en los logs de Cloud Run y el ingress, y fija el valor.
- **Complemento recomendado, no bloqueante:** una regla de rate limit en Cloud Armor para `/api/v1/entorno`, que el propietario aplica por brief.

Sin `import yaml` ni migración. Lleva revisión de Seguridad; no pasa por UX/UI.
