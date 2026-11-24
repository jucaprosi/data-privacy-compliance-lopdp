+++
id = "GEN-01"
titulo = "Aplicación genérica: los artefactos, las especificaciones y las fichas en estado final, sin la marca del operador"
ola = "backlog"
estado = "hecha"
tanda = 99
sala = "gobernanza"
depende_de = ["DIAG-08", "DIAG-09", "DIAG-10", "PRD-02"]
propiedad = ["governance/artefactos/PRD.md", "governance/artefactos/INVARIANTS.md", "governance/artefactos/VPA_MAP.md", "governance/METODOLOGIAS.md", "governance/artefactos/INFORME_CONOCIMIENTOS_EPISTEMICOS.md", "governance/artefactos/FUENTES_Y_BIBLIOGRAFIA.md", "governance/artefactos/APORTES_INEDITOS.md", "governance/especificaciones/CAPA-04.md", "governance/especificaciones/DIAG-08.md", "governance/especificaciones/DIAG-09.md", "governance/especificaciones/FE-24.md", "governance/especificaciones/FIRMA-06.md", "governance/tareas/BIB-102.md", "governance/tareas/BIB-103.md", "governance/tareas/BIB-109.md", "governance/tareas/DIAG-02.md", "governance/tareas/DIAG-05.md", "governance/tareas/DIAG-07b.md", "governance/tareas/DIAG-08.md", "governance/tareas/DIAG-09.md", "governance/tareas/DIAG-10.md", "governance/tareas/DIAG-12.md", "governance/tareas/DIAG-13.md", "governance/tareas/PRD-02.md", "governance/tareas/RET-06.md", "governance/tareas/RM-19.md", "governance/tareas/RM-25a.md", "tests/test_auditoria_grilla.py"]
crea = []
arbitro = "python scripts/verificar_especificaciones.py; python scripts/generar_indice_tareas.py --verificar; python scripts/verificar_reparto.py; pytest tests/test_reparto.py tests/test_indice_tareas.py tests/test_verificar_especificaciones.py tests/test_escala_madurez.py."
rastros = ["¤sdd", "¤arbitro"]
+++

# GEN-01 · Aplicación genérica: los artefactos, las especificaciones y las fichas en estado final, sin la marca del operador

**Contrato:** `governance/especificaciones/GEN-01.md` (manda sobre esta ficha). Programa: governance/especificaciones/GEN-01.md §0.

**Origen.** Decisión del propietario (2026-11-24), brief del CTO `ARQUITECTO_APP_GENERICA_SIN_MARCA_OPERADOR.md`, medido en `origin/main` ea6d26bf: la aplicación es genérica y la marca del operador sale de forma estructural.

## Entrega
- PRD, invariantes, mapa VPA, metodologías, informe epistémico, fuentes y aportes con el vocabulario final de la especificación §3.
- Las cinco especificaciones y las quince fichas que nombraban la marca, reescritas en estado final, con los nombres de archivo nuevos de GEN-02 y GEN-06.

## Límites
- Solo texto de gobernanza; ningún código. Va primero: las fichas GEN-02 a GEN-07 se escriben contra estos artefactos.
- El historial de git, `REGISTRO_MIGRACIONES_MANUALES.md` y los partes ya emitidos no cambian (especificación R6).
