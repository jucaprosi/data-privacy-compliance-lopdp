"use client";

import { useEffect, useState } from "react";
import { useAuditStore } from "@/store/useAuditStore";
import type { BrechaCopiloto } from "@/types/copilot";

let sesionTemporal = 0;
// A new unsaved project, even with an identical company name, gets a new session.
useAuditStore.subscribe((state, previous) => {
  if ((!state.isConfigured && previous.isConfigured) ||
      (previous.proyectoActivo && !state.proyectoActivo)) sesionTemporal += 1;
});

export function useCopilotContext() {
  const audit = useAuditStore();
  const [resolved, setResolved] = useState({ identity: "", scope: "" });
  const identity = JSON.stringify([
    audit.proyectoActivo?.id ?? "temporary-" + sesionTemporal,
    audit.normativaSeleccionada, audit.companyData.razonSocial,
    audit.companyData.sector, audit.companyData.tamano,
  ]);
  const saved = Boolean(audit.proyectoActivo);
  useEffect(() => {
    let vigente = true;
    crypto.subtle.digest("SHA-256", new TextEncoder().encode(identity)).then((bytes) => {
      if (!vigente) return;
      const digest = Array.from(new Uint8Array(bytes), (n) => n.toString(16).padStart(2, "0")).join("");
      setResolved({ identity, scope: (saved ? "project:" : "temporary:") + digest });
    });
    return () => { vigente = false; };
  }, [identity, saved]);

  const assessment = audit.calcularResultadoAssessment("verificado");
  const propias = new Set(audit.respuestas.filter((r) => !r.esReferencia).map((r) => r.preguntaId));
  const brechas: BrechaCopiloto[] = assessment.brechas.filter((b) => propias.has(b.preguntaId)).map((b) => ({
    pregunta_id: b.preguntaId, control: b.control, dimension_id: b.dimensionId, severidad: b.severidad,
  }));
  return {
    scope: resolved.identity === identity ? resolved.scope : "",
    identity, saved, brechas, assessment,
    enabled: audit.isConfigured && audit.normativaSeleccionada === "LOPDP",
    configured: audit.isConfigured,
    normativa: audit.normativaSeleccionada,
  };
}

export const SOLICITUD_COPILOTO = "lopdp:consultar-brechas";
export function pedirPlanCopiloto(brechaId?: number) {
  window.dispatchEvent(new CustomEvent(SOLICITUD_COPILOTO, { detail: brechaId }));
  document.getElementById("copilot-question")?.focus();
}
