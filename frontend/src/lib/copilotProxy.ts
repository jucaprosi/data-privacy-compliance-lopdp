import { NextRequest, NextResponse } from "next/server";
import { sanearCopiloto } from "@/lib/copilotClient";

// === SEC-23 ===
/**
 * El backend exige token verificado y membresía en la organización. El proxy reenvía la identidad
 * de quien llama (lista permitida, igual que el proxy de /api/v1) y nunca la inventa: no hay
 * organización fija en el código. X-User-ID solo existe en el modo «headers» de desarrollo y se
 * descarta en la nube (K_SERVICE).
 */
const CABECERAS_IDENTIDAD = ["authorization", "x-tenant-id", "x-role"] as const;

export function identidadDe(request: NextRequest): Record<string, string> {
  const salida: Record<string, string> = {};
  for (const nombre of CABECERAS_IDENTIDAD) {
    const valor = request.headers.get(nombre);
    if (valor) salida[nombre] = valor;
  }
  const usuario = request.headers.get("x-user-id");
  if (usuario && !process.env.K_SERVICE) salida["x-user-id"] = usuario;
  return salida;
}

function mensajeDeError(estado: number): string {
  if (estado === 422) return "Consulta inválida.";
  if (estado === 401) return "La sesión caducó. Vuelve a identificarte.";
  if (estado === 403) return "No tienes acceso al asistente en esta organización.";
  return "El servicio del asistente no está disponible.";
}
// === fin SEC-23 ===

/** Server-only endpoint configuration. Provider secrets stay in FastAPI. */
export async function proxyCopiloto(request: NextRequest, action: "consulta" | "estado") {
  const origin = (
    process.env.COPILOT_API_URL ||
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:5000"
  ).replace(/\/api\/v1\/?$/, "").replace(/\/$/, "");
  const base = `${origin}/api/v1`;
  try {
    const body = action === "consulta" ? sanearCopiloto(await request.json()) : undefined;
    const response = await fetch(base + "/ai_copilot/" + action, {
      method: action === "consulta" ? "POST" : "GET",
      headers: { "Content-Type": "application/json", ...identidadDe(request) },
      body: body ? JSON.stringify(body) : undefined,
      cache: "no-store",
      signal: AbortSignal.timeout(60_000),
    });
    if (!response.ok) return NextResponse.json(
      { error: mensajeDeError(response.status) },
      { status: response.status >= 500 ? 502 : response.status },
    );
    return NextResponse.json(sanearCopiloto(await response.json()), { headers: { "Cache-Control": "no-store" } });
  } catch {
    return NextResponse.json({ error: "No se pudo conectar con el asistente." }, { status: 503 });
  }
}
