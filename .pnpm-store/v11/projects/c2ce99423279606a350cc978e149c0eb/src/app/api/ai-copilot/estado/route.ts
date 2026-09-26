import { NextRequest } from "next/server";
import { proxyCopiloto } from "@/lib/copilotProxy";
export function GET(request: NextRequest) { return proxyCopiloto(request, "estado"); }
