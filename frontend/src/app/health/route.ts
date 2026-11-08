/** GCP-08 · Salud del contenedor del frontend: responde sin llamar al backend. */
export const dynamic = "force-dynamic";

export function GET(): Response {
  return new Response(JSON.stringify({ estado: "ok" }), {
    status: 200,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}
