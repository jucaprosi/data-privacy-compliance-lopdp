"use client";

import React, { useCallback, useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Download, Loader2 } from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import { rolesDelUsuario } from "@/lib/diagnostico/roles";
import {
  ETIQUETA_ROL,
  ROLES_VISIBILIDAD,
  cargarAtributos,
  definirAtributos,
  descargarPaquete,
  mensajeDePaquete,
  type AtributosDocumento,
} from "@/lib/evidencias/vigencia";

/** Vigencia, visibilidad y paquete para inspección de las evidencias guardadas en el servidor (EVI-02). */
export default function PaqueteInspeccion() {
  const subidaFirmada = useAuditStore((s) => s.permisosEvidencia?.subidaFirmada === true);
  const [documentos, setDocumentos] = useState<AtributosDocumento[] | null>(null);
  const [esDpo, setEsDpo] = useState(false);
  const [descargando, setDescargando] = useState(false);
  const [aviso, setAviso] = useState<{ tipo: "error" | "ok"; texto: string } | null>(null);
  const [edicion, setEdicion] = useState<{ id: string; vence: string; roles: string[] } | null>(null);

  const recargar = useCallback(async () => {
    try {
      setDocumentos(await cargarAtributos());
    } catch {
      setAviso({ tipo: "error", texto: mensajeDePaquete(undefined) });
    }
  }, []);

  useEffect(() => {
    if (!subidaFirmada) return;
    void recargar();
    void rolesDelUsuario().then((roles) => setEsDpo(roles.includes("dpo")));
  }, [subidaFirmada, recargar]);

  if (!subidaFirmada) return null;

  const bajar = async () => {
    setDescargando(true);
    setAviso(null);
    try {
      await descargarPaquete();
      setAviso({ tipo: "ok", texto: "Paquete para inspección descargado." });
    } catch (error) {
      setAviso({ tipo: "error", texto: mensajeDePaquete((error as { code?: string }).code) });
    } finally {
      setDescargando(false);
    }
  };

  const guardar = async () => {
    if (!edicion) return;
    try {
      await definirAtributos(edicion.id, edicion.vence || null, edicion.roles);
      setEdicion(null);
      await recargar();
    } catch (error) {
      setAviso({ tipo: "error", texto: mensajeDePaquete((error as { code?: string }).code) });
    }
  };

  return (
    <section
      aria-labelledby="titulo-paquete-inspeccion"
      data-testid="paquete-inspeccion"
      className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-5 space-y-3"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 id="titulo-paquete-inspeccion" className="text-xs font-bold uppercase tracking-wider text-white">
            Vigencia y paquete para inspección
          </h3>
          <p className="text-[11px] text-[var(--ui-texto-suave)] mt-0.5">
            El paquete reúne los documentos vigentes que tu rol puede ver, ordenados por requisito, con su índice y su huella de integridad.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void bajar()}
          disabled={descargando}
          aria-busy={descargando}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-[var(--ui-primario)] hover:bg-[var(--ui-primario-hover)] text-[var(--ui-primario-texto)] text-xs font-semibold transition cursor-pointer disabled:opacity-60"
        >
          {descargando ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
          ) : (
            <Download className="w-3.5 h-3.5" aria-hidden="true" />
          )}
          Descargar paquete para inspección
        </button>
      </div>

      {aviso && (
        <div
          role={aviso.tipo === "error" ? "alert" : "status"}
          className="flex items-start gap-2 p-2.5 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-campo)] text-xs"
        >
          {aviso.tipo === "error" ? (
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5" aria-hidden="true" />
          ) : (
            <CheckCircle2 className="w-3.5 h-3.5 mt-0.5" aria-hidden="true" />
          )}
          <span>{aviso.texto}</span>
        </div>
      )}

      {documentos && documentos.length === 0 && (
        <p className="text-xs text-[var(--ui-texto-suave)] italic">No hay documentos que tu rol pueda ver.</p>
      )}

      {documentos && documentos.length > 0 && (
        <ul className="divide-y divide-[var(--ui-borde)] border border-[var(--ui-borde)] rounded-lg overflow-hidden">
          {documentos.map((d) => (
            <li key={d.documento_id} data-testid={`atributos-${d.codigo}`} className="px-3.5 py-3 text-xs space-y-2 bg-[var(--ui-campo)]">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono font-bold">{d.codigo}</span>
                <span className="font-medium truncate" title={d.nombre_archivo}>
                  {d.nombre_archivo}
                </span>
                {d.vigente ? (
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold">
                    <CheckCircle2 className="w-3 h-3" aria-hidden="true" />
                    {d.vence_en ? `Vigente hasta ${d.vence_en}` : "Vigente · sin vencimiento"}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold" data-testid="documento-vencido">
                    <AlertTriangle className="w-3 h-3" aria-hidden="true" />
                    {`Vencido el ${d.vence_en} · no respalda ningún requisito`}
                  </span>
                )}
                <span className="text-[10px] text-[var(--ui-texto-suave)]">
                  {`Lo ven: ${d.visible_para.map((r) => ETIQUETA_ROL[r as keyof typeof ETIQUETA_ROL] ?? r).join(", ")}`}
                </span>
                {esDpo && edicion?.id !== d.documento_id && (
                  <button
                    type="button"
                    onClick={() => setEdicion({ id: d.documento_id, vence: d.vence_en ?? "", roles: [...d.visible_para] })}
                    className="ml-auto text-[10px] underline cursor-pointer"
                  >
                    {`Cambiar vigencia y visibilidad de ${d.codigo}`}
                  </button>
                )}
              </div>

              {esDpo && edicion?.id === d.documento_id && (
                <div className="flex flex-wrap items-end gap-3 p-2.5 rounded-lg border border-[var(--ui-borde)]">
                  <label className="text-[11px] space-y-1">
                    <span className="block">Vence el</span>
                    <input
                      type="date"
                      value={edicion.vence}
                      onChange={(e) => setEdicion({ ...edicion, vence: e.target.value })}
                      className="rounded-md px-2 py-1 bg-[var(--ui-boton)] border border-[var(--ui-borde)]"
                    />
                  </label>
                  <fieldset className="text-[11px]">
                    <legend>Lo ven</legend>
                    <div className="flex flex-wrap gap-3 mt-1">
                      {ROLES_VISIBILIDAD.map((rol) => (
                        <label key={rol} className="inline-flex items-center gap-1">
                          <input
                            type="checkbox"
                            checked={edicion.roles.includes(rol)}
                            disabled={rol === "dpo"}
                            onChange={(e) =>
                              setEdicion({
                                ...edicion,
                                roles: e.target.checked ? [...edicion.roles, rol] : edicion.roles.filter((r) => r !== rol),
                              })
                            }
                          />
                          {ETIQUETA_ROL[rol]}
                        </label>
                      ))}
                    </div>
                  </fieldset>
                  <button
                    type="button"
                    onClick={() => void guardar()}
                    className="px-2.5 py-1 rounded-md border border-[var(--ui-borde)] font-semibold cursor-pointer"
                  >
                    Guardar
                  </button>
                  <button
                    type="button"
                    onClick={() => setEdicion(null)}
                    className="px-2.5 py-1 rounded-md border border-[var(--ui-borde)] cursor-pointer"
                  >
                    Cancelar
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
