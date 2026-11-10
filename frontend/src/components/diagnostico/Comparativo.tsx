"use client";
/**
 * Diagnóstico › Comparativo (DIAG-06): el diagnóstico de prueba frente al real, por dimensión y por
 * control. Sin cifra única. Colores solo con las variables del tema.
 */
import { useEffect, useState } from "react";

import { consultarComparativo, tendencia, type ComparativoDiagnostico, type ControlBrecha } from "@/lib/diagnostico/comparativo";

const TEXTO_TENDENCIA = { mejora: "Mejora", empeora: "Empeora", igual: "Sin cambio", sin_dato: "Sin dato" } as const;
const CLASE_TENDENCIA = {
  mejora: "badge-render-success",
  empeora: "badge-render-danger",
  igual: "badge-render-warning",
  sin_dato: "badge-render-warning",
} as const;

function ListaBrechas({ titulo, controles, vacio }: { titulo: string; controles: ControlBrecha[]; vacio: string }) {
  return (
    <section aria-label={titulo} className="rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4">
      <h3 className="text-sm font-semibold">
        {titulo} <span className="text-[var(--ui-texto-suave)]">({controles.length})</span>
      </h3>
      {controles.length === 0 ? (
        <p className="mt-2 text-sm text-[var(--ui-texto-suave)]">{vacio}</p>
      ) : (
        <ul className="mt-2 space-y-1 text-sm">
          {controles.map((c) => (
            <li key={c.pregunta_id}>
              {c.control} <span className="text-[var(--ui-texto-suave)]">· {c.dimension}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function Comparativo() {
  const [datos, setDatos] = useState<ComparativoDiagnostico | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;
    consultarComparativo()
      .then((d) => vigente && setDatos(d))
      .catch((e: unknown) => vigente && setError(e instanceof Error ? e.message : "No se pudo leer el comparativo."));
    return () => {
      vigente = false;
    };
  }, []);

  if (error) return <p role="alert" className="p-6 text-sm">{error}</p>;
  if (!datos) return <p className="p-6 text-sm text-[var(--ui-texto-suave)]">Cargando el comparativo…</p>;
  if (!datos.comparable) {
    return (
      <div className="p-6">
        <h2 className="text-lg font-semibold">Comparativo del diagnóstico</h2>
        <p data-testid="comparativo-sin-comparar" className="mt-2 text-sm text-[var(--ui-texto-suave)]">
          {datos.motivo}
        </p>
      </div>
    );
  }
  return (
    <div className="space-y-6 p-6">
      <header>
        <h2 className="text-lg font-semibold">Comparativo del diagnóstico</h2>
        <p className="text-sm text-[var(--ui-texto-suave)]">
          Diagnóstico de prueba frente al real, dimensión por dimensión. No hay una cifra única de avance.
        </p>
      </header>
      <table className="w-full text-left text-sm" aria-label="Comparativo por dimensión">
        <thead>
          <tr className="border-b border-[var(--ui-borde)]">
            <th className="py-2">Dimensión</th>
            <th>Prueba</th>
            <th>Real</th>
            <th>Cambio</th>
            <th>Brechas cerradas</th>
            <th>Brechas nuevas</th>
            <th>Siguen</th>
          </tr>
        </thead>
        <tbody>
          {datos.por_dimension.map((f) => {
            const t = tendencia(f.diferencia_nivel);
            return (
              <tr key={f.dimension} className="border-b border-[var(--ui-borde)]">
                <td className="py-2">{f.nombre}</td>
                <td>{f.nivel_base ?? "—"}</td>
                <td>{f.nivel_actual ?? "—"}</td>
                <td><span className={CLASE_TENDENCIA[t]}>{TEXTO_TENDENCIA[t]}</span></td>
                <td>{f.cerradas}</td>
                <td>{f.nuevas}</td>
                <td>{f.siguen}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="grid gap-4 md:grid-cols-3">
        <ListaBrechas titulo="Brechas cerradas" controles={datos.brechas.cerradas} vacio="Ninguna brecha se cerró." />
        <ListaBrechas titulo="Brechas nuevas" controles={datos.brechas.nuevas} vacio="No aparecieron brechas nuevas." />
        <ListaBrechas titulo="Brechas que siguen" controles={datos.brechas.siguen} vacio="No quedan brechas abiertas." />
      </div>
    </div>
  );
}
