+++
id = "ORG-14"
titulo = "Datos de la organización para documentos: domicilio, representante legal y contactos"
ola = "backlog"
estado = "pendiente"
sala = "organizacion, frontend"
depende_de = ["ORG-07", "FE-16", "BIB-108"]
propiedad = ["alembic/versions/*_org_datos_documentales.py", "features/organizacion/services/datos_documentales_engine.py", "features/organizacion/organizacion_service.py#ORG-14", "api/routers/organizacion_datos_documentales.py", "frontend/src/lib/organizacion/datosDocumentales.ts", "frontend/src/components/organizacion/DatosDocumentales.tsx", "frontend/src/components/ProjectConfig.tsx#ORG-14", "tests/test_org_14_datos_documentales.py", "frontend/tests/organizacion/datos-documentales.spec.ts", "tests/test_matriz_permisos.py", "tests/test_bib_108_importacion.py"]
arbitro = "pytest tests/test_org_14_datos_documentales.py contra rama Neon propia; npx playwright test tests/organizacion/datos-documentales.spec.ts; suite completa; frontend npm run typecheck y npm run build; verificadores de índice/reparto; mutación documentada"
rastros = ["¤rbac-tenant", "¤arbitro"]
+++

# ORG-14 · Datos de la organización para documentos

**Objetivo.** Que la organización guarde los datos que las plantillas del PMV de Biblioteca necesitan y hoy no existen, para rellenar `organizacion.*` y `representante.*` (`docs/biblioteca-pmv.md`, apartado a).

## Entrega
- Migración nueva con columnas **opcionales** en `tenants`: `direccion`, `ciudad`, `telefono`, `correo_contacto`, `correo_privacidad`, `sitio_web`, `representante_legal_nombre`, `representante_legal_identificacion` y `representante_legal_cargo`. No cambia columnas existentes ni exige valores a organizaciones ya creadas.
- Lectura y edición por la compuerta `organizacion_service.py`, en un router nuevo con `AUTO_REGISTRO = True`. Solo el administrador de la organización edita; la organización sale de la sesión, nunca del cuerpo.
- Formulario «Datos para documentos» en Configuración, con validación de correo, RUC/cédula y URL.
- Un servicio de lectura de solo consulta que Biblioteca (BIB-201) usa por la compuerta para rellenar variables.

## Límites
- No toca `api/routers/organizacion.py` (ORG-13) ni el alta de organizaciones del operador.
- Sin datos reales de personas en pruebas, semillas ni capturas.
- No migra producción.

## Pruebas compartidas (2026-10-27)
- `tests/test_matriz_permisos.py`: añadir las rutas nuevas a la matriz (leer: cualquier usuario de la organización; editar: solo su administrador). Sus otras dueñas (ORG-00, ORG-02, ORG-07, QA-05, RM-03, RM-20) ya están hechas.
- `tests/test_bib_108_importacion.py`: la migración de ORG-14 va tras la del catálogo de BIB-108, así que la prueba debe comprobar solo que hay una única cabeza, sin fijar cuál (ya lo vigila `tests/test_alembic_una_cabeza.py`). Por eso ORG-14 depende de BIB-108.

## Criterios de aceptación
1. Una organización existente sin estos datos sigue funcionando; la Biblioteca los muestra como faltantes.
2. Un usuario de otra organización no lee ni edita estos datos (prueba cruzada entre dos organizaciones).
3. Un usuario sin rol de administración de la organización puede leer, pero no editar.
4. Los valores inválidos se rechazan en el servidor con `ErrorNegocio`.

## Árbitro y prueba de mutación
- `pytest tests/test_org_14_datos_documentales.py` contra rama Neon propia y `npx playwright test tests/organizacion/datos-documentales.spec.ts`.
- Mutación decisiva: tomar la organización del cuerpo de la petición en lugar de la sesión: debe fallar la prueba cruzada. Documentar y restaurar antes del cierre.

## Hecho cuando
Todos los criterios pasan con evidencia y la suite sigue en verde con todos los checks terminados; solo el coordinador cierra la ficha tras integrar su PR.
