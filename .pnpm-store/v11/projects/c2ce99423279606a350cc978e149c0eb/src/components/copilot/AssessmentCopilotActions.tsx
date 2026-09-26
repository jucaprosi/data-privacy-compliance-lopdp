"use client";

import { useCopilotContext, pedirPlanCopiloto } from "./useCopilotContext";

export default function AssessmentCopilotActions() {
  const { brechas, enabled, assessment } = useCopilotContext();
  if (!enabled || !assessment.respuestasPropias) return null;
  return <section aria-label="Implementar las brechas con el asistente" className="rounded-xl border border-[#26262b] bg-[#141417] p-5 space-y-3">
    <h3 className="text-sm font-semibold text-white">Del assessment a la implementación</h3>
    <p className="text-xs text-zinc-400">El asistente usa las brechas de tus respuestas y la evidencia vinculada para proponer pasos, responsables, documentos y artículos de la ley.</p>
    {!brechas.length && <p className="text-xs text-zinc-400">No hay brechas críticas o altas en los controles propios evaluados. Puedes continuar consultando al asistente del panel derecho.</p>}
    <div className="space-y-2 max-h-64 overflow-y-auto">
      {brechas.map((b) => <div key={b.pregunta_id} className="flex items-center justify-between gap-3 border-t border-[#26262b] pt-2 text-xs">
        <span className="text-zinc-300">P{b.pregunta_id} · {b.control} · {b.severidad}</span>
        <button type="button" onClick={() => pedirPlanCopiloto(b.pregunta_id)} className="text-violet-300 shrink-0 underline"
          aria-label={"Resolver brecha P" + b.pregunta_id}>Cómo resolverla</button>
      </div>)}
    </div>
  </section>;
}
