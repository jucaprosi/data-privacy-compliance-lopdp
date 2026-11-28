// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";
// ¤notificaciones ¤frontend-ide
/** Bandeja de avisos de la plataforma (NOTIF-02): Inicio › Avisos, y la campana de la cabecera. */
import { useCallback, useEffect, useState } from "react";
import { Bell } from "lucide-react";
import { cabecerasDeMiembro } from "@/lib/auth/cabeceras";
import { fetchAutenticado } from "@/lib/auth/fetchAutenticado";
import { useAuditStore } from "@/store/useAuditStore";

const BASE = "/api/v1/avisos";

/** NOTIF-05 · El texto del enlace nombra su destino. Un aviso nuevo con otro destino añade su fila aquí (R2). */
const TEXTO_POR_RUTA: readonly (readonly [string, string])[] = [["/plataforma/capacidades", "Ver capacidades editoriales"]];
const TEXTO_POR_DEFECTO = "Revisar la versión";
export const textoDelEnlace = (enlace: string): string =>
  TEXTO_POR_RUTA.find(([prefijo]) => enlace.startsWith(prefijo))?.[1] ?? TEXTO_POR_DEFECTO;

export interface Aviso {
  id: string; titulo: string; texto: string; enlace: string | null; leido: boolean; pendiente: boolean; creado_en: string;
}
interface Bandeja { avisos: Aviso[]; sin_leer: number }

async function pedir(ruta: string, init: RequestInit = {}): Promise<Response> {
  const r = await fetchAutenticado(`${BASE}${ruta}`, init, cabecerasDeMiembro());
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r;
}
async function leerBandeja(filtro: "sin_leer" | "todos", antes?: string): Promise<Bandeja> {
  const p = new URLSearchParams({ filtro });
  if (antes) p.set("antes", antes);
  return (await pedir(`?${p}`)).json();
}
const marcar = (id: string) => pedir(`/${encodeURIComponent(id)}/leido`, { method: "POST" });

export function tiempoRelativo(iso: string, ahora = Date.now()): string {
  const min = Math.max(0, Math.round((ahora - new Date(iso).getTime()) / 60000));
  if (min < 1) return "hace un momento";
  if (min < 60) return `hace ${min} ${min === 1 ? "minuto" : "minutos"}`;
  const h = Math.round(min / 60);
  if (h < 24) return `hace ${h} ${h === 1 ? "hora" : "horas"}`;
  const d = Math.round(h / 24);
  return `hace ${d} ${d === 1 ? "día" : "días"}`;
}

/** Botón de campana de la cabecera: lleva a Inicio › Avisos, sin panel flotante. */
export function CampanaAvisos() {
  const [n, setN] = useState(0);
  const setActiveView = useAuditStore((s) => s.setActiveView);
  useEffect(() => {
    let vivo = true;
    leerBandeja("sin_leer").then((b) => { if (vivo) setN(b.sin_leer); }).catch(() => { if (vivo) setN(0); });
    return () => { vivo = false; };
  }, []);
  return (
    <button type="button" data-testid="campana-avisos" onClick={() => setActiveView("avisos" as never)}
      aria-label={n > 0 ? `Avisos, ${n} sin leer` : "Avisos"}
      className="relative flex items-center gap-1 rounded border border-[var(--ui-borde-control)] px-2 py-1">
      <Bell size={14} aria-hidden="true" />
      {n > 0 ? <span aria-hidden="true" className="rounded-full border border-current px-1 text-[10px] font-semibold">{n}</span> : null}
    </button>
  );
}

export default function BandejaAvisos() {
  const [filtro, setFiltro] = useState<"sin_leer" | "todos">("sin_leer");
  const [avisos, setAvisos] = useState<Aviso[]>([]);
  const [hayMas, setHayMas] = useState(false);
  const [estado, setEstado] = useState<"cargando" | "listo" | "error">("cargando");

  const cargar = useCallback(async () => {
    setEstado("cargando");
    try {
      const b = await leerBandeja(filtro);
      setAvisos(b.avisos); setHayMas(b.avisos.length >= 50); setEstado("listo");
    } catch { setEstado("error"); }
  }, [filtro]);
  useEffect(() => { void cargar(); }, [cargar]);

  const verMas = async () => {
    try {
      const b = await leerBandeja(filtro, avisos[avisos.length - 1]?.creado_en);
      setAvisos((a) => [...a, ...b.avisos]); setHayMas(b.avisos.length >= 50);
    } catch { setEstado("error"); }
  };
  const leer = async (id: string) => {
    try {
      await marcar(id);
      setAvisos((a) => (filtro === "sin_leer" ? a.filter((x) => x.id !== id) : a.map((x) => (x.id === id ? { ...x, leido: true } : x))));
    } catch { setEstado("error"); }
  };

  return (
    <section className="flex max-w-full flex-col gap-3 p-4">
      <h2 className="text-lg font-semibold">Avisos</h2>
      <div role="tablist" aria-label="Filtro de avisos" className="flex gap-1 border-b border-[var(--ui-borde)]">
        {([["sin_leer", "Sin leer"], ["todos", "Todos"]] as const).map(([id, nombre]) => (
          <button key={id} type="button" role="tab" aria-selected={filtro === id} onClick={() => setFiltro(id)}
            className={`px-3 py-2 text-sm ${filtro === id ? "border-b-2 border-current font-medium" : ""}`}>{nombre}</button>
        ))}
      </div>
      {estado === "error" ? (
        <div role="alert" className="text-sm">
          <p>No pudimos cargar tus avisos. Inténtalo de nuevo.</p>
          <button type="button" onClick={() => void cargar()} className="mt-2 rounded border border-[var(--ui-borde-control)] px-2 py-1">Reintentar</button>
        </div>
      ) : estado === "listo" && avisos.length === 0 ? (
        <p role="status" className="text-sm">{filtro === "sin_leer" ? "No tienes avisos sin leer." : "No tienes avisos."}</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {avisos.map((a) => (
            <li key={a.id} className="break-words rounded border border-[var(--ui-borde)] p-3 text-sm">
              <h3 className="font-semibold">{!a.leido ? <span className="sr-only">Sin leer. </span> : null}{a.titulo}</h3>
              {a.texto.split("\n").map((l, i) => <p key={i}>{l}</p>)}
              <time dateTime={a.creado_en} className="block text-xs">{tiempoRelativo(a.creado_en)}</time>
              <div className="mt-2 flex flex-wrap gap-2">
                {a.enlace ? <a href={a.enlace} onClick={() => { void marcar(a.id).catch(() => undefined); }} className="underline">{textoDelEnlace(a.enlace)}</a> : null}
                {!a.leido ? <button type="button" onClick={() => void leer(a.id)} className="rounded border border-[var(--ui-borde-control)] px-2 py-1">Marcar como leído</button> : null}
              </div>
            </li>
          ))}
        </ul>
      )}
      {hayMas && estado === "listo" ? <button type="button" onClick={() => void verMas()} className="self-start rounded border border-[var(--ui-borde-control)] px-2 py-1 text-sm">Ver más</button> : null}
    </section>
  );
}
