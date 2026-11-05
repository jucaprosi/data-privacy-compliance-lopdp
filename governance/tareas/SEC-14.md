+++
id = "SEC-14"
titulo = "El frontend no publica mapas de fuente ni secretos en variables públicas"
ola = "indep"
estado = "pendiente"
sala = "frontend, pruebas"
depende_de = []
propiedad = ["scripts/verificar_bundle_frontend.py", "tests/test_sec14_frontend_sin_mapas.py"]
arbitro = "pytest tests/test_sec14_frontend_sin_mapas.py + suite completa + vigilantes"
rastros = ["¤seguridad", "¤arbitro"]
+++
# SEC-14 · El frontend no publica mapas de fuente ni secretos en variables públicas

**Origen.** Revisión de la constitución de la reventa en la nube contra los diez requisitos de una aplicación vendible, 2026-11-04. Hoy `frontend/next.config.ts` no activa `productionBrowserSourceMaps` y Next.js no publica mapas de fuente por defecto, así que el requisito se cumple; pero nada impide activarlo por descuido. Esta tarea pone el árbitro.

**Contrato:** `governance/especificaciones/SEC-14.md`.

## Entrega
- Prueba estática `tests/test_sec14_frontend_sin_mapas.py`, sin compilar: falla si alguna configuración de Next (`frontend/next.config.ts` y, cuando exista, `frontend/next.config.cloudrun.ts` de GCP-03) activa `productionBrowserSourceMaps`, o si una variable `NEXT_PUBLIC_*` usada en `frontend/src` tiene nombre de secreto.
- Script `scripts/verificar_bundle_frontend.py` para después de `npm run build`: falla si `frontend/.next/static` contiene archivos `.map` o comentarios `sourceMappingURL`, o cadenas con forma de credencial.

## Decisiones asumidas
- Las variables públicas de identidad del modo de desarrollo (`NEXT_PUBLIC_USER_*`, `NEXT_PUBLIC_TENANT_ID`) y `NEXT_PUBLIC_GOOGLE_CLIENT_ID` no son secretos: el identificador de cliente OAuth es público por diseño.
- Conectar el script al workflow del CI es gobernanza reservada: lo decide y aplica el propietario («Sin agente» de los briefs).

## Pruebas
- `pytest tests/test_sec14_frontend_sin_mapas.py` comprueba las dos reglas estáticas y, sobre una carpeta de compilación simulada, que el script detecta un `.map` y una cadena con forma de clave.
