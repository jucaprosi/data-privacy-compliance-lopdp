"use client";

import type { FundamentoCopiloto, PlanCopiloto } from "@/types/copilot";

export function Fundamentos({ fuentes }: { fuentes: FundamentoCopiloto[] }) {
  return <ul className="space-y-1 text-[11px]" aria-label="Fundamento legal">
    {fuentes.map((f, index) => <li key={f.articulo + index} className="rounded border border-zinc-300 dark:border-[#26262b] p-2">
      <a className="text-sky-700 dark:text-sky-300 underline" href={f.url} target="_blank" rel="noreferrer">
        {f.articulo} · {f.titulo}
      </a>
      <p className="text-zinc-500">Versión: {f.version}</p>
      <p>{f.resumen}</p>
    </li>)}
  </ul>;
}

export default function CopilotPlan({ plan, vigente, onSeguir }: {
  plan: PlanCopiloto;
  vigente: boolean;
  onSeguir: () => void;
}) {
  return <article className="rounded-lg border border-zinc-300 dark:border-[#3a3a42] p-3 space-y-3" aria-label={"Plan del control " + plan.pregunta_id}>
    <div>
      <h4 className="font-semibold">P{plan.pregunta_id} · {plan.control}</h4>
      <p className="text-zinc-500">{plan.severidad} · {vigente ? "Brecha del assessment actual" : "Plan histórico: revisar frente al assessment actual"}</p>
    </div>
    <div><p className="font-semibold">Qué hacer</p>
      <ol className="list-decimal pl-4 space-y-1">{plan.pasos.map((paso, i) => <li key={i}>{paso}</li>)}</ol>
    </div>
    <p><strong>Responsable sugerido: </strong>{plan.responsable_sugerido}</p>
    <div><p className="font-semibold">Evidencias a preparar</p>
      <ul className="list-disc pl-4">{plan.evidencias.map((e, i) => <li key={i}>{e}</li>)}</ul>
    </div>
    <p><strong>Criterio para revisión del cierre: </strong>{plan.criterio_cierre}</p>
    <Fundamentos fuentes={plan.fundamento} />
    <button type="button" onClick={onSeguir} className="text-left underline text-violet-600 dark:text-violet-300">
      {plan.seguimiento || "Ayúdame con el siguiente paso"}
    </button>
  </article>;
}
