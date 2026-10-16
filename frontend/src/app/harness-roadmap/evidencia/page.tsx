import { notFound } from "next/navigation";

import { HarnessEvidencia } from "./HarnessEvidencia";

/**
 * Ruta de pruebas de FE-04: monta EvidenciaPanel contra el servidor simulado para que Playwright
 * pueda ejercitarlo antes de que FE-06 lo integre en el panel.
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
    <HarnessEvidencia
      rol={primero(parametros.rol) ?? "encargado"}
      usuario={primero(parametros.usuario) ?? "user-enc-01"}
      tarea={primero(parametros.tarea) ?? "task-002"}
      fallo={primero(parametros.fallo) ?? ""}
    />
  );
}
