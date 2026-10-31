import { notFound } from "next/navigation";

import { HarnessVistas } from "./HarnessVistas";

/**
 * Ruta de pruebas de RM-22: monta VistasTareas contra el servidor simulado para que Playwright
 * pueda ejercitarla antes de integrarla en el menú. No existe en producción: responde 404.
 */
export const dynamic = "force-dynamic";

interface Props {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

function primero(valor: string | string[] | undefined): string | undefined {
  return Array.isArray(valor) ? valor[0] : valor;
}

export default async function Page({ searchParams }: Props) {
  if (process.env.NODE_ENV === "production") notFound();

  const parametros = await searchParams;
  return (
    <HarnessVistas
      rol={primero(parametros.rol) ?? "implementador"}
      usuario={primero(parametros.usuario) ?? "user-impl-01"}
      fallo={primero(parametros.fallo) ?? ""}
    />
  );
}
