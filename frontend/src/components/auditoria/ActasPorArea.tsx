// ¤auditoria-capa ¤hallazgos
import React, { useState } from "react";
import {
  AuditoriaDetalle,
  ActaContenido,
  levantarYFirmarActa,
  obtenerActa,
} from "@/lib/auditoria/auditorias";

interface Props {
  auditoria: AuditoriaDetalle;
  esAuditorEquipo: boolean;
  onActaFirmada: (areaId: string, actaSha256: string) => void;
}

export const ActasPorArea: React.FC<Props> = ({
  auditoria,
  esAuditorEquipo,
  onActaFirmada,
}) => {
  const [areaParaFirmar, setAreaParaFirmar] = useState<string | null>(null);
  const [firmando, setFirmando] = useState(false);
  const [mensajeStatus, setMensajeStatus] = useState<string | null>(null);
  const [errorFirmar, setErrorFirmar] = useState<string | null>(null);

  // Modal de Ver Acta
  const [actaVisualizada, setActaVisualizada] = useState<{ areaId: string; acta: ActaContenido } | null>(null);
  const [cargandoActa, setCargandoActa] = useState(false);
  const [errorVerActa, setErrorVerActa] = useState<string | null>(null);

  const actasMap = new Map(auditoria.actas.map((a) => [a.area_id, a]));

  const handleConfirmarFirma = async () => {
    if (!areaParaFirmar) return;
    setFirmando(true);
    setErrorFirmar(null);
    try {
      const res = await levantarYFirmarActa(auditoria.id, areaParaFirmar);
      onActaFirmada(res.area_id, res.acta_sha256);
      setMensajeStatus(`Acta de ${areaParaFirmar} firmada y guardada.`);
      setAreaParaFirmar(null);
    } catch (err: unknown) {
      setErrorFirmar(err instanceof Error ? err.message : "Error al firmar");
    } finally {
      setFirmando(false);
    }
  };

  const handleVerActa = async (areaId: string) => {
    setCargandoActa(true);
    setErrorVerActa(null);
    try {
      const acta = await obtenerActa(auditoria.id, areaId);
      setActaVisualizada({ areaId, acta });
    } catch (err: unknown) {
      setErrorVerActa(err instanceof Error ? err.message : "Error al cargar acta");
    } finally {
      setCargandoActa(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">Actas por área</h2>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          La auditoría se cierra cuando todas las áreas tienen su acta firmada.
        </p>
        {!esAuditorEquipo && (
          <p className="text-xs text-slate-500 italic">Solo el equipo auditor firma las actas.</p>
        )}
      </div>

      {mensajeStatus && (
        <div role="status" className="p-3 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-200 border border-emerald-200 dark:border-emerald-800 rounded-md text-sm">
          {mensajeStatus}
        </div>
      )}

      {errorVerActa && (
        <div role="alert" className="p-3 bg-rose-50 text-rose-800 border border-rose-200 rounded-md text-sm">
          {errorVerActa}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" role="list" aria-label="Actas por área">
        {auditoria.alcance.map((areaId) => {
          const filasArea = auditoria.filas.filter((f) => f.area_id === areaId);
          const totalArea = filasArea.length;
          const verificadosArea = filasArea.filter((f) => f.verificado != null).length;
          const faltantes = totalArea - verificadosArea;
          const estaFirmada = actasMap.has(areaId);

          return (
            <div
              key={areaId}
              role="listitem"
              className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-sm space-y-3 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100 text-base">
                    Área {areaId}
                  </h3>
                  <span
                    className={`text-xs px-2 py-0.5 rounded font-medium ${
                      estaFirmada
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200"
                        : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                    }`}
                  >
                    {estaFirmada ? "Firmada" : "Sin firmar"}
                  </span>
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
                  {verificadosArea} de {totalArea} controles verificados
                </p>
                {!estaFirmada && faltantes > 0 && (
                  <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                    Faltan {faltantes} controles de esta área por verificar.
                  </p>
                )}
              </div>

              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                {estaFirmada ? (
                  <button
                    type="button"
                    aria-label={`Ver el acta de ${areaId}`}
                    disabled={cargandoActa}
                    onClick={() => handleVerActa(areaId)}
                    className="text-sm font-semibold text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                  >
                    Ver acta
                  </button>
                ) : esAuditorEquipo ? (
                  <button
                    type="button"
                    aria-label={`Firmar el acta de ${areaId}`}
                    aria-disabled={faltantes > 0}
                    disabled={faltantes > 0}
                    onClick={() => setAreaParaFirmar(areaId)}
                    className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Firmar acta
                  </button>
                ) : (
                  <span className="text-xs text-slate-400">Pendiente de firma</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Diálogo de Confirmación de Firma */}
      {areaParaFirmar && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4"
        >
          <div className="w-full max-w-md rounded-lg bg-white dark:bg-slate-900 p-6 shadow-xl border border-slate-200 dark:border-slate-800 space-y-4">
            <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              ¿Firmar el acta de {areaParaFirmar}?
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              El acta recoge los controles que verificaste en esta área y la evidencia revisada.
              Al firmar queda guardada con tu nombre y la fecha, y las filas del área ya no se pueden cambiar.
            </p>

            {errorFirmar && (
              <div role="alert" className="text-xs text-rose-600 dark:text-rose-400 font-medium">
                {errorFirmar}
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                autoFocus
                onClick={() => setAreaParaFirmar(null)}
                className="rounded border border-slate-300 dark:border-slate-700 px-3 py-1.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={firmando}
                onClick={handleConfirmarFirma}
                className="rounded bg-indigo-600 px-3.5 py-1.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
              >
                {firmando ? "Firmando..." : "Firmar el acta"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Diálogo Solo Lectura de Ver Acta */}
      {actaVisualizada && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4"
        >
          <div className="w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-lg bg-white dark:bg-slate-900 p-6 shadow-xl border border-slate-200 dark:border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b pb-3 border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Acta de auditoría · {actaVisualizada.areaId}
              </h3>
              <button
                type="button"
                onClick={() => setActaVisualizada(null)}
                className="text-slate-400 hover:text-slate-600 text-sm"
              >
                ✕ Cerrar
              </button>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/40 p-4 rounded-md border border-slate-100 dark:border-slate-800 font-mono text-xs whitespace-pre-wrap text-slate-800 dark:text-slate-200">
              {actaVisualizada.acta.contenido}
            </div>

            <div className="text-xs text-slate-500 flex items-center justify-between pt-2">
              <span aria-label="Huella de integridad">
                Huella de integridad: {actaVisualizada.acta.acta_sha256.slice(0, 8)}
              </span>
            </div>

            <p className="text-xs text-slate-400 italic">
              Esta acta recoge lo verificado por el equipo auditor en la fecha indicada y no sustituye otras verificaciones.
            </p>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => setActaVisualizada(null)}
                className="rounded border border-slate-300 dark:border-slate-700 px-3.5 py-1.5 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
