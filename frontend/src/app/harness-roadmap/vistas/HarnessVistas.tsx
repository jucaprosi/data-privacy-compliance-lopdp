"use client";

import React, { useEffect, useState } from "react";

import { VistasTareas } from "@/components/modules/roadmap/vistas";
import { hoyGuayaquil } from "@/components/modules/roadmap/vistas/logica";
import type { HallazgoItem, TareaConOrigen } from "@/components/modules/roadmap/vistas/tipos";
import { setIdentitySession } from "@/lib/roadmap/cliente";
import { createInitialMockDatabase, createMockFetch } from "@/lib/roadmap/mockServer";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import type { OrganizacionRole } from "@/types/roadmap";

interface Props {
  rol: string;
  usuario: string;
  /** "estado": el primer cambio de estado responde con un error de negocio. */
  fallo: string;
}

const ROLES: readonly OrganizacionRole[] = ["responsable_area", "coordinador", "dpo", "implementador", "admin_organizacion"];

function sumarDias(fecha: string, dias: number): string {
  const [a, m, d] = fecha.split("-").map(Number);
  return new Date(Date.UTC(a, m - 1, d + dias)).toISOString().slice(0, 10);
}

/**
 * Cinco tareas con fechas relativas a hoy (Guayaquil), para que la prueba no caduque:
 * task-001 completada con fin pasado; task-002 en progreso con origen «diagnóstico»; task-003 sin fechas;
 * task-vencida-1 y task-vencida-2 con fin ayer.
 */
function prepararDatos(db: ReturnType<typeof createInitialMockDatabase>): void {
  const hoy = hoyGuayaquil();
  const ola = db.waves.get("rm-demo-001")?.[0];
  const base = db.tasks.get("task-001");
  if (!ola || !base) return;

  const ajustes: Record<string, Partial<TareaConOrigen>> = {
    "task-001": { start_date: sumarDias(hoy, -30), end_date: sumarDias(hoy, -10) },
    "task-002": { start_date: sumarDias(hoy, -5), end_date: sumarDias(hoy, 10), hallazgo_id: "hal-001" },
    "task-003": { start_date: null, end_date: null },
  };
  for (const [id, cambios] of Object.entries(ajustes)) {
    for (const t of [db.tasks.get(id), ...db.waves.get("rm-demo-001")!.flatMap((o) => o.tasks ?? []).filter((x) => x.id === id)]) {
      if (t) Object.assign(t, cambios);
    }
  }
  const vencidas: TareaConOrigen[] = [
    { ...base, id: "task-vencida-1", title: "Revisar contratos con encargados", status: "pendiente", start_date: sumarDias(hoy, -12), end_date: sumarDias(hoy, -1), evidence: [] },
    { ...base, id: "task-vencida-2", title: "Actualizar el aviso de privacidad", status: "en_progreso", start_date: sumarDias(hoy, -8), end_date: sumarDias(hoy, -1), evidence: [] },
  ];
  for (const t of vencidas) {
    db.tasks.set(t.id, t);
    ola.tasks = [...(ola.tasks ?? []), t];
  }
  const hallazgo: HallazgoItem = {
    id: "hal-001",
    origen: "diagnostico",
    origen_ref: "res-001:P2",
    control_ref: "P2",
    dimension: "D02",
    severidad: "alta",
    titulo: "Sin inventario de tratamientos",
    descripcion: null,
    estado: "en_tratamiento",
    tarea_id: "task-002",
    creado_en: new Date().toISOString(),
  };
  db.hallazgos = [hallazgo];
}

export function HarnessVistas({ rol, usuario, fallo }: Props) {
  const [listo, setListo] = useState(false);

  useEffect(() => {
    const original = window.fetch.bind(window);
    const db = createInitialMockDatabase();
    prepararDatos(db);
    const simulado = createMockFetch(db);
    let yaFallo = false;
    // La prueba cuenta aquí las peticiones, porque el simulado las atiende dentro de la página.
    const peticiones: string[] = [];
    (window as unknown as { __peticiones: string[] }).__peticiones = peticiones;

    window.fetch = async (entrada: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof entrada === "string" ? entrada : entrada instanceof URL ? entrada.href : entrada.url;
      if (!url.includes("/api/v1/")) return original(entrada, init);

      const metodo = (init?.method ?? "GET").toUpperCase();
      peticiones.push(`${metodo} ${url}`);
      if (!yaFallo && fallo === "estado" && metodo === "PATCH" && /\/roadmaps\/tasks\/[^/]+$/.test(url)) {
        yaFallo = true;
        return new Response(
          JSON.stringify({ detail: "La tarea cambió mientras la movías.", code: "TASK_STATE_CONFLICT", action_required: "refresh_and_retry" }),
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
    <main className="h-screen overflow-auto bg-[var(--ui-campo)] p-6">
      <div className="mx-auto max-w-6xl">{listo ? <VistasTareas roadmapId="rm-demo-001" /> : null}</div>
    </main>
  );
}
