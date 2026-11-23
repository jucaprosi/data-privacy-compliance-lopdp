// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
import { NextResponse } from "next/server";

/** Retired ungrounded streaming route: callers must use the cited corpus API. */
export async function POST() {
  return NextResponse.json({
    error: "La ruta de chat anterior fue retirada. Utiliza /api/ai-copilot/consulta con pregunta, brechas e historial.",
  }, { status: 410 });
}
