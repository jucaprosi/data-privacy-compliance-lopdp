"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  FileCheck,
  Loader2,
  PlusCircle,
  ShieldCheck,
  UserCheck,
} from "lucide-react";

import {
  cerrarTicketCapa,
  crearTicketCapa,
  listarTicketsCapa,
  obtenerContextoRolesCapa,
  type SeveridadHallazgoCAPA,
  type TicketCAPAPersistido,
} from "@/lib/capa";
import { useRoadmapStore } from "@/store/useRoadmapStore";

const SEVERIDADES: { valor: SeveridadHallazgoCAPA; etiqueta: string }[] = [
  { valor: "NO_CONFORMIDAD_MENOR", etiqueta: "No conformidad menor" },
  { valor: "NO_CONFORMIDAD_MAYOR", etiqueta: "No conformidad mayor" },
  { valor: "OBSERVACION", etiqueta: "Observación" },
  { valor: "VULNERABILIDAD_CRITICA", etiqueta: "Vulnerabilidad crítica" },
];

export default function CapaModule() {
  const [tickets, setTickets] = useState<TicketCAPAPersistido[]>([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);
  const [errorAccion, setErrorAccion] = useState<string | null>(null);

  const session = useRoadmapStore((s) => s.session);
  const rolStore = session.role;
  const currentUserId = session.userId;

  const [rolesServidor, setRolesServidor] = useState<string[] | null>(null);
  const [userIdServidor, setUserIdServidor] = useState<string>("");

  // Formulario de alta (visible para coordinador y dpo)
  const [controlId, setControlId] = useState("P1");
  const [severidad, setSeveridad] = useState<SeveridadHallazgoCAPA>("NO_CONFORMIDAD_MENOR");
  const [descripcionHallazgo, setDescripcionHallazgo] = useState("");
  const [causaRaiz, setCausaRaiz] = useState("");
  const [accionCorrectiva, setAccionCorrectiva] = useState("");
  const [responsableId, setResponsableId] = useState("");
  const [registrando, setRegistrando] = useState(false);

  // Estado de cierre por ticket (visible para coordinador y admin_organizacion)
  const [evidenciasPorTicket, setEvidenciasPorTicket] = useState<Record<string, string>>({});
  const [cerrandoTicketId, setCerrandoTicketId] = useState<string | null>(null);

  const rolesEfectivos =
    rolesServidor !== null ? rolesServidor : rolStore ? [rolStore] : [];
  const uidEfectivo = userIdServidor || currentUserId;

  const puedeRegistrar =
    rolesEfectivos.includes("coordinador") || rolesEfectivos.includes("dpo");
  const puedeCerrar =
    rolesEfectivos.includes("coordinador") ||
    rolesEfectivos.includes("admin_organizacion");

  const rolRegistroPreferido = rolesEfectivos.includes("coordinador")
    ? "coordinador"
    : "dpo";
  const rolCierrePreferido = rolesEfectivos.includes("admin_organizacion")
    ? "admin_organizacion"
    : "coordinador";

  const cargarTicketsYContexto = useCallback(async () => {
    setCargando(true);
    setErrorCarga(null);
    let rolLectura: string | undefined = rolStore;
    let uid = currentUserId;

    try {
      const ctx = await obtenerContextoRolesCapa();
      setRolesServidor(ctx.roles);
      if (ctx.user_id) {
        setUserIdServidor(ctx.user_id);
        uid = ctx.user_id;
      }
      rolLectura =
        ctx.roles.find(
          (r) =>
            r === "coordinador" ||
            r === "dpo" ||
            r === "admin_organizacion" ||
            r === "implementador",
        ) ?? ctx.roles[0];
    } catch {
      // Si /organizacion/me/roles falla, se conserva el rol de sesión local
    }

    try {
      const data = await listarTicketsCapa(rolLectura, uid || undefined);
      setTickets(Array.isArray(data) ? data : []);
    } catch (error: unknown) {
      setTickets([]);
      setErrorCarga(
        error instanceof Error ? error.message : "No se pudieron cargar los tickets CAPA.",
      );
    } finally {
      setCargando(false);
    }
  }, [rolStore, currentUserId]);

  useEffect(() => {
    void cargarTicketsYContexto();
  }, [cargarTicketsYContexto]);

  const handleRegistrarHallazgo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (
      !controlId.trim() ||
      !descripcionHallazgo.trim() ||
      !accionCorrectiva.trim() ||
      !responsableId.trim()
    ) {
      setErrorAccion(
        "Completa el código de control, la descripción del hallazgo, la acción correctiva y el responsable.",
      );
      return;
    }
    setRegistrando(true);
    setErrorAccion(null);
    try {
      await crearTicketCapa(
        {
          control_id: controlId.trim(),
          severidad,
          descripcion_hallazgo: descripcionHallazgo.trim(),
          causa_raiz: causaRaiz.trim(),
          accion_correctiva: accionCorrectiva.trim(),
          responsable_implementacion_id: responsableId.trim(),
        },
        rolRegistroPreferido,
        uidEfectivo || undefined,
      );
      setDescripcionHallazgo("");
      setCausaRaiz("");
      setAccionCorrectiva("");
      setResponsableId("");
      await cargarTicketsYContexto();
    } catch (err: unknown) {
      setErrorAccion(
        err instanceof Error ? err.message : "No se pudo registrar el hallazgo CAPA.",
      );
    } finally {
      setRegistrando(false);
    }
  };

  const handleCerrarTicket = async (ticketId: string) => {
    const evidencia = (evidenciasPorTicket[ticketId] ?? "").trim();
    if (!evidencia) {
      setErrorAccion("Debes indicar el código o identificador de la evidencia de cierre.");
      return;
    }
    setCerrandoTicketId(ticketId);
    setErrorAccion(null);
    try {
      await cerrarTicketCapa(
        ticketId,
        evidencia,
        rolCierrePreferido,
        uidEfectivo || undefined,
      );
      setEvidenciasPorTicket((prev) => ({ ...prev, [ticketId]: "" }));
      await cargarTicketsYContexto();
    } catch (err: unknown) {
      setErrorAccion(
        err instanceof Error ? err.message : "No se pudo verificar y cerrar el hallazgo CAPA.",
      );
    } finally {
      setCerrandoTicketId(null);
    }
  };

  return (
    <section
      aria-label="Auditoría y Acciones Correctivas (CAPA)"
      className="space-y-6 text-[var(--ui-texto)]"
    >
      <div className="pb-4 border-b border-[var(--ui-borde)] flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-xl font-bold text-[var(--ui-texto)] flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-[var(--ui-alerta)]" />
            <span>Auditoría y Acciones Correctivas (CAPA)</span>
          </h2>
          <p className="text-xs text-[var(--ui-texto-suave)] mt-1">
            Gestión persistida de no conformidades, análisis de causa raíz y cierre con verificación independiente (Segregación de Funciones).
          </p>
        </div>
        <span className="badge-render-warn">Invariante SoD: Auto-verificación prohibida</span>
      </div>

      {errorCarga && (
        <div
          role="alert"
          className="rounded-lg border border-[var(--ui-peligro-borde)] bg-[var(--ui-peligro-fondo)] p-3 text-xs text-[var(--ui-peligro)]"
        >
          No se pudieron cargar los tickets CAPA: {errorCarga}
        </div>
      )}

      {errorAccion && (
        <div
          role="alert"
          className="rounded-lg border border-[var(--ui-peligro-borde)] bg-[var(--ui-peligro-fondo)] p-3 text-xs text-[var(--ui-peligro)]"
        >
          {errorAccion}
        </div>
      )}

      {puedeRegistrar && (
        <form
          onSubmit={handleRegistrarHallazgo}
          data-testid="capa-form-registro"
          className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-4 space-y-4"
        >
          <div className="flex items-center justify-between border-b border-[var(--ui-borde)] pb-2">
            <h3 className="text-sm font-semibold text-[var(--ui-texto)] flex items-center gap-2">
              <PlusCircle className="w-4 h-4 text-[var(--ui-acento)]" />
              <span>Registrar nuevo hallazgo CAPA</span>
            </h3>
            <span className="badge-render-info">Rol activo: {rolRegistroPreferido}</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <label className="space-y-1 block">
              <span className="text-[var(--ui-texto-suave)] font-medium">Control (Pn)</span>
              <input
                type="text"
                value={controlId}
                onChange={(e) => setControlId(e.target.value)}
                placeholder="Ej. P14"
                className="w-full rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] px-3 py-1.5 text-xs text-[var(--ui-texto)]"
              />
            </label>

            <label className="space-y-1 block">
              <span className="text-[var(--ui-texto-suave)] font-medium">Severidad</span>
              <select
                value={severidad}
                onChange={(e) => setSeveridad(e.target.value as SeveridadHallazgoCAPA)}
                className="w-full rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] px-3 py-1.5 text-xs text-[var(--ui-texto)]"
              >
                {SEVERIDADES.map((s) => (
                  <option key={s.valor} value={s.valor}>
                    {s.etiqueta}
                  </option>
                ))}
              </select>
            </label>

            <label className="space-y-1 block">
              <span className="text-[var(--ui-texto-suave)] font-medium">
                Responsable de implementación (ID miembro)
              </span>
              <input
                type="text"
                value={responsableId}
                onChange={(e) => setResponsableId(e.target.value)}
                placeholder="ID del miembro activo"
                className="w-full rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] px-3 py-1.5 text-xs text-[var(--ui-texto)]"
              />
            </label>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <label className="space-y-1 block">
              <span className="text-[var(--ui-texto-suave)] font-medium">
                Descripción del hallazgo
              </span>
              <input
                type="text"
                value={descripcionHallazgo}
                onChange={(e) => setDescripcionHallazgo(e.target.value)}
                placeholder="Describe la no conformidad detectada"
                className="w-full rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] px-3 py-1.5 text-xs text-[var(--ui-texto)]"
              />
            </label>

            <label className="space-y-1 block">
              <span className="text-[var(--ui-texto-suave)] font-medium">Causa raíz</span>
              <input
                type="text"
                value={causaRaiz}
                onChange={(e) => setCausaRaiz(e.target.value)}
                placeholder="Origen técnico u organizativo"
                className="w-full rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] px-3 py-1.5 text-xs text-[var(--ui-texto)]"
              />
            </label>

            <label className="space-y-1 block">
              <span className="text-[var(--ui-texto-suave)] font-medium">Acción correctiva</span>
              <input
                type="text"
                value={accionCorrectiva}
                onChange={(e) => setAccionCorrectiva(e.target.value)}
                placeholder="Plan de remediación verificable"
                className="w-full rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] px-3 py-1.5 text-xs text-[var(--ui-texto)]"
              />
            </label>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={registrando}
              className="rounded-lg bg-[var(--ui-boton-primario)] px-4 py-2 text-xs font-semibold text-[var(--ui-texto)] border border-[var(--ui-borde)] flex items-center gap-2 disabled:opacity-50 cursor-pointer"
            >
              {registrando ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <PlusCircle className="w-3.5 h-3.5" />
              )}
              <span>Registrar hallazgo CAPA</span>
            </button>
          </div>
        </form>
      )}

      <div className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl overflow-hidden">
        <div className="p-4 bg-[var(--ui-campo)] border-b border-[var(--ui-borde)] flex justify-between items-center text-xs">
          <span className="font-semibold text-[var(--ui-texto)]">
            Plan de Acción y Casos Registrados ({tickets.length})
          </span>
          <span className="text-[var(--ui-texto-suave)] font-mono">
            Persistencia PostgreSQL · RLS por organización
          </span>
        </div>

        <div className="divide-y divide-[var(--ui-borde)]">
          {cargando ? (
            <div className="p-8 text-center text-[var(--ui-texto-suave)] text-xs">
              Cargando tickets de auditoría...
            </div>
          ) : tickets.length === 0 ? (
            <div className="p-8 text-center text-[var(--ui-texto-suave)] text-xs">
              No hay no conformidades registradas en la organización.
            </div>
          ) : (
            tickets.map((t) => {
              const estaCerrado = t.estado === "CERRADO_VERIFICADO";
              const esMismoResponsable =
                Boolean(uidEfectivo) && uidEfectivo === t.responsable_implementacion_id;
              const mostrarAccionCierre = puedeCerrar && !estaCerrado && !esMismoResponsable;

              return (
                <div
                  key={t.id}
                  data-testid={`capa-ticket-${t.id}`}
                  className="p-4 space-y-3 text-xs"
                >
                  <div className="flex justify-between items-start gap-3">
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-[var(--ui-texto-suave)] font-bold">
                          {t.id}
                        </span>
                        <span className="badge-render-error">{t.severidad}</span>
                        <span className="text-[11px] text-[var(--ui-texto-suave)]">
                          Control: <strong>{t.control_id}</strong>
                        </span>
                      </div>
                      <div className="font-semibold text-[var(--ui-texto)] text-sm">
                        {t.descripcion_hallazgo}
                      </div>
                    </div>

                    <span
                      className={
                        estaCerrado ? "badge-render-success" : "badge-render-warn"
                      }
                    >
                      {t.estado}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 bg-[var(--ui-campo)] p-3 rounded-lg border border-[var(--ui-borde)]">
                    <div>
                      <span className="text-[10px] text-[var(--ui-texto-suave)] block uppercase font-bold">
                        Causa Raíz
                      </span>
                      <span className="text-[var(--ui-texto)]">{t.causa_raiz || "—"}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-[var(--ui-texto-suave)] block uppercase font-bold">
                        Plan de Remediación
                      </span>
                      <span className="text-[var(--ui-texto)]">{t.accion_correctiva}</span>
                    </div>
                  </div>

                  <div className="flex flex-wrap justify-between items-center gap-2 text-[11px] text-[var(--ui-texto-suave)] pt-1">
                    <div className="flex flex-wrap items-center gap-4">
                      <span>
                        Responsable:{" "}
                        <strong className="text-[var(--ui-texto)]">
                          {t.responsable_implementacion_id}
                        </strong>
                      </span>
                      {t.creado_por && (
                        <span>
                          Registrado por:{" "}
                          <strong className="text-[var(--ui-texto)]">{t.creado_por}</strong>
                        </span>
                      )}
                    </div>

                    {estaCerrado ? (
                      <span className="text-[var(--ui-exito)] font-medium flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>
                          Verificado por {t.auditor_verificador_id} · Evidencia:{" "}
                          {t.evidencia_cierre_id}
                        </span>
                      </span>
                    ) : (
                      <span className="text-[var(--ui-exito)] font-medium flex items-center gap-1">
                        <UserCheck className="w-3.5 h-3.5" />
                        <span>Requiere verificador independiente para cierre</span>
                      </span>
                    )}
                  </div>

                  {puedeCerrar && !estaCerrado && esMismoResponsable && (
                    <div className="pt-2 border-t border-[var(--ui-borde)] text-[11px] text-[var(--ui-alerta)] flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>
                        Auto-verificación bloqueada por SoD: eres el responsable asignado a esta acción correctiva.
                      </span>
                    </div>
                  )}

                  {mostrarAccionCierre && (
                    <div
                      data-testid={`capa-cierre-panel-${t.id}`}
                      className="pt-3 border-t border-[var(--ui-borde)] flex flex-wrap items-center gap-2"
                    >
                      <input
                        type="text"
                        value={evidenciasPorTicket[t.id] ?? ""}
                        onChange={(e) =>
                          setEvidenciasPorTicket((prev) => ({
                            ...prev,
                            [t.id]: e.target.value,
                          }))
                        }
                        placeholder="Código de evidencia de cierre (ej. EVD-2026-01)"
                        aria-label={`Evidencia de cierre para ${t.id}`}
                        className="flex-1 min-w-[220px] rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] px-3 py-1.5 text-xs text-[var(--ui-texto)]"
                      />
                      <button
                        type="button"
                        disabled={cerrandoTicketId === t.id}
                        onClick={() => void handleCerrarTicket(t.id)}
                        className="rounded-lg bg-[var(--ui-boton-primario)] px-3 py-1.5 text-xs font-semibold text-[var(--ui-texto)] border border-[var(--ui-borde)] flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                      >
                        {cerrandoTicketId === t.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <FileCheck className="w-3.5 h-3.5" />
                        )}
                        <span>Verificar y Cerrar CAPA</span>
                      </button>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </section>
  );
}
