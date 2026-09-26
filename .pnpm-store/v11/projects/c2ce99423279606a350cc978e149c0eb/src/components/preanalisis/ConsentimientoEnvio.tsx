"use client";

import React, { useEffect, useId, useRef, useState } from "react";
import { ChevronDown, ChevronRight, ShieldAlert, ShieldCheck, X } from "lucide-react";
import type { EstadoServicioIA, FragmentoDocumento } from "@/lib/preanalisis/tipos";

export interface GrupoConsentimiento {
  clave: string;
  controlEtiqueta: string;
  documento: string;
  fragmentos: FragmentoDocumento[];
  piiEnmascarada: number;
}

interface ConsentimientoEnvioProps {
  grupos: GrupoConsentimiento[];
  estadoServicio: EstadoServicioIA | null;
  modoLote?: boolean;
  onConfirmar: () => void;
  onCancelar: () => void;
}

const SELECTOR_FOCO = 'button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

export default function ConsentimientoEnvio({
  grupos,
  estadoServicio,
  modoLote = false,
  onConfirmar,
  onCancelar,
}: ConsentimientoEnvioProps) {
  const idTitulo = useId();
  const idDescripcion = useId();
  const dialogoRef = useRef<HTMLDivElement>(null);
  const [abiertos, setAbiertos] = useState<Set<string>>(() => new Set());

  useEffect(() => {
    const previo = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    dialogoRef.current?.focus();
    return () => previo?.focus();
  }, []);

  const alPulsarTecla = (evento: React.KeyboardEvent<HTMLDivElement>) => {
    if (evento.key === "Escape") {
      evento.stopPropagation();
      onCancelar();
      return;
    }
    if (evento.key !== "Tab" || !dialogoRef.current) return;
    const foco = Array.from(dialogoRef.current.querySelectorAll<HTMLElement>(SELECTOR_FOCO));
    if (foco.length === 0) return;
    const primero = foco[0];
    const ultimo = foco[foco.length - 1];
    if (evento.shiftKey && (document.activeElement === primero || document.activeElement === dialogoRef.current)) {
      evento.preventDefault();
      ultimo.focus();
    } else if (!evento.shiftKey && document.activeElement === ultimo) {
      evento.preventDefault();
      primero.focus();
    }
  };

  const alternar = (clave: string) =>
    setAbiertos((prev) => {
      const siguiente = new Set(prev);
      if (siguiente.has(clave)) siguiente.delete(clave);
      else siguiente.add(clave);
      return siguiente;
    });

  const totalFragmentos = grupos.reduce((suma, g) => suma + g.fragmentos.length, 0);
  const totalPii = grupos.reduce((suma, g) => suma + g.piiEnmascarada, 0);
  const plegable = modoLote || grupos.length > 1;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70">
      <div
        ref={dialogoRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={idTitulo}
        aria-describedby={idDescripcion}
        tabIndex={-1}
        onKeyDown={alPulsarTecla}
        className="w-full max-w-2xl max-h-[90vh] flex flex-col bg-[#141417] border border-[#26262b] rounded-xl shadow-2xl outline-none text-zinc-200"
      >
        <div className="flex items-start justify-between gap-3 px-5 pt-4 pb-3 border-b border-[#26262b]">
          <div>
            <h2 id={idTitulo} className="text-xs font-bold uppercase tracking-wider text-white flex items-center">
              <ShieldAlert className="w-4 h-4 mr-1.5 text-[#ffab00]" />
              {modoLote ? "Confirmar envío por lote" : "Confirmar envío al modelo de IA"}
            </h2>
            <p id={idDescripcion} className="text-[11px] text-zinc-400 mt-1 leading-relaxed">
              Esto es exactamente lo que saldría hacia el modelo. Revísalo antes de autorizar el envío.
            </p>
          </div>
          <button
            type="button"
            onClick={onCancelar}
            className="p-1 text-zinc-400 hover:text-white cursor-pointer"
            aria-label="Cerrar sin enviar"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-3 space-y-3">
          <div className="flex items-start gap-2 p-2.5 rounded-lg bg-[#3892f3]/5 border border-[#3892f3]/25 text-[11px] text-zinc-300 leading-relaxed">
            <ShieldCheck className="w-3.5 h-3.5 mt-0.5 shrink-0 text-[#3892f3]" />
            <span>
              <strong className="text-white">El documento completo no se envía.</strong> Solo los {totalFragmentos}{" "}
              fragmento(s) listados abajo, ya enmascarados.
            </span>
          </div>

          <div className="p-2.5 rounded-lg bg-[#ffab00]/10 border border-[#ffab00]/30 text-[11px] text-[#ffab00] leading-relaxed">
            Datos personales enmascarados: <span className="font-mono font-bold">{totalPii}</span>. El enmascarado es
            parcial: no detecta todos los nombres propios. Si un fragmento contiene datos que no deban salir, cancela.
          </div>

          <div className="text-[11px] text-zinc-400">
            Proveedor:{" "}
            <span className="font-mono text-zinc-200">{estadoServicio?.proveedor ?? "no informado"}</span> · Modelo:{" "}
            <span className="font-mono text-zinc-200">{estadoServicio?.modelo ?? "no informado"}</span>
          </div>

          {plegable && (
            <div className="flex items-center justify-between gap-3 text-[11px] text-zinc-400">
              <span>Despliega cada control para leer el texto exacto de sus fragmentos antes de autorizar.</span>
              <button
                type="button"
                onClick={() =>
                  setAbiertos(
                    abiertos.size === grupos.length ? new Set() : new Set(grupos.map((g) => g.clave))
                  )
                }
                className="shrink-0 px-2 py-1 rounded-md border border-[#26262b] text-zinc-300 hover:bg-[#1e1e24] cursor-pointer"
              >
                {abiertos.size === grupos.length ? "Plegar todos" : "Desplegar todos"}
              </button>
            </div>
          )}

          <div className="space-y-2">
            {grupos.map((grupo) => {
              const abierto = !plegable || abiertos.has(grupo.clave);
              return (
                <div key={grupo.clave} className="border border-[#26262b] rounded-lg bg-[#0a0a0c] overflow-hidden">
                  {plegable ? (
                    <button
                      type="button"
                      onClick={() => alternar(grupo.clave)}
                      aria-expanded={abierto}
                      className="w-full flex items-center gap-2 px-3 py-2 text-left text-xs hover:bg-[#1e1e24] cursor-pointer"
                    >
                      {abierto ? (
                        <ChevronDown className="w-3.5 h-3.5 shrink-0" />
                      ) : (
                        <ChevronRight className="w-3.5 h-3.5 shrink-0" />
                      )}
                      <span className="font-semibold text-white truncate">{grupo.controlEtiqueta}</span>
                      <span className="font-mono text-[10px] text-[#9a3bf1] shrink-0">{grupo.documento}</span>
                      <span className="ml-auto text-[10px] font-mono text-zinc-500 shrink-0">
                        {grupo.fragmentos.length} fragm.
                      </span>
                    </button>
                  ) : (
                    <div className="flex items-center gap-2 px-3 py-2 text-xs border-b border-[#26262b]">
                      <span className="font-semibold text-white truncate">{grupo.controlEtiqueta}</span>
                      <span className="font-mono text-[10px] text-[#9a3bf1] shrink-0">{grupo.documento}</span>
                    </div>
                  )}
                  {abierto && (
                    <ul className="divide-y divide-[#26262b]">
                      {grupo.fragmentos.map((fragmento, indice) => (
                        <li key={`${grupo.clave}-${indice}`} className="px-3 py-2 space-y-1">
                          <div className="text-[10px] font-mono text-[#3892f3]">{fragmento.origen}</div>
                          <p className="text-[11px] text-zinc-300 whitespace-pre-wrap break-words leading-relaxed">
                            {fragmento.texto}
                          </p>
                        </li>
                      ))}
                      {grupo.fragmentos.length === 0 && (
                        <li className="px-3 py-2 text-[11px] text-zinc-500 italic">Sin fragmentos para enviar.</li>
                      )}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-[#26262b]">
          <button
            type="button"
            onClick={onCancelar}
            className="px-3 py-1.5 rounded-md border border-[#26262b] text-xs text-zinc-300 hover:bg-[#1e1e24] cursor-pointer"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onConfirmar}
            disabled={totalFragmentos === 0}
            className="px-3 py-1.5 rounded-md bg-[#9a3bf1] text-white text-xs font-semibold hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          >
            Enviar y analizar
          </button>
        </div>
      </div>
    </div>
  );
}
