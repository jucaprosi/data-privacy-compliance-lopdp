"use client";

import React, { useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  Award,
  CheckCircle2,
  FileCheck,
  Plus,
  Shield,
  ShieldAlert,
  UserCheck,
  XCircle,
} from "lucide-react";

import type { UserItem } from "@/types/roadmap";
import {
  designacionesApi,
  ETIQUETAS_TIPO_DESIGNACION,
  ETIQUETAS_VINCULO,
  type DesignacionCreatePayload,
  type DesignacionFormal,
  type InformeEstadoDesignaciones,
  type InscripcionSpdpPayload,
  type RevocacionPayload,
  type TipoDesignacion,
  type VinculoDesignacion,
} from "./designaciones";
import { describirError, type ErrorDescrito } from "./errores";
import { BOTON, BOTON_PRIMARIO, BloqueError, CAMPO, ETIQUETA } from "./ui";

export interface DesignacionesTabProps {
  designaciones: DesignacionFormal[];
  estadoDesignaciones: InformeEstadoDesignaciones | null;
  usuarios: UserItem[];
  puedeEditar: boolean;
  alCambiar: () => Promise<void>;
}

export function DesignacionesTab({
  designaciones,
  estadoDesignaciones,
  usuarios,
  puedeEditar,
  alCambiar,
}: DesignacionesTabProps) {
  const [errorAccion, setErrorAccion] = useState<ErrorDescrito | null>(null);
  const [ocupado, setOcupado] = useState(false);

  // Modales
  const [mostrarCrear, setMostrarCrear] = useState(false);
  const [designacionParaInscribir, setDesignacionParaInscribir] = useState<DesignacionFormal | null>(null);
  const [designacionParaRevocar, setDesignacionParaRevocar] = useState<DesignacionFormal | null>(null);

  // Estados formulario crear
  const [tipo, setTipo] = useState<TipoDesignacion>("dpd");
  const [userId, setUserId] = useState<string>("");
  const [representanteNombre, setRepresentanteNombre] = useState<string>("");
  const [representanteIdentificacion, setRepresentanteIdentificacion] = useState<string>("");
  const [representanteCargo, setRepresentanteCargo] = useState<string>("");
  const [fechaDesignacion, setFechaDesignacion] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [docReferencia, setDocReferencia] = useState<string>("");
  const [vinculo, setVinculo] = useState<VinculoDesignacion>("relacion_dependencia");
  const [validTo, setValidTo] = useState<string>("");

  // Estados formulario inscribir
  const [inscripcionFecha, setInscripcionFecha] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [inscripcionRef, setInscripcionRef] = useState<string>("");

  // Estados formulario revocar
  const [revocacionMotivo, setRevocacionMotivo] = useState<string>("");

  function abrirCrear() {
    setTipo("dpd");
    setUserId(usuarios[0]?.id ?? "");
    setRepresentanteNombre("");
    setRepresentanteIdentificacion("");
    setRepresentanteCargo("");
    setFechaDesignacion(new Date().toISOString().split("T")[0]);
    setDocReferencia("");
    setVinculo("relacion_dependencia");
    setValidTo("");
    setErrorAccion(null);
    setMostrarCrear(true);
  }

  function abrirInscribir(d: DesignacionFormal) {
    setDesignacionParaInscribir(d);
    setInscripcionFecha(new Date().toISOString().split("T")[0]);
    setInscripcionRef("");
    setErrorAccion(null);
  }

  function abrirRevocar(d: DesignacionFormal) {
    setDesignacionParaRevocar(d);
    setRevocacionMotivo("");
    setErrorAccion(null);
  }

  async function guardarCrear(e: React.FormEvent) {
    e.preventDefault();
    if (!userId || !representanteNombre || !docReferencia) return;

    setOcupado(true);
    setErrorAccion(null);
    try {
      const payload: DesignacionCreatePayload = {
        tipo,
        user_id: userId,
        representante_nombre: representanteNombre.trim(),
        representante_identificacion: representanteIdentificacion.trim(),
        representante_cargo: representanteCargo.trim(),
        fecha_designacion: fechaDesignacion,
        doc_referencia: docReferencia.trim(),
        vinculo: tipo === "dpd" ? vinculo : null,
        valid_to: validTo ? new Date(validTo).toISOString() : null,
      };

      await designacionesApi.crear(payload);
      setMostrarCrear(false);
      await alCambiar();
    } catch (err: unknown) {
      setErrorAccion(describirError(err));
    } finally {
      setOcupado(false);
    }
  }

  async function guardarInscripcion(e: React.FormEvent) {
    e.preventDefault();
    if (!designacionParaInscribir || !inscripcionRef) return;

    setOcupado(true);
    setErrorAccion(null);
    try {
      const payload: InscripcionSpdpPayload = {
        inscripcion_spdp_fecha: inscripcionFecha,
        inscripcion_spdp_ref: inscripcionRef.trim(),
      };

      await designacionesApi.registrarInscripcionSpdp(designacionParaInscribir.id, payload);
      setDesignacionParaInscribir(null);
      await alCambiar();
    } catch (err: unknown) {
      setErrorAccion(describirError(err));
    } finally {
      setOcupado(false);
    }
  }

  async function guardarRevocacion(e: React.FormEvent) {
    e.preventDefault();
    if (!designacionParaRevocar || !revocacionMotivo) return;

    setOcupado(true);
    setErrorAccion(null);
    try {
      const payload: RevocacionPayload = {
        motivo: revocacionMotivo.trim(),
      };

      await designacionesApi.revocar(designacionParaRevocar.id, payload);
      setDesignacionParaRevocar(null);
      await alCambiar();
    } catch (err: unknown) {
      setErrorAccion(describirError(err));
    } finally {
      setOcupado(false);
    }
  }

  const dpdEstado = estadoDesignaciones?.dpd;
  const coordEstado = estadoDesignaciones?.coordinador;

  return (
    <div className="space-y-6 text-zinc-200">
      {/* Cabecera y botón Crear */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#26262b]">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Award className="w-5 h-5 text-[#3892f3]" aria-hidden="true" />
            Designaciones formales (DPD y Coordinador)
          </h3>
          <p className="text-xs text-zinc-400 mt-0.5">
            Registro formal de mandatos, constancias de inscripción ante la SPDP y control de conflictos
            (Arts. 3, 5, 17 Reglamento del Delegado y Arts. 49, 56 Reglamento General).
          </p>
        </div>

        {puedeEditar && (
          <button
            type="button"
            className={BOTON_PRIMARIO}
            onClick={abrirCrear}
            disabled={ocupado}
            data-testid="btn-crear-designacion"
          >
            <Plus className="w-4 h-4" aria-hidden="true" />
            Nueva designación
          </button>
        )}
      </div>

      {errorAccion && <BloqueError error={errorAccion} testId="error-accion-designaciones" />}

      {/* Resumen del Estado de la Organización (GET /estado) */}
      <section aria-label="Estado de designaciones de la organización" className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Tarjeta DPD */}
        <div
          data-testid="tarjeta-estado-dpd"
          className="p-4 rounded-xl bg-[#18181b] border border-[#26262b] space-y-3"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
              <Shield className="w-4 h-4 text-[#3892f3]" aria-hidden="true" />
              Delegado de Protección de Datos (DPD)
            </span>
            {dpdEstado?.designado ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
                Designado
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-400">
                <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" />
                Falta designar
              </span>
            )}
          </div>

          <div className="space-y-1.5 text-xs text-zinc-300">
            {dpdEstado?.designado && dpdEstado.designacion && (
              <div>
                <p className="font-semibold text-white">
                  {dpdEstado.designacion.usuario_nombre ?? dpdEstado.designacion.user_id}
                </p>
                <p className="text-[11px] text-zinc-400">
                  Ref. {dpdEstado.designacion.doc_referencia} · Fecha: {dpdEstado.designacion.fecha_designacion}
                </p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-2 pt-1 border-t border-[#26262b] text-[11px]">
              <div>
                <span className="text-zinc-500">Declaración de conflictos:</span>
                <p className={dpdEstado?.declaracion_completada ? "text-emerald-400 font-semibold" : "text-amber-400"}>
                  {dpdEstado?.declaracion_completada ? "Completada" : "Pendiente de emitir"}
                </p>
              </div>
              <div>
                <span className="text-zinc-500">Inscripción SPDP:</span>
                <p className={dpdEstado?.inscrito_spdp ? "text-emerald-400 font-semibold" : "text-amber-400"}>
                  {dpdEstado?.inscrito_spdp ? "Inscrito" : "Pendiente de inscribir"}
                </p>
              </div>
            </div>

            {dpdEstado?.conflicto_sobrevenido && (
              <div
                role="alert"
                className="p-2.5 rounded bg-rose-950/40 border border-rose-800 text-rose-300 text-[11px] flex items-start gap-2"
              >
                <ShieldAlert className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" aria-hidden="true" />
                <div>
                  <strong>Conflicto sobrevenido detectado:</strong> La persona designada ocupa cargos incompatibles en la estructura orgánica.
                </div>
              </div>
            )}

            {dpdEstado?.alertas && dpdEstado.alertas.length > 0 && (
              <ul aria-label="Alertas DPD" className="list-disc list-inside text-[11px] text-amber-300/90 pt-1 space-y-0.5">
                {dpdEstado.alertas.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Tarjeta Coordinador */}
        <div
          data-testid="tarjeta-estado-coordinador"
          className="p-4 rounded-xl bg-[#18181b] border border-[#26262b] space-y-3"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
              <UserCheck className="w-4 h-4 text-emerald-400" aria-hidden="true" />
              Coordinador de Protección de Datos
            </span>
            {coordEstado?.designado ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
                Designado
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-400">
                <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" />
                Falta designar
              </span>
            )}
          </div>

          <div className="space-y-1.5 text-xs text-zinc-300">
            {coordEstado?.designado && coordEstado.designacion && (
              <div>
                <p className="font-semibold text-white">
                  {coordEstado.designacion.usuario_nombre ?? coordEstado.designacion.user_id}
                </p>
                <p className="text-[11px] text-zinc-400">
                  Ref. {coordEstado.designacion.doc_referencia} · Fecha: {coordEstado.designacion.fecha_designacion}
                </p>
              </div>
            )}

            <div className="pt-1 border-t border-[#26262b] text-[11px]">
              <span className="text-zinc-500">Mandato escrito de Alta Dirección:</span>
              <p className={coordEstado?.tiene_mandato_escrito ? "text-emerald-400 font-semibold" : "text-amber-400"}>
                {coordEstado?.tiene_mandato_escrito ? "Mandato formal vigente" : "Sin mandato formal"}
              </p>
            </div>

            {coordEstado?.alertas && coordEstado.alertas.length > 0 && (
              <ul aria-label="Alertas Coordinador" className="list-disc list-inside text-[11px] text-amber-300/90 pt-1 space-y-0.5">
                {coordEstado.alertas.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </section>

      {/* Tabla / Lista de Designaciones */}
      <section aria-label="Historial de designaciones formales" className="space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-400">
          Registro histórico de designaciones ({designaciones.length})
        </h4>

        {designaciones.length === 0 ? (
          <div className="p-8 text-center rounded-xl bg-[#18181b] border border-[#26262b] text-zinc-400 text-xs">
            No hay designaciones formales registradas en la organización.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-[#26262b]">
            <table className="w-full text-left text-xs text-zinc-300">
              <thead className="bg-[#1b1b20] text-zinc-400 uppercase text-[10px] tracking-wider border-b border-[#26262b]">
                <tr>
                  <th className="py-2.5 px-3">Tipo</th>
                  <th className="py-2.5 px-3">Persona designada</th>
                  <th className="py-2.5 px-3">Representante legal</th>
                  <th className="py-2.5 px-3">Fecha y Ref.</th>
                  <th className="py-2.5 px-3">Vínculo</th>
                  <th className="py-2.5 px-3">Declaración</th>
                  <th className="py-2.5 px-3">SPDP</th>
                  <th className="py-2.5 px-3">Estado</th>
                  {puedeEditar && <th className="py-2.5 px-3 text-right">Acciones</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#26262b] bg-[#141417]">
                {designaciones.map((d) => {
                  const estaRevocada = Boolean(d.revocada_at);
                  return (
                    <tr
                      key={d.id}
                      data-testid={`fila-designacion-${d.id}`}
                      className={`hover:bg-[#18181b] transition ${estaRevocada ? "opacity-60 bg-[#121214]" : ""}`}
                    >
                      <td className="py-3 px-3 font-semibold text-white whitespace-nowrap">
                        {d.tipo === "dpd" ? (
                          <span className="inline-flex items-center gap-1 text-[#3892f3]">
                            <Shield className="w-3.5 h-3.5" aria-hidden="true" />
                            DPD
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-emerald-400">
                            <UserCheck className="w-3.5 h-3.5" aria-hidden="true" />
                            Coordinador
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-3">
                        <div className="font-semibold text-zinc-200">{d.usuario_nombre ?? d.user_id}</div>
                        <div className="text-[11px] text-zinc-400">{d.usuario_email}</div>
                      </td>
                      <td className="py-3 px-3">
                        <div className="text-zinc-200">{d.representante_nombre}</div>
                        <div className="text-[11px] text-zinc-400">
                          {d.representante_cargo} ({d.representante_identificacion})
                        </div>
                      </td>
                      <td className="py-3 px-3 whitespace-nowrap">
                        <div className="text-zinc-200">{d.fecha_designacion}</div>
                        <div className="text-[11px] text-zinc-400">{d.doc_referencia}</div>
                      </td>
                      <td className="py-3 px-3 whitespace-nowrap">
                        {d.vinculo ? (
                          <span className="text-[11px] text-zinc-300">
                            {ETIQUETAS_VINCULO[d.vinculo]}
                          </span>
                        ) : (
                          <span className="text-zinc-500">—</span>
                        )}
                      </td>
                      <td className="py-3 px-3 whitespace-nowrap">
                        {d.tipo === "dpd" ? (
                          d.declaracion_at ? (
                            <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400">
                              <CheckCircle2 className="w-3 h-3" aria-hidden="true" />
                              Emitida
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[11px] text-amber-400">
                              <AlertCircle className="w-3 h-3" aria-hidden="true" />
                              Pendiente
                            </span>
                          )
                        ) : (
                          <span className="text-zinc-500">No aplica</span>
                        )}
                      </td>
                      <td className="py-3 px-3 whitespace-nowrap">
                        {d.tipo === "dpd" ? (
                          d.inscripcion_spdp_fecha ? (
                            <div className="text-[11px] text-emerald-400">
                              <span>Inscrito: {d.inscripcion_spdp_fecha}</span>
                              <div className="text-[10px] text-zinc-400 font-mono">{d.inscripcion_spdp_ref}</div>
                            </div>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[11px] text-amber-400">
                              <AlertCircle className="w-3 h-3" aria-hidden="true" />
                              Pendiente
                            </span>
                          )
                        ) : (
                          <span className="text-zinc-500">No aplica</span>
                        )}
                      </td>
                      <td className="py-3 px-3 whitespace-nowrap">
                        {estaRevocada ? (
                          <span className="inline-flex items-center gap-1 text-[11px] text-rose-400">
                            <XCircle className="w-3 h-3" aria-hidden="true" />
                            Revocada
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400">
                            <CheckCircle2 className="w-3 h-3" aria-hidden="true" />
                            Vigente
                          </span>
                        )}
                      </td>

                      {puedeEditar && (
                        <td className="py-3 px-3 text-right whitespace-nowrap">
                          {!estaRevocada && (
                            <div className="flex items-center justify-end gap-1.5">
                              {d.tipo === "dpd" && !d.inscripcion_spdp_fecha && (
                                <button
                                  type="button"
                                  className={BOTON}
                                  onClick={() => abrirInscribir(d)}
                                  disabled={ocupado}
                                  data-testid={`btn-inscribir-${d.id}`}
                                >
                                  Inscribir SPDP
                                </button>
                              )}
                              <button
                                type="button"
                                className="px-2.5 py-1 text-xs font-semibold rounded bg-rose-950/60 hover:bg-rose-900 border border-rose-800 text-rose-200 transition focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-500"
                                onClick={() => abrirRevocar(d)}
                                disabled={ocupado}
                                data-testid={`btn-revocar-${d.id}`}
                              >
                                Revocar
                              </button>
                            </div>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Modal / Formulario Crear Designación */}
      {mostrarCrear && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="titulo-crear-designacion"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
        >
          <div className="w-full max-w-lg p-5 rounded-xl bg-[#141417] border border-[#26262b] shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-2 border-b border-[#26262b]">
              <h4 id="titulo-crear-designacion" className="text-sm font-bold text-white flex items-center gap-2">
                <Award className="w-4 h-4 text-[#3892f3]" aria-hidden="true" />
                Registrar designación formal
              </h4>
              <button
                type="button"
                className="text-zinc-400 hover:text-white text-xs"
                onClick={() => setMostrarCrear(false)}
                disabled={ocupado}
              >
                Cerrar
              </button>
            </div>

            <form onSubmit={guardarCrear} className="space-y-3 text-xs">
              <div>
                <label htmlFor="tipo-designacion" className={ETIQUETA}>
                  Tipo de designación
                </label>
                <select
                  id="tipo-designacion"
                  className={CAMPO}
                  value={tipo}
                  onChange={(e) => setTipo(e.target.value as TipoDesignacion)}
                  disabled={ocupado}
                >
                  <option value="dpd">Delegado de Protección de Datos (DPD)</option>
                  <option value="coordinador">Coordinador de Protección de Datos</option>
                </select>
              </div>

              <div>
                <label htmlFor="usuario-designado" className={ETIQUETA}>
                  Persona a designar
                </label>
                <select
                  id="usuario-designado"
                  className={CAMPO}
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  required
                  disabled={ocupado}
                >
                  <option value="">Selecciona un usuario…</option>
                  {usuarios.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.nombre || u.email} ({u.email})
                    </option>
                  ))}
                </select>
              </div>

              {tipo === "dpd" && (
                <div>
                  <label htmlFor="vinculo-designacion" className={ETIQUETA}>
                    Vínculo con la organización (obligatorio para DPD)
                  </label>
                  <select
                    id="vinculo-designacion"
                    className={CAMPO}
                    value={vinculo}
                    onChange={(e) => setVinculo(e.target.value as VinculoDesignacion)}
                    disabled={ocupado}
                  >
                    <option value="relacion_dependencia">Relación de dependencia (laboral)</option>
                    <option value="prestacion_servicios">Prestación de servicios (externo)</option>
                  </select>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label htmlFor="rep-nombre" className={ETIQUETA}>
                    Representante legal (nombre)
                  </label>
                  <input
                    id="rep-nombre"
                    type="text"
                    className={CAMPO}
                    value={representanteNombre}
                    onChange={(e) => setRepresentanteNombre(e.target.value)}
                    placeholder="Ej. Juan Pérez"
                    required
                    disabled={ocupado}
                  />
                </div>

                <div>
                  <label htmlFor="rep-id" className={ETIQUETA}>
                    Identificación / Cédula
                  </label>
                  <input
                    id="rep-id"
                    type="text"
                    className={CAMPO}
                    value={representanteIdentificacion}
                    onChange={(e) => setRepresentanteIdentificacion(e.target.value)}
                    placeholder="Ej. 1712345678"
                    required
                    disabled={ocupado}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="rep-cargo" className={ETIQUETA}>
                  Cargo del representante
                </label>
                <input
                  id="rep-cargo"
                  type="text"
                  className={CAMPO}
                  value={representanteCargo}
                  onChange={(e) => setRepresentanteCargo(e.target.value)}
                  placeholder="Ej. Gerente General / Apoderado Especial"
                  required
                  disabled={ocupado}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label htmlFor="fecha-desig" className={ETIQUETA}>
                    Fecha de designación
                  </label>
                  <input
                    id="fecha-desig"
                    type="date"
                    className={CAMPO}
                    value={fechaDesignacion}
                    onChange={(e) => setFechaDesignacion(e.target.value)}
                    required
                    disabled={ocupado}
                  />
                </div>

                <div>
                  <label htmlFor="doc-ref" className={ETIQUETA}>
                    Documento de referencia
                  </label>
                  <input
                    id="doc-ref"
                    type="text"
                    className={CAMPO}
                    value={docReferencia}
                    onChange={(e) => setDocReferencia(e.target.value)}
                    placeholder="Ej. ACTA-DIR-2026-004"
                    required
                    disabled={ocupado}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="valid-to" className={ETIQUETA}>
                  Vigencia hasta (opcional, dejar vacío para indefinido)
                </label>
                <input
                  id="valid-to"
                  type="date"
                  className={CAMPO}
                  value={validTo}
                  onChange={(e) => setValidTo(e.target.value)}
                  disabled={ocupado}
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#26262b]">
                <button
                  type="button"
                  className={BOTON}
                  onClick={() => setMostrarCrear(false)}
                  disabled={ocupado}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className={BOTON_PRIMARIO}
                  disabled={ocupado}
                  data-testid="btn-confirmar-crear-designacion"
                >
                  {ocupado ? "Guardando…" : "Registrar designación"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Registrar Inscripción SPDP */}
      {designacionParaInscribir && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="titulo-inscribir-spdp"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
        >
          <div className="w-full max-w-md p-5 rounded-xl bg-[#141417] border border-[#26262b] shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[#26262b]">
              <h4 id="titulo-inscribir-spdp" className="text-sm font-bold text-white flex items-center gap-2">
                <FileCheck className="w-4 h-4 text-emerald-400" aria-hidden="true" />
                Constancia de inscripción ante SPDP
              </h4>
              <button
                type="button"
                className="text-zinc-400 hover:text-white text-xs"
                onClick={() => setDesignacionParaInscribir(null)}
                disabled={ocupado}
              >
                Cerrar
              </button>
            </div>

            <p className="text-xs text-zinc-300">
              Registra la constancia oficial emitida por la Superintendencia de Protección de Datos Personales para la designación de{" "}
              <strong>{designacionParaInscribir.usuario_nombre ?? designacionParaInscribir.user_id}</strong> (Arts. 5 y 6 Reglamento del Delegado).
            </p>

            <form onSubmit={guardarInscripcion} className="space-y-3 text-xs">
              <div>
                <label htmlFor="fecha-spdp" className={ETIQUETA}>
                  Fecha de inscripción ante SPDP
                </label>
                <input
                  id="fecha-spdp"
                  type="date"
                  className={CAMPO}
                  value={inscripcionFecha}
                  onChange={(e) => setInscripcionFecha(e.target.value)}
                  required
                  disabled={ocupado}
                />
              </div>

              <div>
                <label htmlFor="ref-spdp" className={ETIQUETA}>
                  Número de registro / constancia SPDP
                </label>
                <input
                  id="ref-spdp"
                  type="text"
                  className={CAMPO}
                  value={inscripcionRef}
                  onChange={(e) => setInscripcionRef(e.target.value)}
                  placeholder="Ej. SPDP-DPD-2026-0089"
                  required
                  disabled={ocupado}
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#26262b]">
                <button
                  type="button"
                  className={BOTON}
                  onClick={() => setDesignacionParaInscribir(null)}
                  disabled={ocupado}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className={BOTON_PRIMARIO}
                  disabled={ocupado}
                  data-testid="btn-confirmar-inscribir"
                >
                  {ocupado ? "Guardando…" : "Registrar constancia"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Revocar Designación */}
      {designacionParaRevocar && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="titulo-revocar-designacion"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
        >
          <div className="w-full max-w-md p-5 rounded-xl bg-[#141417] border border-rose-900/60 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[#26262b]">
              <h4 id="titulo-revocar-designacion" className="text-sm font-bold text-rose-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400" aria-hidden="true" />
                Confirmar revocación de designación
              </h4>
              <button
                type="button"
                className="text-zinc-400 hover:text-white text-xs"
                onClick={() => setDesignacionParaRevocar(null)}
                disabled={ocupado}
              >
                Cerrar
              </button>
            </div>

            <p className="text-xs text-zinc-300">
              ¿Estás seguro de que deseas revocar la designación de{" "}
              <strong>{designacionParaRevocar.usuario_nombre ?? designacionParaRevocar.user_id}</strong> como{" "}
              <strong>{ETIQUETAS_TIPO_DESIGNACION[designacionParaRevocar.tipo]}</strong>? Esta acción queda registrada de forma inmutable.
            </p>

            <form onSubmit={guardarRevocacion} className="space-y-3 text-xs">
              <div>
                <label htmlFor="motivo-revocacion" className={ETIQUETA}>
                  Motivo formal de la revocación
                </label>
                <textarea
                  id="motivo-revocacion"
                  rows={3}
                  className={CAMPO}
                  value={revocacionMotivo}
                  onChange={(e) => setRevocacionMotivo(e.target.value)}
                  placeholder="Ej. Cese de funciones por reestructuración de la alta dirección"
                  required
                  disabled={ocupado}
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#26262b]">
                <button
                  type="button"
                  className={BOTON}
                  onClick={() => setDesignacionParaRevocar(null)}
                  disabled={ocupado}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 text-xs font-semibold rounded bg-rose-600 hover:bg-rose-500 text-white transition focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-400"
                  disabled={ocupado}
                  data-testid="btn-confirmar-revocar"
                >
                  {ocupado ? "Revocando…" : "Confirmar revocación"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
