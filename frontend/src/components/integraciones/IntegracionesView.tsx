// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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
          <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
            Claves de Integración y API
          </h1>
          <p className="text-sm text-[var(--ui-texto-suave)]">
            Administra las claves Bearer (evk_…) para acceder a la API versionada con alcances seguros.
          </p>
        </div>
        <button
          onClick={() => setModalCrear(true)}
          disabled={limiteAlcanzado || procesando}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-[var(--ui-primario-texto)] bg-[var(--ui-primario)] hover:bg-[var(--ui-primario-hover)] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Nueva Clave de Integración
        </button>
      </div>

      {/* Errores */}
      {error && (
        <div className="p-4 rounded-md bg-[var(--ui-error-fondo)] text-[var(--ui-error-texto)] text-sm border border-[var(--ui-error-borde)]">
          {error}
        </div>
      )}

      {/* Alerta de clave generada / rotada en claro */}
      {claveRevelada && (
        <div className="p-5 rounded-lg bg-[var(--ui-aviso-fondo)] border-2 border-[var(--ui-aviso-borde)] space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-[var(--ui-aviso-titulo)]">
              ⚠️ Guarda tu nueva clave de integración
            </h3>
            <button
              onClick={() => setClaveRevelada(null)}
              className="text-xs text-[var(--ui-texto-suave)] hover:text-[var(--foreground)]"
            >
              Cerrar aviso
            </button>
          </div>
          <p className="text-sm text-[var(--ui-aviso-texto)]">
            Esta clave solo se muestra en claro esta única vez. Cópiala y guárdala en tu gestor de secretos seguro:
          </p>
          <div className="flex items-center gap-2">
            <input
              type="text"
              readOnly
              value={claveRevelada}
              className="flex-1 font-mono text-sm p-2 rounded border border-[var(--ui-borde-control)] bg-[var(--ui-campo)] text-[var(--foreground)] select-all"
            />
            <button
              onClick={copiarClave}
              className="px-3 py-2 bg-[var(--ui-primario)] text-[var(--ui-primario-texto)] rounded text-sm font-medium hover:bg-[var(--ui-primario-hover)]"
            >
              {copiado ? "¡Copiada!" : "Copiar"}
            </button>
          </div>
        </div>
      )}

      {/* Tarjetas de Techos de Paquete */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-4 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] shadow-sm">
          <span className="text-xs font-semibold text-[var(--ui-texto-suave)] uppercase tracking-wider">
            Techo de Claves Activas
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-[var(--foreground)]">
              {activasClaves}
            </span>
            <span className="text-sm text-[var(--ui-texto-suave)]">
              de {maxClaves === null || maxClaves === undefined ? "Ilimitadas (Enterprise)" : maxClaves} permitidas
            </span>
          </div>
          {limiteAlcanzado && (
            <p className="mt-1 text-xs text-[var(--ui-error-texto)] font-medium">
              Techo alcanzado. Para emitir una nueva, revoca una clave en desuso o amplía tu paquete.
            </p>
          )}
        </div>

        <div className="p-4 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] shadow-sm">
          <span className="text-xs font-semibold text-[var(--ui-texto-suave)] uppercase tracking-wider">
            Webhooks Activos
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-[var(--foreground)]">
              {techos?.webhooks.activos ?? 0}
            </span>
            <span className="text-sm text-[var(--ui-texto-suave)]">
              de {techos?.webhooks.maximo === null || techos?.webhooks.maximo === undefined ? "Ilimitados" : techos.webhooks.maximo} permitidos
            </span>
          </div>
        </div>
      </div>

      {/* Tabla de Claves */}
      <div className="bg-[var(--ui-superficie)] shadow-sm border border-[var(--ui-borde)] rounded-lg overflow-hidden">
        <div className="px-4 py-3 border-b border-[var(--ui-borde)] bg-[var(--ui-superficie-2)]">
          <h2 className="text-sm font-semibold text-[var(--foreground)]">
            Claves de Integración Registradas
          </h2>
        </div>

        {cargando ? (
          <div className="p-8 text-center text-sm text-[var(--ui-texto-suave)]">Cargando claves...</div>
        ) : claves.length === 0 ? (
          <div className="p-8 text-center text-sm text-[var(--ui-texto-suave)]">
            No hay claves de integración registradas para esta organización.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-[var(--ui-borde)] text-left text-sm">
              <thead className="bg-[var(--ui-superficie-2)] text-[var(--ui-texto-suave)] font-medium">
                <tr>
                  <th className="px-4 py-3">Nombre</th>
                  <th className="px-4 py-3">Prefijo</th>
                  <th className="px-4 py-3">Alcances</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="px-4 py-3">Creada</th>
                  <th className="px-4 py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--ui-borde)]">
                {claves.map((k) => {
                  const esRevocada = !!k.revocada_en;
                  const esRotada = !!k.rotada_en;
                  const esActiva = !esRevocada && !esRotada;

                  return (
                    <tr key={k.id} className="hover:bg-[var(--ui-superficie-2)]">
                      <td className="px-4 py-3 font-medium text-[var(--foreground)]">
                        {k.nombre}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-[var(--ui-texto-suave)]">
                        {k.prefijo}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {k.alcances.map((alc) => (
                            <span
                              key={alc}
                              className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-[var(--ui-info-fondo)] text-[var(--ui-info-texto)]"
                            >
                              {alc}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {esRevocada ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-[var(--ui-error-fondo)] text-[var(--ui-error-texto)]">
                            Revocada
                          </span>
                        ) : esRotada ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-[var(--ui-boton)] text-[var(--ui-texto-suave)]">
                            Rotada
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-[var(--ui-exito-fondo)] text-[var(--ui-exito-texto)]">
                            Activa
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs text-[var(--ui-texto-suave)]">
                        {new Date(k.creada_en).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-right space-x-2">
                        {esActiva && (
                          <>
                            <button
                              onClick={() => handleRotar(k.id, k.nombre)}
                              disabled={procesando}
                              className="text-xs font-medium text-[var(--ui-enlace)] hover:underline"
                            >
                              Rotar
                            </button>
                            <button
                              onClick={() => handleRevocar(k.id, k.nombre)}
                              disabled={procesando}
                              className="text-xs font-medium text-[var(--ui-peligro-texto)] hover:underline"
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
          <div className="bg-[var(--ui-superficie)] rounded-lg shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-[var(--foreground)]">
              Generar Nueva Clave de Integración
            </h3>
            <form onSubmit={handleCrear} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[var(--ui-texto-suave)]">
                  Nombre identificador
                </label>
                <input
                  type="text"
                  required
                  placeholder="ej. ERP Producción, Script Backup"
                  value={nuevoNombre}
                  onChange={(e) => setNuevoNombre(e.target.value)}
                  className="mt-1 block w-full rounded-md border border-[var(--ui-borde-control)] p-2 text-sm bg-[var(--ui-campo)] text-[var(--foreground)]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--ui-texto-suave)] mb-2">
                  Alcances autorizados
                </label>
                <div className="space-y-2">
                  {ALCANCES_DISPONIBLES.map((alc) => (
                    <label key={alc.id} className="flex items-start gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={nuevosAlcances.includes(alc.id)}
                        onChange={() => toggleAlcance(alc.id)}
                        className="mt-1 rounded accent-[var(--ui-primario)] focus:ring-[var(--ui-primario)]"
                      />
                      <div>
                        <div className="text-xs font-semibold text-[var(--foreground)]">
                          {alc.label} ({alc.id})
                        </div>
                        <div className="text-xs text-[var(--ui-texto-suave)]">{alc.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t">
                <button
                  type="button"
                  onClick={() => setModalCrear(false)}
                  className="px-4 py-2 border border-[var(--ui-borde-control)] rounded-md text-sm text-[var(--foreground)] hover:bg-[var(--ui-boton-hover)]"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={procesando || !nuevoNombre.trim()}
                  className="px-4 py-2 rounded-md text-sm font-medium text-[var(--ui-primario-texto)] bg-[var(--ui-primario)] hover:bg-[var(--ui-primario-hover)] disabled:opacity-50"
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
