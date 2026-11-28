// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";

import * as React from "react";
import { Copy, Loader2, Send } from "lucide-react";

import {
  crearEnlaces,
  ErrorAceptacion,
  listarAceptaciones,
  puedeEnviar,
  type EnlaceGenerado,
  type ItemAceptacion,
} from "@/lib/firma/aceptaciones";

type EstadoEnvio = "pendiente" | "aceptado" | "caducado";

const ETIQUETA: Record<EstadoEnvio, string> = {
  pendiente: "Pendiente",
  aceptado: "Aceptado",
  caducado: "Caducado",
};

const CLASE_INSIGNIA: Record<EstadoEnvio, string> = {
  pendiente: "badge-render-warning",
  aceptado: "badge-render-success",
  caducado: "badge-render-danger",
};

export function estadoDelEnvio(item: ItemAceptacion, ahora: Date = new Date()): EstadoEnvio {
  if (item.aceptado_en) return "aceptado";
  return new Date(item.caduca_en) < ahora ? "caducado" : "pendiente";
}

function enlaceAbsoluto(url: string): string {
  return url.startsWith("/") && typeof window !== "undefined" ? `${window.location.origin}${url}` : url;
}

function fecha(valor: string | null): string {
  return valor ? new Date(valor).toLocaleString("es-EC") : "—";
}

function mensaje(err: unknown, porDefecto: string): string {
  return err instanceof ErrorAceptacion || err instanceof Error ? err.message : porDefecto;
}

const CAMPO =
  "w-full rounded-lg border border-[var(--ui-borde-control)] bg-[var(--ui-campo)] px-3 py-2 text-sm text-[var(--foreground)]";

export function EnviosAceptacion() {
  const [items, setItems] = React.useState<ItemAceptacion[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [filtro, setFiltro] = React.useState("");
  const [autorizado, setAutorizado] = React.useState(false);
  const [abierto, setAbierto] = React.useState(false);

  const [documentoId, setDocumentoId] = React.useState("");
  const [personas, setPersonas] = React.useState("");
  const [dias, setDias] = React.useState(7);
  const [enviando, setEnviando] = React.useState(false);
  const [errorEnvio, setErrorEnvio] = React.useState<string | null>(null);
  const [enlaces, setEnlaces] = React.useState<EnlaceGenerado[]>([]);
  const [copiado, setCopiado] = React.useState<string | null>(null);

  const cargar = React.useCallback(async (documento: string) => {
    setError(null);
    try {
      setItems(await listarAceptaciones(documento.trim() || undefined));
    } catch (err) {
      setItems([]);
      setError(mensaje(err, "No se pudieron cargar los envíos."));
    }
  }, []);

  React.useEffect(() => {
    void cargar("");
    puedeEnviar().then(setAutorizado).catch(() => setAutorizado(false));
  }, [cargar]);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    const ids = personas.split(/[\s,;]+/).filter(Boolean);
    if (!documentoId.trim() || ids.length === 0) {
      setErrorEnvio("Indica el documento y al menos una persona.");
      return;
    }
    setEnviando(true);
    setErrorEnvio(null);
    try {
      setEnlaces(
        await crearEnlaces({ documento_id: documentoId.trim(), persona_ids: ids, dias_vigencia: dias }),
      );
      await cargar(filtro);
    } catch (err) {
      setErrorEnvio(mensaje(err, "No se pudo enviar el documento."));
    } finally {
      setEnviando(false);
    }
  }

  async function copiar(url: string) {
    try {
      await navigator.clipboard.writeText(enlaceAbsoluto(url));
      setCopiado(url);
    } catch {
      setCopiado(null);
    }
  }

  return (
    <section
      aria-labelledby="titulo-envios"
      className="rounded-xl border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-6"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 id="titulo-envios" className="text-base font-semibold">
            Firmas
          </h2>
          <p className="mt-1 text-sm text-[var(--ui-texto-suave)]">
            Envíos de documentos aprobados a aceptación, con su estado.
          </p>
        </div>
        {autorizado && (
          <button
            type="button"
            data-testid="btn-enviar-aceptacion"
            onClick={() => setAbierto((a) => !a)}
            className="inline-flex items-center gap-2 rounded-lg bg-[var(--ui-primario)] px-3 py-2 text-sm font-medium text-[var(--ui-primario-texto)]"
          >
            <Send className="h-4 w-4" aria-hidden="true" />
            Enviar a aceptación
          </button>
        )}
      </div>

      {abierto && autorizado && (
        <form onSubmit={enviar} className="mt-4 space-y-3" data-testid="form-enviar">
          <label className="block text-sm">
            Documento
            <input
              className={`${CAMPO} mt-1`}
              value={documentoId}
              onChange={(e) => setDocumentoId(e.target.value)}
              placeholder="Identificador del documento aprobado"
            />
          </label>
          <label className="block text-sm">
            Personas (identificadores separados por coma o espacio)
            <textarea
              className={`${CAMPO} mt-1`}
              rows={2}
              value={personas}
              onChange={(e) => setPersonas(e.target.value)}
            />
          </label>
          <label className="block text-sm">
            Vigencia del enlace (días, de 1 a 30)
            <input
              type="number"
              min={1}
              max={30}
              className={`${CAMPO} mt-1 w-28`}
              value={dias}
              onChange={(e) => setDias(Math.min(30, Math.max(1, Number(e.target.value) || 1)))}
            />
          </label>
          {errorEnvio && (
            <p role="alert" className="rounded-lg border border-[var(--ui-error-borde)] bg-[var(--ui-error-fondo)] px-3 py-2 text-sm text-[var(--ui-error-texto)]">
              {errorEnvio}
            </p>
          )}
          <button
            type="submit"
            disabled={enviando}
            className="inline-flex items-center gap-2 rounded-lg border border-[var(--ui-borde-control)] px-3 py-2 text-sm disabled:opacity-60"
          >
            {enviando && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
            Generar enlaces
          </button>
        </form>
      )}

      {enlaces.length > 0 && (
        <div data-testid="enlaces-generados" className="mt-4 space-y-2 rounded-lg border border-[var(--ui-borde)] p-4">
          <p className="text-sm font-medium">Enlaces generados</p>
          <p className="text-xs text-[var(--ui-texto-suave)]">
            Cópialos y entrégalos a cada persona: no se envían por correo y no se vuelven a mostrar.
          </p>
          <ul className="space-y-2">
            {enlaces.map((e) => (
              <li key={e.persona_id} className="flex flex-wrap items-center gap-2 text-sm">
                <span className="font-medium">{e.persona_id}</span>
                <code className="min-w-0 flex-1 truncate text-xs">{enlaceAbsoluto(e.url)}</code>
                <button
                  type="button"
                  onClick={() => void copiar(e.url)}
                  className="inline-flex items-center gap-1 rounded border border-[var(--ui-borde-control)] px-2 py-1 text-xs"
                >
                  <Copy className="h-3 w-3" aria-hidden="true" />
                  {copiado === e.url ? "Copiado" : "Copiar"}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <form
        className="mt-5 flex flex-wrap items-center gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          void cargar(filtro);
        }}
      >
        <input
          className={`${CAMPO} max-w-xs`}
          value={filtro}
          onChange={(e) => setFiltro(e.target.value)}
          placeholder="Filtrar por documento"
          aria-label="Filtrar por documento"
        />
        <button type="submit" className="rounded-lg border border-[var(--ui-borde-control)] px-3 py-2 text-sm">
          Filtrar
        </button>
      </form>

      {error && (
        <p role="alert" className="mt-4 rounded-lg border border-[var(--ui-error-borde)] bg-[var(--ui-error-fondo)] px-3 py-2 text-sm text-[var(--ui-error-texto)]">
          {error}
        </p>
      )}

      {items === null ? (
        <p className="mt-4 text-sm text-[var(--ui-texto-suave)]" aria-live="polite">
          Cargando…
        </p>
      ) : items.length === 0 ? (
        <p className="mt-4 text-sm text-[var(--ui-texto-suave)]">Todavía no hay envíos.</p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm" data-testid="tabla-envios">
            <thead className="text-xs text-[var(--ui-texto-suave)]">
              <tr>
                <th className="py-2 pr-4 font-medium">Persona</th>
                <th className="py-2 pr-4 font-medium">Documento</th>
                <th className="py-2 pr-4 font-medium">Estado</th>
                <th className="py-2 pr-4 font-medium">Caduca</th>
                <th className="py-2 font-medium">Aceptado</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const estado = estadoDelEnvio(item);
                return (
                  <tr key={item.id} className="border-t border-[var(--ui-borde)]">
                    <td className="py-2 pr-4">
                      {item.nombre || item.persona_id}
                      {item.email && <span className="block text-xs text-[var(--ui-texto-suave)]">{item.email}</span>}
                    </td>
                    <td className="py-2 pr-4">
                      <code className="text-xs">{item.documento_id}</code>
                    </td>
                    <td className="py-2 pr-4">
                      <span className={CLASE_INSIGNIA[estado]}>{ETIQUETA[estado]}</span>
                    </td>
                    <td className="py-2 pr-4">{fecha(item.caduca_en)}</td>
                    <td className="py-2">{fecha(item.aceptado_en)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
