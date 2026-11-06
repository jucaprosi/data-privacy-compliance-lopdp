"use client";

import { useEffect, useState } from "react";
import { consultarHistorial } from "@/lib/diagnostico/clienteResultados";
import { cargarHojaDeRuta, clasificarPlazos, tareasConFecha, type SemaforoPlazos as Plazos } from "@/lib/tableros/plazos";
import { resumirResultado, type ResumenTablero } from "@/lib/tableros/resumen";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import TarjetaDimension from "./TarjetaDimension";
import SemaforoPlazos from "./SemaforoPlazos";

type Estado =
  | { fase: "cargando" }
  | { fase: "error"; mensaje: string }
  | { fase: "sin-datos" }
  | { fase: "listo"; resumen: ResumenTablero };

/** Cuatro dimensiones por separado y brechas críticas, del último resultado sellado. Sin cifra única. */
export default function TableroOrganizacion({ onIrAlAssessment }: { onIrAlAssessment: () => void }) {
  const roadmapId = useRoadmapStore((s) => s.currentRoadmapId);
  const [estado, setEstado] = useState<Estado>({ fase: "cargando" });
  const [plazos, setPlazos] = useState<Plazos | null>(null);
  const [plazosError, setPlazosError] = useState(false);

  useEffect(() => {
    let vivo = true;
    consultarHistorial()
      .then((h) => {
        if (!vivo) return;
        const ultimo = h.resultados[0];
        setEstado(ultimo ? { fase: "listo", resumen: resumirResultado(ultimo) } : { fase: "sin-datos" });
      })
      .catch((e: unknown) => {
        if (vivo) setEstado({ fase: "error", mensaje: e instanceof Error ? e.message : "No se pudo leer el diagnóstico." });
      });
    return () => {
      vivo = false;
    };
  }, []);

  useEffect(() => {
    let vivo = true;
    setPlazos(null);
    setPlazosError(false);
    if (!roadmapId) return;
    cargarHojaDeRuta(roadmapId)
      .then((r) => vivo && setPlazos(clasificarPlazos(tareasConFecha(r))))
      .catch(() => vivo && setPlazosError(true));
    return () => {
      vivo = false;
    };
  }, [roadmapId]);

  if (estado.fase === "cargando") {
    return <p role="status" className="text-xs text-[var(--ui-texto-suave)]">Cargando el diagnóstico…</p>;
  }
  if (estado.fase === "error") {
    return <p role="alert" className="badge-render-danger p-3 rounded-xl text-xs">{estado.mensaje}</p>;
  }
  if (estado.fase === "sin-datos") {
    return (
      <section
        aria-labelledby="tablero-sin-datos"
        className="p-6 rounded-xl bg-[var(--ui-superficie)] border border-[var(--ui-borde)] space-y-3"
      >
        <h2 id="tablero-sin-datos" className="text-sm font-bold">Aún no hay resultados del diagnóstico</h2>
        <p className="text-xs text-[var(--ui-texto-suave)] leading-relaxed">
          El tablero muestra madurez, conformidad, evidencia y riesgo a partir del resultado que el DPO sella en el
          assessment. Mientras no exista, no hay nada que mostrar.
        </p>
        <button
          type="button"
          onClick={onIrAlAssessment}
          className="px-3.5 py-1.5 rounded-lg bg-[var(--ui-primario)] hover:bg-[var(--ui-primario-hover)] text-[var(--ui-primario-texto)] text-xs font-medium"
        >
          Ir al assessment
        </button>
      </section>
    );
  }

  const { resumen } = estado;
  return (
    <div className="space-y-5">
      <p className="text-[11px] text-[var(--ui-texto-suave)]">
        Resultado sellado n.º {resumen.secuencia}. Las cuatro dimensiones se leen por separado: la plataforma no las
        resume en una sola cifra.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {resumen.dimensiones.map((t) => (
          <TarjetaDimension key={t.id} tarjeta={t} />
        ))}
      </div>
      <section
        data-testid="brechas-criticas"
        aria-label="Brechas críticas abiertas"
        className="p-4 rounded-xl bg-[var(--ui-superficie)] border border-[var(--ui-borde)] flex items-center justify-between"
      >
        <span className="text-sm font-semibold">Brechas críticas abiertas</span>
        <span
          className={`badge-render-${resumen.brechasCriticasAbiertas > 0 ? "danger" : "success"} text-sm px-3 py-1 rounded font-bold`}
        >
          {resumen.brechasCriticasAbiertas}
        </span>
      </section>
      <section aria-labelledby="tablero-plazos" className="space-y-2">
        <h3 id="tablero-plazos" className="text-xs font-semibold uppercase tracking-wider text-[var(--ui-texto-suave)]">
          Plazos de tareas
        </h3>
        {plazos ? (
          <SemaforoPlazos plazos={plazos} />
        ) : (
          <p className="text-xs text-[var(--ui-texto-suave)]">
            {plazosError
              ? "No se pudieron leer los plazos de la hoja de ruta."
              : "Sin tareas con fecha: genera la hoja de ruta para ver sus plazos."}
          </p>
        )}
      </section>
    </div>
  );
}
