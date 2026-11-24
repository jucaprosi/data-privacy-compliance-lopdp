+++
id = "DEMO-10"
titulo = "El procedimiento de la web de demo comprueba el permiso de lectura y vuelve atrás sin revisión fija"
ola = "D"
estado = "en_curso"
tanda = 98
sala = "operaciones"
depende_de = ["DEMO-09"]
propiedad = ["governance/operaciones/DEMO_COMERCIAL.md", "tests/test_demo09_web_demo.py"]
crea = []
arbitro = "pytest tests/test_demo09_web_demo.py; mutaciones m5 y m6."
rastros = ["¤demo", "¤arbitro"]
+++

# DEMO-10 · El procedimiento de la web de demo comprueba el permiso de lectura y vuelve atrás sin revisión fija

**Contrato:** `governance/especificaciones/DEMO-10.md` (manda sobre esta ficha).

**Origen.** Revisión del Tech Lead de DEMO-09 (#1000, fusionado en `aceee6f7`, 2026-11-24). Dos desvíos menores de `DEMO_COMERCIAL.md` §5 frente a `governance/especificaciones/DEMO-09.md`. No bloquea nada: el procedimiento sirve tal cual para la primera publicación.

## Entrega
- **R2 de DEMO-09, completa.** El procedimiento de §5.2 empieza con una comprobación de solo lectura de que el agente de servicio de la demo tiene `roles/artifactregistry.reader` sobre `evydentia-containers`, y se detiene si no lo tiene. Hoy §5.2 lo manda al brief del propietario y no lo hace.
- **Volver atrás sin revisión fija.** §5.3 deja de sobrescribir `$ANTERIOR` con `evydentia-web-demo-00005-8f5`. La revisión a la que se vuelve es la anotada en el paso 2 de la publicación que se deshace, y no una constante que queda vieja tras la segunda publicación.
- Una prueba por cada punto, sin red y sin `import yaml`.

## Límites
- Solo los dos archivos de la propiedad. Van después de DEMO-09, que es dueña de los dos y sigue `en_curso`: no se lanza hasta que DEMO-09 se cierre.
- No toca la nube ni usa gcloud: el procedimiento lo sigue el propietario. No cambian el manifiesto, `frontend/cloudbuild.yaml`, `frontend/Dockerfile.cloudrun` ni `.github/workflows/`.
- `$ANTERIOR` no se hereda entre bloques: la revisión anterior queda en Cloud Run como etiqueta de tráfico `anterior` y §5.3 vuelve con `--to-tags` (especificación §3 R2).
