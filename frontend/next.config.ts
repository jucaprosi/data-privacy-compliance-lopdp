import type { NextConfig } from "next";

const backendOrigin = (
  process.env.BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:5000"
).replace(/\/api\/v1\/?$/, "").replace(/\/$/, "");

/**
 * Política de contenido en MODO INFORME (Content-Security-Policy-Report-Only).
 *
 * No bloquea nada: el navegador solo registra en la consola lo que una política estricta
 * habría rechazado. Se empieza así porque la interfaz usa Tailwind y los scripts de Next, y una
 * política obligatoria puede romperla. Pasarla a modo obligatorio es decisión del propietario
 * tras revisar esos avisos (no hay recolector central: se observan en la consola del navegador).
 *
 * Constancia de las concesiones:
 *  - style-src 'unsafe-inline': React escribe atributos `style` en línea (por ejemplo anchos de
 *    barras de progreso). Sin esto la política avisaría de cada uno.
 *  - script-src NO lleva 'unsafe-inline': los scripts en línea que Next inserta para hidratar
 *    aparecerán como avisos a propósito, para decidir si se pasa a nonces.
 *  - connect-src incluye el dominio de R2: la evidencia sube por URL prefirmada directo desde el
 *    navegador. El patrón es el de R2 por defecto; ajústalo a R2_ENDPOINT_URL si los avisos
 *    muestran otro (no verificado contra la cuenta real).
 */
const CSP_INFORME = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob:",
  "font-src 'self' data:",
  "connect-src 'self' https://*.r2.cloudflarestorage.com",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

/**
 * Cabeceras de seguridad de todas las respuestas del frontend.
 *
 * `frame-ancestors` va en una CSP OBLIGATORIA aparte: el navegador la ignora dentro de una
 * política en modo informe. Es la defensa contra el clickjacking (junto con X-Frame-Options,
 * para navegadores antiguos).
 */
const CABECERAS_SEGURIDAD = [
  { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=()" },
  { key: "Content-Security-Policy", value: "frame-ancestors 'none'" },
  { key: "Content-Security-Policy-Report-Only", value: CSP_INFORME },
];

/**
 * Tiempo máximo que el proxy de `/api/v1` espera al backend (ms). Next corta a los 30 s por
 * defecto, y la generación de la hoja de ruta es síncrona: hasta 2 llamadas a la IA de 60 s cada
 * una (RM-18). `tests/test_proxy_timeout.py` exige que este valor cubra ese peor caso.
 */
const PROXY_TIMEOUT_MS = 150_000;

const nextConfig: NextConfig = {
  experimental: { proxyTimeout: PROXY_TIMEOUT_MS },
  async headers() {
    return [{ source: "/(.*)", headers: CABECERAS_SEGURIDAD }];
  },
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendOrigin}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
