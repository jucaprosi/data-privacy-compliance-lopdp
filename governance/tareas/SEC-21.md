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
- **`SALTOS_PROXY_CONFIABLES = n`:** cuántas entradas de proxies de confianza se descartan por la derecha.
  - En la nube (con `K_SERVICE`) es obligatoria: si falta o no es un entero ≥ 0, el arranque falla, como en SEC-17.
  - Fuera de la nube vale 0 por defecto.
  - Detrás del balanceador es n=1, como variable del servicio en el brief de GCP, que aplica el propietario.
- **Regla de `ip_cliente(scope)`:**
  1. Si hay varias cabeceras X-Forwarded-For, se unen en orden antes de dividir; hoy `_cabeceras()` se queda con la última.
  2. Se separa por comas y se quitan espacios y entradas vacías; queda E.
  3. El candidato es E[len(E)-1-n]. Lo que antepone el cliente queda a la izquierda y nunca se lee.
  4. Con n=0 no hay proxy y `scope["client"]` es el par real, de confianza: se usa la última entrada de XFF si existe y es una IP; si no, `scope["client"]`.
  5. Con n>0, falla cerrada: si len(E) ≤ n o el candidato no valida con `ipaddress.ip_address`, se usa la clave común fija `"desconocida"`, nunca la entrada más a la izquierda ni `scope["client"]` (Seguridad, con el matiz del Arquitecto para no romper el entorno local ni el CI).
  6. Las IPv6 se agrupan por /64.
- **Requisito de despliegue, fuera de la propiedad de SEC-21:** el ingress de Cloud Run debe ser `internal-and-cloud-load-balancing`. Si `run.app` queda público con n=1, un atacante entra directo, antepone una IP falsa y rompe el límite. Va en el brief de GCP junto con `SALTOS_PROXY_CONFIABLES=1`. Lo aplica el propietario y lo confirma con un `gcloud run services describe` de lectura. Si hace falta un árbitro, será una ficha de nube aparte, sobre `deploy-gcp.yml` o la plantilla del servicio.
- **Pruebas** (cada una con su mutación):
  - con n=1, «falsa, cliente, balanceador» da «cliente»;
  - el mismo cliente con distintas entradas falsas antepuestas comparte cubeta: la petición 61 da 429;
  - dos clientes detrás del mismo balanceador tienen cubetas distintas;
  - con n>0 y menos entradas de las debidas, o con una entrada inválida, se usa `"desconocida"`;
  - con n=0 y sin XFF, dos `scope["client"]` distintos dan cupos distintos (mutación: devolver `"desconocida"` siempre);
  - con n=0 se toma la última entrada;
  - varias cabeceras XFF se unen en orden;
  - `2001:db8::1` y `2001:db8::2` comparten cupo y `2001:db9::1` no;
  - en la nube, sin la variable o con un valor inválido, el arranque falla.

  Mutaciones: contar desde la izquierda, usar `scope["client"]` o E[0] como respaldo, quedarse solo con la última cabecera y aceptar un n inválido.
- **Despliegue (CTO, 2026-11-09):** `deploy-gcp.yml` despliega con `--set-env-vars`, que reemplaza todas las variables, y se dispara en cada push a main. Hoy el backend no tiene `SALTOS_PROXY_CONFIABLES`, y su ingress es `all`. Si el código se fusionara sin más, el despliegue fallaría al arrancar, y un valor puesto a mano se borraría en el siguiente despliegue.
  - **Entregable de gobernanza reservada:** `governance/apoyo/BRIEF_PROPIETARIO_SEC21_WORKFLOW.md`, con el cambio exacto en `deploy-gcp.yml`: agregar `SALTOS_PROXY_CONFIABLES=0` dentro de `--set-env-vars`. El ingeniero no escribe en `.github/`.
  - **Orden:**
    1. el propietario aplica el workflow con 0;
    2. se fusiona el PR de código;
    3. se crea el balanceador;
    4. se cambia el ingress a `internal-and-cloud-load-balancing`;
    5. se pasa a 1, también en el workflow.
  - El CTO no fusiona el PR de código sin la confirmación escrita del propietario de que aplicó el paso 1.
  - **Árbitro:** con `APP_ENV` de nube (o `K_SERVICE`) y sin la variable, el arranque falla. Hay una prueba con su mutación: aceptar la variable ausente.
- **Evidencia, no árbitro:** cuando exista el balanceador, el propietario anota un XFF real visto en los logs de Cloud Run y el ingress, y confirma n=1.
- **Complemento recomendado, no bloqueante:** una regla de rate limit en Cloud Armor para `/api/v1/entorno`, que el propietario aplica por brief.

Sin `import yaml` ni migración. Lleva revisión de Seguridad; no pasa por UX/UI.
