"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  AlertOctagon,
  AlertTriangle,
  Award,
  CheckCheck,
  CheckCircle2,
  Clock,
  Download,
  FileCheck,
  FileSignature,
  FileText,
  Loader2,
  Send,
  Shield,
} from "lucide-react";

import {
  emitirDictamenDpo,
  firmarAcuseDictamenDpo,
  listarBitacoraDpo,
  obtenerContextoRolesDpo,
  type DictamenBitacoraDPO,
  type TipoDictamenDPO,
} from "@/lib/dpo";
import {
  consultarInformeAnualDpo,
  consultarInscripcionSpdp,
  descargarInformeAnualDpo,
  generarInformeAnualDpo,
  registrarInscripcionSpdp,
  type InformeAnualDpo,
  type InscripcionesSpdp,
} from "@/lib/dpo/informeAnual";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import {
  designacionesApi,
  ETIQUETAS_VINCULO,
  type DeclaracionConflictosPayload,
  type DesignacionFormal,
} from "./roadmap/admin/designaciones";
import { describirError, type ErrorDescrito } from "./roadmap/admin/errores";
import { BOTON, BOTON_PRIMARIO, BloqueError, CAMPO, ETIQUETA } from "./roadmap/admin/ui";

const TIPOS_DICTAMEN: { valor: TipoDictamenDPO; etiqueta: string }[] = [
  { valor: "OPINION_CONSULTIVA", etiqueta: "Opinión consultiva" },
  { valor: "ADVERTENCIA_RIESGO", etiqueta: "Advertencia de riesgo" },
  { valor: "RECOMENDACION_EIPD", etiqueta: "Recomendación sobre EIPD" },
  { valor: "DICTAMEN_TRANSFERENCIA", etiqueta: "Dictamen de transferencia" },
  { valor: "AUDITORIA_INFORME", etiqueta: "Informe de supervisión" },
];

type PestanaDpo = "bitacora" | "informe" | "inscripcion";

export default function DpoCockpitModule() {
  const [pestana, setPestana] = useState<PestanaDpo>("bitacora");
  const [bitacora, setBitacora] = useState<DictamenBitacoraDPO[]>([]);
  const [cargandoBitacora, setCargandoBitacora] = useState(true);
  const [errorBitacora, setErrorBitacora] = useState<string | null>(null);

  // Sesión e identidad
  const session = useRoadmapStore((s) => s.session);
  const rolStore = session.role;
  const currentUserId = session.userId;

  const [rolesServidor, setRolesServidor] = useState<string[] | null>(null);
  const [userIdServidor, setUserIdServidor] = useState<string>("");

  // Formulario de emisión de dictamen (solo rol dpo)
  const [tipoDictamen, setTipoDictamen] = useState<TipoDictamenDPO>("OPINION_CONSULTIVA");
  const [asuntoDictamen, setAsuntoDictamen] = useState("");
  const [referenciaDictamen, setReferenciaDictamen] = useState("Art. 50 LOPDP");
  const [cuerpoDictamen, setCuerpoDictamen] = useState("");
  const [emitiendo, setEmitiendo] = useState(false);
  const [errorAccionBitacora, setErrorAccionBitacora] = useState<string | null>(null);
  const [firmandoId, setFirmandoId] = useState<string | null>(null);

  // Designación formal propia (Mi designación)
  const [miDesignacion, setMiDesignacion] = useState<DesignacionFormal | null>(null);
  const [usuarioVerificadoId, setUsuarioVerificadoId] = useState<string | null>(null);
  const [cargandoDesignacion, setCargandoDesignacion] = useState(true);
  const [errorDesignacion, setErrorDesignacion] = useState<ErrorDescrito | null>(null);

  // Formulario declaración de conflictos
  const [mostrarModalDeclarar, setMostrarModalDeclarar] = useState(false);
  const [textoDeclaracion, setTextoDeclaracion] = useState(
    "Declaro bajo juramento no incurrir en ninguna de las causas de incompatibilidad o conflicto de intereses establecidas en la normativa vigente.",
  );
  const [tieneConflicto, setTieneConflicto] = useState(false);
  const [esSocioAccionista, setEsSocioAccionista] = useState(false);
  const [esParienteAdmin, setEsParienteAdmin] = useState(false);
  const [guardandoDeclaracion, setGuardandoDeclaracion] = useState(false);

  const rolesEfectivos =
    rolesServidor !== null ? rolesServidor : rolStore ? [rolStore] : [];
  const esDpo = rolesEfectivos.includes("dpo");
  const esAdminOrganizacion = rolesEfectivos.includes("admin_organizacion");
  const uidEfectivo = userIdServidor || currentUserId;

  const cargarBitacoraYContexto = useCallback(async () => {
    setCargandoBitacora(true);
    setErrorBitacora(null);
    let rolLectura: string | undefined = rolStore;
    let uid = currentUserId;

    try {
      const ctx = await obtenerContextoRolesDpo();
      setRolesServidor(ctx.roles);
      if (ctx.user_id) {
        setUserIdServidor(ctx.user_id);
        uid = ctx.user_id;
      }
      rolLectura =
        ctx.roles.find(
          (r) => r === "dpo" || r === "admin_organizacion" || r === "coordinador",
        ) ?? ctx.roles[0];
    } catch {
      // Si /organizacion/me/roles no está disponible, se conserva el rol de sesión
    }

    try {
      const data = await listarBitacoraDpo(rolLectura, uid || undefined);
      setBitacora(Array.isArray(data) ? data : []);
    } catch (error: unknown) {
      setBitacora([]);
      setErrorBitacora(
        error instanceof Error ? error.message : "No se pudo cargar la bitácora.",
      );
    } finally {
      setCargandoBitacora(false);
    }
  }, [rolStore, currentUserId]);

  const cargarMiDesignacion = useCallback(async () => {
    setCargandoDesignacion(true);
    setErrorDesignacion(null);
    try {
      const usuarioId = currentUserId || (await designacionesApi.miUsuarioId(rolStore));
      setUsuarioVerificadoId(usuarioId);
      if (!usuarioId) {
        setMiDesignacion(null);
        return;
      }
      const lista = await designacionesApi.listar("dpd", rolStore);
      const items = Array.isArray(lista) ? lista : [];
      const encontrada = items.find((d) => !d.revocada_at && d.user_id === usuarioId);
      setMiDesignacion(encontrada ?? null);
    } catch {
      setMiDesignacion(null);
    } finally {
      setCargandoDesignacion(false);
    }
  }, [rolStore, currentUserId]);

  useEffect(() => {
    void cargarBitacoraYContexto();
    void cargarMiDesignacion();
  }, [cargarBitacoraYContexto, cargarMiDesignacion]);

  async function manejarEmitirDictamen(e: React.FormEvent) {
    e.preventDefault();
    if (!asuntoDictamen.trim() || !cuerpoDictamen.trim()) return;
    setEmitiendo(true);
    setErrorAccionBitacora(null);
    try {
      const creado = await emitirDictamenDpo(
        {
          tipo: tipoDictamen,
          asunto: asuntoDictamen.trim(),
          referencia_normativa: referenciaDictamen.trim() || "Art. 50 LOPDP",
          cuerpo: cuerpoDictamen.trim(),
        },
        "dpo",
        uidEfectivo || undefined,
      );
      setBitacora((prev) => [...prev, creado]);
      setAsuntoDictamen("");
      setCuerpoDictamen("");
    } catch (err: unknown) {
      setErrorAccionBitacora(
        err instanceof Error ? err.message : "No se pudo emitir el dictamen.",
      );
    } finally {
      setEmitiendo(false);
    }
  }

  async function manejarFirmarAcuse(dictamenId: string) {
    setFirmandoId(dictamenId);
    setErrorAccionBitacora(null);
    try {
      const actualizado = await firmarAcuseDictamenDpo(
        dictamenId,
        "admin_organizacion",
        uidEfectivo || undefined,
      );
      setBitacora((prev) =>
        prev.map((d) => (d.id === dictamenId ? actualizado : d)),
      );
    } catch (err: unknown) {
      setErrorAccionBitacora(
        err instanceof Error ? err.message : "No se pudo registrar el acuse de recibo.",
      );
    } finally {
      setFirmandoId(null);
    }
  }

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

      await designacionesApi.registrarDeclaracion(miDesignacion.id, payload, rolStore);
      setMostrarModalDeclarar(false);
      await cargarMiDesignacion();
    } catch (err: unknown) {
      setErrorDesignacion(describirError(err));
    } finally {
      setGuardandoDeclaracion(false);
    }
  }

  const esPersonaDesignada = Boolean(
    miDesignacion && usuarioVerificadoId && miDesignacion.user_id === usuarioVerificadoId,
  );

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-[var(--ui-borde)]">
        <h2 className="text-xl font-bold flex items-center">
          <FileCheck className="w-5 h-5 mr-2" aria-hidden="true" /> Cockpit del DPD/DPO · Bitácora Inviolable
        </h2>
        <p className="text-xs text-[var(--ui-texto-suave)] mt-1">
          Supervisión independiente y registro histórico de asesorías con acuse de recibo directivo (Arts. 49 y 50 LOPDP).
        </p>
      </div>

      <div role="tablist" aria-label="Secciones del cockpit del DPO" className="flex flex-wrap gap-2 border-b border-[var(--ui-borde)]">
        {(
          [
            ["bitacora", "Bitácora"],
            ["informe", "Informe anual"],
            ["inscripcion", "Inscripción SPDP"],
          ] as [PestanaDpo, string][]
        ).map(([id, etiqueta]) => (
          <button
            key={id}
            type="button"
            role="tab"
            id={`pestana-dpo-${id}`}
            aria-selected={pestana === id}
            aria-controls={`panel-dpo-${id}`}
            data-testid={`pestana-dpo-${id}`}
            onClick={() => setPestana(id)}
            className={`px-3 py-2 text-xs font-semibold border-b-2 -mb-px focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ui-primario)] ${
              pestana === id
                ? "border-[var(--ui-primario)] text-[var(--ui-texto)]"
                : "border-transparent text-[var(--ui-texto-suave)] hover:text-[var(--ui-texto)]"
            }`}
          >
            {etiqueta}
          </button>
        ))}
      </div>

      {pestana === "informe" && (
        <div role="tabpanel" id="panel-dpo-informe" aria-labelledby="pestana-dpo-informe">
          <InformeAnualPanel
            esDpo={esDpo}
            rol={esDpo ? "dpo" : rolesEfectivos[0]}
            userId={uidEfectivo || undefined}
          />
        </div>
      )}

      {pestana === "inscripcion" && (
        <div role="tabpanel" id="panel-dpo-inscripcion" aria-labelledby="pestana-dpo-inscripcion">
          <InscripcionPanel
            esAdmin={esAdminOrganizacion}
            rol={
              esAdminOrganizacion
                ? "admin_organizacion"
                : esDpo
                  ? "dpo"
                  : rolesEfectivos.find((r) => r === "coordinador") ?? rolesEfectivos[0]
            }
            userId={uidEfectivo || undefined}
          />
        </div>
      )}

      {pestana === "bitacora" && (
      <div role="tabpanel" id="panel-dpo-bitacora" aria-labelledby="pestana-dpo-bitacora" className="space-y-6">
      {/* Banner SoD */}
      <div className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-4 flex items-start space-x-3 text-xs">
        <Shield className="w-5 h-5 shrink-0 mt-0.5" aria-hidden="true" />
        <div>
          <span className="font-bold">Garantía de Segregación de Funciones (SoD):</span>
          <p className="text-[var(--ui-texto-suave)] mt-0.5">
            Bajo el invariante constitucional{" "}
            <code className="font-mono bg-[var(--ui-superficie-2)] border border-[var(--ui-borde)] px-1 py-0.5 rounded">
              INV_LOPDP_DPO_INDEPENDENCE
            </code>
            , el DPO opera con independencia consultiva: no puede auto-aprobar políticas operativas ni ser juez y parte en remediaciones CAPA.
          </p>
        </div>
      </div>

      {/* SECCIÓN FE-11: Mi Designación Formal y Declaración de Conflictos */}
      <section
        aria-label="Mi designación formal de DPD"
        className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-5 space-y-4"
        data-testid="seccion-mi-designacion"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[var(--ui-borde)]">
          <div className="flex items-center space-x-2">
            <Award className="w-5 h-5" aria-hidden="true" />
            <h3 className="text-sm font-bold">
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
          <p role="status" className="flex items-center gap-2 text-xs text-[var(--ui-texto-suave)] py-4">
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
            Consultando designación formal…
          </p>
        ) : !miDesignacion ? (
          <div
            role="status"
            className="p-4 rounded-lg bg-[var(--ui-superficie-2)] border border-[var(--ui-borde)] text-xs text-[var(--ui-texto-suave)] flex items-start gap-3"
            data-testid="aviso-sin-designacion"
          >
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <p className="font-semibold">No cuentas con una designación formal activa de DPD.</p>
              <p className="text-[11px] text-[var(--ui-texto-suave)] mt-0.5">
                La alta dirección o el administrador de la organización debe registrar tu designación formal en el módulo de Administración
                para habilitar la emisión de tu declaración de conflictos y el registro de la constancia ante la SPDP.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-3 text-xs">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-3.5 rounded-lg bg-[var(--ui-superficie-2)] border border-[var(--ui-borde)]">
              <div>
                <span className="text-[11px] text-[var(--ui-texto-suave)] uppercase font-semibold">Representante legal:</span>
                <p className="font-semibold mt-0.5">{miDesignacion.representante_nombre}</p>
                <p className="text-[11px] text-[var(--ui-texto-suave)]">
                  {miDesignacion.representante_cargo} ({miDesignacion.representante_identificacion})
                </p>
              </div>

              <div>
                <span className="text-[11px] text-[var(--ui-texto-suave)] uppercase font-semibold">Mandato y vigencia:</span>
                <p className="mt-0.5">Ref. {miDesignacion.doc_referencia}</p>
                <p className="text-[11px] text-[var(--ui-texto-suave)]">
                  Fecha: {miDesignacion.fecha_designacion} · Vínculo:{" "}
                  {miDesignacion.vinculo ? ETIQUETAS_VINCULO[miDesignacion.vinculo] : "N/A"}
                </p>
              </div>

              <div>
                <span className="text-[11px] text-[var(--ui-texto-suave)] uppercase font-semibold">Registro SPDP:</span>
                {miDesignacion.inscripcion_spdp_fecha ? (
                  <div className="mt-0.5 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
                    Inscrito: {miDesignacion.inscripcion_spdp_fecha}
                    <span className="text-[10px] text-[var(--ui-texto-suave)] font-mono block">
                      ({miDesignacion.inscripcion_spdp_ref})
                    </span>
                  </div>
                ) : (
                  <p className="text-[var(--ui-texto-suave)] mt-0.5">
                    Pendiente de registro por la administración
                  </p>
                )}
              </div>
            </div>

            {/* Estado de la declaración de conflictos */}
            <div className="p-3.5 rounded-lg bg-[var(--ui-superficie-2)] border border-[var(--ui-borde)] space-y-2">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <span className="font-bold">
                  Declaración previa de conflictos e independencia (Art. 17 Reglamento del Delegado):
                </span>
                {miDesignacion.declaracion_at ? (
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full badge-render-success">
                    <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
                    Declaración emitida el {new Date(miDesignacion.declaracion_at).toLocaleDateString()}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-full badge-render-warning">
                    <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" />
                    Pendiente de emisión por la persona designada
                  </span>
                )}
              </div>

              {miDesignacion.declaracion_texto && (
                <div className="text-[11px] bg-[var(--ui-superficie)] p-2.5 rounded border border-[var(--ui-borde)] font-mono">
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
          <div className="w-full max-w-lg p-5 rounded-xl bg-[var(--ui-superficie)] border border-[var(--ui-borde)] shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--ui-borde)]">
              <h4 id="titulo-declarar-conflictos" className="text-sm font-bold flex items-center gap-2">
                <Shield className="w-4 h-4" aria-hidden="true" />
                Declaración previa de conflictos y aceptación del DPD
              </h4>
              <button
                type="button"
                className="text-[var(--ui-texto-suave)] text-xs"
                onClick={() => setMostrarModalDeclarar(false)}
                disabled={guardandoDeclaracion}
              >
                Cerrar
              </button>
            </div>

            <p className="text-xs text-[var(--ui-texto-suave)]">
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

              <div className="space-y-2 p-3 rounded-lg bg-[var(--ui-superficie-2)] border border-[var(--ui-borde)]">
                <span className="font-semibold block text-[11px] uppercase tracking-wide">
                  Preguntas de control normativo:
                </span>

                <label className="flex items-start gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="mt-0.5"
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
                    className="mt-0.5"
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
                    className="mt-0.5"
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
                  className="p-2.5 rounded badge-render-warning text-[11px]"
                >
                  <AlertTriangle className="w-4 h-4 inline mr-1" aria-hidden="true" />
                  <strong>Advertencia:</strong> Si declaras afirmativamente cualquiera de estas condiciones, el servidor rechazará
                  la aceptación por incompatibilidad legal (Arts. 17 Reglamento del Delegado y 56 Reglamento General).
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-[var(--ui-borde)]">
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

      {/* Formulario de emisión de dictamen (DPO-01): visible SOLO para el rol dpo */}
      {esDpo && (
        <form
          onSubmit={manejarEmitirDictamen}
          data-testid="form-emitir-dictamen"
          aria-label="Emitir dictamen del DPO"
          className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-5 space-y-4 text-xs"
        >
          <div className="pb-3 border-b border-[var(--ui-borde)]">
            <h3 className="text-sm font-bold flex items-center gap-2">
              <Send className="w-4 h-4" aria-hidden="true" />
              Emitir Dictamen en la Bitácora Inviolable
            </h3>
            <p className="text-[11px] text-[var(--ui-texto-suave)] mt-0.5">
              El dictamen se sella con huella SHA-256 encadenada por organización y registra como autor al DPD autenticado (Art. 50 LOPDP).
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="dpo-dictamen-tipo" className={ETIQUETA}>
                Tipo de dictamen
              </label>
              <select
                id="dpo-dictamen-tipo"
                data-testid="select-tipo-dictamen"
                value={tipoDictamen}
                onChange={(e) => setTipoDictamen(e.target.value as TipoDictamenDPO)}
                className={CAMPO}
              >
                {TIPOS_DICTAMEN.map((t) => (
                  <option key={t.valor} value={t.valor}>
                    {t.etiqueta}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="dpo-dictamen-referencia" className={ETIQUETA}>
                Referencia normativa
              </label>
              <input
                id="dpo-dictamen-referencia"
                data-testid="input-referencia-dictamen"
                type="text"
                required
                value={referenciaDictamen}
                onChange={(e) => setReferenciaDictamen(e.target.value)}
                placeholder="Ej. Art. 50 LOPDP"
                className={CAMPO}
              />
            </div>
          </div>

          <div>
            <label htmlFor="dpo-dictamen-asunto" className={ETIQUETA}>
              Asunto del dictamen
            </label>
            <input
              id="dpo-dictamen-asunto"
              data-testid="input-asunto-dictamen"
              type="text"
              required
              value={asuntoDictamen}
              onChange={(e) => setAsuntoDictamen(e.target.value)}
              placeholder="Ej. Evaluación de retención de historias clínicas"
              className={CAMPO}
            />
          </div>

          <div>
            <label htmlFor="dpo-dictamen-cuerpo" className={ETIQUETA}>
              Cuerpo técnico-jurídico de la recomendación
            </label>
            <textarea
              id="dpo-dictamen-cuerpo"
              data-testid="textarea-cuerpo-dictamen"
              rows={3}
              required
              value={cuerpoDictamen}
              onChange={(e) => setCuerpoDictamen(e.target.value)}
              placeholder="Detalle el análisis y las recomendaciones no vinculantes para la Alta Dirección..."
              className={CAMPO}
            />
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              data-testid="btn-emitir-dictamen"
              disabled={emitiendo}
              className={BOTON_PRIMARIO}
            >
              <Send className="w-3.5 h-3.5 mr-1.5" aria-hidden="true" />
              {emitiendo ? "Emitiendo dictamen..." : "Emitir dictamen"}
            </button>
          </div>
        </form>
      )}

      {errorAccionBitacora && (
        <p role="alert" className="p-3 rounded-lg text-xs badge-render-danger">
          {errorAccionBitacora}
        </p>
      )}

      {/* Bitácora Timeline */}
      <div className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-5">
        <h3 className="text-xs font-semibold text-[var(--ui-texto-suave)] uppercase tracking-wider mb-4">
          Historial Cronológico de Dictámenes y Advertencias
        </h3>

        {errorBitacora && (
          <p role="alert" className="mb-4 text-xs">
            No se pudo cargar la bitácora: {errorBitacora}
          </p>
        )}

        {cargandoBitacora ? (
          <div className="p-8 text-center text-[var(--ui-texto-suave)] text-xs">
            Cargando bitácora notarial...
          </div>
        ) : bitacora.length === 0 ? (
          <div className="p-8 text-center text-[var(--ui-texto-suave)] text-xs" data-testid="bitacora-vacia">
            No hay dictámenes asentados en la bitácora.
          </div>
        ) : (
          <div className="space-y-3" data-testid="lista-dictamenes-dpo">
            {bitacora.map((item, idx) => (
              <div
                key={item.id || idx}
                data-testid={`dictamen-card-${item.id || idx}`}
                className="p-4 rounded-lg bg-[var(--ui-superficie-2)] border border-[var(--ui-borde)] space-y-2 text-xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-[var(--ui-texto-suave)] font-bold">{item.id}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        item.tipo === "ADVERTENCIA_RIESGO"
                          ? "badge-render-danger"
                          : "bg-[var(--ui-boton)] border border-[var(--ui-borde)]"
                      }`}
                    >
                      {item.tipo}
                    </span>
                  </div>
                  <div className="flex items-center text-[11px] text-[var(--ui-texto-suave)]">
                    <Clock className="w-3.5 h-3.5 mr-1" aria-hidden="true" />
                    {item.fecha_emision ? new Date(item.fecha_emision).toLocaleDateString() : "Reciente"}
                  </div>
                </div>

                <div className="font-bold text-sm">{item.asunto}</div>
                <div className="text-[11px] text-[var(--ui-texto-suave)] font-mono">
                  Referencia legal: {item.referencia_normativa} · Autor DPD: {item.dpo_id}
                </div>
                <p className="leading-relaxed bg-[var(--ui-superficie)] p-2.5 rounded border border-[var(--ui-borde)]">
                  {item.cuerpo}
                </p>

                <div className="pt-2 flex flex-wrap items-center justify-between gap-2 border-t border-[var(--ui-borde)] text-[11px]">
                  <span className="text-[var(--ui-texto-suave)] italic">
                    Doctrina: Carácter consultivo (No vinculante por ley)
                  </span>
                  <div className="flex flex-wrap items-center gap-2">
                    {item.acuse_recibo_alta_direccion ? (
                      <span
                        data-testid={`estado-acuse-${item.id || idx}`}
                        className="px-2.5 py-0.5 rounded-full font-semibold flex items-center badge-render-success"
                      >
                        <CheckCheck className="w-3.5 h-3.5 mr-1" aria-hidden="true" />
                        Acuse de Recibo Directivo Asentado
                      </span>
                    ) : (
                      <span
                        data-testid={`estado-acuse-${item.id || idx}`}
                        className="px-2.5 py-0.5 rounded-full font-medium flex items-center badge-render-warning"
                      >
                        <AlertOctagon className="w-3.5 h-3.5 mr-1" aria-hidden="true" />
                        Pendiente Acuse de Alta Dirección
                      </span>
                    )}

                    {item.acuse_recibo_alta_direccion && (
                      <span
                        data-testid={`detalle-acuse-${item.id || idx}`}
                        className="text-[var(--ui-texto-suave)]"
                      >
                        Firmado por: <strong>{item.acuse_por || "Alta Dirección"}</strong>
                        {item.fecha_acuse
                          ? ` (${new Date(item.fecha_acuse).toLocaleString()})`
                          : ""}
                      </span>
                    )}

                    {!item.acuse_recibo_alta_direccion && esAdminOrganizacion && item.id && (
                      <button
                        type="button"
                        data-testid={`btn-firmar-acuse-${item.id}`}
                        disabled={firmandoId === item.id}
                        onClick={() => void manejarFirmarAcuse(item.id)}
                        className={BOTON_PRIMARIO}
                      >
                        <FileSignature className="w-3.5 h-3.5 mr-1" aria-hidden="true" />
                        {firmandoId === item.id ? "Firmando..." : "Firmar acuse de recibo"}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      </div>
      )}
    </div>
  );
}

const PANEL = "bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-5 space-y-4";

function InformeAnualPanel({
  esDpo,
  rol,
  userId,
}: {
  esDpo: boolean;
  rol?: string;
  userId?: string;
}) {
  const anioActual = new Date().getFullYear();
  const [anio, setAnio] = useState(anioActual);
  const [informe, setInforme] = useState<InformeAnualDpo | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function cargar() {
    setCargando(true);
    setError(null);
    try {
      setInforme(
        esDpo
          ? await generarInformeAnualDpo(anio, "dpo", userId)
          : await consultarInformeAnualDpo(anio, rol, userId),
      );
    } catch (e: unknown) {
      setInforme(null);
      setError(e instanceof Error ? e.message : "No se pudo obtener el informe.");
    } finally {
      setCargando(false);
    }
  }

  async function descargar() {
    setError(null);
    try {
      const { nombre, contenido } = await descargarInformeAnualDpo(anio, rol, userId);
      const url = URL.createObjectURL(contenido);
      const a = document.createElement("a");
      a.href = url;
      a.download = nombre;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "No se pudo descargar el informe.");
    }
  }

  const r = informe?.resumen;
  return (
    <section aria-label="Informe anual del DPO" className={PANEL} data-testid="panel-informe-anual">
      <p className="text-xs text-[var(--ui-texto-suave)]">
        Resume lo que el delegado dejó asentado en su bitácora durante un año. El delegado supervisa y
        asesora: el informe no ejecuta ni decide.
      </p>
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="anio-informe-dpo" className={ETIQUETA}>
            Año
          </label>
          <input
            id="anio-informe-dpo"
            data-testid="input-anio-informe"
            type="number"
            min={2020}
            max={anioActual}
            value={anio}
            onChange={(e) => setAnio(Number(e.target.value))}
            className={CAMPO}
          />
        </div>
        <button
          type="button"
          data-testid="btn-obtener-informe"
          disabled={cargando}
          onClick={() => void cargar()}
          className={BOTON_PRIMARIO}
        >
          <FileText className="w-3.5 h-3.5" aria-hidden="true" />
          {cargando ? "Cargando..." : esDpo ? "Generar informe" : "Consultar informe"}
        </button>
        <button
          type="button"
          data-testid="btn-descargar-informe"
          disabled={!informe}
          onClick={() => void descargar()}
          className={BOTON}
        >
          <Download className="w-3.5 h-3.5" aria-hidden="true" />
          Descargar documento
        </button>
      </div>

      {error && (
        <p role="alert" data-testid="error-informe" className="p-3 rounded-lg text-xs badge-render-danger">
          {error}
        </p>
      )}

      {informe && r && (
        <div className="space-y-3 text-xs" data-testid="informe-resultado">
          <h3 className="text-sm font-bold">Informe {informe.anio}</h3>
          <dl className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {(
              [
                ["Actuaciones del año", r.total_actuaciones, "total"],
                ["Consultas atendidas", r.consultas_atendidas, "consultas"],
                ["Dictámenes", r.dictamenes, "dictamenes"],
                ["Escalamientos", r.escalamientos, "escalamientos"],
                ["Con acuse de la dirección", r.con_acuse_de_direccion, "con-acuse"],
                ["Sin acuse de la dirección", r.sin_acuse_de_direccion, "sin-acuse"],
              ] as [string, number, string][]
            ).map(([etiqueta, valor, id]) => (
              <div key={id} className="p-3 rounded-lg bg-[var(--ui-superficie-2)] border border-[var(--ui-borde)]">
                <dt className="text-[11px] text-[var(--ui-texto-suave)]">{etiqueta}</dt>
                <dd className="text-lg font-bold" data-testid={`informe-${id}`}>
                  {valor}
                </dd>
              </div>
            ))}
          </dl>
          <p data-testid="informe-inscripcion">
            Inscripción ante la SPDP:{" "}
            {informe.inscripcion_spdp === null
              ? "sin registro en la plataforma"
              : informe.inscripcion_spdp.inscrito
                ? `inscrito el ${informe.inscripcion_spdp.fecha_inscripcion} · trámite ${informe.inscripcion_spdp.numero_tramite}`
                : "declarado como no inscrito"}
          </p>
          <p className="font-mono break-all" data-testid="informe-huella">
            Huella de la cadena: {informe.cadena.huella}{" "}
            <span
              className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                informe.cadena.integra ? "badge-render-success" : "badge-render-danger"
              }`}
            >
              {informe.cadena.integra ? "Cadena íntegra" : "Cadena alterada"}
            </span>
          </p>
        </div>
      )}
    </section>
  );
}

function InscripcionPanel({
  esAdmin,
  rol,
  userId,
}: {
  esAdmin: boolean;
  rol?: string;
  userId?: string;
}) {
  const [datos, setDatos] = useState<InscripcionesSpdp | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inscrito, setInscrito] = useState(true);
  const [fecha, setFecha] = useState("");
  const [tramite, setTramite] = useState("");
  const [guardando, setGuardando] = useState(false);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      setDatos(await consultarInscripcionSpdp(rol, userId));
    } catch (e: unknown) {
      setDatos(null);
      setError(e instanceof Error ? e.message : "No se pudo consultar la inscripción.");
    } finally {
      setCargando(false);
    }
  }, [rol, userId]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  async function registrar(e: React.FormEvent) {
    e.preventDefault();
    setGuardando(true);
    setError(null);
    try {
      await registrarInscripcionSpdp(
        {
          inscrito,
          fecha_inscripcion: inscrito ? fecha || null : null,
          numero_tramite: inscrito ? tramite || null : null,
        },
        "admin_organizacion",
        userId,
      );
      setFecha("");
      setTramite("");
      await cargar();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "No se pudo registrar la inscripción.");
    } finally {
      setGuardando(false);
    }
  }

  const vigente = datos?.vigente ?? null;
  return (
    <section aria-label="Inscripción del delegado ante la SPDP" className={PANEL} data-testid="panel-inscripcion">
      <p className="text-xs text-[var(--ui-texto-suave)]">
        Registro de si el delegado está inscrito ante la SPDP. Cada registro queda en un historial que no
        se edita ni se borra; la inscripción vigente es la última registrada.
      </p>

      {error && (
        <p role="alert" data-testid="error-inscripcion" className="p-3 rounded-lg text-xs badge-render-danger">
          {error}
        </p>
      )}

      {cargando ? (
        <p className="text-xs text-[var(--ui-texto-suave)]">Cargando inscripción...</p>
      ) : (
        <div className="text-xs" data-testid="inscripcion-vigente">
          {vigente === null ? (
            <span className="px-2.5 py-0.5 rounded-full font-semibold badge-render-warning">
              Sin registro de inscripción
            </span>
          ) : vigente.inscrito ? (
            <span className="px-2.5 py-0.5 rounded-full font-semibold badge-render-success">
              Inscrito el {vigente.fecha_inscripcion} · trámite {vigente.numero_tramite}
            </span>
          ) : (
            <span className="px-2.5 py-0.5 rounded-full font-semibold badge-render-warning">
              Declarado como no inscrito
            </span>
          )}
        </div>
      )}

      {esAdmin && (
        <form onSubmit={registrar} data-testid="form-inscripcion" className="grid gap-3 sm:grid-cols-3 items-end">
          <div>
            <label htmlFor="inscrito-spdp" className={ETIQUETA}>
              ¿Inscrito?
            </label>
            <select
              id="inscrito-spdp"
              data-testid="select-inscrito"
              value={inscrito ? "si" : "no"}
              onChange={(e) => setInscrito(e.target.value === "si")}
              className={CAMPO}
            >
              <option value="si">Sí</option>
              <option value="no">No</option>
            </select>
          </div>
          <div>
            <label htmlFor="fecha-inscripcion-spdp" className={ETIQUETA}>
              Fecha de inscripción
            </label>
            <input
              id="fecha-inscripcion-spdp"
              data-testid="input-fecha-inscripcion"
              type="date"
              disabled={!inscrito}
              value={fecha}
              onChange={(e) => setFecha(e.target.value)}
              className={CAMPO}
            />
          </div>
          <div>
            <label htmlFor="tramite-spdp" className={ETIQUETA}>
              Número de trámite
            </label>
            <input
              id="tramite-spdp"
              data-testid="input-numero-tramite"
              type="text"
              maxLength={60}
              disabled={!inscrito}
              value={tramite}
              onChange={(e) => setTramite(e.target.value)}
              className={CAMPO}
            />
          </div>
          <div className="sm:col-span-3">
            <button type="submit" data-testid="btn-registrar-inscripcion" disabled={guardando} className={BOTON_PRIMARIO}>
              <Send className="w-3.5 h-3.5" aria-hidden="true" />
              {guardando ? "Registrando..." : "Registrar"}
            </button>
          </div>
        </form>
      )}

      <div>
        <h3 className="text-xs font-semibold text-[var(--ui-texto-suave)] uppercase tracking-wider mb-2">
          Historial
        </h3>
        {datos && datos.historial.length > 0 ? (
          <ul className="space-y-2 text-xs" data-testid="historial-inscripcion">
            {datos.historial.map((i) => (
              <li
                key={i.id}
                className="p-3 rounded-lg bg-[var(--ui-superficie-2)] border border-[var(--ui-borde)]"
              >
                <strong>{i.inscrito ? "Inscrito" : "No inscrito"}</strong>
                {i.inscrito ? ` · ${i.fecha_inscripcion} · trámite ${i.numero_tramite}` : ""} · registrado por{" "}
                {i.registrado_por}
                {i.registrado_at ? ` el ${new Date(i.registrado_at).toLocaleDateString()}` : ""}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-[var(--ui-texto-suave)]" data-testid="historial-vacio">
            Aún no hay registros.
          </p>
        )}
      </div>
    </section>
  );
}
