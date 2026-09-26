import { NextResponse } from "next/server";
import { NORMATIVAS, NORMATIVA_POR_DEFECTO } from "@/lib/normativas";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const solicitada: unknown = body.normativaSeleccionada;
    const descriptor =
      Object.values(NORMATIVAS).find((n) => n.id === solicitada) ?? NORMATIVAS[NORMATIVA_POR_DEFECTO];
    const normativa = descriptor.etiquetaCorta;
    console.log(
      `[Backend] Configuración de ${normativa} guardada con éxito en el Compliance Graph`
    );

    return NextResponse.json(
      {
        success: true,
        message: `[Backend] Configuración de ${normativa} guardada con éxito en el Compliance Graph`,
        timestamp: new Date().toISOString(),
        data: body,
      },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: "Error al deserializar la Ficha Organizacional",
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 400 }
    );
  }
}
