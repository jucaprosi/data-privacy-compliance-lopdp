// ¤evidencias ¤rbac-tenant
import React, { useState, useEffect } from "react";
import {
  AccionFormativa,
  ContenidoFormativo,
  ParticipanteAccion,
  listarAcciones,
  crearAccion,
  listarContenidos,
  listarParticipantesAccion,
  anadirParticipantes,
} from "@/lib/formacion/formacion";

interface Props {
  puedeGestionar: boolean;
}

export const AccionesPanel: React.FC<Props> = ({ puedeGestionar }) => {
  const [acciones, setAcciones] = useState<AccionFormativa[]>([]);
  const [contenidos, setContenidos] = useState<ContenidoFormativo[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Diálogo Nueva Acción
  const [mostrarCrear, setMostrarCrear] = useState(false);
  const [nombre, setNombre] = useState("");
  const [contenidoId, setContenidoId] = useState("");
  const [inicio, setInicio] = useState("");
  const [fin, setFin] = useState("");
  const [notaMinima, setNotaMinima] = useState(70);
  const [errorFechas, setErrorFechas] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);

  // Detalle de participantes de una acción
  const [accionSeleccionada, setAccionSeleccionada] = useState<AccionFormativa | null>(null);
  const [participantes, setParticipantes] = useState<ParticipanteAccion[]>([]);
  const [personasTexto, setPersonasTexto] = useState("");
  const [errorParticipantes, setErrorParticipantes] = useState<string | null>(null);
  const [anadiendo, setAnadiendo] = useState(false);

  const cargar = async () => {
    setCargando(true);
    setError(null);
    try {
      const [accs, conts] = await Promise.all([listarAcciones(), listarContenidos()]);
      setAcciones(accs);
      setContenidos(conts);
      if (conts.length > 0 && !contenidoId) {
        setContenidoId(conts[0].id);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al cargar acciones.");
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  const handleCrearAccion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nombre.trim() || !contenidoId) return;
    if (fin < inicio) {
      setErrorFechas("La fecha de fin debe ser posterior a la de inicio.");
      return;
    }

    setGuardando(true);
    setErrorFechas(null);
    try {
      await crearAccion({
        contenido_id: contenidoId,
        nombre: nombre.trim(),
        inicio,
        fin,
        nota_minima: Number(notaMinima),
      });
      setMostrarCrear(false);
      setNombre("");
      await cargar();
    } catch (err: unknown) {
      setErrorFechas(err instanceof Error ? err.message : "Error al crear acción.");
    } finally {
      setGuardando(false);
    }
  };

  const handleVerParticipantes = async (a: AccionFormativa) => {
    setAccionSeleccionada(a);
    setErrorParticipantes(null);
    try {
      const parts = await listarParticipantesAccion(a.id);
      setParticipantes(parts);
    } catch (err: unknown) {
      setErrorParticipantes(err instanceof Error ? err.message : "Error al cargar participantes.");
    }
  };

  const handleAnadirParticipantes = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accionSeleccionada || !personasTexto.trim()) return;

    const ids = personasTexto.split(",").map((s) => s.trim()).filter(Boolean);
    if (ids.length === 0) return;

    setAnadiendo(true);
    setErrorParticipantes(null);
    try {
      await anadirParticipantes(accionSeleccionada.id, ids);
      setPersonasTexto("");
      const parts = await listarParticipantesAccion(accionSeleccionada.id);
      setParticipantes(parts);
      await cargar();
    } catch (err: unknown) {
      setErrorParticipantes(err instanceof Error ? err.message : "Error al añadir participantes.");
    } finally {
      setAnadiendo(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">Acciones formativas</h2>
          <p className="text-xs text-slate-500">Programación de capacitaciones y seguimiento de participantes.</p>
        </div>
        {puedeGestionar && (
          <button
            type="button"
            onClick={() => {
              setMostrarCrear(true);
              setErrorFechas(null);
            }}
            className="rounded bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-indigo-500"
          >
            Nueva acción formativa
          </button>
        )}
      </div>

      {cargando ? (
        <div role="status" className="p-4 text-sm text-slate-500">
          Cargando acciones formativas...
        </div>
      ) : error ? (
        <div role="alert" className="p-4 bg-rose-50 text-rose-800 rounded text-sm">
          {error}
        </div>
      ) : acciones.length === 0 ? (
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-8 text-center text-sm text-slate-500">
          Aún no hay acciones formativas. Crea una para empezar.
        </div>
      ) : (
        <div className="divide-y divide-slate-100 dark:divide-slate-800 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
          {acciones.map((a) => (
            <div key={a.id} className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1">
                <h3 className="font-semibold text-slate-900 dark:text-slate-100 text-sm">
                  {a.nombre}
                </h3>
                <p className="text-xs text-slate-500">
                  Del {new Date(a.inicio).toLocaleDateString()} al {new Date(a.fin).toLocaleDateString()} | Nota mínima: {a.nota_minima}
                </p>
                <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
                  {a.terminados} de {a.total_participantes} terminaron
                </span>
              </div>

              <button
                type="button"
                onClick={() => handleVerParticipantes(a)}
                className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 self-start md:self-auto"
              >
                Avance por persona →
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Modal / Panel Avance por Persona */}
      {accionSeleccionada && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4"
        >
          <div className="w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-lg bg-white dark:bg-slate-900 p-6 shadow-xl border border-slate-200 dark:border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b pb-3 border-slate-100 dark:border-slate-800">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Avance por persona · {accionSeleccionada.nombre}
                </h3>
                <p className="text-xs text-slate-500">
                  Seguimiento individual y registro de constancias de formación.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setAccionSeleccionada(null)}
                className="text-slate-400 hover:text-slate-600 text-sm"
              >
                ✕ Cerrar
              </button>
            </div>

            {errorParticipantes && (
              <div role="alert" className="text-xs text-rose-600 font-medium">
                {errorParticipantes}
              </div>
            )}

            {/* Formulario Añadir Participantes */}
            {puedeGestionar && (
              <form onSubmit={handleAnadirParticipantes} className="bg-slate-50 dark:bg-slate-800/40 p-3 rounded-lg border border-slate-100 dark:border-slate-800 space-y-2">
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Añadir participantes
                  </label>
                  <span className="text-xs text-slate-500">
                    Se enviará la formación a las personas elegidas (escribe los IDs o correos separados por coma).
                  </span>
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    required
                    value={personasTexto}
                    onChange={(e) => setPersonasTexto(e.target.value)}
                    placeholder="persona_1, persona_2"
                    className="flex-1 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-xs"
                  />
                  <button
                    type="submit"
                    disabled={anadiendo}
                    className="rounded bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
                  >
                    {anadiendo ? "Añadiendo..." : "Añadir"}
                  </button>
                </div>
              </form>
            )}

            {/* Tabla Avance por persona */}
            <div className="overflow-x-auto rounded border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-xs" aria-label="Avance por persona">
                <thead className="bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-b">
                  <tr>
                    <th scope="col" className="p-2.5 font-semibold">Persona</th>
                    <th scope="col" className="p-2.5 font-semibold">Estado</th>
                    <th scope="col" className="p-2.5 font-semibold">Nota</th>
                    <th scope="col" className="p-2.5 font-semibold">Constancia</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {participantes.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="p-4 text-center text-slate-500 italic">
                        No hay participantes asignados a esta acción.
                      </td>
                    </tr>
                  ) : (
                    participantes.map((p) => {
                      let estadoTexto = "Enviada";
                      if (p.terminado_en) {
                        estadoTexto = (p.nota != null && p.nota >= accionSeleccionada.nota_minima) ? "Aprobó" : "No aprobó";
                      } else if (p.iniciado_en) {
                        estadoTexto = "Iniciada";
                      }

                      return (
                        <tr key={p.id}>
                          <td className="p-2.5 font-medium text-slate-800 dark:text-slate-200">
                            {p.persona_id}
                          </td>
                          <td className="p-2.5">
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                              estadoTexto === "Aprobó"
                                ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
                                : estadoTexto === "No aprobó"
                                ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-200"
                                : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                            }`}>
                              {estadoTexto}
                            </span>
                          </td>
                          <td className="p-2.5 text-slate-600 dark:text-slate-400">
                            {p.nota != null ? `${p.nota} / 100` : "—"}
                          </td>
                          <td className="p-2.5 text-xs">
                            {p.diploma_sha256 ? (
                              <span className="text-indigo-600 dark:text-indigo-400 font-mono" title={p.diploma_sha256}>
                                {p.diploma_sha256.slice(0, 8)}...
                              </span>
                            ) : (
                              <span className="text-slate-400">—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Modal Crear Acción */}
      {mostrarCrear && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4"
        >
          <form
            onSubmit={handleCrearAccion}
            className="w-full max-w-md rounded-lg bg-white dark:bg-slate-900 p-6 shadow-xl border border-slate-200 dark:border-slate-800 space-y-4"
          >
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
              Nueva acción formativa
            </h3>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Nombre de la acción
              </label>
              <input
                type="text"
                required
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                placeholder="Ej. Capacitación LOPDP 2026 - Área Legal"
                className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-xs"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Contenido</label>
              <select
                required
                value={contenidoId}
                onChange={(e) => setContenidoId(e.target.value)}
                className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-xs"
              >
                {contenidos.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.titulo} ({c.tipo})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Fecha de inicio</label>
                <input
                  type="date"
                  required
                  value={inicio}
                  onChange={(e) => setInicio(e.target.value)}
                  className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1.5 text-xs"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Fecha de fin</label>
                <input
                  type="date"
                  required
                  value={fin}
                  onChange={(e) => setFin(e.target.value)}
                  className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-2 py-1.5 text-xs"
                />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Nota mínima para aprobar (0 a 100)
                </label>
                <span className="text-xs text-slate-400">Por ejemplo, 70.</span>
              </div>
              <input
                type="number"
                min={0}
                max={100}
                value={notaMinima}
                onChange={(e) => setNotaMinima(Number(e.target.value))}
                className="w-full rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-1.5 text-xs"
              />
            </div>

            {errorFechas && (
              <div role="alert" className="text-xs text-rose-600 font-medium">
                {errorFechas}
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                autoFocus
                onClick={() => setMostrarCrear(false)}
                className="rounded border border-slate-300 dark:border-slate-700 px-3 py-1.5 text-xs font-medium"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={guardando}
                className="rounded bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {guardando ? "Creando..." : "Crear acción"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
