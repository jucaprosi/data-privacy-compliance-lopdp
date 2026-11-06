import type { SemaforoPlazos as Plazos } from "@/lib/tableros/plazos";
import { DIAS_PROXIMAS } from "@/lib/tableros/plazos";

/** Semáforo de plazos de las tareas con fecha. Reutilizable por la cartera. */
export default function SemaforoPlazos({ plazos }: { plazos: Plazos }) {
  const filas = [
    { clave: "vencidas", tipo: "danger", texto: "Vencidas", n: plazos.vencidas },
    { clave: "proximas", tipo: "warning", texto: `Vencen en ${DIAS_PROXIMAS} días o menos`, n: plazos.proximas },
    { clave: "en-plazo", tipo: "success", texto: "En plazo", n: plazos.enPlazo },
  ] as const;
  return (
    <ul aria-label="Plazos de tareas" className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {filas.map((f) => (
        <li
          key={f.clave}
          data-testid={`plazo-${f.clave}`}
          className="p-3 rounded-xl bg-[var(--ui-superficie)] border border-[var(--ui-borde)] flex items-center justify-between"
        >
          <span className="text-xs">{f.texto}</span>
          <span className={`badge-render-${f.tipo} text-xs px-2 py-0.5 rounded font-bold`}>{f.n}</span>
        </li>
      ))}
    </ul>
  );
}
