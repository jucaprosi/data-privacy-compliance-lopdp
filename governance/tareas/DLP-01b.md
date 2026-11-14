+++
id = "DLP-01b"
titulo = "Descubrimiento DLP: todo escaneo tiene autor (creado_por obligatorio con migración nueva)"
ola = "D"
estado = "en_curso"
sala = "dlp_discovery"
depende_de = ["DLP-01"]
propiedad = ["alembic/versions/dlp01b_creado_por_obligatorio.py", "features/dlp_discovery/models.py", "features/dlp_discovery/schemas.py", "features/dlp_discovery/dlp_discovery_service.py#DLP-01", "api/routers/dlp_discovery.py", "tests/test_dlp01_sampling_discovery.py"]
crea = ["alembic/versions/dlp01b_creado_por_obligatorio.py"]
arbitro = "pytest tests/test_dlp01_sampling_discovery.py + tests/test_alembic_una_cabeza.py + vigilantes"
rastros = ["¤dlp-muestreo", "¤seguridad-tenant"]
+++
# DLP-01b · Descubrimiento DLP: todo escaneo tiene autor

## Entrega
- Migración nueva `dlp01b_creado_por_obligatorio`. La ya fusionada `dlp01_escaneos_muestreados` no se edita: pudo aplicarse en la base del CI, en el arnés de otros chats o en el entorno de pruebas, y Alembic no notaría el cambio bajo el mismo identificador.
- Antes del cambio cuenta las filas con `creado_por` nulo o vacío; si hay alguna, aborta con `RAISE` y solo el número, sin rellenar nada (un autor inventado falsearía la auditoría). Después, `SET NOT NULL` y CHECK de no vacío. SQL literal.
- `creado_en` no cambia: ya era NOT NULL con DEFAULT now().
- `creado_por` sale siempre de `ctx["user_id"]` (token), nunca del cuerpo; el servicio rechaza un escaneo sin autor; modelo y esquema lo declaran obligatorio.
- Columnas `creado_por` y `creado_en` validadas por el Arquitecto ADPA (2026-11-13) como datos de auditoría del escaneo, no de la muestra.

## Orden de migración
- `down_revision` = la cabeza de `main` al empujar (FUSION_ALEMBIC, una sola cabeza). Entra detrás de BOV-01 y DIAG-07 (#759 NORM-02 y #766 TER-01 ya en main); se re-cuelga tras cada fusión con migración.

## Pruebas
- `test_bd_solo_conteos_y_rls`: una fila sin `creado_por` se rechaza. Mutación: sin `dlp01b` (la columna admite nulos) → rojo.
- `test_bd_dlp01b_aborta_si_hay_escaneos_sin_autor`: con una fila sin autor, `upgrade()` aborta con el recuento y no rellena; sin ellas, la columna queda NOT NULL. Mutación: cambiar el `RAISE` por un `UPDATE` que rellene → rojo.
- Sin `import yaml` en las pruebas.
