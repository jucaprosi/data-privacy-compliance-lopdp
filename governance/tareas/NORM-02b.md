+++
id = "NORM-02b"
titulo = "Aviso a las organizaciones de resoluciones nuevas o modificadas"
ola = "D"
estado = "pendiente"
sala = "inteligencia_normativa"
depende_de = ["NORM-02"]
propiedad = ["tests/test_norm02b_avisos_organizaciones.py"]
crea = []
arbitro = "pytest tests/test_norm02b_avisos_organizaciones.py contra un PostgreSQL 16 local en contenedor"
rastros = ["¤inteligencia-normativa", "¤vigilancia-spdp"]
+++

# NORM-02b · Aviso a las organizaciones de resoluciones nuevas o modificadas

**Origen.** Se separó de NORM-02 por decisión del Tech Lead (2026-11-13): el aviso necesita listar las organizaciones con su administrador y su DPO, y hoy ningún pasillo de plataforma lo ofrece.

## Entrega
- Un puerto `DestinatariosNormativos` en una sección `#NORM-02b` de un pasillo de plataforma, que lista por organización el administrador y el DPO.
- Aviso por la compuerta de notificaciones (NOTIF-01) cuando una corrida encuentra resoluciones nuevas o modificadas.
- Prueba de que cada organización recibe un aviso y ninguna recibe datos de otra.

**Propiedad por concretar:** el Arquitecto fija el pasillo y las secciones antes de repartirla. Hasta entonces, la ficha queda en «Sin agente».
