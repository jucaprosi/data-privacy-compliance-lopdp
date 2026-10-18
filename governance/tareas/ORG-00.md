+++
id = "ORG-00"
titulo = "Renombrar el rol «encargado» a «coordinador» (clave, datos, API e interfaz)"
ola = "D"
estado = "pendiente"
sala = "organizacion"
depende_de = ["RM-00", "RM-01", "RM-03", "RM-07", "RM-08", "RM-09", "RM-10", "RM-13", "RM-16", "SEC-04", "SEC-05", "TEST-01", "FE-01", "FE-02", "FE-03", "FE-04", "FE-05", "FE-06", "FE-07", "FE-08"]
propiedad = ["api/rbac.py", "api/routers/roadmaps.py", "api/routers/roadmaps_asignacion.py", "api/routers/roadmaps_auditoria.py", "features/organizacion/domain/roles.py", "features/organizacion/services/regla_tamano_engine.py", "features/organizacion/services/sod_engine.py", "features/organizacion/services/solicitud_responsable_engine.py", "api/routers/areas_responsable_requests.py", "alembic/versions/*_rol_coordinador.py", "governance/contratos/hoja_de_ruta.openapi.json", "governance/artefactos/PRD.md", "tests/test_rol_coordinador.py", "tests/test_encargado_responsable_tamano.py", "tests/test_evidencia_filtro_rol.py", "tests/test_evidencia_http.py", "tests/test_matriz_permisos.py", "tests/test_organizacion_api.py", "tests/test_rbac_rules.py", "tests/test_roadmap_auditoria_consulta.py", "tests/test_roadmap_schema.py", "tests/test_roadmap_tarea_asignacion.py", "tests/test_roadmap_tarea_edicion.py", "tests/test_responsable_requests.py", "frontend/src/types/roadmap.ts", "frontend/src/lib/roadmap/mockServer.ts", "frontend/src/lib/roadmap/cliente.mock.test.ts", "frontend/src/components/modules/roadmap/admin/RolesTab.tsx", "frontend/src/components/modules/roadmap/admin/ConfiguracionTab.tsx", "frontend/src/components/modules/roadmap/admin/errores.ts", "frontend/src/components/modules/roadmap/evidencia/EvidenciaPanel.tsx", "frontend/src/components/modules/roadmap/evidencia/reglas.ts", "frontend/src/components/modules/roadmap/olas/permisos.ts", "frontend/src/app/harness-roadmap/admin/HarnessAdmin.tsx", "frontend/src/app/harness-roadmap/evidencia/HarnessEvidencia.tsx", "frontend/src/app/harness-roadmap/evidencia/page.tsx", "frontend/src/app/harness-roadmap/olas/HarnessOlas.tsx", "frontend/src/app/harness-roadmap/planeacion/HarnessPlaneacion.tsx", "frontend/tests/auth/identidad.spec.ts", "frontend/tests/roadmap/admin.spec.ts", "frontend/tests/roadmap/evidencia.spec.ts", "frontend/tests/roadmap/integracion.spec.ts", "frontend/tests/roadmap/olas.spec.ts", "frontend/tests/roadmap/planeacion.spec.ts", "frontend/tests/tamano/ficha.spec.ts"]
arbitro = "pytest tests/test_rol_coordinador.py tests/test_matriz_permisos.py + suite completa; Playwright de frontend/tests/roadmap, tests/auth y tests/tamano; tsc --noEmit y next build"
rastros = ["¤rbac-tenant", "¤frontend-ide"]
+++

# ORG-00 · Renombrar el rol «encargado» a «coordinador» (clave, datos, API e interfaz)

**Objetivo.** El rol que hoy se llama `encargado` pasa a llamarse `coordinador`: describe mejor su función (coordina el programa de protección de datos de la organización, designa y supervisa a los responsables de área) y deja de chocar con el «encargado del tratamiento» de la LOPDP (Art. 4), que es un **tercero** que trata datos por cuenta del responsable. Decisión del propietario (2026-10-18). Es un renombrado **estructural**: la clave del rol está en la base de datos, en la API y en la interfaz.

## Entrega
- La clave `coordinador` sustituye a `encargado` en el enum `Role`, en las rutas con `require_role`, en los esquemas y en la interfaz (tipo, etiqueta visible «Coordinador», permisos y paneles).
- Migración `*_rol_coordinador.py`: actualiza los datos (`UPDATE user_tenant_roles SET role = 'coordinador' WHERE role = 'encargado'`), reemplaza la restricción `ck_utr_role` y **reescribe las funciones de los dos triggers que nombran el rol** (`fn_utr_dpo_sod` y `fn_utr_encargado_responsable`), renombrando el segundo. El `downgrade` lo revierte. **No edita las migraciones anteriores**: la historia no se reescribe.
- Compatibilidad: `ROLE_ALIASES` de `api/rbac.py` acepta `encargado` como alias de `coordinador` en `X-Role` y en los cuerpos que lo usan, para no romper clientes ya desplegados. El alias se retira en una tarea posterior, cuando no quede ninguno.
- El contrato congelado de la hoja de ruta se regenera con `scripts/exportar_contrato_hoja_ruta.py`.
- PRD: sustituir el nombre del rol y añadir el glosario «Equivalencias con la LOPDP» (`coordinador` ejerce la función del responsable del tratamiento; el encargado del tratamiento es un tercero). ORG-01 amplía esa sección.
- **No se renombra el sentido legal.** «Encargado del tratamiento», «contrato de encargado» y «acceso del encargado» (corpus normativo `features/regulacion_rag`, guías de implementación, vocabulario del copiloto en `features/ai_copilot`, textos de `frontend/src/lib/normativas.ts`) quedan igual: esos archivos **no** son de su propiedad y una prueba comprueba que conservan la palabra.
- Pruebas: la matriz de permisos y todas las que hoy usan `encargado` pasan con `coordinador`; el alias funciona; la migración (ejecutando su SQL real dentro de una transacción que se revierte) convierte los datos, deja los dos triggers con el mismo comportamiento y se deshace; no queda ninguna aparición del rol antiguo fuera del alias y de las migraciones históricas.

## Orden de despliegue (ventana de cambio)
La migración y el código van juntos: con la migración aplicada y el código antiguo, el rol `coordinador` no se reconoce; con el código nuevo y los datos sin migrar, quien tenga el rol antiguo pierde permisos hasta migrar. Por eso el informe da la consulta previa (cuántas filas tienen `encargado` en producción) y el orden: fusionar y aplicar la migración seguidas. Hoy producción tiene una sola organización.

## Límites
- No cambia ninguna regla ni ningún permiso (eso son ORG-01 y siguientes).
- Las especificaciones de otras tareas que mencionan el rol las actualiza el coordinador al integrar: no son de su propiedad.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
