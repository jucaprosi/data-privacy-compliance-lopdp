/**
 * GCP-08 · Proxy de /api/v1 hacia el backend, con BACKEND_URL leída en cada petición.
 *
 * Next fija los rewrites al compilar; este handler permite usar una sola imagen en todos los
 * entornos. Contrato: governance/tareas/GCP-08.md (Arquitecto y Seguridad, 2026-11-08).
 *
 * - Ida: solo una lista permitida de cabeceras. Con K_SERVICE (Cloud Run) se descarta X-User-ID.
 * - Vuelta: estado tal cual (206 y 3xx incluidos) y una lista permitida de cabeceras. Si el backend
 *   no manda Cache-Control, se responde `no-store`.
 * - El cuerpo va en streaming en los dos sentidos: los binarios no se tocan.
 * - Destino: `new URL(BACKEND_URL)` + `/api/v1/` + segmentos codificados; nunca sale de su origen.
 * - Registros: método, ruta sin query, estado y X-Request-ID. Nunca la query, el cuerpo ni tokens.
 * - Autenticación hacia Cloud Run (la elige el propietario con PROXY_AUTH_CLOUD_RUN):
 *   `ninguna` (backend con ingress interno) o `token_servicio` (identidad del servidor de metadatos
 *   en X-Serverless-Authorization, sin tocar Authorization).
 */
import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const CABECERAS_IDA = [
  "authorization",
  "x-tenant-id",
  "x-role",
  "content-type",
  "accept",
  "range",
  "x-request-id",
] as const;

/** Solo fuera de la nube: el modo «headers» de desarrollo identifica al usuario así. */
const CABECERA_USUARIO_DESARROLLO = "x-user-id";

const CABECERAS_VUELTA = [
  "content-type",
  "content-disposition",
  "content-range",
  "accept-ranges",
  "x-content-sha256",
  "retry-after",
  "x-request-id",
  "location",
  "cache-control",
  "vary",
  "x-content-type-options",
  "www-authenticate",
] as const;

const PLAZO_POR_DEFECTO_MS = 150_000; // cubre la generación síncrona de la hoja de ruta (RM-18)
const SIN_CUERPO = new Set([204, 205, 304]);

type Contexto = { params: Promise<{ ruta?: string[] }> };

function enLaNube(): boolean {
  return Boolean(process.env.K_SERVICE);
}

function json(estado: number, cuerpo: Record<string, string>, extra?: HeadersInit): Response {
  const cabeceras = new Headers(extra);
  cabeceras.set("Content-Type", "application/json");
  cabeceras.set("Cache-Control", "no-store");
  return new Response(JSON.stringify(cuerpo), { status: estado, headers: cabeceras });
}

/** Origen del backend, o null si no hay uno válido. Nunca se deriva de la petición. */
function origenDelBackend(entorno: NodeJS.ProcessEnv = process.env): URL | null {
  const nube = Boolean(entorno.K_SERVICE);
  const crudo =
    entorno.BACKEND_URL?.trim() ||
    (nube ? "" : entorno.NEXT_PUBLIC_API_URL?.trim() || "http://127.0.0.1:5000");
  if (!crudo) return null;
  let url: URL;
  try {
    url = new URL(crudo.replace(/\/api\/v1\/?$/, ""));
  } catch {
    return null;
  }
  if (url.protocol !== "https:" && url.protocol !== "http:") return null;
  if (nube && url.protocol !== "https:" && !esHostInterno(url.hostname)) return null;
  return new URL(url.origin);
}

/** En la nube, http solo hacia un host interno: un nombre sin puntos o terminado en `.internal`. */
function esHostInterno(host: string): boolean {
  return !host.includes(".") || host.endsWith(".internal");
}

/** Segmentos decodificados → ruta segura bajo /api/v1/, o null si intentan salir de ella. */
function rutaSegura(segmentos: string[]): string | null {
  if (segmentos.length === 0) return null;
  for (const s of segmentos) {
    if (s === "" || s === "." || s === ".." || s.includes("/") || s.includes("\\")) return null;
  }
  return "/api/v1/" + segmentos.map(encodeURIComponent).join("/");
}

let tokenEnCache: { valor: string; vence: number; audiencia: string } | null = null;

async function tokenDeServicio(audiencia: string): Promise<string> {
  const ahora = Date.now();
  if (tokenEnCache && tokenEnCache.audiencia === audiencia && tokenEnCache.vence > ahora + 60_000) {
    return tokenEnCache.valor;
  }
  const metadatos =
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity" +
    `?audience=${encodeURIComponent(audiencia)}`;
  const r = await fetch(metadatos, { headers: { "Metadata-Flavor": "Google" }, signal: AbortSignal.timeout(5_000) });
  if (!r.ok) throw new Error("metadatos");
  const valor = (await r.text()).trim();
  let vence = ahora + 50 * 60_000;
  try {
    const carga = JSON.parse(Buffer.from(valor.split(".")[1], "base64url").toString("utf8"));
    if (typeof carga.exp === "number") vence = carga.exp * 1000;
  } catch {
    /* se queda con 50 minutos */
  }
  tokenEnCache = { valor, vence, audiencia };
  return valor;
}

function registrar(metodo: string, ruta: string, estado: number, idPeticion: string | null): void {
  console.info(JSON.stringify({ proxy: "api/v1", metodo, ruta, estado, request_id: idPeticion }));
}

async function reenviar(peticion: NextRequest, contexto: Contexto): Promise<Response> {
  const metodo = peticion.method.toUpperCase();
  const rutaRegistro = peticion.nextUrl.pathname; // sin query: puede llevar ?token= (SEC-19)
  const idPeticion = peticion.headers.get("x-request-id");

  const origen = origenDelBackend();
  if (!origen) {
    registrar(metodo, rutaRegistro, 503, idPeticion);
    return json(503, { detail: "Servicio no disponible." });
  }

  const { ruta = [] } = await contexto.params;
  const rutaDestino = rutaSegura(ruta);
  if (!rutaDestino || peticion.nextUrl.pathname.includes("//")) {
    registrar(metodo, rutaRegistro, 400, idPeticion);
    return json(400, { detail: "Ruta no válida." });
  }
  const destino = new URL(rutaDestino + peticion.nextUrl.search, origen);
  if (destino.origin !== origen.origin) {
    registrar(metodo, rutaRegistro, 400, idPeticion);
    return json(400, { detail: "Ruta no válida." });
  }

  const ida = new Headers();
  for (const nombre of CABECERAS_IDA) {
    const valor = peticion.headers.get(nombre);
    if (valor !== null) ida.set(nombre, valor);
  }
  if (!enLaNube()) {
    const usuario = peticion.headers.get(CABECERA_USUARIO_DESARROLLO);
    if (usuario !== null) ida.set(CABECERA_USUARIO_DESARROLLO, usuario);
  }
  if (process.env.PROXY_AUTH_CLOUD_RUN === "token_servicio") {
    try {
      ida.set("X-Serverless-Authorization", `Bearer ${await tokenDeServicio(origen.origin)}`);
    } catch {
      registrar(metodo, rutaRegistro, 503, idPeticion);
      return json(503, { detail: "Servicio no disponible." });
    }
  }

  const plazo = Number(process.env.PROXY_TIMEOUT_MS) || PLAZO_POR_DEFECTO_MS;
  const conCuerpo = metodo !== "GET" && metodo !== "HEAD" && peticion.body !== null;
  let respuesta: Response;
  try {
    respuesta = await fetch(destino, {
      method: metodo,
      headers: ida,
      body: conCuerpo ? peticion.body : undefined,
      redirect: "manual",
      signal: AbortSignal.timeout(plazo),
      cache: "no-store",
      ...(conCuerpo ? { duplex: "half" } : {}),
    } as RequestInit);
  } catch (error) {
    const agotado = error instanceof Error && (error.name === "TimeoutError" || error.name === "AbortError");
    const estado = agotado ? 504 : 502;
    registrar(metodo, rutaRegistro, estado, idPeticion);
    return json(estado, { detail: agotado ? "El servicio tardó demasiado." : "Servicio no disponible." });
  }

  const vuelta = new Headers();
  for (const nombre of CABECERAS_VUELTA) {
    const valor = respuesta.headers.get(nombre);
    if (valor !== null) vuelta.set(nombre, valor);
  }
  if (!vuelta.has("cache-control")) vuelta.set("Cache-Control", "no-store");

  registrar(metodo, rutaRegistro, respuesta.status, idPeticion);
  const sinCuerpo = metodo === "HEAD" || SIN_CUERPO.has(respuesta.status);
  return new Response(sinCuerpo ? null : respuesta.body, { status: respuesta.status, headers: vuelta });
}

export const GET = reenviar;
export const HEAD = reenviar;
export const POST = reenviar;
export const PUT = reenviar;
export const PATCH = reenviar;
export const DELETE = reenviar;

/** Cualquier otro método: 405 (Next respondería OPTIONS por su cuenta). */
export function OPTIONS(): Response {
  return json(405, { detail: "Método no permitido." }, { Allow: "GET, HEAD, POST, PUT, PATCH, DELETE" });
}
