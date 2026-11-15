"use client";
/**
 * DIAG-07: Diagnóstico › Revisión. El DPO revisa lo declarado por quien respondió, ve el nivel de
 * evidencia que calcula el sistema (de solo lectura), objeta con motivo y sella. Con objeciones
 * abiertas «Sellar el diagnóstico» queda deshabilitado y explica por qué.
 */
import React, { useCallback, useEffect, useId, useRef, useState } from "react";
import { Lock } from "lucide-react";

import { consultarHistorial, sellarDiagnostico } from "@/lib/diagnostico/clienteResultados";
import {
  LONGITUD_MINIMA_MOTIVO,
  abiertaPorPregunta,
  cargarObjeciones,
  cargarRevision,
  motivoSuficiente,
  objetar,
  textoBloqueoSello,
  type FilaRevision,
  type Objecion,
} from "@/lib/diagnostico/objeciones";
import { etiquetaEstadoCumplimiento } from "@/lib/estadosCumplimiento";
import { useAuditStore } from "@/store/useAuditStore";

const SELLOS_MAXIMOS = 2;

function codigoDe(fila: FilaRevision): string {
  return `P${String(fila.pregunta_id).padStart(2, "0")}`;
}

function DialogoObjecion({
  fila,
  alCerrar,
  alObjetar,
}: {
  fila: FilaRevision;
  alCerrar: () => void;
  alObjetar: (motivo: string) => Promise<void>;
}) {
  const [motivo, setMotivo] = useState("");
  const [intentado, setIntentado] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cancelar = useRef<HTMLButtonElement>(null);
  const dialogo = useRef<HTMLDivElement>(null);
  const ids = useId();
  const codigo = codigoDe(fila);
  const largo = motivo.trim().length;
  const insuficiente = intentado && !motivoSuficiente(motivo);

  useEffect(() => cancelar.current?.focus(), []);

  const atraparFoco = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") return alCerrar();
    if (e.key !== "Tab" || !dialogo.current) return;
    const focos = dialogo.current.querySelectorAll<HTMLElement>("textarea, button:not([disabled])");
    const primero = focos[0];
    const ultimo = focos[focos.length - 1];
    if (e.shiftKey && document.activeElement === primero) {
      e.preventDefault();
      ultimo.focus();
    } else if (!e.shiftKey && document.activeElement === ultimo) {
      e.preventDefault();
      primero.focus();
    }
  };

  const enviar = async () => {
    setIntentado(true);
    if (!motivoSuficiente(motivo)) return;
    setEnviando(true);
    setError(null);
    try {
      await alObjetar(motivo);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo registrar la objeción.");
      setEnviando(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div
        ref={dialogo}
        role="dialog"
        aria-modal="true"
        aria-labelledby={`${ids}-titulo`}
        onKeyDown={atraparFoco}
        className="w-full max-w-md rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-5 space-y-4"
      >
        <h2 id={`${ids}-titulo`} className="text-sm font-semibold text-white">
          Objetar la respuesta de {codigo}
        </h2>
        <div className="space-y-1">
          <label htmlFor={`${ids}-motivo`} className="block text-xs font-medium text-white">
            Motivo de la objeción
          </label>
          <textarea
            id={`${ids}-motivo`}
            data-testid="motivo-objecion"
            value={motivo}
            onChange={(e) => setMotivo(e.target.value)}
            rows={4}
            aria-invalid={insuficiente}
            aria-describedby={`${ids}-contador ${ids}-error`}
            className="w-full rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-2 text-xs text-white"
          />
          <p id={`${ids}-contador`} className="text-[11px] text-[var(--ui-texto-suave)]">
            {largo} de {LONGITUD_MINIMA_MOTIVO} caracteres como mínimo
          </p>
          <p id={`${ids}-error`} aria-live="polite" className="text-[11px] text-white">
            {insuficiente ? "Explica el motivo con al menos 20 caracteres." : error}
          </p>
        </div>
        <div className="flex justify-end gap-2">
          <button
            ref={cancelar}
            type="button"
            onClick={alCerrar}
            className="px-4 py-2 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-campo)] text-xs text-white cursor-pointer"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => void enviar()}
            disabled={enviando}
            className="px-4 py-2 rounded-lg bg-[var(--ui-primario)] text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] text-xs font-semibold cursor-pointer disabled:opacity-50"
          >
            Objetar la respuesta
          </button>
        </div>
      </div>
    </div>
  );
}

function RespuestaDeclarada({ fila }: { fila: FilaRevision }) {
  if (fila.no_aplica) {
    return (
      <div className="space-y-1">
        <span>No aplica</span>
        {fila.justificacion_no_aplica && (
          <p className="text-[11px] text-[var(--ui-texto-suave)]">Justificación: {fila.justificacion_no_aplica}</p>
        )}
      </div>
    );
  }
  return (
    <div className="space-y-1">
      <span>{etiquetaEstadoCumplimiento(fila.estado)}</span>
      <p className="text-[11px] text-[var(--ui-texto-suave)]">Nivel de evidencia declarado: {fila.nivel_evidencia}</p>
    </div>
  );
}

export default function GrillaRevision() {
  const perfil = useAuditStore((s) => s.companyData.perfil);
  const [filas, setFilas] = useState<FilaRevision[] | null>(null);
  const [objeciones, setObjeciones] = useState<Objecion[]>([]);
  const [sellos, setSellos] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [estado, setEstado] = useState<string | null>(null);
  const [objetando, setObjetando] = useState<FilaRevision | null>(null);
  const [confirmando, setConfirmando] = useState(false);
  const [sellando, setSellando] = useState(false);
  const idBloqueo = useId();

  const recargar = useCallback(async () => {
    try {
      const [revision, todas, historial] = await Promise.all([
        cargarRevision(),
        cargarObjeciones(false),
        consultarHistorial(),
      ]);
      setFilas(revision);
      setObjeciones(todas);
      setSellos(historial.resultados.length);
      setError(null);
    } catch {
      setError("No se pudo cargar la revisión del diagnóstico. Inténtalo de nuevo.");
    }
  }, []);

  useEffect(() => {
    void recargar();
  }, [recargar]);

  const porPregunta = abiertaPorPregunta(objeciones);
  const bloqueo = textoBloqueoSello(porPregunta.size);
  const agotado = sellos !== null && sellos >= SELLOS_MAXIMOS;
  const siguiente = sellos === 0 ? "prueba" : "real";
  const sinFilas = filas !== null && filas.length === 0;
  const sellarDeshabilitado = bloqueo !== null || sellando || agotado || sinFilas || filas === null;

  const sellar = async () => {
    setConfirmando(false);
    setSellando(true);
    setEstado(null);
    try {
      await sellarDiagnostico(perfil);
      setEstado("Diagnóstico sellado.");
      await recargar();
    } catch {
      setError("No se pudo sellar el diagnóstico. Revisa que no haya objeciones abiertas.");
    } finally {
      setSellando(false);
    }
  };

  const alPulsarSellar = () => {
    if (sellarDeshabilitado) return;
    if (siguiente === "real") setConfirmando(true);
    else void sellar();
  };

  return (
    <section className="space-y-4" aria-labelledby="titulo-revision">
      <h1 id="titulo-revision" className="text-lg font-semibold text-white">
        Revisión del diagnóstico
      </h1>

      {error && (
        <p role="alert" className="badge-render-danger rounded px-2 py-1 text-xs">
          {error}
        </p>
      )}
      <p role="status" className="text-xs text-[var(--ui-texto-suave)]">
        {estado}
      </p>

      {sinFilas && <p className="text-sm text-[var(--ui-texto-suave)]">Aún no hay respuestas para revisar.</p>}

      {filas !== null && filas.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-[var(--ui-borde)]">
          <table className="w-full text-xs text-white" data-testid="grilla-revision">
            <thead className="bg-[var(--ui-campo)] text-left">
              <tr>
                <th scope="col" className="p-2">Pregunta</th>
                <th scope="col" className="p-2">Respuesta declarada</th>
                <th scope="col" className="p-2">Evidencia vinculada</th>
                <th scope="col" className="p-2">Nivel calculado</th>
                <th scope="col" className="p-2">Objeción</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((fila) => {
                const abierta = porPregunta.get(fila.pregunta_id);
                const codigo = codigoDe(fila);
                return (
                  <tr key={fila.pregunta_id} data-testid={`fila-revision-${fila.pregunta_id}`} className="border-t border-[var(--ui-borde)] align-top">
                    <th scope="row" className="p-2 text-left font-normal">
                      <span className="font-semibold">{codigo}</span>
                      <span className="block text-[11px] text-[var(--ui-texto-suave)]">{fila.control}</span>
                    </th>
                    <td className="p-2"><RespuestaDeclarada fila={fila} /></td>
                    <td className="p-2">{fila.con_documento ? "Con documento" : "Sin documento"}</td>
                    <td className="p-2">{fila.nivel_calculado}</td>
                    <td className="p-2">
                      {abierta ? (
                        <div className="space-y-1">
                          <span className="badge-render-warning inline-block rounded px-1.5 py-0.5 text-[11px] font-semibold">
                            Objetada
                          </span>
                          <p className="text-[11px]">Motivo: {abierta.motivo}</p>
                        </div>
                      ) : (
                        <button
                          type="button"
                          aria-label={`Objetar la pregunta ${codigo}`}
                          onClick={() => setObjetando(fila)}
                          className="px-3 py-1.5 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-campo)] hover:bg-[var(--ui-boton)] text-xs cursor-pointer"
                        >
                          Objetar
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center gap-2">
        <button
          type="button"
          data-testid="sellar-desde-revision"
          aria-disabled={sellarDeshabilitado}
          aria-describedby={bloqueo ? idBloqueo : undefined}
          onClick={alPulsarSellar}
          className={`w-full sm:w-auto px-5 py-2.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 ${
            sellarDeshabilitado
              ? "bg-[var(--ui-campo)] text-[var(--ui-texto-suave)] cursor-not-allowed"
              : "bg-[var(--ui-primario)] text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] cursor-pointer"
          }`}
        >
          <Lock aria-hidden="true" className="w-3.5 h-3.5" />
          <span>{sellando ? "Sellando…" : "Sellar el diagnóstico"}</span>
        </button>
        {bloqueo && (
          <p id={idBloqueo} data-testid="bloqueo-sello" className="text-xs text-[var(--ui-texto-suave)]">
            {bloqueo}
          </p>
        )}
      </div>

      {objetando && (
        <DialogoObjecion
          fila={objetando}
          alCerrar={() => setObjetando(null)}
          alObjetar={async (motivo) => {
            await objetar(objetando.pregunta_id, motivo);
            setObjetando(null);
            setEstado("Objeción registrada.");
            await recargar();
          }}
        />
      )}

      {confirmando && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="titulo-sellar-real-revision"
            aria-describedby="texto-sellar-real-revision"
            className="w-full max-w-sm rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-5 space-y-4"
            onKeyDown={(e) => {
              if (e.key === "Escape") setConfirmando(false);
            }}
          >
            <h2 id="titulo-sellar-real-revision" className="text-sm font-semibold text-white">
              ¿Sellar el diagnóstico real?
            </h2>
            <p id="texto-sellar-real-revision" className="text-xs text-[var(--ui-texto-suave)]">
              Quedará como línea base y nadie podrá cambiar sus respuestas.
            </p>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                autoFocus
                onClick={() => setConfirmando(false)}
                className="px-4 py-2 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-campo)] text-xs text-white cursor-pointer"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={() => void sellar()}
                className="px-4 py-2 rounded-lg bg-[var(--ui-primario)] text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] text-xs font-semibold cursor-pointer"
              >
                Sellar diagnóstico real
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
