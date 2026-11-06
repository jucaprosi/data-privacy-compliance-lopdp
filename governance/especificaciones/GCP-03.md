# GCP-03 · Migración del Frontend Next.js a Google Cloud Run Standalone
`¤sdd` `¤cloud-run-perf` `¤frontend-ide` `¤seguridad`

## 1. Datos

Configuración de compilación `NextCloudRunConfig` (`output: 'standalone'`, `poweredByHeader: false`, `compress: true`, `env: { NEXT_PUBLIC_API_URL: str }`).

## 2. API

- `GET /health` (en el contenedor frontend) -> `200 OK` con verificación de runtime de Next.js.

## 3. Reglas

- **R1 · Modo standalone obligatorio (`INV_LOPDP_STANDALONE_FRONTEND_CONTAINER`).** La compilación para producción en Cloud Run debe usar exclusivamente `output: 'standalone'` para reducir la imagen a $< 120	ext{ MB}$.
- **R2 · Ejecución non-root.** El contenedor en Cloud Run se ejecuta bajo el usuario no privilegiado `nextjs` (UID 1001).
- **R3 · Cero colisiones con Vercel.** Los archivos de configuración de Cloud Run coexisten de forma ortogonal sin modificar `frontend/vercel.json` hasta el cutover definitivo.

## 4. Interfaz

Mantiene el 100% de la interfaz de usuario existente en Next.js 15.5+ y Tailwind CSS.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** la configuración de compilación de Cloud Run, **cuando** se valida en `test_gcp03_frontend_cloudrun.py`, **entonces** `output` es `'standalone'` y desactiva cabeceras identificadoras de tecnología. | `test_next_standalone_config_valida` |
| **Dado** el manifiesto de despliegue `cloudrun_frontend_service.yaml`, **cuando** se inspecciona, **entonces** mapea las variables de entorno de producción sin secretos embebidos en texto plano. | `test_cloudrun_frontend_manifest_seguro` |

## 6. Trazabilidad

- PRD §8.4, §9 criterio 24 e invariante `INV_LOPDP_STANDALONE_FRONTEND_CONTAINER`.
