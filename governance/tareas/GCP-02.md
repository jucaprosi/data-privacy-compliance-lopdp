+++
id = "GCP-02"
titulo = "Acelerador CI/CD con Test Impact Analysis (TIA) determinista por grafo ADPA y sharding"
ola = "indep"
estado = "en_curso"
sala = "pruebas, operaciones"
depende_de = ["ADPA-06", "CI-10"]
propiedad = ["app_core/cloud/tia_adpa_selector.py", "governance/operaciones/ci_tia_matrix.json", "tests/test_gcp02_tia_adpa_selector.py"]
arbitro = "pytest tests/test_gcp02_tia_adpa_selector.py + suite completa + vigilantes"
rastros = ["¤cloud-run-perf", "¤adpa", "¤arbitro"]
+++
# GCP-02 · Acelerador CI/CD con Test Impact Analysis (TIA) determinista por grafo ADPA y sharding

## Entrega
- Selector determinista `app_core/cloud/tia_adpa_selector.py` que recibe la lista de archivos modificados en una rama (`git diff --name-only`), resuelve las salas ADPA afectadas y sus consumidores en `app_core/pasillo/`, y devuelve exactamente las suites de `pytest` necesarias y si debe omitirse la compilación/E2E de `frontend/`.
- Matriz declarativa `governance/operaciones/ci_tia_matrix.json` que vincula cada sala del catálogo PRD §7.1 con sus pruebas de contrato, unidad y shard de Playwright.

## Pruebas
- `pytest tests/test_gcp02_tia_adpa_selector.py` verifica que un cambio confinado a una sala backend selecciona únicamente las pruebas de esa sala y sus dependientes de pasillo, omitiendo el build de frontend, y que un cambio en `app_core/db/` activa la suite transversal completa.
