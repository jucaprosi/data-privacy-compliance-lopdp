"use client";

import React, { useEffect, useState } from "react";

import { EvidenciaPanel } from "@/components/modules/roadmap/evidencia";
import { setIdentitySession, type EvidenciaConDobleValidacion } from "@/lib/roadmap/cliente";
import { createInitialMockDatabase, createMockFetch } from "@/lib/roadmap/mockServer";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import type { OrganizacionRole } from "@/types/roadmap";

interface Props {
  rol: string;
  usuario: string;
  tarea: string;
  /**
   * "subida": el primer PUT al almacenamiento falla; "url": la primera solicitud de URL falla;
   * "cuatroojos": la primera validación responde con la violación de cuatro ojos;
   * "lista": la primera carga del listado falla; "vacia": la tarea no tiene evidencia;
   * "conprimera": evi-ajena ya tiene la primera validación de un coordinador (RM-25c);
   * "primera409": la primera solicitud de primera validación responde que ya estaba registrada;
   * "validada": evi-ajena ya tiene primera validación y validación final con sus roles.
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

function evidenciaSembrada(id: string, tarea: string, subidaPor: string, archivo: string): EvidenciaConDobleValidacion {
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

/** RM-25c: siembra la primera validación (y la final) de evi-ajena según el caso pedido. */
function conDobleValidacion(evidencia: EvidenciaConDobleValidacion, fallo: string): EvidenciaConDobleValidacion {
  if (fallo !== "conprimera" && fallo !== "validada") return evidencia;
  const sembrada: EvidenciaConDobleValidacion = {
    ...evidencia,
    primera_validacion_por: "user-enc-02",
    primera_validacion_rol: "coordinador",
    primera_validacion_en: "2026-11-10T15:00:00.000Z",
  };
  if (fallo === "conprimera") return sembrada;
  return {
    ...sembrada,
    validation_status: "approved",
    validated_by: "user-dpo-01",
    validado_rol: "dpo",
    validated_at: "2026-11-11T16:30:00.000Z",
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
    const rolValido = (ROLES as readonly string[]).includes(rol) ? (rol as OrganizacionRole) : "coordinador";
    // Dos evidencias pendientes: una de otra persona y otra del usuario por defecto (coordinador).
    db.evidence.set(
      tarea,
      fallo === "vacia"
        ? []
        : [
            conDobleValidacion(evidenciaSembrada("evi-ajena", tarea, "user-resp-01", "rat_consolidado.pdf"), fallo),
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
      const primera = url.match(/\/evidence\/([^/]+)\/primera-validacion$/);
      if (metodo === "POST" && primera) {
        if (rolValido !== "coordinador") return respuestaError(403, "Rol no autorizado.", "FORBIDDEN", "change_role");
        if (unaVez("primera409")) {
          return respuestaError(409, "Ya registrada.", "RM_PRIMERA_VALIDACION_YA_REGISTRADA", "refresh");
        }
        const evidencia = (db.evidence.get(tarea) ?? []).find((e) => e.id === primera[1]) as
          | EvidenciaConDobleValidacion
          | undefined;
        if (!evidencia) return respuestaError(404, "Evidencia no encontrada", "NOT_FOUND", "none");
        if (evidencia.uploaded_by === usuario) {
          return respuestaError(409, "Cuatro ojos.", "SOD_VIOLATION", "ask_another_validator");
        }
        evidencia.primera_validacion_por = usuario;
        evidencia.primera_validacion_rol = "coordinador";
        evidencia.primera_validacion_en = new Date().toISOString();
        return new Response(JSON.stringify(evidencia), { status: 200, headers: { "Content-Type": "application/json" } });
      }
      return simulado(entrada, init);
    };

    setIdentitySession({ role: rolValido, userId: usuario });
    useRoadmapStore.getState().setSession({ role: rolValido, userId: usuario });
    setListo(true);

    return () => {
      window.fetch = original;
    };
  }, [rol, usuario, tarea, fallo]);

  return (
    <main className="h-screen overflow-auto bg-[var(--ui-campo)] p-6">
      <div className="mx-auto max-w-4xl">{listo ? <EvidenciaPanel taskId={tarea} titulo="Inventario y Registro de Actividades de Tratamiento" /> : null}</div>
    </main>
  );
}
