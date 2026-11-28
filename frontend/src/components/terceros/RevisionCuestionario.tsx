// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";

import React, { useState } from "react";
import { FileText } from "lucide-react";
import { CuestionarioResumen, revisarCuestionario, RevisionPayload } from "@/lib/terceros/cuestionario";

interface Props {
  cuestionario: CuestionarioResumen;
  terceroNombre: string;
  onCerrar: () => void;
  onRevisionGuardada: (resultado: { estado: string; informe_sha256?: string; url_nueva?: string }) => void;
}

export default function RevisionCuestionario({
  cuestionario,
  terceroNombre,
  onCerrar,
  onRevisionGuardada,
}: Props) {
  const [decision, setDecision] = useState<"conforme" | "correccion" | "rechazado">("conforme");
  const [comentario, setComentario] = useState("");
  const [proximaRevision, setProximaRevision] = useState("");
  const [errorValidacion, setErrorValidacion] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);
  const [errorServidor, setErrorServidor] = useState<string | null>(null);

  const guardar = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorValidacion(null);
    setErrorServidor(null);

    if (decision === "conforme" && !proximaRevision) {
      setErrorValidacion("Elige la fecha de la próxima revisión.");
      return;
    }

    if ((decision === "correccion" || decision === "rechazado") && !comentario.trim()) {
      setErrorValidacion("Explica tu decisión.");
      return;
    }

    setGuardando(true);
    try {
      const payload: RevisionPayload = {
        decision,
        comentario: comentario.trim() || undefined,
        proxima_revision: decision === "conforme" ? proximaRevision : undefined,
      };
      const res = await revisarCuestionario(cuestionario.id, payload);
      onRevisionGuardada(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes("CUESTIONARIO_NO_RESPONDIDO")) {
        setErrorServidor("El proveedor aún no respondió. Podrás revisarlo cuando envíe sus respuestas.");
      } else {
        setErrorServidor("No pudimos guardar la revisión. Inténtalo de nuevo.");
      }
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-5 max-w-lg w-full text-[var(--foreground)] shadow-2xl">
        <h3 className="text-sm font-bold text-[var(--ui-exito-texto)] mb-3 flex items-center">
          <FileText className="w-4 h-4 mr-2" />
          Respuestas de {terceroNombre}
        </h3>

        <form onSubmit={guardar} className="space-y-4 text-xs">
          <div role="radiogroup" aria-label="Decisión" className="space-y-2">
            <span className="block font-medium text-[var(--ui-texto-suave)]">Decisión</span>

            <label className="flex items-start space-x-2.5 p-2 bg-[var(--ui-superficie-2)] border border-[var(--ui-borde)] rounded cursor-pointer hover:bg-[var(--ui-superficie-2)]">
              <input
                type="radio"
                name="decision"
                value="conforme"
                checked={decision === "conforme"}
                onChange={() => setDecision("conforme")}
                className="mt-0.5"
              />
              <div>
                <span className="font-semibold text-[var(--foreground)]">Aceptar las respuestas</span>
                <p className="text-[var(--ui-texto-suave)] text-[11px]">
                  Se genera el informe y se cierra el hallazgo de garantía, si lo hay.
                </p>
              </div>
            </label>

            <label className="flex items-start space-x-2.5 p-2 bg-[var(--ui-superficie-2)] border border-[var(--ui-borde)] rounded cursor-pointer hover:bg-[var(--ui-superficie-2)]">
              <input
                type="radio"
                name="decision"
                value="correccion"
                checked={decision === "correccion"}
                onChange={() => setDecision("correccion")}
                className="mt-0.5"
              />
              <div>
                <span className="font-semibold text-[var(--ui-aviso-texto)]">Pedir corrección</span>
                <p className="text-[var(--ui-texto-suave)] text-[11px]">
                  Se crea un enlace nuevo para que el proveedor corrija sus respuestas.
                </p>
              </div>
            </label>

            <label className="flex items-start space-x-2.5 p-2 bg-[var(--ui-superficie-2)] border border-[var(--ui-borde)] rounded cursor-pointer hover:bg-[var(--ui-superficie-2)]">
              <input
                type="radio"
                name="decision"
                value="rechazado"
                checked={decision === "rechazado"}
                onChange={() => setDecision("rechazado")}
                className="mt-0.5"
              />
              <div>
                <span className="font-semibold text-[var(--ui-error-texto)]">Rechazar</span>
                <p className="text-[var(--ui-texto-suave)] text-[11px]">
                  Se registra un hallazgo de prioridad alta en el plan de acción.
                </p>
              </div>
            </label>
          </div>

          {decision === "conforme" && (
            <div>
              <label htmlFor="proxima-revision" className="block text-[var(--ui-texto-suave)] mb-1 font-medium">
                Próxima revisión
              </label>
              <input
                id="proxima-revision"
                type="date"
                value={proximaRevision}
                onChange={(e) => setProximaRevision(e.target.value)}
                className="w-full bg-[var(--ui-campo)] border border-[var(--ui-borde-control)] rounded p-2 text-[var(--foreground)]"
                required
              />
            </div>
          )}

          <div>
            <label htmlFor="comentario-revision" className="block text-[var(--ui-texto-suave)] mb-1 font-medium">
              Comentario {decision !== "conforme" ? "(obligatorio)" : "(opcional)"}
            </label>
            <textarea
              id="comentario-revision"
              value={comentario}
              onChange={(e) => setComentario(e.target.value)}
              placeholder={decision === "conforme" ? "Observaciones adicionales..." : "Explica el motivo..."}
              className="w-full bg-[var(--ui-campo)] border border-[var(--ui-borde-control)] rounded p-2 text-[var(--foreground)] h-20"
              required={decision !== "conforme"}
            />
          </div>

          {errorValidacion && (
            <p role="alert" className="text-[var(--ui-error-texto)] text-xs">
              {errorValidacion}
            </p>
          )}

          {errorServidor && (
            <p role="alert" className="text-[var(--ui-error-texto)] text-xs">
              {errorServidor}
            </p>
          )}

          <div className="flex justify-end space-x-2 pt-2 border-t border-[var(--ui-borde)]">
            <button
              type="button"
              onClick={onCerrar}
              className="px-3.5 py-1.5 bg-[var(--ui-boton)] text-[var(--foreground)] rounded hover:bg-[var(--ui-boton-hover)] font-medium"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={guardando}
              className="px-4 py-1.5 bg-[var(--ui-primario)] text-[var(--ui-primario-texto)] rounded font-semibold hover:bg-[var(--ui-primario-hover)] disabled:opacity-50"
            >
              {guardando ? "Guardando..." : "Guardar la revisión"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
