"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarClock, CheckCircle2, Loader2, PlusCircle } from "lucide-react";

import { obtenerContextoRolesCapa } from "@/lib/capa";
import {
  crearControl,
  hoyGuayaquil,
  listarControles,
  retirarControl,
  semaforoDe,
  vencerControles,
  verificarControl,
  type ControlPeriodico,
  type FrecuenciaControl,
  type Semaforo,
} from "@/lib/controles/api";
import { useAuditStore, type ActiveView } from "@/store/useAuditStore";
import { useRoadmapStore } from "@/store/useRoadmapStore";

const FRECUENCIAS: { valor: FrecuenciaControl; etiqueta: string }[] = [
  { valor: "mensual", etiqueta: "Mensual" },
  { valor: "trimestral", etiqueta: "Trimestral" },
  { valor: "semestral", etiqueta: "Semestral" },
  { valor: "anual", etiqueta: "Anual" },
];

const SEMAFORO: Record<Semaforo, { etiqueta: string; clase: string }> = {
  vigente: { etiqueta: "Vigente", clase: "badge-render-success" },
  por_vencer: { etiqueta: "Por vencer", clase: "badge-render-warning" },
  vencido: { etiqueta: "Vencido", clase: "badge-render-danger" },
  retirado: { etiqueta: "Retirado", clase: "" },
};

// Orden en que se elige con qué rol leer: el más amplio primero.
const ROLES_LECTURA = ["implementador", "coordinador", "admin_organizacion", "dpo", "responsable_area"];
const CAMPO =
  "w-full rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] px-3 py-1.5 text-xs text-[var(--ui-texto)]";

const BOTON =
  "rounded-lg bg-[var(--ui-boton-primario)] px-3 py-1.5 text-xs font-semibold text-[var(--ui-texto)] border border-[var(--ui-borde)] disabled:opacity-50 cursor-pointer";

type Accion = { id: string; tipo: "verificar" | "retirar" } | null;

function mensajeDe(error: unknown, porDefecto: string): string {
  return error instanceof Error ? error.message : porDefecto;
}

export default function ControlesPeriodicos() {
  const sesion = useRoadmapStore((s) => s.session);
  const setActiveView = useAuditStore((s) => s.setActiveView);

  const [roles, setRoles] = useState<string[]>(sesion.role ? [sesion.role] : []);
  const [uid, setUid] = useState(sesion.userId);
  const [controles, setControles] = useState<ControlPeriodico[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  const [nombre, setNombre] = useState("");
  const [controlRef, setControlRef] = useState("");
  const [frecuencia, setFrecuencia] = useState<FrecuenciaControl>("trimestral");
  const [responsable, setResponsable] = useState("");
  const [proxima, setProxima] = useState("");

  const [accion, setAccion] = useState<Accion>(null);
  const [nota, setNota] = useState("");
  const [huella, setHuella] = useState("");
  const [motivo, setMotivo] = useState("");

  const hoy = useMemo(() => hoyGuayaquil(), []);
  const esImplementador = roles.includes("implementador");
  const rolGestion = esImplementador ? "implementador" : roles.includes("coordinador") ? "coordinador" : null;
  const rolNoDpo = roles.find((r) => r !== "dpo");

  const rolVerificacion = (control: ControlPeriodico): string | null => {
    if (control.estado === "retirado") return null;
    if (esImplementador) return "implementador";
    return control.responsable_user_id === uid && rolNoDpo ? rolNoDpo : null;
  };

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    let rolesActuales: string[] = sesion.role ? [sesion.role] : [];
    let usuario = sesion.userId;
    try {
      const contexto = await obtenerContextoRolesCapa();
      rolesActuales = contexto.roles;
      usuario = contexto.user_id || usuario;
      setRoles(rolesActuales);
      setUid(usuario);
    } catch {
      // Sin /organizacion/me/roles se conserva el rol de la sesión local.
    }
    const rolLectura = ROLES_LECTURA.find((r) => rolesActuales.includes(r));
    if (!rolLectura) {
      setControles([]);
      setCargando(false);
      return;
    }
    try {
      // La revisión de vencimientos corre al abrir la pantalla quien la tiene permitida.
      if (rolesActuales.includes("implementador")) await vencerControles("implementador", usuario);
      setControles(await listarControles(rolLectura, usuario));
    } catch (e: unknown) {
      setControles([]);
      setError(mensajeDe(e, "No se pudieron cargar los controles."));
    } finally {
      setCargando(false);
    }
  }, [sesion.role, sesion.userId]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const ejecutar = async (operacion: () => Promise<unknown>, porDefecto: string) => {
    setOcupado(true);
    setError(null);
    try {
      await operacion();
      setAccion(null);
      await cargar();
      return true;
    } catch (e: unknown) {
      setError(mensajeDe(e, porDefecto));
      return false;
    } finally {
      setOcupado(false);
    }
  };

  const crear = async (evento: React.FormEvent) => {
    evento.preventDefault();
    if (!rolGestion) return;
    const creado = await ejecutar(
      () =>
        crearControl(
          {
            nombre: nombre.trim(),
            ...(controlRef.trim() ? { control_ref: controlRef.trim() } : {}),
            frecuencia,
            responsable_user_id: responsable.trim(),
            proxima_verificacion: proxima,
          },
          rolGestion,
          uid,
        ),
      "No se pudo crear el control.",
    );
    if (creado) {
      setNombre("");
      setControlRef("");
      setResponsable("");
      setProxima("");
    }
  };

  const abrirAccion = (id: string, tipo: "verificar" | "retirar") => {
    setNota("");
    setHuella("");
    setMotivo("");
    setAccion(accion?.id === id && accion.tipo === tipo ? null : { id, tipo });
  };

  return (
    <div data-testid="controles-periodicos" className="space-y-6 text-[var(--ui-texto)]">
      <div className="pb-4 border-b border-[var(--ui-borde)]">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <CalendarClock className="w-5 h-5 text-[var(--ui-acento)]" />
          Controles periódicos
        </h2>
        <p className="text-xs text-[var(--ui-texto-suave)] mt-1">
          Lo que debe revisarse cada cierto tiempo, quién responde y cuándo toca. Un control vencido genera un hallazgo.
        </p>
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-[var(--ui-peligro-borde)] bg-[var(--ui-peligro-fondo)] p-3 text-xs text-[var(--ui-peligro)]"
        >
          {error}
        </div>
      )}

      {rolGestion && (
        <form
          onSubmit={crear}
          aria-label="Nuevo control"
          className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-4 space-y-3"
        >
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <PlusCircle className="w-4 h-4 text-[var(--ui-acento)]" />
            Nuevo control
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs">
            <label className="space-y-1 block md:col-span-2">
              <span className="text-[var(--ui-texto-suave)] font-medium">Nombre</span>
              <input required maxLength={200} value={nombre} onChange={(e) => setNombre(e.target.value)} className={CAMPO} />
            </label>
            <label className="space-y-1 block">
              <span className="text-[var(--ui-texto-suave)] font-medium">Requisito (opcional)</span>
              <input
                value={controlRef}
                onChange={(e) => setControlRef(e.target.value)}
                placeholder="P12"
                pattern="P([1-9]|[1-7][0-9]|80)"
                className={CAMPO}
              />
            </label>
            <label className="space-y-1 block">
              <span className="text-[var(--ui-texto-suave)] font-medium">Frecuencia</span>
              <select
                value={frecuencia}
                onChange={(e) => setFrecuencia(e.target.value as FrecuenciaControl)}
                className={CAMPO}
              >
                {FRECUENCIAS.map((f) => (
                  <option key={f.valor} value={f.valor}>
                    {f.etiqueta}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 block">
              <span className="text-[var(--ui-texto-suave)] font-medium">Primera verificación</span>
              <input type="date" required value={proxima} onChange={(e) => setProxima(e.target.value)} className={CAMPO} />
            </label>
            <label className="space-y-1 block md:col-span-2">
              <span className="text-[var(--ui-texto-suave)] font-medium">Responsable (usuario)</span>
              <input required value={responsable} onChange={(e) => setResponsable(e.target.value)} className={CAMPO} />
            </label>
          </div>
          <button type="submit" disabled={ocupado} className={BOTON}>
            Crear control
          </button>
        </form>
      )}

      {cargando ? (
        <div className="flex items-center gap-2 text-xs text-[var(--ui-texto-suave)]">
          <Loader2 className="w-4 h-4 animate-spin" />
          Cargando controles…
        </div>
      ) : controles.length === 0 ? (
        <p className="text-xs text-[var(--ui-texto-suave)]">Todavía no hay controles periódicos.</p>
      ) : (
        <ul aria-label="Controles periódicos" className="space-y-3">
          {controles.map((control) => {
            const semaforo = semaforoDe(control, hoy);
            const rolVerifica = rolVerificacion(control);
            const puedeRetirar = rolGestion !== null && control.estado !== "retirado";
            return (
              <li
                key={control.id}
                data-testid={`control-${control.id}`}
                className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-4 space-y-2 text-xs"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-sm font-semibold">
                    {control.nombre}
                    {control.control_ref ? ` · ${control.control_ref}` : ""}
                  </span>
                  <span data-testid="semaforo" data-semaforo={semaforo} className={SEMAFORO[semaforo].clase}>
                    {SEMAFORO[semaforo].etiqueta}
                  </span>
                </div>
                <dl className="grid grid-cols-1 md:grid-cols-3 gap-2 text-[var(--ui-texto-suave)]">
                  <div>
                    <dt className="inline">Frecuencia: </dt>
                    <dd className="inline capitalize">{control.frecuencia}</dd>
                  </div>
                  <div>
                    <dt className="inline">Responsable: </dt>
                    <dd className="inline break-all">{control.responsable_user_id}</dd>
                  </div>
                  <div>
                    <dt className="inline">Próxima verificación: </dt>
                    <dd className="inline">{control.proxima_verificacion}</dd>
                  </div>
                </dl>
                <div className="flex flex-wrap items-center gap-3">
                  {rolVerifica && (
                    <button
                      type="button"
                      onClick={() => abrirAccion(control.id, "verificar")}
                      className="inline-flex items-center gap-1 font-semibold text-[var(--ui-acento)]"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Registrar verificación
                    </button>
                  )}
                  {puedeRetirar && (
                    <button
                      type="button"
                      onClick={() => abrirAccion(control.id, "retirar")}
                      className="text-[var(--ui-texto-suave)] underline"
                    >
                      Retirar
                    </button>
                  )}
                  {control.hallazgo_vigente_id && (
                    <button
                      type="button"
                      onClick={() => setActiveView("roadmap" as ActiveView)}
                      title={`Hallazgo ${control.hallazgo_vigente_id}`}
                      className="font-semibold text-[var(--ui-peligro)] underline"
                    >
                      Ver hallazgo
                    </button>
                  )}
                </div>

                {accion?.id === control.id && accion.tipo === "verificar" && rolVerifica && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-[var(--ui-borde)]">
                    <label className="space-y-1 block">
                      <span className="text-[var(--ui-texto-suave)] font-medium">Nota (opcional)</span>
                      <input value={nota} maxLength={2000} onChange={(e) => setNota(e.target.value)} className={CAMPO} />
                    </label>
                    <label className="space-y-1 block">
                      <span className="text-[var(--ui-texto-suave)] font-medium">Huella de la evidencia (opcional)</span>
                      <input value={huella} onChange={(e) => setHuella(e.target.value)} className={CAMPO} />
                    </label>
                    <button
                      type="button"
                      disabled={ocupado}
                      onClick={() =>
                        void ejecutar(
                          () =>
                            verificarControl(
                              control.id,
                              {
                                ...(nota.trim() ? { nota: nota.trim() } : {}),
                                ...(huella.trim() ? { evidencia_sha256: huella.trim() } : {}),
                              },
                              rolVerifica,
                              uid,
                            ),
                          "No se pudo registrar la verificación.",
                        )
                      }
                      className={`${BOTON} md:w-fit`}
                    >
                      Guardar verificación
                    </button>
                  </div>
                )}

                {accion?.id === control.id && accion.tipo === "retirar" && rolGestion && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-[var(--ui-borde)]">
                    <label className="space-y-1 block">
                      <span className="text-[var(--ui-texto-suave)] font-medium">Motivo</span>
                      <input value={motivo} maxLength={500} onChange={(e) => setMotivo(e.target.value)} className={CAMPO} />
                    </label>
                    <button
                      type="button"
                      disabled={ocupado || !motivo.trim()}
                      onClick={() =>
                        void ejecutar(
                          () => retirarControl(control.id, motivo.trim(), rolGestion, uid),
                          "No se pudo retirar el control.",
                        )
                      }
                      className={`${BOTON} md:w-fit`}
                    >
                      Confirmar retiro
                    </button>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
