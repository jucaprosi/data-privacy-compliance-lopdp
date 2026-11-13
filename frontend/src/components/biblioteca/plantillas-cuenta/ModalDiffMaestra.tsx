"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Diálogo para comparar la copia de la cuenta con la maestra vigente (BIB-401).
 *
 * Foco inicial en «Cerrar», Escape cierra, el foco queda atrapado dentro y vuelve a quien abrió al cerrar
 * (lo devuelve la vista). Las líneas del diff no dependen solo del color: llevan el prefijo +/− y un texto oculto.
 */
import React from "react";
import { GitCompare, X, Check } from "lucide-react";

interface Props {
  abierto: boolean;
  cerrar: () => void;
  codigo: string;
  /** Versión de la maestra vigente; vacía mientras se carga. */
  versionMaestra: string;
  cambios: string[];
  cargando: boolean;
  /** Mensaje fijo si no se pudo aplicar. */
  error: string | null;
  alAplicar: () => void;
  aplicando: boolean;
}

function claseDeLinea(linea: string): { clase: string; aviso: string } {
  if (linea.startsWith("+") && !linea.startsWith("+++")) return { clase: "badge-render-success", aviso: "añadida" };
  if (linea.startsWith("-") && !linea.startsWith("---")) return { clase: "badge-render-danger", aviso: "quitada" };
  if (linea.startsWith("@@")) return { clase: "text-[var(--ui-primario)]", aviso: "" };
  return { clase: "text-[var(--ui-texto)]", aviso: "" };
}

const FOCALIZABLES = "button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex='-1'])";

export default function ModalDiffMaestra({
  abierto, cerrar, codigo, versionMaestra, cambios, cargando, error, alAplicar, aplicando,
}: Props) {
  const caja = React.useRef<HTMLDivElement>(null);
  const botonCerrar = React.useRef<HTMLButtonElement>(null);

  React.useEffect(() => {
    if (abierto) botonCerrar.current?.focus();
  }, [abierto]);

  if (!abierto) return null;

  const alTeclear = (evento: React.KeyboardEvent<HTMLDivElement>) => {
    if (evento.key === "Escape") {
      evento.stopPropagation();
      cerrar();
      return;
    }
    if (evento.key !== "Tab" || !caja.current) return;
    const dentro = Array.from(caja.current.querySelectorAll<HTMLElement>(FOCALIZABLES));
    if (dentro.length === 0) return;
    const primero = dentro[0];
    const ultimo = dentro[dentro.length - 1];
    if (evento.shiftKey && document.activeElement === primero) {
      evento.preventDefault();
      ultimo.focus();
    } else if (!evento.shiftKey && document.activeElement === ultimo) {
      evento.preventDefault();
      primero.focus();
    }
  };

  const sinCambios = !cargando && cambios.length === 0;
  const titulo = versionMaestra
    ? `Comparar ${codigo} con la maestra vigente (versión ${versionMaestra})`
    : `Comparar ${codigo} con la maestra vigente`;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="titulo-modal-diff"
      data-testid="modal-diff-maestra"
      onKeyDown={alTeclear}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
    >
      <div
        ref={caja}
        className="flex max-h-[85vh] w-full max-w-3xl flex-col rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-fondo)] shadow-lg"
      >
        <div className="flex items-center justify-between border-b border-[var(--ui-borde)] px-4 py-3">
          <div className="flex items-center gap-2">
            <GitCompare className="h-5 w-5 text-[var(--ui-primario)]" aria-hidden="true" />
            <h3 id="titulo-modal-diff" className="font-semibold text-sm">{titulo}</h3>
          </div>
          <button
            ref={botonCerrar}
            type="button"
            aria-label="Cerrar la comparación"
            onClick={cerrar}
            className="rounded-md p-1 text-[var(--ui-texto-suave)] hover:bg-[var(--ui-boton-hover)] cursor-pointer"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        <div className="flex-1 overflow-auto p-4 text-xs">
          {cargando ? (
            <p role="status" className="text-[var(--ui-texto-suave)]">Cargando las diferencias…</p>
          ) : sinCambios ? (
            <p className="text-[var(--ui-texto-suave)]">No hay diferencias de texto con la maestra vigente.</p>
          ) : (
            <div
              data-testid="contenedor-diff"
              className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-3 font-mono leading-relaxed"
            >
              {cambios.map((linea, idx) => {
                const { clase, aviso } = claseDeLinea(linea);
                return (
                  <div key={idx} className={`px-1 rounded-sm whitespace-pre-wrap ${clase}`}>
                    {aviso && <span className="sr-only">{aviso}: </span>}
                    {linea}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="flex flex-col gap-2 border-t border-[var(--ui-borde)] px-4 py-3">
          {error && (
            <p role="alert" className="badge-render-danger rounded-md px-2.5 py-2 text-xs">{error}</p>
          )}
          <p className="text-xs text-[var(--ui-texto-suave)]">
            Al aplicar, tu copia toma el contenido de la maestra vigente. Se conserva la marca de tu cuenta.
          </p>
          <div className="flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={cerrar}
              className="rounded-md border border-[var(--ui-borde)] px-3 py-1.5 font-medium text-xs hover:bg-[var(--ui-boton-hover)] cursor-pointer"
            >
              Cerrar
            </button>
            {!sinCambios && (
              <button
                type="button"
                data-testid="boton-confirmar-aplicar-maestra"
                onClick={alAplicar}
                disabled={aplicando || cargando}
                className="flex items-center gap-1 rounded-md bg-[var(--ui-primario)] px-3 py-1.5 font-medium text-xs text-[var(--ui-primario-texto)] hover:opacity-90 disabled:opacity-50 cursor-pointer"
              >
                <Check className="h-3.5 w-3.5" aria-hidden="true" />
                {aplicando ? "Aplicando…" : "Aplicar la versión de la maestra"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
