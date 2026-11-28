// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤auditoria-capa ¤hallazgos
import React, { useState, useEffect } from "react";
import {
  CierrePendiente,
  listarCierresPendientes,
  verificarCierreHallazgo,
} from "@/lib/auditoria/auditorias";

export const CierresPorVerificar: React.FC = () => {
  const [cierres, setCierres] = useState<CierrePendiente[]>([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);

  // Diálogo de verificación
  const [cierreSeleccionado, setCierreSeleccionado] = useState<CierrePendiente | null>(null);
  const [resultado, setResultado] = useState<"conforme" | "no_conforme">("conforme");
  const [motivo, setMotivo] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [errorGuardar, setErrorGuardar] = useState<string | null>(null);
  const [mensajeStatus, setMensajeStatus] = useState<string | null>(null);

  const cargarCierres = async () => {
    setCargando(true);
    setErrorCarga(null);
    try {
      const data = await listarCierresPendientes();
      setCierres(data);
    } catch (err: unknown) {
      setErrorCarga(err instanceof Error ? err.message : "No pudimos cargar los cierres pendientes.");
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarCierres();
  }, []);

  const handleGuardarVerificacion = async () => {
    if (!cierreSeleccionado) return;
    if (motivo.trim().length < 10) {
      setErrorGuardar("Explica tu resultado con al menos 10 caracteres.");
      return;
    }

    setGuardando(true);
    setErrorGuardar(null);
    try {
      await verificarCierreHallazgo(cierreSeleccionado.id, {
        resultado,
        motivo,
      });
      setMensajeStatus("Verificación guardada.");
      setCierreSeleccionado(null);
      setMotivo("");
      await cargarCierres();
    } catch (err: unknown) {
      setErrorGuardar(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setGuardando(false);
    }
  };

  if (cargando) {
    return (
      <div role="status" className="p-4 text-sm text-[var(--ui-texto-suave)]">
        Cargando cierres por verificar...
      </div>
    );
  }

  if (errorCarga) {
    return (
      <div role="alert" className="p-4 bg-[var(--ui-error-fondo)] text-[var(--ui-error-texto)] rounded-md text-sm border border-[var(--ui-error-borde)]">
        {errorCarga}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {mensajeStatus && (
        <div role="status" className="p-3 bg-[var(--ui-exito-fondo)] text-[var(--ui-exito-texto)] border border-[var(--ui-exito-borde)] rounded-md text-sm">
          {mensajeStatus}
        </div>
      )}

      {cierres.length === 0 ? (
        <div className="rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-8 text-center text-sm text-[var(--ui-texto-suave)]">
          No hay cierres pendientes de verificar.
        </div>
      ) : (
        <div className="divide-y divide-[var(--ui-borde)] rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] shadow-sm">
          {cierres.map((c) => (
            <div key={c.id} className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-[var(--ui-superficie-2)] text-[var(--ui-texto-suave)]">
                    {c.control_ref || "Auditoría"}
                  </span>
                  <span className="font-medium text-[var(--foreground)] text-sm">
                    {c.titulo}
                  </span>
                </div>
                <div className="text-xs text-[var(--ui-texto-suave)]">
                  {c.task_owner || "Responsable"} · {c.completed_at ? new Date(c.completed_at).toLocaleDateString() : "Fecha pendiente"}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-xs px-2.5 py-1 rounded-full font-medium bg-[var(--ui-aviso-fondo)] text-[var(--ui-aviso-texto)]">
                  {c.estado === "cerrado" ? "Verificado" : "Por verificar"}
                </span>
                {c.estado !== "cerrado" && (
                  <button
                    type="button"
                    onClick={() => {
                      setCierreSeleccionado(c);
                      setResultado("conforme");
                      setMotivo("");
                      setErrorGuardar(null);
                    }}
                    className="rounded bg-[var(--ui-primario)] text-[var(--ui-primario-texto)] px-3 py-1.5 text-xs font-semibold shadow-sm hover:bg-[var(--ui-primario-hover)]"
                  >
                    Verificar cierre
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Diálogo Verificar el Cierre */}
      {cierreSeleccionado && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4"
        >
          <div className="w-full max-w-lg rounded-lg bg-[var(--ui-superficie)] p-6 shadow-xl border border-[var(--ui-borde)] space-y-4">
            <h3 className="text-lg font-bold text-[var(--foreground)]">
              Verificar el cierre
            </h3>
            <div className="bg-[var(--ui-superficie-2)] p-3 rounded text-xs space-y-1">
              <div className="font-semibold text-[var(--foreground)]">
                {cierreSeleccionado.titulo}
              </div>
              <div className="text-[var(--ui-texto-suave)]">
                Control: {cierreSeleccionado.control_ref} | Tarea: {cierreSeleccionado.task_title || "Acción del plan"}
              </div>
            </div>

            {/* Selector de resultado sin palabras conforme / no conforme */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-[var(--foreground)]">
                Resultado de la verificación
              </label>
              <div role="radiogroup" aria-label="Resultado de la verificación" className="space-y-2">
                <label className="flex items-center gap-2 text-sm text-[var(--ui-texto-suave)] cursor-pointer">
                  <input
                    type="radio"
                    name="resultado"
                    value="conforme"
                    checked={resultado === "conforme"}
                    onChange={() => setResultado("conforme")}
                    className="text-[var(--ui-enlace)] focus:ring-[var(--ui-primario)]"
                  />
                  <span>Cierre verificado</span>
                </label>
                <label className="flex items-center gap-2 text-sm text-[var(--ui-texto-suave)] cursor-pointer">
                  <input
                    type="radio"
                    name="resultado"
                    value="no_conforme"
                    checked={resultado === "no_conforme"}
                    onChange={() => setResultado("no_conforme")}
                    className="text-[var(--ui-enlace)] focus:ring-[var(--ui-primario)]"
                  />
                  <span>Cierre no verificado</span>
                </label>
              </div>
            </div>

            <p className="text-xs text-[var(--ui-texto-suave)]">
              {resultado === "conforme"
                ? "El hallazgo se marca como cerrado solo si el cierre queda verificado."
                : "El hallazgo sigue abierto hasta que se vuelva a cerrar y verificar."}
            </p>

            <div className="space-y-1">
              <div className="flex justify-between items-center">
                <label htmlFor="motivo-verificacion" className="text-xs font-semibold text-[var(--ui-texto-suave)]">
                  Motivo (obligatorio)
                </label>
                <span className="text-xs text-[var(--ui-texto-suave)]">
                  {motivo.length} de 10 caracteres como mínimo
                </span>
              </div>
              <textarea
                id="motivo-verificacion"
                rows={3}
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                placeholder="Explica la verificación técnica realizada..."
                className="w-full rounded border border-[var(--ui-borde-control)] bg-[var(--ui-campo)] p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ui-primario)]"
              />
            </div>

            {errorGuardar && (
              <div role="alert" className="text-xs text-[var(--ui-error-texto)] font-medium">
                {errorGuardar}
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                autoFocus
                onClick={() => setCierreSeleccionado(null)}
                className="rounded border border-[var(--ui-borde-control)] px-3 py-1.5 text-sm font-medium text-[var(--ui-texto-suave)] hover:bg-[var(--ui-superficie-2)]"
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={guardando || motivo.trim().length < 10}
                onClick={handleGuardarVerificacion}
                className="rounded bg-[var(--ui-primario)] text-[var(--ui-primario-texto)] px-3.5 py-1.5 text-sm font-semibold shadow-sm hover:bg-[var(--ui-primario-hover)] disabled:opacity-50"
              >
                {guardando ? "Guardando..." : "Guardar verificación"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
