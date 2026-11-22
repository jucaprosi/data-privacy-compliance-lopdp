### GCP-04b · exclusion-de-la-firma-942421-en-cloud-armor-y-registro-perma  (tanda 90)

**Prioridad: normal.** El repositorio queda igual que la nube después del incidente del WAF del 2026-11-22. La nube ya está corregida: esta ficha no cambia nada en producción.

**Contexto.** Sala: `operaciones`. Depende de: ninguna pendiente (todas hechas). Especificaciones: `governance/tareas/GCP-04b.md` y `governance/especificaciones/GCP-04b.md` (manda la especificación).

**Cómo se ejecuta** (esta sesión no tiene el contexto del equipo; todo lo necesario está aquí y en la ficha).

- **Rama:** `tarea/juan-carlos/gcp-04b`, creada desde `origin/main` (`git fetch origin` y `git switch -c tarea/juan-carlos/gcp-04b origin/main`), en un worktree propio en `C:/Users/Juan Carlos/worktrees-evydentia/gcp-04b`, nunca dentro del escritorio.
- **Ficha:** en tu propio PR pon `estado = "en_curso"` en `governance/tareas/GCP-04b.md`. No la marques «hecha».
- **Un PR por ficha.** No lo fusiones: el propietario se lo pasa al CTO, que lo simula y lo fusiona.
- **Entorno:** sin `.env` y sin base de datos: la ficha es solo un YAML y una prueba de texto.
- **No edites** `.github/workflows/`, `verificadores/`, `AGENTS.md` ni `.claude/`.
- Archivos nuevos en LF; no cambies el estilo de líneas de los existentes. Pruebas sin `import yaml` (usa `tests/_lector_yaml.py`).
- Pytest como un solo comando con rutas absolutas y `--rootdir`, para que lo observen los hooks.
- Antes de pedir revisión: `python scripts/generar_indice_tareas.py --verificar`, `python scripts/verificar_reparto.py` y el árbitro de abajo, con su salida en el PR. Si algo no lo pudiste probar, dilo en el PR y no lo des por probado.

**Estado de la nube** (leído por el CTO el 2026-11-22 con gcloud de solo lectura; es la fuente de R4):

- La regla 1000 de `evydentia-waf` es `evaluatePreconfiguredWaf('sqli-v33-stable', {'sensitivity': 4, 'opt_out_rule_ids': ['owasp-crs-v030301-id942421-sqli']})`, con `deny(403)`.
- `evydentia-backend-bs` y `evydentia-web-bs` tienen `logConfig` con `enable=True` y `sampleRate=1.0`.

**Objetivo** (en este orden):

1. `GCP-04b` — Exclusión de la firma 942421 en Cloud Armor y registro permanente del balanceador

- **Regla 1000.** En `governance/operaciones/cloud_load_balancer.yaml` lleva la expresión exacta de la nube, citada arriba. La 1001, la 2000 y la regla final no cambian.
- **Registro.** Los dos elementos de `servicios_backend` llevan `registro: {habilitado: true, muestreo: 1}`.
- **Árbitro.** `tests/test_gcp04b_waf_y_registro.py` con los cuatro casos de la §5 de la especificación.
  - La prueba de evidencia (R2) lee `governance/especificaciones/GCP-04b.md` y exige que cada id de `opt_out_rule_ids` aparezca en su §1.
  - Las mutaciones m1 a m4 deben dar rojo. Pégalas en el PR con su salida.
- **Formato del YAML.** No reordenes ni reformatees el resto del archivo; lo leen `tests/test_gcp04_cloudsql_migration_cutover.py` y `tests/test_gcp09_dominio_e_ingress.py`.

**Rastro ¤**:

- `¤seguridad`, `¤arbitro`.

**Escribe** (lista exclusiva):

  - `governance/operaciones/cloud_load_balancer.yaml`
  - `tests/test_gcp04b_waf_y_registro.py`

**No hagas:**

- No escribas fuera de la lista anterior. No cambies la especificación: si la nube y la especificación difieren, para y avisa al CTO.
- No ejecutes `gcloud` que escriba. Las comprobaciones en la nube las hace el propietario.
- No toques producción ni una base compartida; no despliegues.
- No marques la tarea como hecha ni retires tu bloque: lo hace el coordinador en un PR de cierre.

**Hecho si** (árbitro exógeno):

- `GCP-04b`: pytest tests/test_gcp04b_waf_y_registro.py tests/test_gcp04_cloudsql_migration_cutover.py tests/test_gcp09_dominio_e_ingress.py; mutaciones m1 a m4.
- Condición 1: la expresión de la regla 1000 en el YAML es carácter a carácter la de la nube citada arriba.
- `python scripts/generar_indice_tareas.py --verificar` con código 0.
