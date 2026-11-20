+++
id = "NORM-02b"
titulo = "Aviso a las organizaciones de resoluciones nuevas o modificadas"
ola = "D"
estado = "pendiente"
sala = "inteligencia_normativa"
depende_de = ["NORM-02", "BOV-01", "NOTIF-01"]
propiedad = ["features/plataforma/services/destinatarios_normativos_engine.py", "tests/test_norm02b_avisos_organizaciones.py", "alembic/versions/norm02b_destinatarios_normativos.py", "governance/operaciones/BRIEF_PROPIETARIO_NORM02B.md"]
crea = ["features/plataforma/services/destinatarios_normativos_engine.py", "tests/test_norm02b_avisos_organizaciones.py", "alembic/versions/norm02b_destinatarios_normativos.py", "governance/operaciones/BRIEF_PROPIETARIO_NORM02B.md"]
arbitro = "pytest tests/test_norm02b_avisos_organizaciones.py contra un PostgreSQL 16 local con lopdp_app, y tests/test_alembic_cabeza_por_sala.py; mutaciones: un solo correo con todos los destinatarios, GRANT EXECUTE TO PUBLIC sobre fn_destinatarios_normativos, añadir una columna a la función y quitar la condición de valid_to"
rastros = ["¤inteligencia-normativa", "¤vigilancia-spdp"]
+++

# NORM-02b · Aviso a las organizaciones de resoluciones nuevas o modificadas

**Origen.** Se separó de NORM-02 por decisión del Tech Lead (2026-11-13): el aviso necesita listar las organizaciones con su administrador y su DPO, y hoy ningún pasillo de plataforma lo ofrece.

## Entrega
- Un puerto `DestinatariosNormativos` en una sección `#NORM-02b` de un pasillo de plataforma, que lista por organización el administrador y el DPO.
- Aviso por la compuerta de notificaciones (NOTIF-01) cuando una corrida encuentra resoluciones nuevas o modificadas.
- Prueba de que cada organización recibe un aviso y ninguna recibe datos de otra.

**Propiedad.** Fijada por la especificación (§6): secciones `#NORM-02b` en `app_core/pasillo/plataforma.py`, `app_core/pasillo/notificaciones.py`, `features/plataforma/plataforma_service.py` y `features/inteligencia_normativa/inteligencia_normativa_service.py`, más el motor y la prueba nuevos. Las secciones no pueden declararse en la propiedad mientras sus archivos no tengan la marca `# === NORM-02b ===` (R-PROP-EXISTE): el PR de implementación abre las cuatro marcas y amplía en él la propiedad de esta ficha con las secciones, como hace DER-01 con la matriz.
