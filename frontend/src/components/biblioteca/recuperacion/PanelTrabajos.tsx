"use client";

// ¤adpa ¤frontend-ide
// ¤¤frontend-architect
/**
 * Trabajos de generación del documento elegido (BIB-207), en la ranura `documento:acciones`.
 *
 * - Cada petición lleva una clave de idempotencia; si la red falla, volver a pedir reutiliza la misma clave y
 *   el servidor devuelve el mismo trabajo, sin duplicar archivo.
 * - Se ve Pendiente, Generando, Listo o Fallido; un fallo o un intento vencido ofrecen «Reintentar».
 * - Los mensajes se anuncian con `role="status"`; si la carga falla no se muestra alerta.
 */
import React from "react";
import { useSeleccionBiblioteca } from "@/lib/biblioteca/registro";
import type { FormatoGeneracion, ModoGeneracion } from "@/lib/biblioteca/generacion";
import {
  estadoVisible, listarTrabajos, nuevaClave, obtenerTrabajo, reintentable, reintentarTrabajo, solicitarTrabajo,
  type Trabajo,
} from "@/lib/biblioteca/trabajos";

declare global {
  interface Window {
    __LOPDP_TRABAJOS_PRUEBAS__?: { borradorId?: string; intervaloMs?: number };
  }
}

const EN_CURSO = (t: Trabajo) => (t.estado === "pendiente" || t.estado === "generando") && !t.vencido;

export default function PanelTrabajos() {
  const seleccion = useSeleccionBiblioteca((s) => s.documentoId);
  const pruebas = typeof window !== "undefined" ? window.__LOPDP_TRABAJOS_PRUEBAS__ : undefined;
  const borradorId = seleccion || pruebas?.borradorId || null;
  const intervalo = pruebas?.intervaloMs ?? 2000;
  const [formato, setFormato] = React.useState<FormatoGeneracion>("docx");
  const [modo, setModo] = React.useState<ModoGeneracion>("borrador");
  const [lista, setLista] = React.useState<Trabajo[]>([]);
  const [mensaje, setMensaje] = React.useState("");
  const [ocupado, setOcupado] = React.useState(false);
  const pendiente = React.useRef<{ clave: string; modo: ModoGeneracion; formato: FormatoGeneracion } | null>(null);

  const poner = React.useCallback((t: Trabajo) => {
    setLista((actual) => [t, ...actual.filter((x) => x.id !== t.id)]);
  }, []);

  React.useEffect(() => {
    if (!borradorId) return;
    let vigente = true;
    listarTrabajos(borradorId).then((t) => vigente && setLista(t)).catch(() => vigente && setLista([]));
    return () => { vigente = false; };
  }, [borradorId]);

  const enCurso = lista.filter(EN_CURSO).map((t) => t.id).join(",");
  React.useEffect(() => {
    if (!enCurso) return;
    const id = window.setInterval(() => {
      enCurso.split(",").forEach((t) => obtenerTrabajo(t).then(poner).catch(() => undefined));
    }, intervalo);
    return () => window.clearInterval(id);
  }, [enCurso, intervalo, poner]);

  if (!borradorId) return null;

  const pedir = async () => {
    const previo = pendiente.current;
    const peticion = previo && previo.modo === modo && previo.formato === formato
      ? previo : { clave: nuevaClave(), modo, formato };
    pendiente.current = peticion;
    setOcupado(true);
    setMensaje("");
    try {
      const t = await solicitarTrabajo(borradorId, peticion.modo, peticion.formato, peticion.clave);
      pendiente.current = null;
      poner(t);
      setMensaje(`Archivo pedido: ${estadoVisible(t)}.`);
    } catch (e) {
      setMensaje(`No se pudo pedir el archivo: ${e instanceof Error ? e.message : "error desconocido"}. `
        + "Si vuelves a pedirlo se usará la misma petición.");
    } finally {
      setOcupado(false);
    }
  };

  const reintentar = async (t: Trabajo) => {
    setMensaje("");
    try {
      const nuevo = await reintentarTrabajo(t.id);
      poner(nuevo);
      setMensaje("Reintento en curso.");
    } catch (e) {
      setMensaje(`No se pudo reintentar: ${e instanceof Error ? e.message : "error desconocido"}`);
    }
  };

  return (
    <section aria-label="Trabajos de generación" data-testid="trabajos-generacion"
      className="mt-3 space-y-2 border-t border-[var(--ui-borde)] pt-3 text-xs">
      <h4 className="font-semibold">Trabajos de generación</h4>
      <p className="text-[var(--ui-texto-suave)]">
        Pedir el mismo archivo dos veces no crea copias. Si algo falla, puedes reintentar sin duplicar versiones.
      </p>
      <div className="flex flex-wrap items-center gap-2">
        <select aria-label="Formato del trabajo" value={formato}
          onChange={(e) => setFormato(e.target.value as FormatoGeneracion)} className="rounded border px-2 py-1">
          <option value="docx">Word</option>
          <option value="xlsx">Excel</option>
        </select>
        <select aria-label="Modo del trabajo" value={modo}
          onChange={(e) => setModo(e.target.value as ModoGeneracion)} className="rounded border px-2 py-1">
          <option value="borrador">Borrador</option>
          <option value="revision">Para revisión</option>
        </select>
        <button type="button" disabled={ocupado} onClick={pedir} className="rounded border px-2 py-1">
          Pedir archivo
        </button>
      </div>
      {mensaje && <p role="status">{mensaje}</p>}
      {lista.length > 0 && (
        <ul aria-label="Trabajos pedidos" className="space-y-1">
          {lista.map((t) => (
            <li key={t.id} className="flex flex-wrap items-center gap-2">
              <span>{t.formato === "docx" ? "Word" : "Excel"} · {t.modo === "borrador" ? "Borrador" : "Para revisión"}</span>
              <span data-testid="estado-trabajo">{estadoVisible(t)}</span>
              {t.intentos > 1 && <span>Intentos: {t.intentos}</span>}
              {t.estado === "fallido" && t.error_detalle && <span>{t.error_detalle}</span>}
              {reintentable(t) && (
                <button type="button" onClick={() => reintentar(t)} className="rounded border px-2 py-1">
                  Reintentar
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
