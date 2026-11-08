+++
id = "ADPA-06"
titulo = "Andamiar módulos y secciones #ID en app_core/pasillo/ para integraciones entre salas pendientes"
ola = "C"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["ADPA-04", "ADPA-05"]
propiedad = ["app_core/pasillo/auditoria_capa.py", "app_core/pasillo/biblioteca.py", "app_core/pasillo/derechos_arco.py", "app_core/pasillo/diagnostico.py#ADPA-06", "app_core/pasillo/dpo_cockpit.py", "app_core/pasillo/evidencias.py#ADPA-06", "app_core/pasillo/firma_electronica.py", "app_core/pasillo/incidentes.py", "app_core/pasillo/notificaciones.py", "app_core/pasillo/organizacion.py#ADPA-06", "app_core/pasillo/rat.py#ADPA-06", "app_core/pasillo/regulacion_rag.py", "app_core/pasillo/riesgos_mtge.py", "app_core/pasillo/roadmap.py#ADPA-06", "app_core/pasillo/terceros.py", "app_core/pasillo/transferencias.py", "tests/test_adpa06_pasillos_secciones.py"]
crea = ["app_core/pasillo/auditoria_capa.py", "app_core/pasillo/biblioteca.py", "app_core/pasillo/derechos_arco.py", "app_core/pasillo/dpo_cockpit.py", "app_core/pasillo/firma_electronica.py", "app_core/pasillo/incidentes.py", "app_core/pasillo/notificaciones.py", "app_core/pasillo/regulacion_rag.py", "app_core/pasillo/riesgos_mtge.py", "app_core/pasillo/terceros.py", "app_core/pasillo/transferencias.py", "tests/test_adpa06_pasillos_secciones.py"]
siembra = ["app_core/pasillo/auditoria_capa.py#CAPA-03", "app_core/pasillo/auditoria_capa.py#CAPA-04", "app_core/pasillo/auditoria_capa.py#DPO-03", "app_core/pasillo/biblioteca.py#BIB-401", "app_core/pasillo/biblioteca.py#DEMO-03d", "app_core/pasillo/biblioteca.py#ORG-15", "app_core/pasillo/biblioteca.py#ORG-17", "app_core/pasillo/biblioteca.py#ORG-18", "app_core/pasillo/biblioteca.py#ORG-20", "app_core/pasillo/biblioteca.py#RAT-07", "app_core/pasillo/derechos_arco.py#CCTV-02", "app_core/pasillo/derechos_arco.py#DER-01", "app_core/pasillo/derechos_arco.py#DPO-03", "app_core/pasillo/derechos_arco.py#FIRMA-02", "app_core/pasillo/dpo_cockpit.py#BOV-04", "app_core/pasillo/dpo_cockpit.py#CAPA-03", "app_core/pasillo/dpo_cockpit.py#CON-01", "app_core/pasillo/dpo_cockpit.py#DER-01", "app_core/pasillo/dpo_cockpit.py#DPO-03", "app_core/pasillo/dpo_cockpit.py#FOR-01", "app_core/pasillo/dpo_cockpit.py#INC-02", "app_core/pasillo/dpo_cockpit.py#MTGE-03", "app_core/pasillo/dpo_cockpit.py#RAT-07", "app_core/pasillo/dpo_cockpit.py#TER-02", "app_core/pasillo/firma_electronica.py#DER-01", "app_core/pasillo/firma_electronica.py#FIRMA-02", "app_core/pasillo/firma_electronica.py#MTGE-03", "app_core/pasillo/firma_electronica.py#RAT-07", "app_core/pasillo/incidentes.py#CCTV-02", "app_core/pasillo/incidentes.py#DPO-03", "app_core/pasillo/incidentes.py#INC-02", "app_core/pasillo/notificaciones.py#CAPA-03", "app_core/pasillo/notificaciones.py#DER-01", "app_core/pasillo/notificaciones.py#INC-02", "app_core/pasillo/notificaciones.py#NORM-02", "app_core/pasillo/regulacion_rag.py#DIAG-04", "app_core/pasillo/regulacion_rag.py#DIAG-07", "app_core/pasillo/regulacion_rag.py#NORM-03", "app_core/pasillo/regulacion_rag.py#REG-01", "app_core/pasillo/regulacion_rag.py#VTX-01", "app_core/pasillo/riesgos_mtge.py#DPO-03", "app_core/pasillo/riesgos_mtge.py#FIRMA-02", "app_core/pasillo/riesgos_mtge.py#MTGE-03", "app_core/pasillo/terceros.py#DPO-03", "app_core/pasillo/terceros.py#TER-01", "app_core/pasillo/terceros.py#TER-02", "app_core/pasillo/transferencias.py#DPO-03", "app_core/pasillo/transferencias.py#TER-02"]
arbitro = "pytest tests/test_adpa06_pasillos_secciones.py tests/test_adpa_dependencias.py"
rastros = ["¤adpa"]
+++
# ADPA-06 · Andamiar módulos y secciones `#ID` en `app_core/pasillo/` para integraciones entre salas pendientes

## Entrega
- Crear/ampliar los módulos `app_core/pasillo/<sala>.py` con secciones `# --- INICIO <ID> ---` / `# --- FIN <ID> ---` reservadas para cada tarea que provee o consume contratos entre salas (`CAPA-03`, `CAPA-04`, `DER-01`, `DIAG-04`, `DIAG-07`, `DPO-03`, `FIRMA-02`, `FOR-01`, `INC-02`, `MTGE-03`, `ORG-15`, `ORG-17`, `ORG-18`, `ORG-20`, `RAT-07`, `REG-01`, `TER-01`, `TER-02`, `CON-01`, `BIB-208`, `BIB-302`, `BIB-303`, `BIB-304`, `BIB-401`, `BIB-402`).

## Pruebas
- `pytest tests/test_adpa06_pasillos_secciones.py` verifica que cada sección `app_core/pasillo/<sala>.py#<ID>` existe y no realiza imports de nivel superior hacia `features/`.

## Creadora (2026-11-07, decisión del CTO)

Crea los archivos de `crea` y es dueña de cada uno entero. Siembra marcas vacías `# === ID ===` / `# === fin ID ===` para las fichas que dependen de ella (`siembra`). Lo comprobará la regla R-PROP-EXISTE (ADPA-10).
