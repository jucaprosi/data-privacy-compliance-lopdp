"use client";

import React, { useEffect, useState } from "react";

import { OlasView } from "@/components/modules/roadmap/olas";
import { setIdentitySession } from "@/lib/roadmap/cliente";
import { createInitialMockDatabase, createMockFetch } from "@/lib/roadmap/mockServer";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import type { OrganizacionRole } from "@/types/roadmap";

interface Props {
  rol: string;
  usuario: string;
  /** "estado", "editar" o "asignar": esa acción responde la primera vez con un error de negocio. */
  fallo: string;
  /** Hoja de ruta que se muestra; una inexistente sirve para probar el error de carga. */
  roadmapId: string;
}

const ROLES: readonly OrganizacionRole[] = [
  "responsable_area",
  "coordinador",
  "dpo",
  "implementador",
  "admin_organizacion",
];

/** Área de cada tarea del simulado, para probar filtros y el alcance del responsable de área. */
const AREA_POR_TAREA: Record<string, string> = {
  "task-001": "area-001",
  "task-002": "area-001",
  "task-003": "area-002",
};

function bloqueada(fallo: string, metodo: string, url: string): boolean {
  if (fallo === "estado") return metodo === "PATCH" && /\/roadmaps\/tasks\/[^/]+$/.test(url);
  if (fallo === "editar") return metodo === "PATCH" && url.endsWith("/details");
  if (fallo === "asignar") return metodo === "POST" && url.endsWith("/assign");
  return false;
}

export function HarnessOlas({ rol, usuario, fallo, roadmapId }: Props) {
  const [listo, setListo] = useState(false);

  useEffect(() => {
    const original = window.fetch.bind(window);
    const db = createInitialMockDatabase();
    for (const tarea of db.tasks.values()) tarea.area_id = AREA_POR_TAREA[tarea.id] ?? null;
    for (const olas of db.waves.values()) {
      for (const ola of olas) for (const tarea of ola.tasks ?? []) tarea.area_id = AREA_POR_TAREA[tarea.id] ?? null;
    }
    const simulado = createMockFetch(db);
    let yaFallo = false;

    window.fetch = async (entrada: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof entrada === "string" ? entrada : entrada instanceof URL ? entrada.href : entrada.url;
      if (!url.includes("/api/v1/")) return original(entrada, init);

      const metodo = (init?.method ?? "GET").toUpperCase();
      if (!yaFallo && bloqueada(fallo, metodo, url)) {
        yaFallo = true;
        return new Response(
          JSON.stringify({
            detail: "La tarea cambió mientras la editabas.",
            code: "TASK_STATE_CONFLICT",
            action_required: "refresh_and_retry",
          }),
          { status: 409, headers: { "Content-Type": "application/json" } },
        );
      }
      return simulado(entrada, init);
    };

    const rolValido = (ROLES as readonly string[]).includes(rol) ? (rol as OrganizacionRole) : "implementador";
    setIdentitySession({ role: rolValido, userId: usuario });
    useRoadmapStore.getState().setSession({ role: rolValido, userId: usuario });
    setListo(true);

    return () => {
      window.fetch = original;
    };
  }, [rol, usuario, fallo]);

  return (
    <main className="h-screen overflow-auto bg-[#0a0a0c] p-6">
      <div className="mx-auto max-w-5xl">{listo ? <OlasView roadmapId={roadmapId} /> : null}</div>
    </main>
  );
}
