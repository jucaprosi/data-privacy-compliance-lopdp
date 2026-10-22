"use client";

import React, { useEffect, useState } from "react";

import { EvidenciaPanel } from "@/components/modules/roadmap/evidencia";
import { setIdentitySession } from "@/lib/roadmap/cliente";
import { createInitialMockDatabase, createMockFetch } from "@/lib/roadmap/mockServer";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import type { OrganizacionRole, TaskEvidence } from "@/types/roadmap";

interface Props {
  rol: string;
  usuario: string;
  tarea: string;
  /**
   * "subida": el primer PUT al almacenamiento falla; "url": la primera solicitud de URL falla;
   * "cuatroojos": la primera validación responde con la violación de cuatro ojos;
   * "lista": la primera carga del listado falla; "vacia": la tarea no tiene evidencia.
   */
  fallo: string;
}

const ROLES: readonly OrganizacionRole[] = [
  "responsable_area",
  "coordinador",
  "dpo",
  "implementador",
  "admin_organizacion",
];

function evidenciaSembrada(id: string, tarea: string, subidaPor: string, archivo: string): TaskEvidence {
  return {
    id,
    task_id: tarea,
    tenant_id: "tenant-corp-demo",
    r2_key: `tenant-corp-demo/${tarea}/${archivo}`,
    mime_type: "application/pdf",
    file_size: 204800,
    file_hash: "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
    uploaded_by: subidaPor,
    uploaded_at: new Date(Date.now() - 3600_000).toISOString(),
    validation_status: "pending",
    notes: null,
  };
}

function respuestaError(estado: number, detalle: string, codigo: string, accion: string): Response {
  return new Response(JSON.stringify({ detail: detalle, code: codigo, action_required: accion }), {
    status: estado,
    headers: { "Content-Type": "application/json" },
  });
}

export function HarnessEvidencia({ rol, usuario, tarea, fallo }: Props) {
  const [listo, setListo] = useState(false);

  useEffect(() => {
    const original = window.fetch.bind(window);
    const db = createInitialMockDatabase();
    // Dos evidencias pendientes: una de otra persona y otra del usuario por defecto (coordinador).
    db.evidence.set(
      tarea,
      fallo === "vacia"
        ? []
        : [
            evidenciaSembrada("evi-ajena", tarea, "user-resp-01", "rat_consolidado.pdf"),
            evidenciaSembrada("evi-propia", tarea, "user-enc-01", "acta_comite.pdf"),
          ],
    );
    const simulado = createMockFetch(db);
    const yaFallo: Record<string, boolean> = {};
    const unaVez = (clave: string) => {
      if (fallo !== clave || yaFallo[clave]) return false;
      yaFallo[clave] = true;
      return true;
    };

    window.fetch = async (entrada: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof entrada === "string" ? entrada : entrada instanceof URL ? entrada.href : entrada.url;
      const metodo = (init?.method ?? "GET").toUpperCase();

      // Almacenamiento prefirmado simulado: acepta el archivo salvo que se pida un fallo.
      if (url.startsWith("https://mock-r2.local/")) {
        if (metodo === "PUT" && unaVez("subida")) return new Response("error", { status: 500 });
        return new Response(null, { status: 200 });
      }
      if (!url.includes("/api/v1/")) return original(entrada, init);

      if (metodo === "POST" && url.includes("/evidence/upload-url") && unaVez("url")) {
        return respuestaError(503, "No se pudo autorizar la subida.", "UPLOAD_URL_UNAVAILABLE", "retry_upload");
      }
      if (metodo === "GET" && /\/evidence$/.test(url) && unaVez("lista")) {
        return respuestaError(503, "No se pudo cargar la evidencia.", "EVIDENCE_UNAVAILABLE", "retry_later");
      }
      if (metodo === "PATCH" && /\/evidence\/[^/]+$/.test(url) && unaVez("cuatroojos")) {
        return respuestaError(
          409,
          "Violación de la regla de cuatro ojos: quien sube la evidencia no puede validarla",
          "FOUR_EYES_VIOLATION",
          "ask_another_validator",
        );
      }
      return simulado(entrada, init);
    };

    const rolValido = (ROLES as readonly string[]).includes(rol) ? (rol as OrganizacionRole) : "coordinador";
    setIdentitySession({ role: rolValido, userId: usuario });
    useRoadmapStore.getState().setSession({ role: rolValido, userId: usuario });
    setListo(true);

    return () => {
      window.fetch = original;
    };
  }, [rol, usuario, tarea, fallo]);

  return (
    <main className="h-screen overflow-auto bg-[#0a0a0c] p-6">
      <div className="mx-auto max-w-4xl">{listo ? <EvidenciaPanel taskId={tarea} titulo="Inventario y Registro de Actividades de Tratamiento" /> : null}</div>
    </main>
  );
}
