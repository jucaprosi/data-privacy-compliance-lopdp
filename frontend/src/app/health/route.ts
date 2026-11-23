// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
/** GCP-08 · Salud del contenedor del frontend: responde sin llamar al backend. */
export const dynamic = "force-dynamic";

export function GET(): Response {
  return new Response(JSON.stringify({ estado: "ok" }), {
    status: 200,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}
