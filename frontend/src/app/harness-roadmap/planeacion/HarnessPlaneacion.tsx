"use client";

import React, { useEffect, useState } from "react";

import { PlaneacionForm } from "@/components/modules/roadmap/planeacion";
import { setIdentitySession } from "@/lib/roadmap/cliente";
import { createInitialMockDatabase, createMockFetch } from "@/lib/roadmap/mockServer";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import type { OrganizacionRole } from "@/types/roadmap";

interface Props {
  rol: string;
  latenciaMs: number;
  fallarPrimerIntento: boolean;
}

const ROLES: readonly OrganizacionRole[] = [
  "responsable_area",
  "coordinador",
  "dpo",
  "implementador",
  "admin_organizacion",
];

/**
 * Instala un fetch simulado que atiende /api/v1/* con el servidor de FE-01 y deja pasar el resto.
 * Parámetros de la ruta: rol, latencia (ms de espera en la generación) y fallo=1 (el primer
 * intento de generar responde con un error de negocio).
 */
export function HarnessPlaneacion({ rol, latenciaMs, fallarPrimerIntento }: Props) {
  const [listo, setListo] = useState(false);

  useEffect(() => {
    const original = window.fetch.bind(window);
    const simulado = createMockFetch(createInitialMockDatabase());
    let intentosDeGeneracion = 0;

    window.fetch = async (entrada: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof entrada === "string" ? entrada : entrada instanceof URL ? entrada.href : entrada.url;
      if (!url.includes("/api/v1/")) return original(entrada, init);

      const metodo = (init?.method ?? "GET").toUpperCase();
      if (metodo === "POST" && url.endsWith("/roadmaps/generate")) {
        intentosDeGeneracion += 1;
        if (latenciaMs > 0) await new Promise((r) => setTimeout(r, latenciaMs));
        if (fallarPrimerIntento && intentosDeGeneracion === 1) {
          return new Response(
            JSON.stringify({
              detail: "El modelo no respondió a tiempo.",
              code: "GENERATION_FAILED",
              action_required: "retry_generation",
            }),
            { status: 500, headers: { "Content-Type": "application/json" } },
          );
        }
      }
      return simulado(entrada, init);
    };

    const rolValido = (ROLES as readonly string[]).includes(rol) ? (rol as OrganizacionRole) : "implementador";
    setIdentitySession({ role: rolValido });
    useRoadmapStore.getState().setSession({ role: rolValido });
    setListo(true);

    return () => {
      window.fetch = original;
    };
  }, [rol, latenciaMs, fallarPrimerIntento]);

  return (
    <main className="h-screen overflow-auto bg-[#0a0a0c] p-6">
      <div className="mx-auto max-w-4xl">{listo ? <PlaneacionForm /> : null}</div>
    </main>
  );
}
