import { NextRequest, NextResponse } from "next/server";
import { sanearCopiloto } from "@/lib/copilotClient";

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
      headers: {
        "Content-Type": "application/json",
        // The existing local deployment has one demo tenant and no production authentication.
        "X-Tenant-ID": "tenant-corp-demo",
      },
      body: body ? JSON.stringify(body) : undefined,
      cache: "no-store",
      signal: AbortSignal.timeout(60_000),
    });
    if (!response.ok) return NextResponse.json(
      { error: response.status === 422 ? "Consulta inválida." : "El servicio del asistente no está disponible." },
      { status: response.status >= 500 ? 502 : response.status },
    );
    return NextResponse.json(sanearCopiloto(await response.json()), { headers: { "Cache-Control": "no-store" } });
  } catch {
    return NextResponse.json({ error: "No se pudo conectar con el asistente." }, { status: 503 });
  }
}
