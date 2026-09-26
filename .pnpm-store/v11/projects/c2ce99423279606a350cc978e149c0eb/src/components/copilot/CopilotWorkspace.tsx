"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CircleDashed, RefreshCw, Scale, Send, Trash2, Wrench } from "lucide-react";
import { consultarCopiloto, sanearCopiloto } from "@/lib/copilotClient";
import { SESION_VACIA, useCopilotStore } from "@/store/useCopilotStore";
import type { ConsultaCopiloto, TurnoCopiloto } from "@/types/copilot";
import { SOLICITUD_COPILOTO, useCopilotContext } from "./useCopilotContext";
import CopilotPlan, { Fundamentos } from "./CopilotPlan";

function normalizarBusqueda(valor: string) {
  return valor.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

export default function CopilotWorkspace() {
  const context = useCopilotContext();
  const { scope, identity, enabled, brechas } = context;
  const { sesiones, agregar, limpiar } = useCopilotStore();
  const session = sesiones[scope] ?? SESION_VACIA;
  const [prompt, setPrompt] = useState("");
  const [selected, setSelected] = useState<number | undefined>();
  const [busqueda, setBusqueda] = useState("");
  const [estadoConsulta, setEstadoConsulta] = useState<ConsultaCopiloto["estado"] | undefined>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [pending, setPending] = useState("");
  const currentScope = useRef(scope);
  const request = useRef<AbortController | null>(null);
  const end = useRef<HTMLDivElement | null>(null);
  const textarea = useRef<HTMLTextAreaElement | null>(null);
  const buscador = useRef<HTMLInputElement | null>(null);
  currentScope.current = scope;

  useEffect(() => {
    request.current?.abort();
    request.current = null;
    setBusy(false); setPrompt(""); setPending(""); setError(""); setSelected(undefined); setBusqueda(""); setEstadoConsulta(undefined);
    return () => { request.current?.abort(); };
  }, [identity]);


  useEffect(() => { end.current?.scrollIntoView({ block: "nearest" }); }, [session.turnos.length, busy]);

  useEffect(() => {
    const campo = textarea.current;
    if (!campo) return;
    campo.style.height = "0px";
    const limite = Math.min(240, Math.max(120, Math.floor(window.innerHeight * 0.35)));
    const altura = Math.min(campo.scrollHeight, limite);
    campo.style.height = altura + "px";
    campo.style.overflowY = campo.scrollHeight > limite ? "auto" : "hidden";
  }, [prompt]);

  const enviar = useCallback(async (texto: string, brechaId?: number) => {
    if (!texto.trim() || !scope || !enabled || request.current) return;
    const pregunta = sanearCopiloto(texto.trim());
    if (!estadoConsulta) {
      setError("Selecciona si la brecha está por iniciar, en implementación o en seguimiento.");
      return;
    }
    const brechasConsulta = brechaId === undefined
      ? brechas
      : brechas.filter((brecha) => brecha.pregunta_id === brechaId);
    if (brechaId !== undefined && brechasConsulta.length !== 1) {
      setError("La brecha seleccionada ya no pertenece al assessment actual. Vuelve a seleccionarla.");
      return;
    }
    const controller = new AbortController();
    request.current = controller;
    setBusy(true); setError(""); setPending(pregunta); setPrompt(""); setSelected(brechaId);
    const historial = session.turnos.slice(-6).flatMap((t) => [
      { rol: "usuario" as const, contenido: t.pregunta },
      { rol: "asistente" as const, contenido: t.respuesta.respuesta },
    ]);
    try {
      const respuesta = await consultarCopiloto({
        pregunta, brechas: brechasConsulta, historial, estado: estadoConsulta,
        ...(brechaId !== undefined ? { brecha_id: brechaId } : {}),
      }, controller.signal);
      if (currentScope.current !== scope || controller.signal.aborted) return;
      const turno: TurnoCopiloto = { id: crypto.randomUUID(), pregunta, respuesta, creado: new Date().toISOString() };
      agregar(scope, turno);
      setPending("");
    } catch (reason) {
      if (currentScope.current === scope && !controller.signal.aborted) {
        setError(reason instanceof Error ? reason.message : "No se pudo consultar al asistente.");
      }
    } finally {
      if (request.current === controller) { request.current = null; setBusy(false); }
    }
  }, [scope, enabled, session.turnos, brechas, agregar, estadoConsulta]);

  useEffect(() => {
    const listener = (event: Event) => {
      const id = (event as CustomEvent<number | undefined>).detail;
      const brecha = brechas.find((item) => item.pregunta_id === id);
      if (!brecha) return;
      setSelected(brecha.pregunta_id);
      setBusqueda("P" + brecha.pregunta_id + " · " + brecha.control);
      setPrompt("Explícame cómo resolver la brecha P" + brecha.pregunta_id + ", con pasos concretos y fundamento legal.");
      document.getElementById("copilot-question")?.focus();
    };
    window.addEventListener(SOLICITUD_COPILOTO, listener);
    return () => window.removeEventListener(SOLICITUD_COPILOTO, listener);
  }, [brechas]);

  const coincidencias = useMemo(() => {
    const criterio = normalizarBusqueda(busqueda.trim());
    if (!criterio) return [];
    return brechas.filter((brecha) => (
      String(brecha.pregunta_id).includes(criterio) || normalizarBusqueda(brecha.control).includes(criterio)
    )).slice(0, 6);
  }, [brechas, busqueda]);

  const ejecutarBusqueda = () => {
    const brechaId = selected ?? (coincidencias.length === 1 ? coincidencias[0].pregunta_id : undefined);
    if (brechaId === undefined) {
      setError(coincidencias.length > 1
        ? "Hay varias coincidencias. Escoge una brecha de la lista."
        : "Escribe o selecciona una brecha válida.");
      buscador.current?.focus();
      return;
    }
    if (!estadoConsulta) {
      setError("Selecciona si la brecha está por iniciar, en implementación o en seguimiento.");
      return;
    }
    const brecha = brechas.find((item) => item.pregunta_id === brechaId);
    if (!brecha) return;
    setSelected(brechaId);
    setBusqueda("P" + brechaId + " · " + brecha.control);
    void enviar("Explícame cómo solucionar únicamente la brecha P" + brechaId + " en estado " + estadoConsulta + ", con pasos concretos y fundamento legal.", brechaId);
  };

  const ultimaPlan = new Map<number, string>();
  for (const t of session.turnos) for (const p of t.respuesta.planes) ultimaPlan.set(p.pregunta_id, t.id);

  return <section aria-label="Asistente de implementación LOPDP" className="h-full min-h-0 flex flex-col bg-white dark:bg-[#141417] text-zinc-900 dark:text-zinc-100 text-xs">
    <header className="relative flex items-center gap-2 border-b border-zinc-200 dark:border-[#26262b] p-2 shrink-0">
      <button type="button" onClick={ejecutarBusqueda} disabled={busy || !enabled}
        aria-label="Consultar la brecha seleccionada" title="Consultar la brecha seleccionada"
        className="grid h-9 w-9 shrink-0 place-items-center rounded-lg text-violet-600 dark:text-violet-400 hover:bg-violet-50 dark:hover:bg-violet-500/10 disabled:opacity-40">
        <Scale className="h-5 w-5" />
      </button>
      <div className="relative min-w-0 flex-1">
        <input ref={buscador} aria-label="Buscar brecha por número o descripción" type="search"
          value={busqueda} disabled={busy || !enabled}
          onChange={(e) => { setBusqueda(e.target.value); setSelected(undefined); }}
          placeholder="¿En qué brecha trabajamos hoy?"
          className="h-9 w-full rounded-lg border border-zinc-300 dark:border-[#3a3a42] bg-white dark:bg-[#0a0a0c] px-3 text-xs outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20" />
        {selected === undefined && coincidencias.length > 0 && <ul aria-label="Coincidencias de brechas"
          className="absolute left-0 right-0 top-full z-30 mt-1 max-h-40 overflow-y-auto rounded-lg border border-zinc-200 dark:border-[#3a3a42] bg-white dark:bg-[#141417] shadow-xl">
          {coincidencias.map((brecha) => <li key={brecha.pregunta_id}>
            <button type="button" disabled={busy} onClick={() => {
              setSelected(brecha.pregunta_id); setBusqueda("P" + brecha.pregunta_id + " · " + brecha.control);
            }} className="w-full px-3 py-2 text-left hover:bg-zinc-100 dark:hover:bg-[#1e1e24]">
              P{brecha.pregunta_id} · {brecha.control} · {brecha.severidad}
            </button>
          </li>)}
        </ul>}
      </div>
      <div className="flex shrink-0 items-center gap-1" role="group" aria-label="Estado de trabajo">
        <button type="button" disabled={busy || !enabled} onClick={() => setEstadoConsulta("Por iniciar")}
          aria-label="Por iniciar" aria-pressed={estadoConsulta === "Por iniciar"} title="Por iniciar"
          style={estadoConsulta === "Por iniciar" ? { color: "#9a3bf1", backgroundColor: "rgba(154, 59, 241, 0.16)", boxShadow: "inset 0 0 0 1px rgba(154, 59, 241, 0.55)" } : undefined}
          className={`grid h-9 w-9 place-items-center rounded-lg transition-colors ${estadoConsulta === "Por iniciar" ? "" : "bg-zinc-100 text-zinc-500 hover:text-zinc-700 dark:bg-[#1e1e24] dark:text-zinc-400"}`}>
          <CircleDashed className="h-4 w-4" />
        </button>
        <button type="button" disabled={busy || !enabled} onClick={() => setEstadoConsulta("Implementación")}
          aria-label="Implementación" aria-pressed={estadoConsulta === "Implementación"} title="Implementación"
          style={estadoConsulta === "Implementación" ? { color: "#9a3bf1", backgroundColor: "rgba(154, 59, 241, 0.16)", boxShadow: "inset 0 0 0 1px rgba(154, 59, 241, 0.55)" } : undefined}
          className={`grid h-9 w-9 place-items-center rounded-lg transition-colors ${estadoConsulta === "Implementación" ? "" : "bg-zinc-100 text-zinc-500 hover:text-zinc-700 dark:bg-[#1e1e24] dark:text-zinc-400"}`}>
          <Wrench className="h-4 w-4" />
        </button>
        <button type="button" disabled={busy || !enabled} onClick={() => setEstadoConsulta("Seguimiento")}
          aria-label="Seguimiento" aria-pressed={estadoConsulta === "Seguimiento"} title="Seguimiento"
          style={estadoConsulta === "Seguimiento" ? { color: "#9a3bf1", backgroundColor: "rgba(154, 59, 241, 0.16)", boxShadow: "inset 0 0 0 1px rgba(154, 59, 241, 0.55)" } : undefined}
          className={`grid h-9 w-9 place-items-center rounded-lg transition-colors ${estadoConsulta === "Seguimiento" ? "" : "bg-zinc-100 text-zinc-500 hover:text-zinc-700 dark:bg-[#1e1e24] dark:text-zinc-400"}`}>
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>
    </header>

    {!enabled ? <div className="p-4 space-y-3">
      <p>{!context.configured ? "Guarda la ficha organizacional para comenzar." : "El corpus de este asistente cubre LOPDP. No hay fuentes configuradas para " + context.normativa + "."}</p>
    </div> : <>

      <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-4 select-text" aria-live="polite">

        {session.turnos.map((t) => <div key={t.id} className="space-y-2">
          <div className="rounded-lg bg-zinc-100 dark:bg-[#1e1e24] p-3 whitespace-pre-wrap select-text cursor-text" data-testid="copilot-user-message">{t.pregunta}</div>
          <article className="space-y-3 rounded-lg border border-zinc-200 dark:border-[#26262b] p-3 select-text cursor-text" aria-label="Respuesta del asistente">
            <p className="text-[10px] text-zinc-500">{t.respuesta.modo === "deepseek" ? "DeepSeek · artículos verificados localmente" : t.respuesta.modo === "sin_fuente" ? "Sin fuente suficiente" : "Respaldo normativo local"} · {new Date(t.creado).toLocaleString()}</p>
            <p className="whitespace-pre-wrap">{t.respuesta.respuesta}</p>
            {t.respuesta.advertencias.map((a, i) => <p key={i} className="text-amber-700 dark:text-amber-300">{a}</p>)}
            {t.respuesta.fundamentos.length > 0 && <Fundamentos fuentes={t.respuesta.fundamentos} />}
            {t.respuesta.planes.map((p) => ultimaPlan.get(p.pregunta_id) === t.id && <CopilotPlan key={p.pregunta_id}
              plan={p} vigente={brechas.some((b) => b.pregunta_id === p.pregunta_id)}
              onSeguir={() => {
                setSelected(p.pregunta_id);
                setBusqueda("P" + p.pregunta_id + " · " + p.control);
                setEstadoConsulta("Seguimiento");
                setPrompt("Ayúdame a continuar con P" + p.pregunta_id + ". " + p.seguimiento);
                document.getElementById("copilot-question")?.focus();
              }} />)}
          </article>
        </div>)}
        {pending && <p className="rounded bg-zinc-100 dark:bg-[#1e1e24] p-3 whitespace-pre-wrap">{pending}</p>}
        {busy && <p role="status">Consultando el corpus normativo y preparando los pasos…</p>}
        {error && <div role="alert" className="space-y-2 text-red-600 dark:text-red-400">
          <p>{error}</p>
          <button type="button" className="underline" onClick={() => void enviar(pending, selected)}>Reintentar consulta</button>
        </div>}
        <div ref={end} />
      </div>

      <form onSubmit={(e) => { e.preventDefault(); void enviar(prompt, selected); }} className="p-3 border-t border-zinc-200 dark:border-[#26262b] space-y-2 shrink-0">
        <label htmlFor="copilot-question" className="sr-only">Pregunta al asistente</label>
        <textarea ref={textarea} id="copilot-question" aria-label="Pregunta al asistente" value={prompt} rows={1} maxLength={4000}
          onChange={(e) => setPrompt(e.target.value)} disabled={busy || !scope}
          placeholder="¿Cómo implemento el siguiente paso?"
          className="block min-h-11 w-full resize-none overflow-hidden rounded p-2 bg-white dark:bg-[#0a0a0c] border border-zinc-300 dark:border-[#3a3a42] transition-[height] duration-150 ease-out select-text" />
        <div className="flex items-center justify-between gap-2">
          <button type="button" disabled={busy || !session.turnos.length} onClick={() => limpiar(scope)}
            aria-label="Borrar conversación de este proyecto" className="p-1 text-zinc-500 disabled:opacity-30"><Trash2 className="w-4 h-4" /></button>
          <button type="submit" disabled={busy || !scope || !prompt.trim() || estadoConsulta === undefined} className="flex items-center gap-1 bg-violet-700 text-white rounded px-3 py-2 disabled:opacity-40"><Send className="w-3 h-3" /> Consultar</button>
        </div>
        <p className="text-[10px] text-zinc-500">Comparte procesos y roles, sin datos personales. Las recomendaciones requieren implementación y revisión humana.</p>
      </form>
    </>}
  </section>;
}
