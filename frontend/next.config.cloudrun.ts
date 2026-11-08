import type { NextConfig } from "next";
import base from "./next.config";

/**
 * GCP-03 / GCP-08 · Configuración de Next.js para Cloud Run. ¤cloud-run-perf ¤frontend-ide
 *
 * Extiende `next.config.ts` (cabeceras de seguridad) sin cambiarlo, para no tocar el despliegue
 * de Vercel (R3). `frontend/Dockerfile.cloudrun` la coloca como configuración activa solo dentro
 * de la imagen.
 *
 * - `output: "standalone"`: la imagen lleva solo el servidor y las dependencias que se usan.
 * - Sin rewrites de /api/v1: Next los fija al compilar. El proxy es el route handler
 *   `src/app/api/v1/[...ruta]/route.ts`, que lee BACKEND_URL en cada petición (GCP-08).
 * - `images.unoptimized` y sin sharp ni TypeScript en el trazado: la imagen baja de 120 MB.
 *   Los logos se sirven tal cual; no hay optimización de imágenes en el servidor.
 * - El entorno (APP_ENV) no se fija aquí: se lee al ejecutar, por servicio (EP-02).
 */
const nextConfigCloudRun: NextConfig = {
  ...base,
  rewrites: undefined,
  output: "standalone",
  poweredByHeader: false,
  compress: true,
  images: { ...base.images, unoptimized: true },
  outputFileTracingExcludes: {
    "*": ["node_modules/@img/**", "node_modules/sharp/**", "node_modules/typescript/**"],
  },
};

export default nextConfigCloudRun;
