// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤auditoria-capa ¤hallazgos
import React, { useState } from "react";
import { AuditoriaDetalle, AuditoriaFila, actualizarFilaAuditoria } from "@/lib/auditoria/auditorias";

interface Props {
  auditoria: AuditoriaDetalle;
  esAuditorEquipo: boolean;
  onFilaActualizada: (fila: AuditoriaFila) => void;
}

function calcularEtiquetaRiesgo(riesgo: number): { texto: string; clase: string } {
  if (riesgo >= 15) {
    return { texto: "Crítico", clase: "badge-critico" };
  }
  if (riesgo >= 9) {
    return { texto: "Alto", clase: "badge-alto" };
  }
  return { texto: "Medio", clase: "badge-medio" };
}

export const GrillaAuditoria: React.FC<Props> = ({
  auditoria,
  esAuditorEquipo,
  onFilaActualizada,
}) => {
  const [guardando, setGuardando] = useState<string | null>(null);
  const [mensajeEstado, setMensajeEstado] = useState<string | null>(null);
  const [errorFila, setErrorFila] = useState<{ controlRef: string; mensaje: string } | null>(null);

  // Estados locales editables por fila
  const [valoresVerificados, setValoresVerificados] = useState<Record<string, number>>(() => {
    const inicial: Record<string, number> = {};
    for (const f of auditoria.filas) {
      if (f.verificado != null) {
        inicial[f.control_ref] = f.verificado;
      }
    }
    return inicial;
  });

  const [evidencias, setEvidencias] = useState<Record<string, string>>(() => {
    const inicial: Record<string, string> = {};
    for (const f of auditoria.filas) {
      if (f.evidencia_sha256) {
        inicial[f.control_ref] = f.evidencia_sha256;
      }
    }
    return inicial;
  });

  const actasFirmadas = new Set(auditoria.actas.map((a) => a.area_id));

  const handleGuardarFila = async (fila: AuditoriaFila) => {
    const verificadoVal = valoresVerificados[fila.control_ref];
    if (verificadoVal == null) return;

    setGuardando(fila.control_ref);
    setErrorFila(null);
    setMensajeEstado(null);

    // Fórmula: riesgo_final = (5 - verificado) * criticidad
    const criticidad = fila.declarado > 0 ? Math.round(fila.riesgo_inicial / Math.max(1, 5 - fila.declarado)) : 1;
    const riesgoFinal = (5 - verificadoVal) * criticidad;

    try {
      const filaActualizada = await actualizarFilaAuditoria(auditoria.id, fila.control_ref, {
        verificado: verificadoVal,
        riesgo_final: riesgoFinal,
        evidencia_sha256: evidencias[fila.control_ref] || null,
      });
      onFilaActualizada(filaActualizada);
      setMensajeEstado(`Control ${fila.control_ref} guardado.`);
    } catch (err: unknown) {
      setErrorFila({
        controlRef: fila.control_ref,
        mensaje: err instanceof Error ? err.message : "Error al guardar control",
      });
    } finally {
      setGuardando(null);
    }
  };

  return (
    <div className="space-y-4">
      {mensajeEstado && (
        <div role="status" className="p-3 bg-[var(--ui-exito-fondo)] text-[var(--ui-exito-texto)] border border-[var(--ui-exito-borde)] rounded-md text-sm">
          {mensajeEstado}
        </div>
      )}

      {/* Vista desktop: Tabla accesible */}
      <div className="hidden md:block overflow-x-auto rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] shadow-sm">
        <table className="w-full text-left text-sm" aria-label="Verificación de controles">
          <thead className="bg-[var(--ui-superficie-2)] text-[var(--ui-texto-suave)] border-b border-[var(--ui-borde)]">
            <tr>
              <th scope="col" className="px-4 py-3 font-semibold">Control</th>
              <th scope="col" className="px-3 py-3 font-semibold">Declarado</th>
              <th scope="col" className="px-3 py-3 font-semibold">Riesgo inicial</th>
              <th scope="col" className="px-4 py-3 font-semibold">Verificado</th>
              <th scope="col" className="px-4 py-3 font-semibold">Evidencia</th>
              <th scope="col" className="px-3 py-3 font-semibold">Riesgo final</th>
              <th scope="col" className="px-4 py-3 font-semibold">Revisado por</th>
              <th scope="col" className="px-4 py-3 font-semibold text-right">Acción</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--ui-borde)]">
            {auditoria.filas.map((fila) => {
              const estaFirmada = actasFirmadas.has(fila.area_id);
              const puedeEditar = esAuditorEquipo && auditoria.estado === "abierta" && !estaFirmada;
              const valVerificado = valoresVerificados[fila.control_ref] ?? fila.verificado;
              const porDebajo = valVerificado != null && valVerificado < fila.declarado;
              const riesgoInicialInfo = calcularEtiquetaRiesgo(fila.riesgo_inicial);
              const riesgoFinalVal = fila.riesgo_final ?? (valVerificado != null ? (5 - valVerificado) * 3 : null);
              const riesgoFinalInfo = riesgoFinalVal != null ? calcularEtiquetaRiesgo(riesgoFinalVal) : null;

              return (
                <tr key={fila.id} className="hover:bg-[var(--ui-superficie-2)]">
                  <td className="px-4 py-3 font-medium text-[var(--foreground)]">
                    <span className="font-mono text-xs px-2 py-0.5 rounded bg-[var(--ui-superficie-2)] text-[var(--ui-texto-suave)]">
                      {fila.control_ref}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-[var(--ui-texto-suave)]">
                    Nivel {fila.declarado}
                  </td>
                  <td className="px-3 py-3">
                    <span className="text-xs px-2 py-0.5 rounded font-medium bg-[var(--ui-aviso-fondo)] text-[var(--ui-aviso-texto)]">
                      {riesgoInicialInfo.texto} ({fila.riesgo_inicial})
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {puedeEditar ? (
                      <select
                        aria-label={`Nivel verificado del control ${fila.control_ref}`}
                        value={valVerificado ?? ""}
                        onChange={(e) => {
                          const val = Number(e.target.value);
                          setValoresVerificados((prev) => ({ ...prev, [fila.control_ref]: val }));
                        }}
                        className="rounded border border-[var(--ui-borde-control)] bg-[var(--ui-campo)] px-2.5 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--ui-primario)]"
                      >
                        <option value="">Elegir...</option>
                        <option value="1">Nivel 1</option>
                        <option value="2">Nivel 2</option>
                        <option value="3">Nivel 3</option>
                        <option value="4">Nivel 4</option>
                        <option value="5">Nivel 5</option>
                      </select>
                    ) : (
                      <span className="text-[var(--ui-texto-suave)]">
                        {fila.verificado != null ? `Nivel ${fila.verificado}` : "Sin verificar"}
                      </span>
                    )}

                    {porDebajo && (
                      <div className="mt-1 flex items-center gap-1 text-xs text-[var(--ui-aviso-texto)] font-medium">
                        <span aria-hidden="true">⚠️</span>
                        <span>Por debajo de lo declarado</span>
                      </div>
                    )}
                    {fila.hallazgo_id && (
                      <div className="mt-0.5 text-xs text-[var(--ui-enlace)]">
                        Hallazgo registrado
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-[var(--ui-texto-suave)] text-xs">
                    {puedeEditar ? (
                      <input
                        type="text"
                        placeholder="Huella sha256..."
                        value={evidencias[fila.control_ref] || ""}
                        onChange={(e) =>
                          setEvidencias((prev) => ({ ...prev, [fila.control_ref]: e.target.value }))
                        }
                        className="w-32 rounded border border-[var(--ui-borde-control)] bg-[var(--ui-campo)] px-2 py-1 text-xs"
                      />
                    ) : (
                      <span>{fila.evidencia_sha256 ? `${fila.evidencia_sha256.slice(0, 10)}...` : "—"}</span>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    {riesgoFinalInfo ? (
                      <span className="text-xs px-2 py-0.5 rounded font-medium bg-[var(--ui-superficie-2)] text-[var(--ui-texto-suave)]">
                        {riesgoFinalInfo.texto} ({riesgoFinalVal})
                      </span>
                    ) : (
                      <span className="text-[var(--ui-texto-suave)] text-xs">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-[var(--ui-texto-suave)]">
                    {fila.revisado_por || "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {puedeEditar && (
                      <button
                        type="button"
                        aria-label={`Guardar el control ${fila.control_ref}`}
                        disabled={guardando === fila.control_ref || valVerificado == null}
                        onClick={() => handleGuardarFila(fila)}
                        className="rounded bg-[var(--ui-primario)] text-[var(--ui-primario-texto)] px-2.5 py-1 text-xs font-semibold shadow-sm hover:bg-[var(--ui-primario-hover)] disabled:opacity-50"
                      >
                        {guardando === fila.control_ref ? "Guardando..." : "Guardar"}
                      </button>
                    )}
                    {errorFila?.controlRef === fila.control_ref && (
                      <div role="alert" className="mt-1 text-xs text-[var(--ui-error-texto)]">
                        {errorFila.mensaje}
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Vista móvil: Tarjetas apiladas sin scroll horizontal */}
      <div className="md:hidden space-y-3">
        {auditoria.filas.map((fila) => {
          const estaFirmada = actasFirmadas.has(fila.area_id);
          const puedeEditar = esAuditorEquipo && auditoria.estado === "abierta" && !estaFirmada;
          const valVerificado = valoresVerificados[fila.control_ref] ?? fila.verificado;
          const porDebajo = valVerificado != null && valVerificado < fila.declarado;

          return (
            <div
              key={fila.id}
              className="rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4 shadow-sm space-y-2.5"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[var(--ui-superficie-2)] text-[var(--foreground)]">
                  {fila.control_ref}
                </span>
                <span className="text-xs text-[var(--ui-texto-suave)]">
                  Declarado: Nivel {fila.declarado}
                </span>
              </div>

              <div className="flex flex-col gap-1 text-sm">
                <label className="text-xs font-medium text-[var(--ui-texto-suave)]">
                  Nivel verificado:
                </label>
                {puedeEditar ? (
                  <select
                    aria-label={`Nivel verificado del control ${fila.control_ref}`}
                    value={valVerificado ?? ""}
                    onChange={(e) => {
                      const val = Number(e.target.value);
                      setValoresVerificados((prev) => ({ ...prev, [fila.control_ref]: val }));
                    }}
                    className="rounded border border-[var(--ui-borde-control)] bg-[var(--ui-campo)] px-2 py-1.5 text-sm"
                  >
                    <option value="">Elegir nivel...</option>
                    <option value="1">Nivel 1</option>
                    <option value="2">Nivel 2</option>
                    <option value="3">Nivel 3</option>
                    <option value="4">Nivel 4</option>
                    <option value="5">Nivel 5</option>
                  </select>
                ) : (
                  <span className="text-[var(--ui-texto-suave)]">
                    {fila.verificado != null ? `Nivel ${fila.verificado}` : "Sin verificar"}
                  </span>
                )}
              </div>

              {porDebajo && (
                <div className="text-xs text-[var(--ui-aviso-texto)] font-medium flex items-center gap-1">
                  <span>⚠️</span> Por debajo de lo declarado
                </div>
              )}

              {fila.hallazgo_id && (
                <div className="text-xs text-[var(--ui-enlace)] font-medium">
                  Hallazgo registrado
                </div>
              )}

              {puedeEditar && (
                <div className="pt-2 flex justify-end">
                  <button
                    type="button"
                    aria-label={`Guardar el control ${fila.control_ref}`}
                    disabled={guardando === fila.control_ref || valVerificado == null}
                    onClick={() => handleGuardarFila(fila)}
                    className="rounded bg-[var(--ui-primario)] text-[var(--ui-primario-texto)] px-3 py-1.5 text-xs font-semibold shadow-sm hover:bg-[var(--ui-primario-hover)] disabled:opacity-50"
                  >
                    {guardando === fila.control_ref ? "Guardando..." : "Guardar control"}
                  </button>
                </div>
              )}

              {errorFila?.controlRef === fila.control_ref && (
                <div role="alert" className="text-xs text-[var(--ui-error-texto)]">
                  {errorFila.mensaje}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
