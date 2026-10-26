+++
id = "MTGE-02"
titulo = "Obligaciones del tratamiento a gran escala: auditoría anual, informe anual, política de privacidad y plazo del DPO"
ola = "D"
estado = "pendiente"
sala = "riesgos_mtge, frontend"
depende_de = ["MTGE-01", "RAT-01", "ENT-02", "RM-00"]
propiedad = ["features/riesgos_mtge/services/obligaciones_engine.py", "features/riesgos_mtge/riesgos_mtge_service.py#MTGE-02", "api/routers/riesgos_mtge_obligaciones.py", "main.py#MTGE-02", "alembic/versions/20261025_gran_escala_obligaciones.py", "tests/test_mtge_obligaciones.py", "frontend/src/components/modules/mtge/ObligacionesGranEscala.tsx", "frontend/src/components/modules/MtgeModule.tsx", "frontend/tests/mtge/obligaciones.spec.ts"]
arbitro = "pytest tests/test_mtge_obligaciones.py contra una rama Neon de revisión (incluido RLS) + suite completa + Playwright de frontend/tests/mtge/obligaciones.spec.ts; prueba de mutación documentada"
rastros = ["¤mtge-granescala", "¤rbac-tenant"]
+++

# MTGE-02 · Obligaciones del tratamiento a gran escala

**Fuente vinculante.** Res. SPDP-SPD-2026-0005-R (véase `MTGE-01` y la entrada F11 de la bibliografía). Lo que exige cuando un tratamiento es de gran escala, además del RAT ampliado (art. 15, lo cubre RAT-01):
- **Art. 16:** privacidad desde el diseño y por defecto antes y durante el tratamiento, según la normativa específica que expida la SPDP.
- **Art. 17:** auditoría interna o externa **al menos cada 12 meses** y cuando cambien la naturaleza, el alcance, los fines, la tecnología o el riesgo; informe conservado **5 años**. Se exime si una certificación vigente lo cubre de forma equivalente.
- **Art. 18:**
  - la política de privacidad identifica los tratamientos a gran escala, con finalidades, categorías de datos, titulares y derechos;
  - **informe anual de cumplimiento**, conservado **5 años**, con control interno, auditorías, revisiones del MTGE, actualizaciones de la EIPD y mejoras.
- **Disposición transitoria:** **90 días** desde la vigencia de la norma para designar y registrar al DPO, salvo quien ya estaba obligado por el art. 4 del RGLOPDP.

## Entrega
- **Registro por organización**, con RLS y migración Alembic (id de revisión de 32 caracteres como máximo):
  - auditorías: fecha, tipo (interna o externa), alcance, auditor, archivo del informe (con el mecanismo de evidencias existente), fecha de vencimiento y certificación equivalente si la hay;
  - informes anuales de cumplimiento: año, archivo y fecha de aprobación;
  - constancia de que la política de privacidad identifica los tratamientos a gran escala: versión, fecha y enlace.
- **Motor de vencimientos (`obligaciones_engine.py`):** si la organización tiene al menos un tratamiento calificado como gran escala por MTGE-01, calcula para cada obligación su estado (al día, por vencer en 30 días, vencida o no aplica), con el artículo que la exige.
- **Plazo del DPO:** los 90 días se cuentan desde la **fecha de vigencia que registre el administrador**. La plataforma no la fija de memoria, porque el número de Registro Oficial no está verificado. Si no hay fecha registrada, el estado es «falta la fecha de vigencia».
- **Conservación:** los informes de auditoría y los anuales no se pueden borrar antes de 5 años desde su fecha; un intento de borrado devuelve 409 con el artículo.
- **Permisos:** escribe el `dpo`; consultan `coordinador` y `admin_organizacion`. Cada alta deja un evento en `audit_events`.
- **Pantalla `ObligacionesGranEscala.tsx`:** lista de obligaciones con su estado, artículo y acción siguiente.
- **Pruebas:**
  - sin tratamientos a gran escala, todo «no aplica»;
  - con uno, auditoría vencida a los 12 meses y un día;
  - certificación equivalente vigente cuenta como al día;
  - el borrado antes de 5 años da 409;
  - RLS entre organizaciones;
  - rol sin permiso da 403.
- **Prueba de mutación documentada:** cambiar el plazo de la auditoría a 13 meses y comprobar que la prueba de vencimiento falla.

## Límites
- No redacta la política de privacidad ni el informe anual; registra que existen y avisa de su vencimiento.
- El art. 16 queda como recordatorio enlazado hasta que la SPDP expida la normativa específica de privacidad desde el diseño.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.
