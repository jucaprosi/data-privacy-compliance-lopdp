"use client";
// ¤frontend-ide ¤videovigilancia-cctv ¤incidentes ¤derechos ¤conservacion
/**
 * Pantalla CCTV-02: Congelamiento Forense (Hold Legal) y Actas Quincenales SHA-256.
 *
 * Invariante INV_LOPDP_CCTV_LEGAL_HOLD_OVERRIDE:
 * - Línea de tiempo de clips de los últimos 15 días con estado de custodia.
 * - Promoción WORM en 1 clic al bucket 'long-retention' ante incidentes o solicitudes ARCOP+.
 * - Ejecución del barrido de purga quincenal con sellado criptográfico inmutable SHA-256.
 */
import React, { useCallback, useEffect, useState } from "react";
import type { RegistroPantallas } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    videovigilancia_cctv: true;
  }
}

export interface ClipCCTV {
  id: string;
  tenant_id: string;
  camara_id: string;
  sha256_clip: string;
  fecha_captura: string;
  expira_en: string;
  hold_legal_activo: boolean;
  expediente_origen_tipo: "INCIDENTE" | "ARCOP" | null;
  expediente_origen_id: string | null;
  bucket_actual: "short-ttl" | "long-retention";
  acta_destruccion_hash: string | null;
}

export interface ActaPurga {
  tipo_acta: string;
  tenant_id: string;
  fecha_emision: string;
  periodo_dias: number;
  total_clips_destruidos: number;
  hashes_destruidos: string[];
  total_clips_preservados_hold: number;
  clips_preservados_ids: string[];
  hash_maestro_sha256: string;
}

export default function CCTV02Pantalla(): React.JSX.Element {
  const [clips, setClips] = useState<ClipCCTV[]>([]);
  const [actas, setActas] = useState<ActaPurga[]>([]);
  const [cargando, setCargando] = useState<boolean>(true);
  const [errorMensaje, setErrorMensaje] = useState<string | null>(null);
  const [exitoMensaje, setExitoMensaje] = useState<string | null>(null);

  // Modal Hold Legal
  const [clipSeleccionado, setClipSeleccionado] = useState<ClipCCTV | null>(null);
  const [tipoExpediente, setTipoExpediente] = useState<"INCIDENTE" | "ARCOP">("INCIDENTE");
  const [idExpediente, setIdExpediente] = useState<string>("");
  const [procesandoHold, setProcesandoHold] = useState<boolean>(false);

  // Modal Purga
  const [ejecutandoPurga, setEjecutandoPurga] = useState<boolean>(false);
  const [actaReciente, setActaReciente] = useState<ActaPurga | null>(null);

  const cargarDatos = useCallback(async () => {
    setCargando(true);
    setErrorMensaje(null);
    try {
      const [resClips, resActas] = await Promise.all([
        fetch("/api/v1/videovigilancia/clips", {
          headers: { "X-Tenant-ID": "default", "X-Role": "dpo" },
        }),
        fetch("/api/v1/videovigilancia/purga-quincenal/actas", {
          headers: { "X-Tenant-ID": "default", "X-Role": "dpo" },
        }),
      ]);

      if (resClips.ok) {
        const datosClips = await resClips.json();
        setClips(datosClips);
      }
      if (resActas.ok) {
        const datosActas = await resActas.json();
        setActas(datosActas);
      }
    } catch {
      setErrorMensaje("No fue posible sincronizar el inventario de grabaciones.");
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargarDatos();
  }, [cargarDatos]);

  const aplicarHoldLegal = async () => {
    if (!clipSeleccionado || !idExpediente.trim()) return;
    setProcesandoHold(true);
    setErrorMensaje(null);
    setExitoMensaje(null);

    try {
      const res = await fetch(`/api/v1/videovigilancia/clips/${clipSeleccionado.id}/hold-legal`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": "default",
          "X-Role": "dpo",
        },
        body: JSON.stringify({
          expediente_origen_tipo: tipoExpediente,
          expediente_origen_id: idExpediente.trim(),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Error al aplicar Hold Legal" }));
        throw new Error(err.detail || err.message || "Error al congelar el clip");
      }

      setExitoMensaje(
        `Clip ${clipSeleccionado.id.slice(0, 8)} congelado con éxito en bucket WORM 'long-retention'.`
      );
      setClipSeleccionado(null);
      setIdExpediente("");
      await cargarDatos();
    } catch (err: unknown) {
      setErrorMensaje(err instanceof Error ? err.message : "Error inesperado al aplicar Hold Legal.");
    } finally {
      setProcesandoHold(false);
    }
  };

  const ejecutarPurga = async () => {
    if (!window.confirm("¿Confirmas la ejecución de la purga quincenal? Los clips ordinarios >= 15 días serán destruidos irreversiblemente.")) {
      return;
    }
    setEjecutandoPurga(true);
    setErrorMensaje(null);
    setExitoMensaje(null);

    try {
      const res = await fetch("/api/v1/videovigilancia/purga-quincenal/ejecutar", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": "default",
          "X-Role": "implementador",
        },
        body: JSON.stringify({}),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Error en la purga quincenal" }));
        throw new Error(err.detail || "Fallo en la ejecución de la purga.");
      }

      const acta: ActaPurga = await res.json();
      setActaReciente(acta);
      setExitoMensaje(
        `Purga quincenal completada: ${acta.total_clips_destruidos} clips destruidos, ${acta.total_clips_preservados_hold} preservados bajo Hold Legal.`
      );
      await cargarDatos();
    } catch (err: unknown) {
      setErrorMensaje(err instanceof Error ? err.message : "Error durante la purga quincenal.");
    } finally {
      setEjecutandoPurga(false);
    }
  };

  return (
    <div className="p-6 space-y-8 max-w-7xl mx-auto">
      {/* Encabezado y Reglas de Gobernanza */}
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300">
                CCTV-02
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
                INV_LOPDP_CCTV_LEGAL_HOLD_OVERRIDE
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300">
                WORM Object Lock
              </span>
            </div>
            <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 mt-2">
              Congelamiento Forense (Hold Legal) y Actas Quincenales CCTV
            </h1>
            <p className="text-sm text-zinc-600 dark:text-zinc-400 mt-1">
              Custodia probatoria de videovigilancia: los clips vinculados a vulneraciones o derechos ARCOP+ prevalecen sobre la purga quincenal.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => void cargarDatos()}
              disabled={cargando}
              className="px-4 py-2 text-sm font-medium text-zinc-700 dark:text-zinc-300 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-lg transition"
            >
              {cargando ? "Sincronizando..." : "Actualizar"}
            </button>
            <button
              type="button"
              onClick={() => void ejecutarPurga()}
              disabled={ejecutandoPurga}
              className="px-4 py-2 text-sm font-medium text-white bg-rose-600 hover:bg-rose-700 disabled:opacity-50 rounded-lg shadow-sm transition"
            >
              {ejecutandoPurga ? "Ejecutando Purga..." : "Ejecutar Purga Quincenal"}
            </button>
          </div>
        </div>

        {/* Notificaciones */}
        {errorMensaje && (
          <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-300 text-sm">
            {errorMensaje}
          </div>
        )}
        {exitoMensaje && (
          <div className="p-4 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-sm">
            {exitoMensaje}
          </div>
        )}
      </div>

      {/* Línea de tiempo de clips (15 días) */}
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
              Línea de Tiempo de Grabaciones (Ventana 15 Días)
            </h2>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Clips en custodia en Bóveda Cloud. Los marcados con Hold Legal residen en bucket WORM inmutable.
            </p>
          </div>
          <span className="text-xs font-mono text-zinc-500">
            Total clips: {clips.length}
          </span>
        </div>

        {clips.length === 0 ? (
          <div className="py-12 text-center text-sm text-zinc-500">
            No hay grabaciones registradas en la ventana quincenal activa.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-800 text-zinc-500 text-xs uppercase tracking-wider">
                  <th className="py-3 px-4">Clip ID</th>
                  <th className="py-3 px-4">Captura</th>
                  <th className="py-3 px-4">Expiración</th>
                  <th className="py-3 px-4">Huella SHA-256</th>
                  <th className="py-3 px-4">Bucket</th>
                  <th className="py-3 px-4">Estado Hold</th>
                  <th className="py-3 px-4 text-right">Acción Forense</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {clips.map((clip) => (
                  <tr key={clip.id} className="hover:bg-zinc-50/50 dark:hover:bg-zinc-800/40">
                    <td className="py-3 px-4 font-mono text-xs">{clip.id.slice(0, 8)}...</td>
                    <td className="py-3 px-4 text-xs">
                      {clip.fecha_captura ? new Date(clip.fecha_captura).toLocaleString() : "—"}
                    </td>
                    <td className="py-3 px-4 text-xs">
                      {clip.expira_en ? new Date(clip.expira_en).toLocaleString() : "—"}
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-zinc-500">
                      {clip.sha256_clip.slice(0, 12)}...
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          clip.bucket_actual === "long-retention"
                            ? "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300"
                            : "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-300"
                        }`}
                      >
                        {clip.bucket_actual}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {clip.hold_legal_activo ? (
                        <div className="flex flex-col">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
                            HOLD ACTIVO
                          </span>
                          <span className="text-[10px] text-zinc-500 mt-0.5">
                            {clip.expediente_origen_tipo}: {clip.expediente_origen_id}
                          </span>
                        </div>
                      ) : (
                        <span className="text-xs text-zinc-400">Ordinario (15d)</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {clip.hold_legal_activo ? (
                        <span className="text-xs text-emerald-600 font-medium">Blindado WORM</span>
                      ) : (
                        <button
                          type="button"
                          onClick={() => setClipSeleccionado(clip)}
                          className="px-2.5 py-1 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded transition shadow-sm"
                        >
                          Hold Legal 1-Clic
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Historial de Actas Quincenales */}
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-6 shadow-sm space-y-4">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          Certificados Quincenales de Destrucción (Inmutabilidad SHA-256)
        </h2>
        <p className="text-xs text-zinc-500 dark:text-zinc-400">
          Actas criptográficas emitidas tras cada purga de 15 días. Constituyen evidencia legal auditada por el DPO.
        </p>

        {actas.length === 0 ? (
          <div className="py-8 text-center text-sm text-zinc-500">
            Aún no se han ejecutado ciclos de purga quincenales.
          </div>
        ) : (
          <div className="space-y-3">
            {actas.map((acta, idx) => (
              <div
                key={acta.hash_maestro_sha256 || idx}
                className="p-4 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-800/30 flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
                      Acta Quincenal: {new Date(acta.fecha_emision).toLocaleDateString()}
                    </span>
                    <span className="text-xs text-emerald-600 font-medium">
                      ✓ {acta.total_clips_destruidos} destruidos
                    </span>
                    <span className="text-xs text-purple-600 font-medium">
                      🛡️ {acta.total_clips_preservados_hold} preservados
                    </span>
                  </div>
                  <p className="text-xs font-mono text-zinc-500 mt-1 break-all">
                    Hash Maestro: {acta.hash_maestro_sha256}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setActaReciente(acta)}
                  className="px-3 py-1.5 text-xs font-medium text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 rounded-md hover:bg-zinc-50 transition"
                >
                  Ver Certificado
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal Hold Legal */}
      {clipSeleccionado && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
              Congelamiento Forense (Hold Legal)
            </h3>
            <p className="text-xs text-zinc-600 dark:text-zinc-400">
              Vincula el clip <code className="font-mono">{clipSeleccionado.id.slice(0, 8)}</code> a un expediente legal.
              El clip será promovido inmediatamente al bucket WORM &apos;long-retention&apos; con bloqueo de eliminación.
            </p>

            <div className="space-y-3 pt-2">
              <div>
                <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Tipo de Expediente
                </label>
                <select
                  value={tipoExpediente}
                  onChange={(e) => setTipoExpediente(e.target.value as "INCIDENTE" | "ARCOP")}
                  className="w-full text-sm border border-zinc-300 dark:border-zinc-700 rounded-lg p-2 bg-transparent"
                >
                  <option value="INCIDENTE">Incidente de Seguridad / Vulneración (INC-01/02)</option>
                  <option value="ARCOP">Solicitud de Derechos ARCOP+ (DER-01)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1">
                  Identificador del Expediente
                </label>
                <input
                  type="text"
                  placeholder="Ej. inc-sec-2026-001 o sol-arco-882"
                  value={idExpediente}
                  onChange={(e) => setIdExpediente(e.target.value)}
                  className="w-full text-sm border border-zinc-300 dark:border-zinc-700 rounded-lg p-2 bg-transparent"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <button
                type="button"
                onClick={() => setClipSeleccionado(null)}
                className="px-4 py-2 text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={() => void aplicarHoldLegal()}
                disabled={procesandoHold || !idExpediente.trim()}
                className="px-4 py-2 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded-lg transition"
              >
                {procesandoHold ? "Congelando..." : "Confirmar Hold Legal"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Certificado / Acta Reciente */}
      {actaReciente && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4 max-h-[85vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-zinc-900 dark:text-zinc-100">
              Certificado Quincenal de Destrucción CCTV
            </h3>
            <p className="text-xs font-mono text-zinc-500 break-all">
              SHA-256 Maestro: {actaReciente.hash_maestro_sha256}
            </p>

            <div className="bg-zinc-50 dark:bg-zinc-950 p-4 rounded-lg text-xs font-mono space-y-2 border border-zinc-200 dark:border-zinc-800">
              <div>Fecha: {actaReciente.fecha_emision}</div>
              <div>Período: {actaReciente.periodo_dias} días</div>
              <div>Clips destruidos: {actaReciente.total_clips_destruidos}</div>
              <div>Clips en Hold Legal preservados: {actaReciente.total_clips_preservados_hold}</div>
              <div className="pt-2 text-zinc-400">Hashes SHA-256 destruidos:</div>
              <ul className="list-disc pl-4 space-y-0.5 text-[11px] max-h-40 overflow-y-auto">
                {actaReciente.hashes_destruidos.length === 0 ? (
                  <li className="text-zinc-400">Ningún clip ordinario vencido</li>
                ) : (
                  actaReciente.hashes_destruidos.map((h) => <li key={h}>{h}</li>)
                )}
              </ul>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => setActaReciente(null)}
                className="px-4 py-2 text-xs font-medium text-zinc-700 dark:text-zinc-300 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 rounded-lg transition"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export const PANTALLAS_CCTV_02: RegistroPantallas = {
  videovigilancia_cctv: () => <CCTV02Pantalla />,
};
