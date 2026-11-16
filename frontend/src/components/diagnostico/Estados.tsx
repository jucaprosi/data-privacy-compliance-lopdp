"use client";
/**
 * Diagnóstico › Estado actual (DIAG-12): los estados emitidos por el DPO a partir del diagnóstico real,
 * el actual y su comparación por dimensión y por control. Sin cifra única. Colores con variables del tema.
 */
import { useCallback, useEffect, useState } from "react";
import { ShieldAlert } from "lucide-react";

import { tendencia } from "@/lib/diagnostico/comparativo";
import {
  ErrorEstados,
  compararEstado,
  consultarEstados,
  emitirEstado,
  type ComparacionEstado,
  type ComparativoEstado,
  type HistorialEstados,
} from "@/lib/diagnostico/estados";
import { puedeSellar, rolesDelUsuario } from "@/lib/diagnostico/roles";

const TEXTO_TENDENCIA = { mejora: "Mejora", empeora: "Empeora", igual: "Sin cambio", sin_dato: "Sin dato" } as const;
const CLASE_TENDENCIA = {
  mejora: "badge-render-success",
  empeora: "badge-render-danger",
  igual: "badge-render-warning",
  sin_dato: "badge-render-warning",
} as const;

const AVISO_EMITIR = "No se pudo emitir el estado. Inténtalo de nuevo.";
const AVISO_POR_CODIGO: Record<string, string> = {
  DIAG_ESTADO_SIN_DIAGNOSTICO_REAL: "Primero hay que sellar el diagnóstico real.",
};
const BOTON = "rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 text-sm hover:bg-[var(--ui-boton-hover)]";

const fecha = (iso: string) => new Date(iso).toLocaleDateString("es-EC", { year: "numeric", month: "long", day: "numeric" });
const tareas = (n: number) => (n === 0 ? "sin tareas nuevas" : n === 1 ? "1 tarea sumada" : `${n} tareas sumadas`);

export default function Estados() {
  const [historial, setHistorial] = useState<HistorialEstados | null>(null);
  const [fallo, setFallo] = useState(false);
  const [puedeEmitir, setPuedeEmitir] = useState(false);
  const [confirmando, setConfirmando] = useState(false);
  const [emitiendo, setEmitiendo] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);
  const [emitido, setEmitido] = useState<number | null>(null);
  const [con, setCon] = useState<ComparacionEstado>("real");
  const [comparativo, setComparativo] = useState<ComparativoEstado | null>(null);
  const [intento, setIntento] = useState(0);

  const recargar = useCallback(() => setIntento((n) => n + 1), []);

  useEffect(() => {
    let vigente = true;
    setFallo(false);
    consultarEstados()
      .then((h) => vigente && setHistorial(h))
      .catch(() => vigente && setFallo(true));
    rolesDelUsuario().then((roles) => vigente && setPuedeEmitir(puedeSellar(roles)));
    return () => {
      vigente = false;
    };
  }, [intento]);

  const actual = historial?.estados[0] ?? null;
  const hayAnterior = (historial?.estados.length ?? 0) > 1;
  const modo: ComparacionEstado = con === "anterior" && hayAnterior ? "anterior" : "real";

  useEffect(() => {
    let vigente = true;
    setComparativo(null);
    if (actual) {
      compararEstado(actual.id, modo)
        .then((c) => vigente && setComparativo(c))
        .catch(() => vigente && setAviso("No se pudo comparar el estado. Inténtalo de nuevo."));
    }
    return () => {
      vigente = false;
    };
  }, [actual?.id, modo]); // eslint-disable-line react-hooks/exhaustive-deps

  async function emitir() {
    setAviso(null);
    setEmitido(null);
    setEmitiendo(true);
    try {
      const nuevo = await emitirEstado();
      setConfirmando(false);
      setEmitido(nuevo.secuencia);
      recargar();
    } catch (e) {
      setConfirmando(false);
      setAviso((e instanceof ErrorEstados && e.codigo && AVISO_POR_CODIGO[e.codigo]) || AVISO_EMITIR);
    } finally {
      setEmitiendo(false);
    }
  }

  if (fallo) {
    return (
      <div role="alert" className="space-y-3 p-6 text-sm">
        <p>No se pudieron cargar los estados. Inténtalo de nuevo.</p>
        <button type="button" onClick={recargar} className={BOTON}>Reintentar</button>
      </div>
    );
  }
  if (!historial) {
    return <p role="status" className="p-6 text-sm text-[var(--ui-texto-suave)]">Cargando los estados…</p>;
  }

  return (
    <div className="space-y-6 p-6">
      {!historial.cadena_integra && (
        <div role="alert" className="flex items-start gap-3 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie-2)] p-4 text-sm">
          <ShieldAlert aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0" />
          <p className="font-medium">
            Los estados emitidos no coinciden con su registro de integridad. No los uses como evidencia hasta que el
            equipo de EVYDENTIA lo revise.
          </p>
        </div>
      )}

      <header className="space-y-1">
        <h2 className="text-lg font-semibold">Estado actual del diagnóstico</h2>
        <p className="text-sm text-[var(--ui-texto-suave)]">
          Un estado es una fotografía del avance en una fecha de corte. Cada estado parte de los niveles del
          diagnóstico real y suma las tareas cerradas con evidencia validada. No hay una cifra única de avance, y el
          diagnóstico sellado no cambia.
        </p>
        <p className="text-sm text-[var(--ui-texto-suave)]">
          Nivel de madurez de 1 (Inicial) a 5 (Optimizado). Un guion (—) significa que no hay dato.
        </p>
        {puedeEmitir && !confirmando && (
          <button
            type="button"
            onClick={() => setConfirmando(true)}
            className="mt-2 rounded-md border border-[var(--ui-borde)] bg-[var(--ui-primario)] px-3 py-1.5 text-sm text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)]"
          >
            Emitir un estado
          </button>
        )}
        {puedeEmitir && confirmando && (
          <div role="group" aria-label="Confirmar la emisión" className="mt-2 space-y-2 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4 text-sm">
            <p>¿Emitir un estado? Quedará registrado con la fecha de hoy y no se podrá borrar.</p>
            <div className="flex gap-2">
              <button type="button" autoFocus onClick={() => setConfirmando(false)} disabled={emitiendo} className={BOTON}>
                Cancelar
              </button>
              <button
                type="button"
                onClick={emitir}
                disabled={emitiendo}
                aria-busy={emitiendo}
                className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-primario)] px-3 py-1.5 text-sm text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)]"
              >
                {emitiendo ? "Emitiendo…" : "Emitir estado"}
              </button>
            </div>
          </div>
        )}
        {aviso && <p role="alert" className="text-sm">{aviso}</p>}
        {emitido !== null && <p role="status" className="text-sm">Estado {emitido} emitido.</p>}
      </header>

      {!actual ? (
        <p data-testid="estados-vacio" className="text-sm text-[var(--ui-texto-suave)]">
          Todavía no hay estados emitidos.{puedeEmitir ? " Emite el primero cuando el diagnóstico real esté sellado." : " El DPO emite el primero cuando el diagnóstico real esté sellado."}
        </p>
      ) : (
        <>
          <section aria-label="Estados emitidos">
            <h3 className="text-sm font-semibold">Estados emitidos</h3>
            <ol className="mt-2 space-y-1 text-sm">
              {historial.estados.map((e) => (
                <li key={e.id}>
                  Estado {e.secuencia} · corte del {fecha(e.fecha_corte)} · {tareas(e.tareas.length)}
                  {e.id === actual.id && (
                    <span className="badge-render-success ml-2">Actual</span>
                  )}
                </li>
              ))}
            </ol>
            <p className="mt-1 text-xs text-[var(--ui-texto-suave)]">Cuentan las tareas cerradas con evidencia validada.</p>
          </section>

          <section aria-label="Comparación del estado actual" className="space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <label htmlFor="estados-comparar" className="text-sm font-semibold">
                Comparar el estado {actual.secuencia} con:
              </label>
              <select
                id="estados-comparar"
                value={modo}
                onChange={(e) => setCon(e.target.value as ComparacionEstado)}
                className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-2 py-1 text-sm"
              >
                <option value="real">el diagnóstico real</option>
                {hayAnterior && <option value="anterior">el estado anterior</option>}
              </select>
            </div>
            {comparativo && comparativo.comparable && (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm" aria-label="Estado por dimensión">
                    <caption className="sr-only">Nivel de cada dimensión en el punto de partida y en el estado actual.</caption>
                    <thead>
                      <tr className="border-b border-[var(--ui-borde)]">
                        <th scope="col" className="py-2">Dimensión</th>
                        <th scope="col" className="text-right">Nivel de partida</th>
                        <th scope="col" className="text-right">Nivel actual</th>
                        <th scope="col" className="px-3">Evolución</th>
                        <th scope="col" className="text-right">Brechas cerradas</th>
                        <th scope="col" className="text-right">Brechas nuevas</th>
                        <th scope="col" className="text-right">Siguen abiertas</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparativo.por_dimension.map((f) => {
                        const t = tendencia(f.diferencia_nivel);
                        return (
                          <tr key={f.dimension} className="border-b border-[var(--ui-borde)]">
                            <th scope="row" className="py-2 font-normal">{f.nombre}</th>
                            <td className="text-right tabular-nums">{f.nivel_base ?? "—"}</td>
                            <td className="text-right tabular-nums">{f.nivel_actual ?? "—"}</td>
                            <td className="px-3"><span className={CLASE_TENDENCIA[t]}>{TEXTO_TENDENCIA[t]}</span></td>
                            <td className="text-right tabular-nums">{f.cerradas}</td>
                            <td className="text-right tabular-nums">{f.nuevas}</td>
                            <td className="text-right tabular-nums">{f.siguen}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <div className="grid gap-4 md:grid-cols-3">
                  {([
                    ["Brechas cerradas", comparativo.brechas.cerradas],
                    ["Brechas nuevas", comparativo.brechas.nuevas],
                    ["Brechas que siguen", comparativo.brechas.siguen],
                  ] as const).map(([titulo, controles]) => (
                    <section key={titulo} aria-label={titulo} className="rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4">
                      <h4 className="text-sm font-semibold">{titulo} <span className="text-[var(--ui-texto-suave)]">({controles.length})</span></h4>
                      <ul className="mt-2 space-y-1 text-sm">
                        {controles.map((c) => (
                          <li key={c.pregunta_id}>{c.control} <span className="text-[var(--ui-texto-suave)]">· {c.dimension}</span></li>
                        ))}
                      </ul>
                    </section>
                  ))}
                </div>
              </>
            )}
          </section>
        </>
      )}
    </div>
  );
}
