import { NextRequest } from "next/server";
import { proxyCopiloto } from "@/lib/copilotProxy";
export const maxDuration = 65;
export function POST(request: NextRequest) { return proxyCopiloto(request, "consulta"); }
