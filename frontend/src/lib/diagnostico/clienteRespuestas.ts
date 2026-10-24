export interface RespuestaServidor { pregunta_id: number; control_ref: string; dimension: string; estado: "Conforme" | "Parcial" | "No Conforme" | "Pendiente"; nivel_evidencia: number; criticidad: number; }

export async function cargarRespuestas(): Promise<RespuestaServidor[]> {
  const response = await fetch("/api/v1/diagnostico/respuestas");
  if (!response.ok) return [];
  return (await response.json() as { respuestas: RespuestaServidor[] }).respuestas;
}

export async function guardarRespuestas(respuestas: RespuestaServidor[]): Promise<void> {
  await fetch("/api/v1/diagnostico/respuestas", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ respuestas }) });
}
