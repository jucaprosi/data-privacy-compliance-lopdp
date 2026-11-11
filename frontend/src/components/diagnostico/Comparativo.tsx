"use client";
/**
 * Diagnóstico › Comparativo (DIAG-06): el diagnóstico de prueba frente al real, por dimensión y por
 * control. Sin cifra única. Colores solo con las variables del tema.
 */
import { useCallback, useEffect, useState } from "react";
import { ArrowDown, ArrowUp, Minus } from "lucide-react";

import { consultarComparativo, tendencia, type ComparativoDiagnostico, type ControlBrecha } from "@/lib/diagnostico/comparativo";

const TEXTO_TENDENCIA = { mejora: "Mejora", empeora: "Empeora", igual: "Sin cambio", sin_dato: "Sin dato" } as const;
const CLASE_TENDENCIA = {
  mejora: "badge-render-success",
  empeora: "badge-render-danger",
  igual: "badge-render-warning",
  sin_dato: "badge-render-warning",
} as const;
const ICONO_TENDENCIA = { mejora: ArrowUp, empeora: ArrowDown, igual: Minus, sin_dato: Minus } as const;

const MOTIVOS = {
  sin_real: "Falta el diagnóstico real: cuando el DPO lo selle podrás compararlo con el de prueba.",
  sin_sellos:
    "Todavía no hay diagnósticos sellados. El DPO sella primero el de prueba y después el real; entonces podrás compararlos.",
} as const;

const CELDA_NUMERICA = "text-right tabular-nums";

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
  const [fallo, setFallo] = useState(false);
  const [intento, setIntento] = useState(0);

  const cargar = useCallback(() => {
    setDatos(null);
    setFallo(false);
    setIntento((n) => n + 1);
  }, []);

  useEffect(() => {
    let vigente = true;
    consultarComparativo()
      .then((d) => vigente && setDatos(d))
      .catch(() => vigente && setFallo(true));
    return () => {
      vigente = false;
    };
  }, [intento]);

  if (fallo) {
    return (
      <div role="alert" className="space-y-3 p-6 text-sm">
        <p>No se pudo cargar el comparativo. Inténtalo de nuevo.</p>
        <button
          type="button"
          onClick={cargar}
          className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 hover:bg-[var(--ui-boton-hover)]"
        >
          Reintentar
        </button>
      </div>
    );
  }
  if (!datos) {
    return (
      <p role="status" className="p-6 text-sm text-[var(--ui-texto-suave)]">
        Cargando el comparativo…
      </p>
    );
  }
  if (!datos.comparable) {
    // El código manda; el texto del servidor es el respaldo si llega un código que no conocemos.
    const texto = (datos.codigo_motivo && MOTIVOS[datos.codigo_motivo]) || datos.motivo;
    return (
      <div className="p-6">
        <h2 className="text-lg font-semibold">Comparativo del diagnóstico</h2>
        <p data-testid="comparativo-sin-comparar" className="mt-2 text-sm text-[var(--ui-texto-suave)]">
          {texto}
        </p>
      </div>
    );
  }
  return (
    <div className="space-y-6 p-6">
      <header>
        <h2 className="text-lg font-semibold">Comparativo del diagnóstico</h2>
        <p className="text-sm text-[var(--ui-texto-suave)]">
          Diagnóstico de prueba frente al real, dimensión por dimensión. No hay una cifra única de avance. Compara los
          dos diagnósticos sellados.
        </p>
        <p className="mt-1 text-sm text-[var(--ui-texto-suave)]">
          Nivel de madurez de 1 (Inicial) a 5 (Optimizado). Un guion (—) significa que esa dimensión no tiene dato.
        </p>
      </header>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm" aria-label="Comparativo por dimensión">
          <caption className="sr-only">
            Nivel de cada dimensión en el diagnóstico de prueba y en el real, con sus brechas cerradas, nuevas y abiertas.
          </caption>
          <thead>
            <tr className="border-b border-[var(--ui-borde)]">
              <th scope="col" className="py-2">Dimensión</th>
              <th scope="col" className={CELDA_NUMERICA}>Nivel en la prueba</th>
              <th scope="col" className={CELDA_NUMERICA}>Nivel en el real</th>
              <th scope="col" className="px-3">Evolución</th>
              <th scope="col" className={CELDA_NUMERICA}>Brechas cerradas</th>
              <th scope="col" className={CELDA_NUMERICA}>Brechas nuevas</th>
              <th scope="col" className={CELDA_NUMERICA}>Siguen abiertas</th>
            </tr>
          </thead>
          <tbody>
            {datos.por_dimension.map((f) => {
              const t = tendencia(f.diferencia_nivel);
              const Icono = ICONO_TENDENCIA[t];
              return (
                <tr key={f.dimension} className="border-b border-[var(--ui-borde)]">
                  <th scope="row" className="py-2 font-normal">{f.nombre}</th>
                  <td className={CELDA_NUMERICA}>{f.nivel_base ?? "—"}</td>
                  <td className={CELDA_NUMERICA}>{f.nivel_actual ?? "—"}</td>
                  <td className="px-3">
                    <span className={`${CLASE_TENDENCIA[t]} inline-flex items-center gap-1`}>
                      <Icono aria-hidden="true" className="h-3 w-3" />
                      {TEXTO_TENDENCIA[t]}
                    </span>
                  </td>
                  <td className={CELDA_NUMERICA}>{f.cerradas}</td>
                  <td className={CELDA_NUMERICA}>{f.nuevas}</td>
                  <td className={CELDA_NUMERICA}>{f.siguen}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <ListaBrechas titulo="Brechas cerradas" controles={datos.brechas.cerradas} vacio="Ninguna brecha se cerró." />
        <ListaBrechas titulo="Brechas nuevas" controles={datos.brechas.nuevas} vacio="No aparecieron brechas nuevas." />
        <ListaBrechas titulo="Brechas que siguen" controles={datos.brechas.siguen} vacio="No quedan brechas abiertas." />
      </div>
    </div>
  );
}
