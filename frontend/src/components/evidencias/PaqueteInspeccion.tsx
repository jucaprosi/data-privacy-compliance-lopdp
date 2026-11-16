"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, Download, Loader2 } from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import { rolesDelUsuario } from "@/lib/diagnostico/roles";
import {
  ETIQUETA_ROL,
  ROLES_VISIBILIDAD,
  cargarAtributos,
  definirAtributos,
  descargarPaquete,
  formatearFecha,
  mensajeDePaquete,
  type AtributosDocumento,
} from "@/lib/evidencias/vigencia";

const MAXIMO_ROLES_VISIBLES = 3;

function visiblePara(roles: string[]): string {
  const nombres = roles.map((r) => ETIQUETA_ROL[r as keyof typeof ETIQUETA_ROL] ?? r);
  if (nombres.length <= MAXIMO_ROLES_VISIBLES) return nombres.join(", ");
  return `${nombres.slice(0, MAXIMO_ROLES_VISIBLES).join(", ")} y ${nombres.length - MAXIMO_ROLES_VISIBLES} más`;
}

interface Aviso {
  tipo: "error" | "ok";
  texto: string;
}

function AvisoPanel({ aviso }: { aviso: Aviso }) {
  return (
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
  );
}

/** Vigencia, visibilidad y paquete para inspección de las evidencias guardadas en el servidor (EVI-02). */
export default function PaqueteInspeccion() {
  const subidaFirmada = useAuditStore((s) => s.permisosEvidencia?.subidaFirmada === true);
  const hayDocumentosEnLaOrganizacion = useAuditStore((s) => s.evidencias.length > 0);
  const [documentos, setDocumentos] = useState<AtributosDocumento[] | null>(null);
  const [esDpo, setEsDpo] = useState(false);
  const [descargando, setDescargando] = useState(false);
  const [aviso, setAviso] = useState<Aviso | null>(null);
  const [avisoEdicion, setAvisoEdicion] = useState<Aviso | null>(null);
  const [edicion, setEdicion] = useState<{ id: string; vence: string; sinVencimiento: boolean; roles: string[] } | null>(null);
  const botonesCambiar = useRef<Record<string, HTMLButtonElement | null>>({});

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
    if (descargando) return; // aria-disabled no impide el clic: el guardia mantiene el foco en el botón
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
    const id = edicion.id;
    try {
      await definirAtributos(id, edicion.sinVencimiento ? null : edicion.vence || null, edicion.roles);
      setEdicion(null);
      setAvisoEdicion({ tipo: "ok", texto: "Vigencia y visibilidad guardadas. El cambio queda en el historial." });
      await recargar();
      botonesCambiar.current[id]?.focus();
    } catch (error) {
      setAvisoEdicion({ tipo: "error", texto: mensajeDePaquete((error as { code?: string }).code) });
    }
  };

  const hoy = new Date().toISOString().slice(0, 10);

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
          aria-disabled={descargando}
          aria-busy={descargando}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-[var(--ui-primario)] hover:bg-[var(--ui-primario-hover)] text-[var(--ui-primario-texto)] text-xs font-semibold transition cursor-pointer aria-disabled:opacity-60"
        >
          {descargando ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
          ) : (
            <Download className="w-3.5 h-3.5" aria-hidden="true" />
          )}
          {descargando ? "Preparando el paquete…" : "Descargar paquete para inspección"}
        </button>
      </div>

      {aviso && <AvisoPanel aviso={aviso} />}
      {avisoEdicion && <AvisoPanel aviso={avisoEdicion} />}

      {documentos && documentos.length === 0 && (
        <p className="text-xs text-[var(--ui-texto-suave)] italic">
          {hayDocumentosEnLaOrganizacion
            ? "No hay documentos que tu rol pueda ver."
            : "Todavía no hay documentos. Se cargan desde Evidencias."}
        </p>
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
                    {d.vence_en ? `Vigente hasta ${formatearFecha(d.vence_en)}` : "Vigente · sin vencimiento"}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold" data-testid="documento-vencido">
                    <AlertTriangle className="w-3 h-3" aria-hidden="true" />
                    {`Vencido el ${formatearFecha(d.vence_en)} · ya no cuenta como respaldo`}
                  </span>
                )}
                <span className="text-[10px] text-[var(--ui-texto-suave)]">{`Visible para: ${visiblePara(d.visible_para)}`}</span>
                {esDpo && edicion?.id !== d.documento_id && (
                  <button
                    type="button"
                    ref={(el) => {
                      botonesCambiar.current[d.documento_id] = el;
                    }}
                    onClick={() => {
                      setAvisoEdicion(null);
                      setEdicion({
                        id: d.documento_id,
                        vence: d.vence_en ?? "",
                        sinVencimiento: d.vence_en === null,
                        roles: [...d.visible_para],
                      });
                    }}
                    className="ml-auto text-[10px] underline cursor-pointer"
                  >
                    {`Cambiar vigencia y visibilidad de ${d.nombre_archivo} (${d.codigo})`}
                  </button>
                )}
              </div>

              {esDpo && edicion?.id === d.documento_id && (
                <div className="flex flex-wrap items-end gap-3 p-2.5 rounded-lg border border-[var(--ui-borde)]">
                  <div className="text-[11px] space-y-1">
                    <label className="block">
                      <span className="block">Vence el</span>
                      <input
                        type="date"
                        value={edicion.vence}
                        disabled={edicion.sinVencimiento}
                        onChange={(e) => setEdicion({ ...edicion, vence: e.target.value })}
                        className="rounded-md px-2 py-1 bg-[var(--ui-boton)] border border-[var(--ui-borde)]"
                      />
                    </label>
                    <label className="inline-flex items-center gap-1">
                      <input
                        type="checkbox"
                        checked={edicion.sinVencimiento}
                        onChange={(e) => setEdicion({ ...edicion, sinVencimiento: e.target.checked })}
                      />
                      Sin vencimiento
                    </label>
                    {!edicion.sinVencimiento && edicion.vence !== "" && edicion.vence < hoy && (
                      <p role="status" className="text-[10px]">
                        Esa fecha ya pasó: el documento quedará vencido.
                      </p>
                    )}
                  </div>
                  <fieldset className="text-[11px]">
                    <legend>Visible para</legend>
                    <div className="flex flex-wrap gap-3 mt-1">
                      {ROLES_VISIBILIDAD.map((rol) => (
                        <label key={rol} className="inline-flex items-center gap-1">
                          <input
                            type="checkbox"
                            checked={edicion.roles.includes(rol)}
                            disabled={rol === "dpo"}
                            aria-describedby={rol === "dpo" ? `ayuda-dpo-${d.documento_id}` : undefined}
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
                    <p id={`ayuda-dpo-${d.documento_id}`} className="text-[10px] text-[var(--ui-texto-suave)] mt-1">
                      El DPO siempre ve los documentos.
                    </p>
                  </fieldset>
                  <button
                    type="button"
                    onClick={() => void guardar()}
                    className="px-2.5 py-1 rounded-md border border-[var(--ui-borde)] font-semibold cursor-pointer"
                  >
                    Guardar cambios
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setEdicion(null);
                      botonesCambiar.current[d.documento_id]?.focus();
                    }}
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
