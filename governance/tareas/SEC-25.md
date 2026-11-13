+++
id = "SEC-25"
titulo = "Cabecera Cache-Control: no-store por defecto en /api/v1"
ola = "backlog"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["GCP-06"]
propiedad = ["app_core/seguridad/no_store.py", "main.py#SEC-25", "tests/test_sec25_no_store.py"]
crea = ["app_core/seguridad/no_store.py", "tests/test_sec25_no_store.py"]
arbitro = "pytest tests/test_sec25_no_store.py + suite completa; mutación: quitar el middleware → rojo"
rastros = ["¤seguridad-tenant"]
+++

# SEC-25 · Cabecera Cache-Control: no-store por defecto en /api/v1

**Origen.** La pidió el CTO el 2026-11-13, porque GCP-06 deja fuera el backend: su caché y el CDN solo cubren lo estático. Modelo previsto: sonnet.

## Entrega
- Un middleware que añade `Cache-Control: no-store` a toda respuesta de `/api/v1/*` que no haya fijado ya su propio `Cache-Control`.
- Las descargas que fijan su propia cabecera (biblioteca, evidencias) se respetan; no se pisan.
- Registro del middleware en la sección `main.py#SEC-25`, usando la constante `CABECERA_NO_STORE` de `app_core/cache`.

## Pruebas
- Una ruta de `/api/v1` sin cabecera del router devuelve `no-store`.
- Una descarga con su propio `Cache-Control` lo conserva.
- Mutación: quitar el middleware → rojo.

**Pendiente de comprobar:** la CSP en modo informe no declara `frame-src blob:`, y el visor de NORM-02 usa un blob. Antes de que la CSP pase a bloquear, una ficha con la configuración de la CSP tiene que añadirlo.
