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
      <div role="status" className="p-4 text-sm text-slate-500">
        Cargando cierres por verificar...
      </div>
    );
  }

  if (errorCarga) {
    return (
      <div role="alert" className="p-4 bg-rose-50 text-rose-800 rounded-md text-sm border border-rose-200">
        {errorCarga}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {mensajeStatus && (
        <div role="status" className="p-3 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-200 border border-emerald-200 dark:border-emerald-800 rounded-md text-sm">
          {mensajeStatus}
        </div>
      )}

      {cierres.length === 0 ? (
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-8 text-center text-sm text-slate-500">
          No hay cierres pendientes de verificar.
        </div>
      ) : (
        <div className="divide-y divide-slate-100 dark:divide-slate-800 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
          {cierres.map((c) => (
            <div key={c.id} className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                    {c.control_ref || "Auditoría"}
                  </span>
                  <span className="font-medium text-slate-900 dark:text-slate-100 text-sm">
                    {c.titulo}
                  </span>
                </div>
                <div className="text-xs text-slate-500">
                  {c.task_owner || "Responsable"} · {c.completed_at ? new Date(c.completed_at).toLocaleDateString() : "Fecha pendiente"}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-xs px-2.5 py-1 rounded-full font-medium bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300">
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
                    className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-indigo-500"
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
          <div className="w-full max-w-lg rounded-lg bg-white dark:bg-slate-900 p-6 shadow-xl border border-slate-200 dark:border-slate-800 space-y-4">
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Verificar el cierre
            </h3>
            <div className="bg-slate-50 dark:bg-slate-800/40 p-3 rounded text-xs space-y-1">
              <div className="font-semibold text-slate-800 dark:text-slate-200">
                {cierreSeleccionado.titulo}
              </div>
              <div className="text-slate-500">
                Control: {cierreSeleccionado.control_ref} | Tarea: {cierreSeleccionado.task_title || "Acción del plan"}
              </div>
            </div>

            {/* Selector de resultado sin palabras conforme / no conforme */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                Resultado de la verificación
              </label>
              <div role="radiogroup" aria-label="Resultado de la verificación" className="space-y-2">
                <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300 cursor-pointer">
                  <input
                    type="radio"
                    name="resultado"
                    value="conforme"
                    checked={resultado === "conforme"}
                    onChange={() => setResultado("conforme")}
                    className="text-indigo-600 focus:ring-indigo-500"
                  />
                  <span>Cierre verificado</span>
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300 cursor-pointer">
                  <input
                    type="radio"
                    name="resultado"
                    value="no_conforme"
                    checked={resultado === "no_conforme"}
                    onChange={() => setResultado("no_conforme")}
                    className="text-indigo-600 focus:ring-indigo-500"
                  />
                  <span>Cierre no verificado</span>
                </label>
              </div>
            </div>

            <p className="text-xs text-slate-500">
              {resultado === "conforme"
                ? "El hallazgo se marca como cerrado solo si el cierre queda verificado."
                : "El hallazgo sigue abierto hasta que se vuelva a cerrar y verificar."}
            </p>

            <div className="space-y-1">
              <div className="flex justify-between items-center">
                <label htmlFor="motivo-verificacion" className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Motivo (obligatorio)
                </label>
                <span className="text-xs text-slate-400">
                  {motivo.length} de 10 caracteres como mínimo
                </span>
              </div>
              <textarea
                id="motivo-verificacion"
                rows={3}
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                placeholder="Explica la verificación técnica realizada..."
                className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 p-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            {errorGuardar && (
              <div role="alert" className="text-xs text-rose-600 dark:text-rose-400 font-medium">
                {errorGuardar}
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                autoFocus
                onClick={() => setCierreSeleccionado(null)}
                className="rounded border border-slate-300 dark:border-slate-700 px-3 py-1.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={guardando || motivo.trim().length < 10}
                onClick={handleGuardarVerificacion}
                className="rounded bg-indigo-600 px-3.5 py-1.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
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
