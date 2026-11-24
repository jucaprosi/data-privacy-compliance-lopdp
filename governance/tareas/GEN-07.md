+++
id = "GEN-07"
titulo = "Firma electrónica, plantilla RAT y documentos de apoyo sin marca: el cliente de ANF en la configuración y los binarios fuera del repositorio"
ola = "backlog"
estado = "hecha"
tanda = 100
sala = "firma_electronica, rat, plataforma, gobernanza"
depende_de = ["GEN-01", "FIRMA-06", "RAT-02", "MARCA-01"]
propiedad = ["features/firma_electronica/firma_electronica_service.py", "features/firma_electronica/services/anf_stb_client.py", "app_core/config.py", "tests/test_firma_anf_stb.py", "features/rat/domain/plantillas/salud.json", "governance/arquitectura/FIRMA_ELECTRONICA_BOCETO.md", "governance/apoyo/INFORME_MODULO_FIRMA_ELECTRONICA.md", "Guia_Diseno_Plataforma_LOPDP_SMARTCIDI_2026_v1.1.docx.pdf", "Guia_Modulo_Exposicion_Sancionatoria_LOPDP_SMARTCIDI_v1.1_FINAL (1).docx", "Reporte_Assessment_LOPDP_PJL_17sep2026.pdf", "data/Guia_Integracion_OneShot_SMARTCIDI.pdf", "data/V1. Informe de entrega de STBS - SmartCidi.pdf"]
crea = []
arbitro = "pytest tests/test_firma_anf_stb.py tests/test_rat_plantilla_salud.py; mutación m1; decisiones del propietario sobre salud.json y los binarios anotadas en la especificación (R2 y R3)."
rastros = ["¤adpa", "¤arbitro"]
+++

# GEN-07 · Firma electrónica, plantilla RAT y documentos de apoyo sin marca: el cliente de ANF en la configuración y los binarios fuera del repositorio

**Contrato:** `governance/especificaciones/GEN-07.md` (manda sobre esta ficha). Programa: governance/especificaciones/GEN-01.md §0.

**Origen.** Decisión del propietario (2026-11-24), brief del CTO `ARQUITECTO_APP_GENERICA_SIN_MARCA_OPERADOR.md`, medido en `origin/main` ea6d26bf: la aplicación es genérica y la marca del operador sale de forma estructural.

## Entrega
- El identificador de cliente de ANF AC sale del código hacia la configuración (`ANF_CLIENTE`), y las pruebas usan valores de prueba.
- `salud.json` con la autoría y la nota que decida el propietario; los documentos de apoyo de firma con el vocabulario final.
- Los binarios con la marca en el nombre salen del repositorio hacia los documentos del propietario, según su decisión.

## Límites
- No se lanza sin las decisiones del propietario de la especificación R2 y R3. El historial de git no cambia.
