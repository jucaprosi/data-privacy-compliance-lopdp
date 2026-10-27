"use client";

/**
 * Historial de resultados sellados del diagnóstico (DIAG-03).
 *
 * Lee del servidor, nunca de un archivo: los resultados de la organización, del más reciente al
 * más antiguo, y si la cadena de huellas sigue íntegra. Los sella el DPO y los consultan el DPO,
 * el implementador, el coordinador y el administrador.
 */
import React, { useCallback, useEffect, useState } from "react";
import { AlertTriangle, GitCommit, Hash, RefreshCw, ShieldCheck, X } from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import { etiquetaEstadoCumplimiento } from "@/lib/estadosCumplimiento";
import type { EstadoCumplimiento } from "@/store/useAuditStore";
import {
  consultarHistorial,
  type HistorialResultados,
  type ResultadoSellado,
} from "@/lib/diagnostico/clienteResultados";

function formatearFecha(iso: string): string {
  try {
    return new Intl.DateTimeFormat("es-EC", { dateStyle: "medium", timeStyle: "short" }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function Indicadores({ resultado }: { resultado: ResultadoSellado }) {
  const i = resultado.indicadores;
  return (
    <dl className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono">
      <div>
        <dt className="text-[var(--ui-texto-suave)]">Cumplimiento</dt>
        <dd className="font-semibold">
          {i.cumplimiento ? "Sin incumplimientos críticos" : `${i.brechas_criticas} incumplimiento(s) crítico(s)`}
        </dd>
      </div>
      <div>
        <dt className="text-[var(--ui-texto-suave)]">Madurez</dt>
        <dd className="font-semibold">{i.madurez} %</dd>
      </div>
      <div>
        <dt className="text-[var(--ui-texto-suave)]">Respaldo con documentos</dt>
        <dd className="font-semibold">{i.respaldo_documental} %</dd>
      </div>
      <div>
        <dt className="text-[var(--ui-texto-suave)]">Riesgo que queda</dt>
        <dd className="font-semibold">{i.riesgo_residual} %</dd>
      </div>
    </dl>
  );
}

export default function AuditHistory() {
  const razonSocial = useAuditStore((state) => state.companyData.razonSocial);
  const [historial, setHistorial] = useState<HistorialResultados | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const [seleccionado, setSeleccionado] = useState<ResultadoSellado | null>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      setHistorial(await consultarHistorial());
    } catch (err) {
      setHistorial(null);
      setError(err instanceof Error ? err.message : "No se pudo leer el historial de resultados.");
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const resultados = historial?.resultados ?? [];
  const alterado = historial && !historial.cadena_integra
    ? resultados.find((r) => r.id === historial.primer_alterado)
    : undefined;

  return (
    <section aria-labelledby="historial-resultados-titulo" className="max-w-5xl mx-auto space-y-4 font-sans">
      <div className="p-5 rounded-xl bg-[var(--ui-superficie)] border border-[var(--ui-borde)] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[var(--ui-boton)] border border-[var(--ui-borde)] flex items-center justify-center">
            <GitCommit className="w-4 h-4" />
          </div>
          <div>
            <h1 id="historial-resultados-titulo" className="text-base font-bold tracking-tight">
              Historial de resultados sellados del diagnóstico
            </h1>
            <p className="text-xs text-[var(--ui-texto-suave)] mt-0.5">
              {razonSocial.trim() || "Organización activa"} · los sella el DPO; no se pueden editar ni borrar.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => void cargar()}
          disabled={cargando}
          className="px-3 py-1.5 rounded-lg bg-[var(--ui-boton)] hover:bg-[var(--ui-boton-hover)] border border-[var(--ui-borde)] text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${cargando ? "animate-spin" : ""}`} />
          <span>Actualizar</span>
        </button>
      </div>

      {error && (
        <div role="alert" className="badge-render-danger flex items-center gap-2 p-3 rounded-lg text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>No se pudo cargar el historial: {error}</span>
        </div>
      )}

      {historial && !historial.cadena_integra && (
        <div role="alert" className="badge-render-danger flex items-start gap-2 p-3 rounded-lg text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>
            La cadena de huellas no cuadra
            {alterado ? ` desde el resultado n.º ${alterado.secuencia}` : ""}: un resultado sellado se modificó fuera
            de la plataforma. Los resultados desde ese punto no son confiables.
          </span>
        </div>
      )}

      {historial && historial.cadena_integra && resultados.length > 0 && (
        <p className="badge-render-success inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-mono">
          <ShieldCheck className="w-3.5 h-3.5" />
          Cadena de huellas verificada: {resultados.length} resultado(s) sin alteraciones
        </p>
      )}

      {historial && !historial.dpo_vigente && (
        <div role="status" className="p-3 rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] text-xs leading-relaxed">
          Esta organización todavía no tiene un DPO con rol vigente. El administrador debe designarlo (puede ser una
          persona externa) para que el diagnóstico pueda responderse y sellarse.
        </div>
      )}

      {historial && resultados.length === 0 && !error && (
        <p className="p-4 rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] text-xs text-[var(--ui-texto-suave)]">
          Todavía no hay resultados sellados en esta organización.
        </p>
      )}

      {resultados.length > 0 && (
        <ul aria-label="Resultados sellados" className="space-y-2.5">
          {resultados.map((r) => (
            <li key={r.id}>
              <button
                type="button"
                onClick={() => setSeleccionado(r)}
                aria-label={`Resultado sellado n.º ${r.secuencia}`}
                className="w-full text-left p-4 rounded-xl bg-[var(--ui-superficie)] hover:bg-[var(--ui-superficie-2)] border border-[var(--ui-borde)] space-y-2.5 cursor-pointer transition"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                  <strong>Resultado n.º {r.secuencia}</strong>
                  <span className="font-mono text-[var(--ui-texto-suave)]">
                    {formatearFecha(r.sellado_en)} · {r.normativa} {r.version_normativa}
                  </span>
                </div>
                <Indicadores resultado={r} />
              </button>
            </li>
          ))}
        </ul>
      )}

      {seleccionado && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="detalle-resultado-titulo"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60"
        >
          <div className="w-full max-w-3xl max-h-[85vh] overflow-y-auto rounded-xl bg-[var(--ui-superficie)] border border-[var(--ui-borde)] p-5 space-y-4">
            <div className="flex items-center justify-between gap-2">
              <h2 id="detalle-resultado-titulo" className="text-sm font-bold">
                Resultado sellado n.º {seleccionado.secuencia}
              </h2>
              <button
                type="button"
                aria-label="Cerrar detalle"
                onClick={() => setSeleccionado(null)}
                className="p-1 rounded hover:bg-[var(--ui-boton)] cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <Indicadores resultado={seleccionado} />
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono">
              <div>
                <dt className="text-[var(--ui-texto-suave)]">Sellado el</dt>
                <dd>{formatearFecha(seleccionado.sellado_en)}</dd>
              </div>
              <div>
                <dt className="text-[var(--ui-texto-suave)]">Tamaño de la organización</dt>
                <dd>{seleccionado.tamano}</dd>
              </div>
              <div className="sm:col-span-2 break-all">
                <dt className="text-[var(--ui-texto-suave)] flex items-center gap-1">
                  <Hash className="w-3 h-3" /> Código de verificación
                </dt>
                <dd>{seleccionado.huella}</dd>
              </div>
              <div className="sm:col-span-2 break-all">
                <dt className="text-[var(--ui-texto-suave)]">Código del resultado anterior</dt>
                <dd>{seleccionado.huella_anterior}</dd>
              </div>
            </dl>
            <table className="w-full text-[11px]">
              <caption className="text-left text-xs font-semibold pb-2">
                Respuestas usadas ({seleccionado.respuestas.length})
              </caption>
              <thead>
                <tr className="text-left text-[var(--ui-texto-suave)] border-b border-[var(--ui-borde)]">
                  <th className="py-1 pr-2">Control</th>
                  <th className="py-1 pr-2">Estado</th>
                  <th className="py-1 pr-2">Respaldo declarado</th>
                  <th className="py-1">Respaldo sellado</th>
                </tr>
              </thead>
              <tbody>
                {seleccionado.respuestas.map((r) => (
                  <tr key={r.pregunta_id} className="border-b border-[var(--ui-borde)]">
                    <td className="py-1 pr-2">
                      P{r.pregunta_id} · {r.control}
                    </td>
                    <td className="py-1 pr-2">{etiquetaEstadoCumplimiento(r.estado as EstadoCumplimiento)}</td>
                    <td className="py-1 pr-2 font-mono">E{r.nivel_declarado}</td>
                    <td className="py-1 font-mono">
                      E{r.nivel_sellado}
                      {!r.con_documento && r.nivel_declarado > 0 ? " (sin documento comprobable)" : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
