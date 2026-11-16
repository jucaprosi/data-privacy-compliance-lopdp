// ¤auditoria-capa ¤hallazgos
import React, { useState, useEffect } from "react";
import {
  AuditoriaResumen,
  AuditoriaDetalle,
  listarAuditorias,
  obtenerAuditoria,
  crearAuditoria,
} from "@/lib/auditoria/auditorias";
import { GrillaAuditoria } from "./GrillaAuditoria";
import { ActasPorArea } from "./ActasPorArea";
import { CierresPorVerificar } from "./CierresPorVerificar";

interface Props {
  rolActual?: string;
  usuarioId?: string;
}

export const AuditoriasView: React.FC<Props> = ({ rolActual = "auditor", usuarioId = "" }) => {
  const [tabActiva, setTabActiva] = useState<"auditorias" | "cierres">("auditorias");
  const [auditorias, setAuditorias] = useState<AuditoriaResumen[]>([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);

  // Auditoría en detalle
  const [auditoriaSeleccionada, setAuditoriaSeleccionada] = useState<AuditoriaDetalle | null>(null);

  // Diálogo de Nueva Auditoría
  const [mostrarDialogoCrear, setMostrarDialogoCrear] = useState(false);
  const [nombreNueva, setNombreNueva] = useState("");
  const [areasTexto, setAreasTexto] = useState("D01, D02");
  const [equipoTexto, setEquipoTexto] = useState(usuarioId || "auditor_1");
  const [creando, setCreando] = useState(false);
  const [errorCrear, setErrorCrear] = useState<string | null>(null);

  const puedeCrear = rolActual === "implementador" || rolActual === "coordinador" || rolActual === "admin_organizacion";
  const esAuditor = rolActual === "auditor";

  const cargarLista = async () => {
    setCargando(true);
    setErrorCarga(null);
    try {
      const data = await listarAuditorias();
      setAuditorias(data);
    } catch (err: unknown) {
      setErrorCarga(err instanceof Error ? err.message : "No pudimos cargar las auditorías. Inténtalo de nuevo.");
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarLista();
  }, []);

  const handleSeleccionarAuditoria = async (id: string) => {
    try {
      const det = await obtenerAuditoria(id);
      setAuditoriaSeleccionada(det);
    } catch (err: unknown) {
      setErrorCarga(err instanceof Error ? err.message : "Error al cargar auditoría");
    }
  };

  const handleCrearAuditoria = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nombreNueva.trim()) {
      setErrorCrear("Escribe el nombre.");
      return;
    }
    const alcance = areasTexto.split(",").map((s) => s.trim()).filter(Boolean);
    if (alcance.length === 0) {
      setErrorCrear("Elige al menos un área.");
      return;
    }
    const equipo = equipoTexto.split(",").map((s) => s.trim()).filter(Boolean);
    if (equipo.length === 0) {
      setErrorCrear("Elige al menos una persona del equipo.");
      return;
    }

    setCreando(true);
    setErrorCrear(null);
    try {
      const nueva = await crearAuditoria({
        nombre: nombreNueva.trim(),
        alcance,
        equipo,
      });
      setMostrarDialogoCrear(false);
      setNombreNueva("");
      await cargarLista();
      setAuditoriaSeleccionada(nueva);
    } catch (err: unknown) {
      setErrorCrear(err instanceof Error ? err.message : "Error al crear auditoría");
    } finally {
      setCreando(false);
    }
  };

  return (
    <main className="p-6 max-w-7xl mx-auto space-y-6" aria-label="Auditorías">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Auditorías
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Cada auditoría verifica los controles de las áreas elegidas y termina en un acta por área.
          </p>
        </div>

        {puedeCrear && !auditoriaSeleccionada && (
          <button
            type="button"
            onClick={() => {
              setMostrarDialogoCrear(true);
              setErrorCrear(null);
            }}
            className="inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-600"
          >
            Nueva auditoría
          </button>
        )}
      </div>

      {/* Selector de Pestañas (Auditorías / Cierres por verificar) */}
      <div className="border-b border-slate-200 dark:border-slate-800">
        <div role="tablist" aria-label="Auditorías" className="flex gap-4">
          <button
            role="tab"
            aria-selected={tabActiva === "auditorias"}
            onClick={() => setTabActiva("auditorias")}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
              tabActiva === "auditorias"
                ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                : "border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
            }`}
          >
            Auditorías
          </button>
          {esAuditor && (
            <button
              role="tab"
              aria-selected={tabActiva === "cierres"}
              onClick={() => {
                setTabActiva("cierres");
                setAuditoriaSeleccionada(null);
              }}
              className={`pb-3 text-sm font-semibold border-b-2 transition-colors ${
                tabActiva === "cierres"
                  ? "border-indigo-600 text-indigo-600 dark:text-indigo-400"
                  : "border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
              }`}
            >
              Cierres por verificar
            </button>
          )}
        </div>
      </div>

      {tabActiva === "cierres" ? (
        <CierresPorVerificar />
      ) : auditoriaSeleccionada ? (
        /* Vista de Detalle de Auditoría */
        <div className="space-y-6">
          <div className="flex items-center justify-between bg-slate-50 dark:bg-slate-800/40 p-4 rounded-lg border border-slate-200 dark:border-slate-800">
            <div>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setAuditoriaSeleccionada(null)}
                  className="text-xs text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 font-semibold"
                >
                  ← Volver a la lista
                </button>
                <span className="text-slate-300">|</span>
                <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  {auditoriaSeleccionada.nombre}
                </h2>
                <span
                  className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                    auditoriaSeleccionada.estado === "cerrada"
                      ? "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200"
                      : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
                  }`}
                >
                  {auditoriaSeleccionada.estado === "cerrada" ? "Cerrada" : "Abierta"}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Áreas: {auditoriaSeleccionada.alcance.join(", ")} | Creada:{" "}
                {new Date(auditoriaSeleccionada.creado_en).toLocaleDateString()}
              </p>
            </div>

            {/* Avance */}
            <div className="text-right">
              <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">
                {auditoriaSeleccionada.filas.filter((f) => f.verificado != null).length} de{" "}
                {auditoriaSeleccionada.filas.length} controles verificados
              </span>
              <div
                role="progressbar"
                aria-label="Controles verificados"
                aria-valuenow={auditoriaSeleccionada.filas.filter((f) => f.verificado != null).length}
                aria-valuemin={0}
                aria-valuemax={auditoriaSeleccionada.filas.length}
                className="w-40 h-2 bg-slate-200 dark:bg-slate-700 rounded-full mt-1.5 overflow-hidden"
              >
                <div
                  className="bg-indigo-600 h-full rounded-full transition-all"
                  style={{
                    width: `${
                      auditoriaSeleccionada.filas.length > 0
                        ? (auditoriaSeleccionada.filas.filter((f) => f.verificado != null).length /
                            auditoriaSeleccionada.filas.length) *
                          100
                        : 0
                    }%`,
                  }}
                />
              </div>
            </div>
          </div>

          {/* Grilla de Controles */}
          <GrillaAuditoria
            auditoria={auditoriaSeleccionada}
            esAuditorEquipo={esAuditor && auditoriaSeleccionada.equipo.includes(usuarioId || "auditor_1")}
            onFilaActualizada={(fila) => {
              setAuditoriaSeleccionada((prev) => {
                if (!prev) return null;
                return {
                  ...prev,
                  filas: prev.filas.map((f) => (f.id === fila.id ? fila : f)),
                };
              });
            }}
          />

          {/* Actas por Área */}
          <ActasPorArea
            auditoria={auditoriaSeleccionada}
            esAuditorEquipo={esAuditor && auditoriaSeleccionada.equipo.includes(usuarioId || "auditor_1")}
            onActaFirmada={async () => {
              const actualizada = await obtenerAuditoria(auditoriaSeleccionada.id);
              setAuditoriaSeleccionada(actualizada);
              await cargarLista();
            }}
          />
        </div>
      ) : (
        /* Lista General de Auditorías */
        <div>
          {cargando ? (
            <div role="status" className="p-8 text-center text-sm text-slate-500">
              Cargando las auditorías…
            </div>
          ) : errorCarga ? (
            <div role="alert" className="p-6 bg-rose-50 text-rose-800 rounded-lg border border-rose-200 space-y-3">
              <p className="text-sm font-medium">No pudimos cargar las auditorías. Inténtalo de nuevo.</p>
              <button
                type="button"
                onClick={cargarLista}
                className="rounded bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-rose-500"
              >
                Volver a cargar
              </button>
            </div>
          ) : auditorias.length === 0 ? (
            <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-12 text-center text-slate-500 text-sm">
              Aún no hay auditorías. Crea una para verificar los controles declarados en el diagnóstico.
            </div>
          ) : (
            <div role="list" aria-label="Auditorías" className="space-y-3">
              {auditorias.map((a) => (
                <div
                  key={a.id}
                  role="listitem"
                  onClick={() => handleSeleccionarAuditoria(a.id)}
                  className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-sm hover:border-indigo-400 cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-slate-900 dark:text-slate-100 text-base">
                        {a.nombre}
                      </h3>
                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                          a.estado === "cerrada"
                            ? "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                            : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
                        }`}
                      >
                        {a.estado === "cerrada" ? "Cerrada" : "Abierta"}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500">
                      Áreas: {a.alcance.join(", ")} | Fecha: {new Date(a.creado_en).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="flex items-center gap-4">
                    <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
                      {a.verificados} de {a.total_controles} controles verificados
                    </span>
                    <span className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold">
                      Abrir →
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Diálogo Nueva Auditoría */}
      {mostrarDialogoCrear && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4"
        >
          <form
            onSubmit={handleCrearAuditoria}
            className="w-full max-w-lg rounded-lg bg-white dark:bg-slate-900 p-6 shadow-xl border border-slate-200 dark:border-slate-800 space-y-4"
          >
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Nueva auditoría
            </h3>
            <p className="text-xs text-slate-500">
              Los controles se cargan con el último diagnóstico sellado.
            </p>

            <div className="space-y-1">
              <label htmlFor="nombre-auditoria" className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Nombre de la auditoría (obligatorio)
              </label>
              <input
                id="nombre-auditoria"
                type="text"
                required
                value={nombreNueva}
                onChange={(e) => setNombreNueva(e.target.value)}
                placeholder="Ej. Auditoría de Protección de Datos 2026"
                className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="space-y-1">
              <label htmlFor="areas-auditoria" className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Áreas a auditar (al menos una, separadas por coma)
              </label>
              <input
                id="areas-auditoria"
                type="text"
                required
                value={areasTexto}
                onChange={(e) => setAreasTexto(e.target.value)}
                placeholder="D01, D02, D03"
                className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="space-y-1">
              <label htmlFor="equipo-auditoria" className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Equipo auditor (al menos una persona con rol auditor)
              </label>
              <input
                id="equipo-auditoria"
                type="text"
                required
                value={equipoTexto}
                onChange={(e) => setEquipoTexto(e.target.value)}
                placeholder="user_id_auditor"
                className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            {errorCrear && (
              <div role="alert" className="text-xs text-rose-600 dark:text-rose-400 font-medium">
                {errorCrear}
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                autoFocus
                onClick={() => setMostrarDialogoCrear(false)}
                className="rounded border border-slate-300 dark:border-slate-700 px-3.5 py-1.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={creando}
                className="rounded bg-indigo-600 px-4 py-1.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
              >
                {creando ? "Creando..." : "Crear auditoría"}
              </button>
            </div>
          </form>
        </div>
      )}
    </main>
  );
};
