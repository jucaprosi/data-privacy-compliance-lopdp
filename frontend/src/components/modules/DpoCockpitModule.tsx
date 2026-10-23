"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  FileCheck,
  Shield,
  CheckCheck,
  Clock,
  AlertOctagon,
  Award,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Loader2,
} from "lucide-react";
import { DictamenDPO } from "@/types";
import { getBitacoraDPO } from "@/lib/api";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import {
  designacionesApi,
  type DeclaracionConflictosPayload,
  type DesignacionFormal,
  ETIQUETAS_VINCULO,
} from "./roadmap/admin/designaciones";
import { describirError, type ErrorDescrito } from "./roadmap/admin/errores";
import { BOTON, BOTON_PRIMARIO, BloqueError, CAMPO, ETIQUETA } from "./roadmap/admin/ui";

export default function DpoCockpitModule() {
  const [bitacora, setBitacora] = useState<DictamenDPO[]>([]);
  const [cargandoBitacora, setCargandoBitacora] = useState(true);

  // Sesión e identidad
  const session = useRoadmapStore((s) => s.session);
  const rol = session.role;
  const currentUserId = session.userId;

  // Designación formal propia (Mi designación)
  const [miDesignacion, setMiDesignacion] = useState<DesignacionFormal | null>(null);
  const [usuarioVerificadoId, setUsuarioVerificadoId] = useState<string | null>(null);
  const [cargandoDesignacion, setCargandoDesignacion] = useState(true);
  const [errorDesignacion, setErrorDesignacion] = useState<ErrorDescrito | null>(null);

  // Formulario declaración de conflictos
  const [mostrarModalDeclarar, setMostrarModalDeclarar] = useState(false);
  const [textoDeclaracion, setTextoDeclaracion] = useState(
    "Declaro bajo juramento no incurrir en ninguna de las causas de incompatibilidad o conflicto de intereses establecidas en la normativa vigente."
  );
  const [tieneConflicto, setTieneConflicto] = useState(false);
  const [esSocioAccionista, setEsSocioAccionista] = useState(false);
  const [esParienteAdmin, setEsParienteAdmin] = useState(false);
  const [guardandoDeclaracion, setGuardandoDeclaracion] = useState(false);

  const cargarBitacora = async () => {
    setCargandoBitacora(true);
    try {
      const data = await getBitacoraDPO();
      setBitacora(Array.isArray(data) ? data : []);
    } catch {
      setBitacora([]);
    } finally {
      setCargandoBitacora(false);
    }
  };

  const cargarMiDesignacion = useCallback(async () => {
    setCargandoDesignacion(true);
    setErrorDesignacion(null);
    try {
      // La identidad la da el servidor (en modo oidc la sesión del frontend no lleva el id).
      // Sin identidad conocida no se atribuye ninguna designación: nunca «la primera que haya».
      const usuarioId = currentUserId || (await designacionesApi.miUsuarioId(rol));
      setUsuarioVerificadoId(usuarioId);
      if (!usuarioId) {
        setMiDesignacion(null);
        return;
      }
      const lista = await designacionesApi.listar("dpd", rol);
      const items = Array.isArray(lista) ? lista : [];
      const encontrada = items.find((d) => !d.revocada_at && d.user_id === usuarioId);
      setMiDesignacion(encontrada ?? null);
    } catch {
      // Si el endpoint no responde o no hay permiso, mostramos aviso amigable, sin fallo técnico
      setMiDesignacion(null);
    } finally {
      setCargandoDesignacion(false);
    }
  }, [rol, currentUserId]);

  useEffect(() => {
    cargarBitacora();
    cargarMiDesignacion();
  }, [cargarMiDesignacion]);

  async function handleEnviarDeclaracion(e: React.FormEvent) {
    e.preventDefault();
    if (!miDesignacion || !textoDeclaracion.trim()) return;

    setGuardandoDeclaracion(true);
    setErrorDesignacion(null);
    try {
      const payload: DeclaracionConflictosPayload = {
        declaracion_texto: textoDeclaracion.trim(),
        declaracion_tiene_conflicto: tieneConflicto,
        declaracion_es_socio_accionista: esSocioAccionista,
        declaracion_es_pariente_admin: esParienteAdmin,
      };

      await designacionesApi.registrarDeclaracion(miDesignacion.id, payload, rol);
      setMostrarModalDeclarar(false);
      await cargarMiDesignacion();
    } catch (err: unknown) {
      setErrorDesignacion(describirError(err));
    } finally {
      setGuardandoDeclaracion(false);
    }
  }

  const esPersonaDesignada = Boolean(
    miDesignacion && usuarioVerificadoId && miDesignacion.user_id === usuarioVerificadoId
  );

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-zinc-800">
        <h2 className="text-xl font-bold text-zinc-100 flex items-center">
          <FileCheck className="w-5 h-5 mr-2 text-sky-400" /> Cockpit del DPD/DPO · Bitácora Inviolable
        </h2>
        <p className="text-xs text-zinc-400 mt-1">
          Supervisión independiente y registro histórico de asesorías con acuse de recibo directivo (Arts. 49 y 50 LOPDP).
        </p>
      </div>

      {/* Banner SoD */}
      <div className="bg-sky-950/40 border border-sky-800/60 rounded-xl p-4 flex items-start space-x-3 text-xs">
        <Shield className="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-sky-300">Garantía de Segregación de Funciones (SoD):</span>
          <p className="text-zinc-300 mt-0.5">
            Bajo el invariante constitucional <code className="font-mono bg-sky-900/50 px-1 py-0.5 rounded text-sky-200">INV_LOPDP_DPO_INDEPENDENCE</code>, 
            el DPO opera con independencia consultiva: no puede auto-aprobar políticas operativas ni ser juez y parte en remediaciones CAPA.
          </p>
        </div>
      </div>

      {/* SECCIÓN FE-11: Mi Designación Formal y Declaración de Conflictos */}
      <section
        aria-label="Mi designación formal de DPD"
        className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 space-y-4"
        data-testid="seccion-mi-designacion"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-zinc-800">
          <div className="flex items-center space-x-2">
            <Award className="w-5 h-5 text-sky-400" aria-hidden="true" />
            <h3 className="text-sm font-bold text-zinc-100">
              Mi designación formal (Delegado de Protección de Datos)
            </h3>
          </div>

          {miDesignacion && esPersonaDesignada && !miDesignacion.declaracion_at && (
            <button
              type="button"
              className={BOTON_PRIMARIO}
              onClick={() => {
                setErrorDesignacion(null);
                setMostrarModalDeclarar(true);
              }}
              data-testid="btn-abrir-declaracion-conflictos"
            >
              <FileText className="w-4 h-4 mr-1.5" aria-hidden="true" />
              Emitir declaración de no conflicto
            </button>
          )}
        </div>

        {errorDesignacion && (
          <BloqueError error={errorDesignacion} testId="error-mi-designacion" />
        )}

        {cargandoDesignacion ? (
          <p role="status" className="flex items-center gap-2 text-xs text-zinc-400 py-4">
            <Loader2 className="w-4 h-4 animate-spin text-sky-400" aria-hidden="true" />
            Consultando designación formal…
          </p>
        ) : !miDesignacion ? (
          <div
            role="status"
            className="p-4 rounded-lg bg-zinc-950/80 border border-zinc-800/80 text-xs text-zinc-400 flex items-start gap-3"
            data-testid="aviso-sin-designacion"
          >
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <p className="font-semibold text-zinc-200">No cuentas con una designación formal activa de DPD.</p>
              <p className="text-[11px] text-zinc-400 mt-0.5">
                La alta dirección o el administrador de la organización debe registrar tu designación formal en el módulo de Administración
                para habilitar la emisión de tu declaración de conflictos y el registro de la constancia ante la SPDP.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-3 text-xs text-zinc-300">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-3.5 rounded-lg bg-zinc-950/70 border border-zinc-800">
              <div>
                <span className="text-[11px] text-zinc-500 uppercase font-semibold">Representante legal:</span>
                <p className="font-semibold text-zinc-200 mt-0.5">{miDesignacion.representante_nombre}</p>
                <p className="text-[11px] text-zinc-400">
                  {miDesignacion.representante_cargo} ({miDesignacion.representante_identificacion})
                </p>
              </div>

              <div>
                <span className="text-[11px] text-zinc-500 uppercase font-semibold">Mandato y vigencia:</span>
                <p className="text-zinc-200 mt-0.5">Ref. {miDesignacion.doc_referencia}</p>
                <p className="text-[11px] text-zinc-400">
                  Fecha: {miDesignacion.fecha_designacion} · Vínculo: {miDesignacion.vinculo ? ETIQUETAS_VINCULO[miDesignacion.vinculo] : "N/A"}
                </p>
              </div>

              <div>
                <span className="text-[11px] text-zinc-500 uppercase font-semibold">Registro SPDP:</span>
                {miDesignacion.inscripcion_spdp_fecha ? (
                  <div className="mt-0.5 text-emerald-400 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
                    Inscrito: {miDesignacion.inscripcion_spdp_fecha}
                    <span className="text-[10px] text-zinc-400 font-mono block">({miDesignacion.inscripcion_spdp_ref})</span>
                  </div>
                ) : (
                  <p className="text-amber-400 mt-0.5">Pendiente de registro por la administración</p>
                )}
              </div>
            </div>

            {/* Estado de la declaración de conflictos */}
            <div className="p-3.5 rounded-lg bg-zinc-950/70 border border-zinc-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-zinc-200">
                  Declaración previa de conflictos e independencia (Art. 17 Reglamento del Delegado):
                </span>
                {miDesignacion.declaracion_at ? (
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
                    Declaración emitida el {new Date(miDesignacion.declaracion_at).toLocaleDateString()}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-400">
                    <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" />
                    Pendiente de emisión por la persona designada
                  </span>
                )}
              </div>

              {miDesignacion.declaracion_texto && (
                <div className="text-[11px] bg-zinc-900/60 p-2.5 rounded border border-zinc-800 text-zinc-300 font-mono">
                  &ldquo;{miDesignacion.declaracion_texto}&rdquo;
                </div>
              )}
            </div>
          </div>
        )}
      </section>

      {/* Modal Declaración de Conflictos */}
      {mostrarModalDeclarar && miDesignacion && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="titulo-declarar-conflictos"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
        >
          <div className="w-full max-w-lg p-5 rounded-xl bg-[#141417] border border-[#26262b] shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[#26262b]">
              <h4 id="titulo-declarar-conflictos" className="text-sm font-bold text-white flex items-center gap-2">
                <Shield className="w-4 h-4 text-sky-400" aria-hidden="true" />
                Declaración previa de conflictos y aceptación del DPD
              </h4>
              <button
                type="button"
                className="text-zinc-400 hover:text-white text-xs"
                onClick={() => setMostrarModalDeclarar(false)}
                disabled={guardandoDeclaracion}
              >
                Cerrar
              </button>
            </div>

            <p className="text-xs text-zinc-300">
              Conforme al Art. 17 del Reglamento del Delegado y Arts. 4.7 y 56 del Reglamento General, la persona designada
              debe manifestar expresamente que no incurre en causas de incompatibilidad ni conflictos de interés.
            </p>

            <form onSubmit={handleEnviarDeclaracion} className="space-y-3.5 text-xs">
              <div>
                <label htmlFor="texto-declaracion" className={ETIQUETA}>
                  Texto de la declaración y compromiso de independencia
                </label>
                <textarea
                  id="texto-declaracion"
                  rows={3}
                  className={CAMPO}
                  value={textoDeclaracion}
                  onChange={(e) => setTextoDeclaracion(e.target.value)}
                  required
                  disabled={guardandoDeclaracion}
                />
              </div>

              <div className="space-y-2 p-3 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-300">
                <span className="font-semibold text-zinc-200 block text-[11px] uppercase tracking-wide">
                  Preguntas de control normativo:
                </span>

                <label className="flex items-start gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="mt-0.5 rounded border-zinc-700 bg-zinc-900 text-sky-500 focus:ring-sky-400"
                    checked={tieneConflicto}
                    onChange={(e) => setTieneConflicto(e.target.checked)}
                    disabled={guardandoDeclaracion}
                    data-testid="check-tiene-conflicto"
                  />
                  <span>Tengo un conflicto de intereses real, potencial o aparente con el tratamiento de datos de la entidad.</span>
                </label>

                <label className="flex items-start gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="mt-0.5 rounded border-zinc-700 bg-zinc-900 text-sky-500 focus:ring-sky-400"
                    checked={esSocioAccionista}
                    onChange={(e) => setEsSocioAccionista(e.target.checked)}
                    disabled={guardandoDeclaracion}
                    data-testid="check-socio-accionista"
                  />
                  <span>Soy socio o accionista con participación en la administración o control de la organización.</span>
                </label>

                <label className="flex items-start gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="mt-0.5 rounded border-zinc-700 bg-zinc-900 text-sky-500 focus:ring-sky-400"
                    checked={esParienteAdmin}
                    onChange={(e) => setEsParienteAdmin(e.target.checked)}
                    disabled={guardandoDeclaracion}
                    data-testid="check-pariente-admin"
                  />
                  <span>Tengo parentesco hasta cuarto grado de consanguinidad o segundo de afinidad con administradores o directores.</span>
                </label>
              </div>

              {(tieneConflicto || esSocioAccionista || esParienteAdmin) && (
                <div
                  role="alert"
                  className="p-2.5 rounded bg-amber-950/50 border border-amber-800 text-amber-300 text-[11px]"
                >
                  <AlertTriangle className="w-4 h-4 inline mr-1 text-amber-400" />
                  <strong>Advertencia:</strong> Si declaras afirmativamente cualquiera de estas condiciones, el servidor rechazará
                  la aceptación por incompatibilidad legal (Arts. 17 Reglamento del Delegado y 56 Reglamento General).
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#26262b]">
                <button
                  type="button"
                  className={BOTON}
                  onClick={() => setMostrarModalDeclarar(false)}
                  disabled={guardandoDeclaracion}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className={BOTON_PRIMARIO}
                  disabled={guardandoDeclaracion}
                  data-testid="btn-confirmar-declaracion"
                >
                  {guardandoDeclaracion ? "Enviando…" : "Registrar declaración"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Bitácora Timeline */}
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5">
        <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-4">
          Historial Cronológico de Dictámenes y Advertencias
        </h3>

        {cargandoBitacora ? (
          <div className="p-8 text-center text-zinc-500 text-xs">Cargando bitácora notarial...</div>
        ) : bitacora.length === 0 ? (
          <div className="p-8 text-center text-zinc-500 text-xs">No hay dictámenes asentados en la bitácora.</div>
        ) : (
          <div className="space-y-3">
            {bitacora.map((item) => (
              <div
                key={item.id}
                className="p-4 rounded-lg bg-zinc-950/70 border border-zinc-800 hover:border-zinc-700 transition space-y-2 text-xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-zinc-400 font-bold">{item.id}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        item.tipo === "ADVERTENCIA_RIESGO"
                          ? "bg-rose-950 text-rose-300 border border-rose-800"
                          : "bg-sky-950 text-sky-300 border border-sky-800"
                      }`}
                    >
                      {item.tipo}
                    </span>
                  </div>
                  <div className="flex items-center text-[11px] text-zinc-500">
                    <Clock className="w-3.5 h-3.5 mr-1" />
                    {item.fecha_emision ? new Date(item.fecha_emision).toLocaleDateString() : "Reciente"}
                  </div>
                </div>

                <div className="font-bold text-zinc-200 text-sm">{item.asunto}</div>
                <div className="text-[11px] text-zinc-400 font-mono">Referencia legal: {item.referencia_normativa}</div>
                <p className="text-zinc-300 leading-relaxed bg-zinc-900/60 p-2.5 rounded border border-zinc-800/80">
                  {item.cuerpo}
                </p>

                <div className="pt-2 flex items-center justify-between border-t border-zinc-900 text-[11px]">
                  <span className="text-zinc-500 italic">Doctrina: Carácter consultivo (No vinculante por ley)</span>
                  <div>
                    {item.acuse_recibo_alta_direccion ? (
                      <span className="text-emerald-400 font-semibold flex items-center">
                        <CheckCheck className="w-3.5 h-3.5 mr-1" /> Acuse de Recibo Directivo Asentado
                      </span>
                    ) : (
                      <span className="text-amber-400 font-medium flex items-center">
                        <AlertOctagon className="w-3.5 h-3.5 mr-1" /> Pendiente Acuse de Alta Dirección
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
