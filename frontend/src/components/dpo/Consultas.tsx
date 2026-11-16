"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";

import { obtenerContextoRolesDpo } from "@/lib/dpo";
import {
  crearConsulta,
  enviarMensaje,
  ErrorConsultas,
  ETIQUETA_ROL,
  listarConsultas,
  responderYCerrar,
  type ConsultaDpo,
  type EstadoConsulta,
  type MensajeConsulta,
} from "@/lib/dpo/consultas";

/**
 * Consultas de la organización al DPO (DPO-03), un solo componente con dos modos:
 * «mias» (Operación › Consultas al DPO) y «atendidas» (DPO › Consultas atendidas).
 * Los textos son los cerrados por UX/UI en governance/tareas/DPO-03.md; el texto de las consultas se
 * muestra siempre como texto plano. La pantalla no deduce el estado: pinta el que da el servidor.
 */

const ROLES_BANDEJA = ["dpo", "admin_organizacion", "coordinador"] as const;
const ASUNTO_MAX = 120;

const ESTADO: Record<EstadoConsulta, { etiqueta: string; clase: string }> = {
  abierta: { etiqueta: "Abierta", clase: "badge-render-warning" },
  respondida: { etiqueta: "Respondida", clase: "badge-render-success" },
  cerrada: { etiqueta: "Cerrada", clase: "" },
};

const FILTROS: { valor: EstadoConsulta | "todas"; etiqueta: string }[] = [
  { valor: "todas", etiqueta: "Todas" },
  { valor: "abierta", etiqueta: "Abiertas" },
  { valor: "respondida", etiqueta: "Respondidas" },
  { valor: "cerrada", etiqueta: "Cerradas" },
];
const VACIO_POR_FILTRO: Record<string, string> = {
  abierta: "No hay consultas abiertas.",
  respondida: "No hay consultas respondidas.",
  cerrada: "No hay consultas cerradas.",
  todas: "No hay consultas.",
};

const CAMPO =
  "w-full rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] px-3 py-2 text-sm text-[var(--ui-texto)]";
const BOTON =
  "rounded-lg bg-[var(--ui-boton)] px-3 py-1.5 text-xs font-semibold text-[var(--ui-texto)] border border-[var(--ui-borde)] disabled:opacity-50 cursor-pointer";
const BOTON_PRIMARIO =
  "rounded-lg bg-[var(--ui-primario)] px-3 py-1.5 text-xs font-semibold text-[var(--ui-primario-texto)] border border-[var(--ui-borde)] disabled:opacity-50 cursor-pointer";

const MSG_CERRADA = "Esta consulta ya está cerrada. Para otra pregunta, crea una nueva consulta.";

function fecha(iso: string): string {
  return new Date(iso).toLocaleString("es-EC", { dateStyle: "medium", timeStyle: "short" });
}

function autorDe(m: MensajeConsulta): string {
  const rol = ETIQUETA_ROL[m.autor_rol] ?? m.autor_rol;
  if (m.es_mio) return `Tú · ${rol}`;
  return m.autor_nombre ? `${m.autor_nombre} · ${rol}` : rol;
}

export default function Consultas({ modo }: { modo: "mias" | "atendidas" }) {
  const atendidas = modo === "atendidas";
  const [roles, setRoles] = useState<string[] | null>(null);
  const [uid, setUid] = useState<string | undefined>(undefined);
  const [consultas, setConsultas] = useState<ConsultaDpo[]>([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState(false);
  const [filtro, setFiltro] = useState<EstadoConsulta | "todas">("abierta");
  const [aviso, setAviso] = useState<string | null>(null);

  const [nueva, setNueva] = useState(false);
  const [asunto, setAsunto] = useState("");
  const [texto, setTexto] = useState("");
  const [erroresForm, setErroresForm] = useState<{ asunto?: string; texto?: string }>({});
  const [errorEnvio, setErrorEnvio] = useState<string | null>(null);

  const [borradores, setBorradores] = useState<Record<string, string>>({});
  const [erroresHilo, setErroresHilo] = useState<Record<string, string>>({});
  const [cerrando, setCerrando] = useState<ConsultaDpo | null>(null);
  const [respuesta, setRespuesta] = useState("");
  const [errorRespuesta, setErrorRespuesta] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const disparador = useRef<HTMLElement | null>(null);
  const botonCancelar = useRef<HTMLButtonElement | null>(null);

  const esDpo = roles?.includes("dpo") ?? false;
  const veBandeja = ROLES_BANDEJA.some((r) => roles?.includes(r));
  const rolLectura = atendidas
    ? ROLES_BANDEJA.find((r) => roles?.includes(r))
    : (roles?.find((r) => !(ROLES_BANDEJA as readonly string[]).includes(r)) ?? roles?.[0]);

  const cargar = useCallback(async () => {
    setCargando(true);
    setErrorCarga(false);
    try {
      const ctx = await obtenerContextoRolesDpo();
      setRoles(ctx.roles);
      setUid(ctx.user_id || undefined);
      const rol = atendidas
        ? ROLES_BANDEJA.find((r) => ctx.roles.includes(r))
        : (ctx.roles.find((r) => !(ROLES_BANDEJA as readonly string[]).includes(r)) ?? ctx.roles[0]);
      if (!rol) {
        setConsultas([]);
        return;
      }
      const todas = await listarConsultas(rol, ctx.user_id || undefined);
      setConsultas(atendidas ? todas : todas.filter((c) => c.mensajes[0]?.es_mio));
    } catch {
      setErrorCarga(true);
    } finally {
      setCargando(false);
    }
  }, [atendidas]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  useEffect(() => {
    if (cerrando) botonCancelar.current?.focus();
  }, [cerrando]);

  const cerrarDialogo = () => {
    setCerrando(null);
    setRespuesta("");
    setErrorRespuesta(null);
    setTimeout(() => disparador.current?.focus(), 0);
  };

  const enviarNueva = async (e: React.FormEvent) => {
    e.preventDefault();
    const errores: { asunto?: string; texto?: string } = {};
    if (!asunto.trim()) errores.asunto = "Escribe el asunto.";
    if (!texto.trim()) errores.texto = "Escribe tu consulta.";
    setErroresForm(errores);
    setErrorEnvio(null);
    if (errores.asunto || errores.texto || !rolLectura) return;
    setOcupado(true);
    try {
      await crearConsulta(rolLectura, uid, asunto.trim(), texto.trim());
      setNueva(false);
      setAsunto("");
      setTexto("");
      await cargar();
    } catch {
      setErrorEnvio("No pudimos enviar tu mensaje. Inténtalo de nuevo.");
    } finally {
      setOcupado(false);
    }
  };

  const enviarEnHilo = async (c: ConsultaDpo) => {
    const cuerpo = (borradores[c.id] ?? "").trim();
    if (!cuerpo || !rolLectura) return;
    setOcupado(true);
    setErroresHilo((p) => ({ ...p, [c.id]: "" }));
    try {
      await enviarMensaje(esDpo && atendidas ? "dpo" : rolLectura, uid, c.id, cuerpo);
      setBorradores((p) => ({ ...p, [c.id]: "" }));
      await cargar();
    } catch (err) {
      if (err instanceof ErrorConsultas && err.codigo === "CONSULTA_CERRADA") {
        setErroresHilo((p) => ({ ...p, [c.id]: MSG_CERRADA }));
        await cargar();
      } else {
        setErroresHilo((p) => ({ ...p, [c.id]: "No pudimos enviar tu mensaje. Inténtalo de nuevo." }));
      }
    } finally {
      setOcupado(false);
    }
  };

  const confirmarCierre = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cerrando) return;
    if (!respuesta.trim()) {
      setErrorRespuesta("Escribe tu respuesta final.");
      return;
    }
    setOcupado(true);
    setErrorRespuesta(null);
    try {
      const cerrada = await responderYCerrar(uid, cerrando.id, respuesta.trim());
      cerrarDialogo();
      setAviso(`Consulta cerrada. Tu respuesta quedó guardada en la bitácora.`);
      setConsultas((prev) => prev.map((c) => (c.id === cerrada.id ? cerrada : c)));
    } catch (err) {
      if (err instanceof ErrorConsultas && err.estado === 403) {
        setErrorRespuesta("Solo el DPO puede responder y cerrar consultas.");
      } else if (err instanceof ErrorConsultas && err.codigo === "CONSULTA_CERRADA") {
        setErrorRespuesta(MSG_CERRADA);
        await cargar();
      } else {
        setErrorRespuesta("No pudimos cerrar la consulta. Sigue abierta.");
      }
    } finally {
      setOcupado(false);
    }
  };

  const titulo = atendidas ? "Consultas atendidas" : "Consultas al DPO";
  const visibles = atendidas && filtro !== "todas" ? consultas.filter((c) => c.estado === filtro) : consultas;

  if (atendidas && roles && !veBandeja) {
    return (
      <main aria-label={titulo} data-testid="consultas-dpo" className="p-4 text-sm text-[var(--ui-texto-suave)]">
        <p>Esta sección es para el DPO, la administración y la coordinación de la organización.</p>
      </main>
    );
  }

  return (
    <main aria-label={titulo} data-testid="consultas-dpo" className="mx-auto w-full max-w-3xl space-y-4 p-4">
      <header className="space-y-1">
        <h1 className="text-lg font-semibold text-[var(--ui-texto)]">{titulo}</h1>
        {!atendidas && (
          <p className="text-sm text-[var(--ui-texto-suave)]">
            Escribe tu pregunta al delegado de protección de datos. Su respuesta queda guardada con la consulta.
          </p>
        )}
      </header>

      {aviso && (
        <p role="status" className="rounded-lg border border-[var(--ui-borde)] p-2 text-sm text-[var(--ui-texto)]">
          {aviso}
        </p>
      )}

      {atendidas && (
        <div className="space-y-2">
          <label className="flex flex-col gap-1 text-xs text-[var(--ui-texto-suave)] sm:max-w-xs">
            Estado
            <select
              className={CAMPO}
              value={filtro}
              onChange={(e) => setFiltro(e.target.value as EstadoConsulta | "todas")}
            >
              {FILTROS.map((f) => (
                <option key={f.valor} value={f.valor}>
                  {f.etiqueta}
                </option>
              ))}
            </select>
          </label>
          {!esDpo && (
            <p role="note" className="text-xs text-[var(--ui-texto-suave)]">
              Solo el DPO responde y cierra las consultas.
            </p>
          )}
        </div>
      )}

      {!atendidas && !nueva && (
        <button type="button" className={BOTON_PRIMARIO} onClick={() => setNueva(true)}>
          Nueva consulta
        </button>
      )}

      {!atendidas && nueva && (
        <form onSubmit={enviarNueva} noValidate className="space-y-3 rounded-lg border border-[var(--ui-borde)] p-3">
          <label className="flex flex-col gap-1 text-xs text-[var(--ui-texto-suave)]">
            Asunto
            <input
              className={CAMPO}
              value={asunto}
              maxLength={ASUNTO_MAX}
              onChange={(e) => setAsunto(e.target.value)}
              aria-describedby="ayuda-asunto"
              aria-invalid={!!erroresForm.asunto}
            />
            <span id="ayuda-asunto">Resume el tema en una línea.</span>
            {erroresForm.asunto && <span role="alert" className="text-[var(--ui-error,inherit)]">{erroresForm.asunto}</span>}
          </label>
          <label className="flex flex-col gap-1 text-xs text-[var(--ui-texto-suave)]">
            Tu consulta
            <textarea
              className={CAMPO}
              rows={5}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              aria-invalid={!!erroresForm.texto}
            />
            {erroresForm.texto && <span role="alert">{erroresForm.texto}</span>}
          </label>
          {errorEnvio && <p role="alert" className="text-sm">{errorEnvio}</p>}
          <div className="flex gap-2">
            <button type="button" className={BOTON} onClick={() => { setNueva(false); setErroresForm({}); setErrorEnvio(null); }}>
              Cancelar
            </button>
            <button type="submit" className={BOTON_PRIMARIO} disabled={ocupado}>
              Enviar consulta
            </button>
          </div>
        </form>
      )}

      {cargando && <p className="text-sm text-[var(--ui-texto-suave)]">Cargando…</p>}

      {errorCarga && (
        <div role="alert" className="space-y-2 text-sm">
          <p>No pudimos cargar las consultas. Inténtalo de nuevo.</p>
          <button type="button" className={BOTON} onClick={() => void cargar()}>
            Volver a cargar
          </button>
        </div>
      )}

      {!cargando && !errorCarga && visibles.length === 0 && (
        <p className="text-sm text-[var(--ui-texto-suave)]">
          {atendidas ? VACIO_POR_FILTRO[filtro] : "Aún no hiciste ninguna consulta al DPO."}
        </p>
      )}

      {!errorCarga && visibles.length > 0 && (
        <ul aria-label={atendidas ? "Consultas de la organización" : "Mis consultas"} className="space-y-3">
          {visibles.map((c) => {
            const est = ESTADO[c.estado];
            const puedeEscribir = c.estado !== "cerrada" && (atendidas ? esDpo : true);
            return (
              <li key={c.id} className="space-y-3 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h2 className="text-sm font-semibold text-[var(--ui-texto)]">{c.asunto}</h2>
                    <p className="text-xs text-[var(--ui-texto-suave)]">{fecha(c.creado_en)}</p>
                  </div>
                  <span className={`rounded px-2 py-0.5 text-xs ${est.clase}`}>{est.etiqueta}</span>
                </div>

                <ul aria-label="Mensajes de la consulta" className="space-y-2">
                  {c.mensajes.map((m) => (
                    <li key={m.secuencia} className="text-sm text-[var(--ui-texto)]">
                      <p className="text-xs text-[var(--ui-texto-suave)]">
                        {autorDe(m)} · {fecha(m.creado_en)}
                      </p>
                      <p className="whitespace-pre-wrap break-words">{m.texto}</p>
                    </li>
                  ))}
                </ul>

                {c.estado === "cerrada" && (
                  <div className="space-y-1 text-xs text-[var(--ui-texto-suave)]">
                    <p>Esta consulta está cerrada. Para otra pregunta, crea una nueva consulta.</p>
                    {c.huella_hilo && (
                      <p>
                        Respuesta guardada como evidencia de asesoría{" "}
                        <code aria-label="Huella de integridad">{c.huella_hilo.slice(0, 8)}</code>
                      </p>
                    )}
                  </div>
                )}

                {puedeEscribir && (
                  <div className="space-y-2">
                    <label className="flex flex-col gap-1 text-xs text-[var(--ui-texto-suave)]">
                      {atendidas ? "Tu mensaje" : "Tu mensaje"}
                      <textarea
                        className={CAMPO}
                        rows={3}
                        value={borradores[c.id] ?? ""}
                        onChange={(e) => setBorradores((p) => ({ ...p, [c.id]: e.target.value }))}
                      />
                    </label>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        className={BOTON}
                        disabled={ocupado || !(borradores[c.id] ?? "").trim()}
                        onClick={() => void enviarEnHilo(c)}
                      >
                        Enviar mensaje
                      </button>
                      {atendidas && esDpo && (
                        <button
                          type="button"
                          className={BOTON_PRIMARIO}
                          aria-label={`Responder y cerrar la consulta ${c.asunto}`}
                          onClick={(e) => {
                            disparador.current = e.currentTarget;
                            setAviso(null);
                            setCerrando(c);
                          }}
                        >
                          Responder y cerrar
                        </button>
                      )}
                    </div>
                  </div>
                )}
                {erroresHilo[c.id] && <p role="alert" className="text-sm">{erroresHilo[c.id]}</p>}
              </li>
            );
          })}
        </ul>
      )}

      {cerrando && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <form
            role="dialog"
            aria-modal="true"
            aria-label="Responder y cerrar la consulta"
            onSubmit={confirmarCierre}
            onKeyDown={(e) => e.key === "Escape" && cerrarDialogo()}
            noValidate
            className="w-full max-w-lg space-y-3 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4"
          >
            <h2 className="text-sm font-semibold text-[var(--ui-texto)]">Responder y cerrar la consulta</h2>
            <label className="flex flex-col gap-1 text-xs text-[var(--ui-texto-suave)]">
              Tu respuesta final
              <textarea
                className={CAMPO}
                rows={5}
                value={respuesta}
                onChange={(e) => setRespuesta(e.target.value)}
                aria-invalid={!!errorRespuesta}
              />
            </label>
            <p className="text-xs text-[var(--ui-texto-suave)]">
              Al cerrar, la consulta ya no admite más mensajes. Tu respuesta y el hilo quedan guardados en tu bitácora y
              como evidencia de asesoría.
            </p>
            {errorRespuesta && <p role="alert" className="text-sm">{errorRespuesta}</p>}
            <div className="flex justify-end gap-2">
              <button type="button" ref={botonCancelar} className={BOTON} onClick={cerrarDialogo}>
                Cancelar
              </button>
              <button type="submit" className={BOTON_PRIMARIO} disabled={ocupado}>
                Responder y cerrar
              </button>
            </div>
          </form>
        </div>
      )}
    </main>
  );
}
