// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤arbitro ¤demo
/**
 * QA-17 R4 · Calentamiento medido del humo desplegado: un único `GET /api/v1/entorno` con un plazo de 60 s.
 *
 * Mide el arranque en frío de Cloud Run antes de probar y lo deja en la salida y, por HUMO_CALENTAMIENTO_MS,
 * en las anotaciones de cada prueba (demo.spec.ts). Sin reintentos: si no responde 200 a tiempo, el humo falla
 * con la latencia medida. Ruta pública, sin credenciales.
 */
const PLAZO_MS = 60_000;

export default async function calentamiento(): Promise<void> {
  const origen = process.env.HUMO_DESPLEGADO_ORIGEN;
  if (!origen) throw new Error("[PRECONDICION FALLIDA] falta HUMO_DESPLEGADO_ORIGEN: lo fija playwright.desplegado.config.ts.");
  const url = `${origen}/api/v1/entorno`;
  const inicio = performance.now();
  let estado: number | string;
  try {
    const r = await fetch(url, {
      headers: { Accept: "application/json" },
      cache: "no-store",
      signal: AbortSignal.timeout(PLAZO_MS),
    });
    estado = r.status;
  } catch (e) {
    estado = e instanceof Error ? e.name : String(e);
  }
  const ms = Math.round(performance.now() - inicio);
  process.env.HUMO_CALENTAMIENTO_MS = String(ms);
  console.log(`[CALENTAMIENTO] GET ${url} → ${estado} en ${ms} ms`);
  if (estado !== 200) {
    throw new Error(`[CALENTAMIENTO] GET /api/v1/entorno no respondió 200 en ${PLAZO_MS} ms: ${estado} tras ${ms} ms.`);
  }
}
