import type { TarjetaDimension as Tarjeta } from "@/lib/tableros/resumen";

const ETIQUETA = { success: "Favorable", warning: "Atención", danger: "Crítico" } as const;

/** Una dimensión del diagnóstico, sola: nunca se promedia con las demás. Reutilizable por la cartera. */
export default function TarjetaDimension({ tarjeta }: { tarjeta: Tarjeta }) {
  return (
    <article
      data-testid={`dimension-${tarjeta.id}`}
      aria-label={tarjeta.titulo}
      className="p-4 rounded-xl bg-[var(--ui-superficie)] border border-[var(--ui-borde)] space-y-2"
    >
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--ui-texto-suave)]">{tarjeta.titulo}</h3>
        <span className={`badge-render-${tarjeta.semaforo} text-[10px] px-2 py-0.5 rounded font-semibold`}>
          {ETIQUETA[tarjeta.semaforo]}
        </span>
      </div>
      <p className="text-base font-bold">{tarjeta.valor}</p>
      <p className="text-[11px] text-[var(--ui-texto-suave)] leading-relaxed">{tarjeta.detalle}</p>
    </article>
  );
}
