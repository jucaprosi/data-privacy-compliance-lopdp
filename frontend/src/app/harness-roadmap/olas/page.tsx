import { notFound } from "next/navigation";

import { HarnessOlas } from "./HarnessOlas";

/**
 * Ruta de pruebas de FE-03: monta OlasView contra el servidor simulado para que Playwright
 * pueda ejercitarla antes de que FE-06 la integre en el panel.
 * No existe en producción: responde 404.
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
    <HarnessOlas
      rol={primero(parametros.rol) ?? "implementador"}
      usuario={primero(parametros.usuario) ?? "user-impl-01"}
      fallo={primero(parametros.fallo) ?? ""}
      roadmapId={primero(parametros.roadmap) ?? "rm-demo-001"}
    />
  );
}
