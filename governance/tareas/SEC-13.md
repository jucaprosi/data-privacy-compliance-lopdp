+++
id = "SEC-13"
titulo = "Límite de peticiones en la API por IP, usuario y organización, con tope de gasto de IA"
ola = "D"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["ENT-02", "SEC-03", "SEC-10"]
propiedad = ["app_core/limites/__init__.py", "app_core/limites/limitador.py", "app_core/limites/politicas.py", "api/middleware/limite_peticiones.py", "main.py#SEC-13", "alembic/versions/20261121_sec13_ventana_peticiones.py", "app_core/errors.py#SEC-13", "tests/test_sec13_limite_peticiones.py"]
arbitro = "pytest tests/test_sec13_limite_peticiones.py + suite completa + vigilantes"
rastros = ["¤seguridad", "¤seguridad-tenant", "¤copiloto-ia"]
+++
# SEC-13 · Límite de peticiones en la API por IP, usuario y organización, con tope de gasto de IA

**Cambio 2026-11-07 (todo en Google Cloud, decisión del propietario):** el limitador vive en Cloud SQL, en una tabla, sin costo. Memorystore no entra: cuesta unos 35 USD/mes y supera el presupuesto de 30 USD/mes. El tope de IA por organización (SEC-13a) usa el mismo mecanismo. **Cuándo pasar a Memorystore:** cuando haya carga medida y la latencia del limitador en Cloud SQL supere su presupuesto; la interfaz de `limitador.py` no cambia.

**Origen.** Revisión de la constitución de la reventa en la nube (`PRD_EVYDENTIA_REVENTA_NUBE.md`) contra los diez requisitos de una aplicación vendible, 2026-11-04: el PRD solo prevé límites para la consulta a la web de la SPDP (`INV_NORMATIVA_SCHEDULED_MONITORING_QUOTA`) y el código no tiene ningún limitador (ninguna respuesta 429 fuera del diseño de DER-02).

**Contrato:** `governance/especificaciones/SEC-13.md` (manda sobre esta ficha en datos, API y aceptación).

## Entrega
- Limitador de ventana deslizante en `app_core/limites/limitador.py` sobre una tabla de Cloud SQL (`ventana_peticiones`: clave, ventana y contador, con UPSERT atómico y limpieza de ventanas vencidas), con una implementación en memoria solo para pruebas. Sin Redis ni Upstash.
- Catálogo de políticas en `app_core/limites/politicas.py`: inicio de sesión, copiloto e IA, emisión de URLs firmadas y API general, con los valores iniciales de la especificación como parámetros.
- Middleware `api/middleware/limite_peticiones.py`, registrado en la sección `#SEC-13` de `main.py`, que responde 429 con `Retry-After` y el código `LIMITE_PETICIONES` (sección `#SEC-13` de `app_core/errors.py`).
- El limitador queda disponible para otras salas por `app_core/limites` (núcleo compartido, no es una sala). DER-02 conserva sus límites del portal público; puede reutilizar este limitador, pero no es dependencia.

## Decisiones asumidas
- Los valores iniciales de la especificación son una propuesta; los ajusta el propietario sin tocar código, por variables de entorno.
- Ante una caída de la base del limitador, la IA **se cierra** (responde 503, para no gastar sin control) y el resto **se abre** (deja pasar y registra un aviso), para no tumbar la aplicación por el limitador.

## Pruebas
- `pytest tests/test_sec13_limite_peticiones.py` comprueba el 429 al superar cada política, el `Retry-After`, la separación por organización (el consumo de una no afecta a otra), el cierre de la IA y la apertura del resto ante la base del limitador caída.
