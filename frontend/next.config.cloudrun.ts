import type { NextConfig } from "next";
import base from "./next.config";

/**
 * GCP-03 · Configuración de Next.js para Cloud Run (us-east1). ¤cloud-run-perf ¤frontend-ide
 *
 * Extiende `next.config.ts` (cabeceras de seguridad, proxy de /api/v1, timeout) sin cambiarlo,
 * para no tocar el despliegue de Vercel (R3). `frontend/Dockerfile.cloudrun` la coloca como
 * configuración activa solo dentro de la imagen.
 *
 * - `output: "standalone"`: la imagen lleva solo el servidor y las dependencias que se usan (R1).
 * - `poweredByHeader: false`: no anuncia la tecnología del servidor.
 * - El entorno (APP_ENV) no se fija aquí: se lee al ejecutar, por servicio (EP-02).
 */
const nextConfigCloudRun: NextConfig = {
  ...base,
  output: "standalone",
  poweredByHeader: false,
  compress: true,
};

export default nextConfigCloudRun;
