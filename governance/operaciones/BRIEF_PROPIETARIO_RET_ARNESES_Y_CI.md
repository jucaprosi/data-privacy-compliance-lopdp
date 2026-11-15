# Brief al propietario · Arneses y CI sin plataformas retiradas
`¤sdd` `¤ci-cd`

Para: el propietario. De: Arquitecto ADPA, 2026-11-14. Paso 5 del programa RET (`governance/partes/arquitecto/2026-11-14_COBERTURA_PLATAFORMA_UNICA.md`). `verificadores/` y `.github/workflows/` son tuyos: las fichas no los tocan.

## Qué hay, medido en `origin/main`

- **`.github/workflows/`.** Ni `zero-regression-pipeline.yml` ni `deploy-gcp.yml` nombran una plataforma retirada ni un archivo que el programa elimine. No hay que cambiar nada.
- **`verificadores/arnes_local.py`.** Es el arnés local, que corre la suite contra PostgreSQL local, y sigue haciendo falta. Lo único que sobra son dos frases del docstring, en las líneas 2 y 10, que lo comparan con la base anterior.
- **`verificadores/README.md`.** La línea 91 compara el arnés con la base anterior.
- **`verificadores/arnes_cero_regresiones.py`.** No nombra ninguna plataforma.

## Qué hacer

Cuando RET-00 esté fusionada, en una ventana de PowerShell:

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
git fetch origin
git switch -c tarea/juan-carlos/ret-arneses origin/main
code verificadores\arnes_local.py verificadores\README.md
```

En los dos archivos, cambia la frase que compara con la base anterior por una descripción en positivo. Por ejemplo, en la línea 2: «Arnés rápido: la suite contra PostgreSQL local, en un solo comando.» En la línea 10 y en la 91 del README: «No ejercita la latencia de Cloud SQL; para eso está la corrida del CI y el entorno de pruebas.»

```powershell
python -m pytest -q
git add verificadores\arnes_local.py verificadores\README.md
git commit -m "Arneses: descripción en positivo"
git push -u origin tarea/juan-carlos/ret-arneses
```

Árbitro: la suite en verde. Después abre el PR, y el CTO lo fusiona.

## Lo que haces fuera del repositorio

Cada cosa, después de fusionar su ficha:

| Tras | Acción |
| :--- | :--- |
| RET-01 | Borrar de Secret Manager y de los secretos del repositorio en GitHub los de las plataformas retiradas. |
| RET-03 | Crear la cola de Cloud Tasks, solo si la especificación la usa. |
| RET-05 | Borrar el proyecto de la plataforma de despliegue anterior y su integración con GitHub. |
| RET-08 | Elegir el proveedor de correo (recomendado: la Gmail API de Workspace) y dar la delegación de envío. |
| Fin del programa | Cerrar las cuentas de la base, la caché, el almacén y la IA anteriores. |
| Cuando quieras | Decidir si algún archivo de `data/` sobra. Es material tuyo y ninguna ficha lo toca. |
