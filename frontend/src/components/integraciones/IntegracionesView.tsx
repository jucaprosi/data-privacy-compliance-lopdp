"use client";

// ¤api-integraciones ¤frontend-ide
/**
 * Vista de administración de Claves de Integración y Techos de Paquete (API-02).
 *
 * Permite listar, generar, rotar y revocar claves con scopes acotados.
 * Muestra la clave en claro una sola vez al crearla o rotarla.
 */
import React, { useEffect, useState } from "react";
import {
  ClaveIntegracion,
  TechosIntegracion,
  obtenerTechos,
  listarClaves,
  crearClave,
  rotarClave,
  revocarClave,
} from "@/lib/integraciones/clavesIntegracion";

const ALCANCES_DISPONIBLES = [
  { id: "rat:lectura", label: "Lectura de RAT", desc: "Consultar actividades de tratamiento" },
  { id: "tareas:lectura", label: "Lectura de Tareas", desc: "Consultar tareas de la hoja de ruta" },
  { id: "evidencias:lectura", label: "Lectura de Evidencias", desc: "Consultar metadatos de evidencias" },
];

export default function IntegracionesView() {
  const [techos, setTechos] = useState<TechosIntegracion | null>(null);
  const [claves, setClaves] = useState<ClaveIntegracion[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal crear
  const [modalCrear, setModalCrear] = useState(false);
  const [nuevoNombre, setNuevoNombre] = useState("");
  const [nuevosAlcances, setNuevosAlcances] = useState<string[]>([
    "rat:lectura",
    "tareas:lectura",
  ]);

  // Visualización de clave en claro (una sola vez)
  const [claveRevelada, setClaveRevelada] = useState<string | null>(null);
  const [copiado, setCopiado] = useState(false);

  // Acción en progreso
  const [procesando, setProcesando] = useState(false);

  const cargarDatos = async () => {
    try {
      setCargando(true);
      setError(null);
      const [techosData, clavesData] = await Promise.all([
        obtenerTechos(),
        listarClaves(),
      ]);
      setTechos(techosData);
      setClaves(clavesData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al cargar datos";
      setError(msg);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarDatos();
  }, []);

  const handleCrear = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nuevoNombre.trim()) return;

    try {
      setProcesando(true);
      setError(null);
      const res = await crearClave(nuevoNombre.trim(), nuevosAlcances);
      setClaveRevelada(res.clave_en_claro);
      setModalCrear(false);
      setNuevoNombre("");
      await cargarDatos();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al crear la clave";
      setError(msg);
    } finally {
      setProcesando(false);
    }
  };

  const handleRotar = async (id: string, nombre: string) => {
    if (
      !confirm(
        `¿Rotar la clave «${nombre}»? La versión anterior quedará invalidada inmediatamente.`
      )
    ) {
      return;
    }

    try {
      setProcesando(true);
      setError(null);
      const res = await rotarClave(id);
      setClaveRevelada(res.clave_en_claro);
      await cargarDatos();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al rotar la clave";
      setError(msg);
    } finally {
      setProcesando(false);
    }
  };

  const handleRevocar = async (id: string, nombre: string) => {
    if (
      !confirm(
        `¿Revocar permanentemente la clave «${nombre}»? Ninguna integración podrá seguir usándola.`
      )
    ) {
      return;
    }

    try {
      setProcesando(true);
      setError(null);
      await revocarClave(id);
      await cargarDatos();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al revocar la clave";
      setError(msg);
    } finally {
      setProcesando(false);
    }
  };

  const copiarClave = () => {
    if (claveRevelada) {
      navigator.clipboard.writeText(claveRevelada);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2500);
    }
  };

  const toggleAlcance = (alcanceId: string) => {
    setNuevosAlcances((prev) =>
      prev.includes(alcanceId)
        ? prev.filter((a) => a !== alcanceId)
        : [...prev, alcanceId]
    );
  };

  const maxClaves = techos?.claves.maximo;
  const activasClaves = techos?.claves.activas ?? 0;
  const limiteAlcanzado = maxClaves !== null && maxClaves !== undefined && activasClaves >= maxClaves;

  return (
    <div className="space-y-6 p-6 max-w-6xl mx-auto">
      {/* Encabezado */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
            Claves de Integración y API
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Administra las claves Bearer (evk_…) para acceder a la API versionada con alcances seguros.
          </p>
        </div>
        <button
          onClick={() => setModalCrear(true)}
          disabled={limiteAlcanzado || procesando}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Nueva Clave de Integración
        </button>
      </div>

      {/* Errores */}
      {error && (
        <div className="p-4 rounded-md bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm border border-red-200 dark:border-red-800">
          {error}
        </div>
      )}

      {/* Alerta de clave generada / rotada en claro */}
      {claveRevelada && (
        <div className="p-5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border-2 border-amber-400 dark:border-amber-600 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-amber-800 dark:text-amber-200">
              ⚠️ Guarda tu nueva clave de integración
            </h3>
            <button
              onClick={() => setClaveRevelada(null)}
              className="text-xs text-gray-500 hover:text-gray-800 dark:hover:text-gray-200"
            >
              Cerrar aviso
            </button>
          </div>
          <p className="text-sm text-amber-700 dark:text-amber-300">
            Esta clave solo se muestra en claro esta única vez. Cópiala y guárdala en tu gestor de secretos seguro:
          </p>
          <div className="flex items-center gap-2">
            <input
              type="text"
              readOnly
              value={claveRevelada}
              className="flex-1 font-mono text-sm p-2 rounded border bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 select-all"
            />
            <button
              onClick={copiarClave}
              className="px-3 py-2 bg-amber-600 text-white rounded text-sm font-medium hover:bg-amber-700"
            >
              {copiado ? "¡Copiada!" : "Copiar"}
            </button>
          </div>
        </div>
      )}

      {/* Tarjetas de Techos de Paquete */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-4 rounded-lg border bg-white dark:bg-gray-800 shadow-sm">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Techo de Claves Activas
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-gray-900 dark:text-gray-100">
              {activasClaves}
            </span>
            <span className="text-sm text-gray-500">
              de {maxClaves === null || maxClaves === undefined ? "Ilimitadas (Enterprise)" : maxClaves} permitidas
            </span>
          </div>
          {limiteAlcanzado && (
            <p className="mt-1 text-xs text-red-600 dark:text-red-400 font-medium">
              Techo alcanzado. Para emitir una nueva, revoca una clave en desuso o amplía tu paquete.
            </p>
          )}
        </div>

        <div className="p-4 rounded-lg border bg-white dark:bg-gray-800 shadow-sm">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Webhooks Activos
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-gray-900 dark:text-gray-100">
              {techos?.webhooks.activos ?? 0}
            </span>
            <span className="text-sm text-gray-500">
              de {techos?.webhooks.maximo === null || techos?.webhooks.maximo === undefined ? "Ilimitados" : techos.webhooks.maximo} permitidos
            </span>
          </div>
        </div>
      </div>

      {/* Tabla de Claves */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b bg-gray-50 dark:bg-gray-700/50">
          <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-200">
            Claves de Integración Registradas
          </h2>
        </div>

        {cargando ? (
          <div className="p-8 text-center text-sm text-gray-500">Cargando claves...</div>
        ) : claves.length === 0 ? (
          <div className="p-8 text-center text-sm text-gray-500">
            No hay claves de integración registradas para esta organización.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-left text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800 text-gray-500 font-medium">
                <tr>
                  <th className="px-4 py-3">Nombre</th>
                  <th className="px-4 py-3">Prefijo</th>
                  <th className="px-4 py-3">Alcances</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="px-4 py-3">Creada</th>
                  <th className="px-4 py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {claves.map((k) => {
                  const esRevocada = !!k.revocada_en;
                  const esRotada = !!k.rotada_en;
                  const esActiva = !esRevocada && !esRotada;

                  return (
                    <tr key={k.id} className="hover:bg-gray-50 dark:hover:bg-gray-750">
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">
                        {k.nombre}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-600 dark:text-gray-300">
                        {k.prefijo}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {k.alcances.map((alc) => (
                            <span
                              key={alc}
                              className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300"
                            >
                              {alc}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {esRevocada ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300">
                            Revocada
                          </span>
                        ) : esRotada ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                            Rotada
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300">
                            Activa
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">
                        {new Date(k.creada_en).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-right space-x-2">
                        {esActiva && (
                          <>
                            <button
                              onClick={() => handleRotar(k.id, k.nombre)}
                              disabled={procesando}
                              className="text-xs font-medium text-indigo-600 hover:text-indigo-800 dark:text-indigo-400"
                            >
                              Rotar
                            </button>
                            <button
                              onClick={() => handleRevocar(k.id, k.nombre)}
                              disabled={procesando}
                              className="text-xs font-medium text-red-600 hover:text-red-800 dark:text-red-400"
                            >
                              Revocar
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal Crear */}
      {modalCrear && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              Generar Nueva Clave de Integración
            </h3>
            <form onSubmit={handleCrear} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Nombre identificador
                </label>
                <input
                  type="text"
                  required
                  placeholder="ej. ERP Producción, Script Backup"
                  value={nuevoNombre}
                  onChange={(e) => setNuevoNombre(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 p-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Alcances autorizados
                </label>
                <div className="space-y-2">
                  {ALCANCES_DISPONIBLES.map((alc) => (
                    <label key={alc.id} className="flex items-start gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={nuevosAlcances.includes(alc.id)}
                        onChange={() => toggleAlcance(alc.id)}
                        className="mt-1 rounded text-indigo-600 focus:ring-indigo-500"
                      />
                      <div>
                        <div className="text-xs font-semibold text-gray-800 dark:text-gray-200">
                          {alc.label} ({alc.id})
                        </div>
                        <div className="text-xs text-gray-500">{alc.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t">
                <button
                  type="button"
                  onClick={() => setModalCrear(false)}
                  className="px-4 py-2 border rounded-md text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={procesando || !nuevoNombre.trim()}
                  className="px-4 py-2 rounded-md text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
                >
                  {procesando ? "Emitiendo..." : "Emitir Clave"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* === API-02b === */}
      {/* --- INICIO API-02b --- */}
      {(() => {
        type PropsPanel = { techoMaximo: number | null; onCambioActivos: () => void };
        type TipoPanel = React.LazyExoticComponent<React.ComponentType<PropsPanel>>;
        const clave = Symbol.for("evydentia.api02b.webhooksPanel");
        const almacen = globalThis as unknown as Record<symbol, TipoPanel | undefined>;
        const PanelWebhooks =
          almacen[clave] ??
          (almacen[clave] = React.lazy(() => import("@/components/integraciones/WebhooksPanel")));
        return (
          <React.Suspense fallback={null}>
            <PanelWebhooks
              techoMaximo={techos?.webhooks.maximo ?? null}
              onCambioActivos={() => {
                void cargarDatos();
              }}
            />
          </React.Suspense>
        );
      })()}
      {/* --- FIN API-02b --- */}
      {/* === fin API-02b === */}
    </div>
  );
}
