// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
import { NextRequest } from "next/server";
import { proxyCopiloto } from "@/lib/copilotProxy";
export function GET(request: NextRequest) { return proxyCopiloto(request, "estado"); }
