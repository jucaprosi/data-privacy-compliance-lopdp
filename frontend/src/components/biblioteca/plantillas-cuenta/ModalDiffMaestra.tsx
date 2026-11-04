"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Diálogo modal para comparar la copia de cuenta con la versión maestra publicada vigente (BIB-401).
 *
 * Muestra el diff unificado línea a línea usando únicamente variables de diseño acromático (--ui-*).
 */
import React from "react";
import { GitCompare, X, Check } from "lucide-react";

interface Props {
  abierto: boolean;
  cerrar: () => void;
  maestraCodigo: string;
  maestraVigente: string;
  cambios: string[];
  alAplicar: () => Promise<void>;
  aplicando: boolean;
}

export default function ModalDiffMaestra({
  abierto,
  cerrar,
  maestraCodigo,
  maestraVigente,
  cambios,
  alAplicar,
  aplicando,
}: Props) {
  if (!abierto) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="titulo-modal-diff"
      data-testid="modal-diff-maestra"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
    >
      <div className="flex max-h-[85vh] w-full max-w-3xl flex-col rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-fondo)] shadow-lg">
        {/* Cabecera */}
        <div className="flex items-center justify-between border-b border-[var(--ui-borde)] px-4 py-3">
          <div className="flex items-center gap-2">
            <GitCompare className="h-5 w-5 text-[var(--ui-primario)]" />
            <h3 id="titulo-modal-diff" className="font-semibold text-sm">
              Comparación de {maestraCodigo} con maestra vigente (v{maestraVigente})
            </h3>
          </div>
          <button
            type="button"
            aria-label="Cerrar modal"
            onClick={cerrar}
            className="rounded-md p-1 text-[var(--ui-texto-suave)] hover:bg-[var(--ui-boton-hover)] cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Cuerpo del diff */}
        <div className="flex-1 overflow-auto p-4 text-xs">
          {cambios.length === 0 ? (
            <p className="text-[var(--ui-texto-suave)] italic">
              No se detectaron diferencias textuales con la maestra vigente.
            </p>
          ) : (
            <div
              data-testid="contenedor-diff"
              className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-3 font-mono leading-relaxed"
            >
              {cambios.map((linea, idx) => {
                let estilo = "text-[var(--ui-texto)]";
                if (linea.startsWith("+") && !linea.startsWith("+++")) {
                  estilo = "text-emerald-500 bg-emerald-500/10";
                } else if (linea.startsWith("-") && !linea.startsWith("---")) {
                  estilo = "text-rose-500 bg-rose-500/10";
                } else if (linea.startsWith("@@")) {
                  estilo = "text-[var(--ui-primario)] opacity-80";
                }
                return (
                  <div key={idx} className={`px-1 rounded-sm whitespace-pre-wrap ${estilo}`}>
                    {linea}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Acciones */}
        <div className="flex items-center justify-end gap-2 border-t border-[var(--ui-borde)] px-4 py-3">
          <button
            type="button"
            onClick={cerrar}
            className="rounded-md border border-[var(--ui-borde)] px-3 py-1.5 font-medium text-xs hover:bg-[var(--ui-boton-hover)] cursor-pointer"
          >
            Cerrar
          </button>
          <button
            type="button"
            data-testid="boton-confirmar-aplicar-maestra"
            onClick={alAplicar}
            disabled={aplicando}
            className="flex items-center gap-1 rounded-md bg-[var(--ui-primario)] px-3 py-1.5 font-medium text-xs text-[var(--ui-primario-texto)] hover:opacity-90 disabled:opacity-50 cursor-pointer"
          >
            <Check className="h-3.5 w-3.5" />
            {aplicando ? "Aplicando..." : "Aplicar maestra"}
          </button>
        </div>
      </div>
    </div>
  );
}
