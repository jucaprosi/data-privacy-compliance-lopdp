"use client";

// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Modal para registrar una corrección humana de aplicabilidad (BIB-204).
 *
 * Conserva resultado original, motivo, evidencia, autor y fecha.
 * Una obligación confirmada exige revisión jurídica para ser excluida.
 */
import React, { useState } from "react";
import { AlertTriangle, CheckCircle, X } from "lucide-react";
import {
  registrarModificacion,
  type ModificacionHumana,
  type PlantillaAplicable,
} from "@/lib/biblioteca/aplicabilidad";

interface Props {
  plantilla: PlantillaAplicable;
  onCerrar: () => void;
  onGuardado: (mod: ModificacionHumana) => void;
}

export default function ModalModificarAplicabilidad({
  plantilla,
  onCerrar,
  onGuardado,
}: Props) {
  const [resultado, setResultado] = useState<"Aplica" | "No aplica">(
    plantilla.resultado === "No aplica" ? "Aplica" : "No aplica",
  );
  const [motivo, setMotivo] = useState("");
  const [evidencia, setEvidencia] = useState("");
  const [esJuridico, setEsJuridico] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const esExclusionObligacion =
    plantilla.es_obligacion &&
    plantilla.resultado_calculado === "Aplica" &&
    resultado === "No aplica";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!motivo.trim() || motivo.trim().length < 3) {
      setError("El motivo debe tener al menos 3 caracteres.");
      return;
    }
    if (!evidencia.trim()) {
      setError("Debe proporcionar la evidencia que respalda la corrección.");
      return;
    }
    if (esExclusionObligacion && !esJuridico) {
      setError("Una obligación legal confirmada exige confirmación de revisión jurídica.");
      return;
    }

    setEnviando(true);
    setError(null);
    const resp = await registrarModificacion(
      plantilla.codigo,
      resultado,
      motivo.trim(),
      evidencia.trim(),
      esJuridico ? "revisor-juridico-confirmado" : undefined,
    );
    setEnviando(false);

    if (!resp.ok || !resp.modificacion) {
      setError(resp.error ?? "No se pudo guardar la corrección.");
      return;
    }

    onGuardado(resp.modificacion);
    onCerrar();
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="titulo-modal-modificar"
      data-testid="modal-modificar"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
    >
      <div className="w-full max-w-lg rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-6 shadow-xl text-xs flex flex-col gap-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b border-[var(--ui-borde)] pb-3">
          <h3 id="titulo-modal-modificar" className="text-sm font-semibold">
            Modificar aplicabilidad: {plantilla.codigo}
          </h3>
          <button
            type="button"
            aria-label="Cerrar modal"
            onClick={onCerrar}
            className="rounded p-1 text-[var(--ui-texto-suave)] hover:bg-[var(--ui-boton-hover)]"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="rounded bg-[var(--ui-fondo)] p-3 flex flex-col gap-1 border border-[var(--ui-borde)]">
          <p className="font-medium text-[var(--ui-texto)]">{plantilla.nombre}</p>
          <p className="text-[var(--ui-texto-suave)]">
            Resultado calculado: <span className="font-semibold">{plantilla.resultado_calculado}</span>
            {plantilla.es_obligacion ? " · Obligación legal confirmada" : ""}
          </p>
        </div>

        {esExclusionObligacion && (
          <div
            role="alert"
            className="rounded border border-amber-500/40 bg-amber-500/10 p-3 text-amber-800 dark:text-amber-200 flex items-start gap-2"
          >
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Exclusión de obligación legal confirmada</p>
              <p>
                Esta plantilla corresponde a una obligación normativa. Su exclusión exige
                revisión y fundamento jurídico estricto (criterio 3 de BIB-204).
              </p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div>
            <label className="block font-medium mb-1" htmlFor="select-resultado">
              Nuevo resultado
            </label>
            <select
              id="select-resultado"
              data-testid="select-resultado-modificado"
              value={resultado}
              onChange={(e) => setResultado(e.target.value as "Aplica" | "No aplica")}
              className="w-full rounded border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-2 text-xs"
            >
              <option value="Aplica">Aplica</option>
              <option value="No aplica">No aplica</option>
            </select>
          </div>

          <div>
            <label className="block font-medium mb-1" htmlFor="input-motivo">
              Motivo de la corrección
            </label>
            <textarea
              id="input-motivo"
              data-testid="input-motivo"
              rows={2}
              required
              placeholder="Explique la justificación fáctica o legal..."
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              className="w-full rounded border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-2 text-xs"
            />
          </div>

          <div>
            <label className="block font-medium mb-1" htmlFor="input-evidencia">
              Evidencia de respaldo
            </label>
            <input
              id="input-evidencia"
              data-testid="input-evidencia"
              type="text"
              required
              placeholder="Referencia a informe, acta o resolución..."
              value={evidencia}
              onChange={(e) => setEvidencia(e.target.value)}
              className="w-full rounded border border-[var(--ui-borde)] bg-[var(--ui-campo)] p-2 text-xs"
            />
          </div>

          {esExclusionObligacion && (
            <label className="flex items-center gap-2 cursor-pointer font-medium p-1">
              <input
                type="checkbox"
                data-testid="check-revisado-juridico"
                checked={esJuridico}
                onChange={(e) => setEsJuridico(e.target.checked)}
                className="rounded border-[var(--ui-borde)]"
              />
              Confirmo que esta exclusión cuenta con dictamen o revisión jurídica aprobada
            </label>
          )}

          {error && (
            <p role="alert" className="text-red-600 dark:text-red-400 font-medium">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-2 pt-2 border-t border-[var(--ui-borde)]">
            <button
              type="button"
              onClick={onCerrar}
              className="rounded border border-[var(--ui-borde)] px-3 py-1.5 hover:bg-[var(--ui-boton-hover)]"
            >
              Cancelar
            </button>
            <button
              type="submit"
              data-testid="boton-guardar-modificacion"
              disabled={enviando}
              className="rounded bg-[var(--ui-primario)] text-white px-3 py-1.5 font-medium hover:opacity-90 flex items-center gap-1.5"
            >
              <CheckCircle className="h-3.5 w-3.5" />
              {enviando ? "Guardando..." : "Guardar corrección"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
