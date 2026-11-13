"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, ShieldAlert } from "lucide-react";

import {
  ErrorPaquetes,
  esPlazo,
  ETIQUETA_ESTADO,
  ETIQUETA_TERMINO,
  ETIQUETA_UNIDAD,
  formatearFecha,
  nombreParametro,
  paquetesApi,
  type DetallePaquete,
  type Impacto,
  type Parametro,
  type ParametroEntrada,
  type TerminoLegal,
  type UnidadPlazo,
} from "@/lib/plataforma/paquetes";

const aEntrada = (p: Parametro): ParametroEntrada => ({
  valor: p.valor,
  unidad: p.unidad,
  termino_legal: p.termino_legal,
  articulo: p.articulo,
  fuente_url: p.fuente_url,
  verificado: p.verificado,
});

const campo = "mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm disabled:opacity-60";

function EditorParametro({
  parametro,
  editable,
  onGuardar,
}: {
  parametro: Parametro;
  editable: boolean;
  onGuardar: (clave: string, datos: ParametroEntrada) => Promise<void>;
}) {
  const [datos, setDatos] = React.useState<ParametroEntrada>(aEntrada(parametro));
  const [guardando, setGuardando] = React.useState(false);
  React.useEffect(() => setDatos(aEntrada(parametro)), [parametro]);
  const id = `param-${parametro.clave}`;
  const plazo = esPlazo(parametro.clave);

  async function guardar(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setGuardando(true);
    try {
      await onGuardar(parametro.clave, datos);
    } finally {
      setGuardando(false);
    }
  }

  return (
    <form
      onSubmit={guardar}
      aria-labelledby={`${id}-titulo`}
      className="space-y-3 rounded-2xl border border-zinc-800 bg-zinc-900/70 p-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 id={`${id}-titulo`} className="text-base font-semibold">{nombreParametro(parametro.clave)}</h3>
        {parametro.verificado ? (
          <p className="text-xs text-emerald-300">
            Verificado por {parametro.verificado_por_nombre ?? "un operador"} el {formatearFecha(parametro.verificado_en)}
          </p>
        ) : (
          <p className="text-xs font-semibold text-amber-300">Pendiente de verificar</p>
        )}
      </div>
      <fieldset disabled={!editable || guardando} className="grid gap-3 md:grid-cols-2">
        <label className="text-sm">
          Valor
          <input
            className={campo}
            value={datos.valor}
            required
            onChange={(e) => setDatos({ ...datos, valor: e.target.value })}
          />
        </label>
        {plazo && (
          <>
            <label className="text-sm">
              Unidad
              <select
                className={campo}
                value={datos.unidad ?? ""}
                required
                onChange={(e) => setDatos({ ...datos, unidad: (e.target.value || null) as UnidadPlazo | null })}
              >
                <option value="">Elige la unidad</option>
                {(Object.keys(ETIQUETA_UNIDAD) as UnidadPlazo[]).map((u) => (
                  <option key={u} value={u}>{ETIQUETA_UNIDAD[u]}</option>
                ))}
              </select>
            </label>
            <label className="text-sm">
              Término legal (como lo dice la norma)
              <select
                className={campo}
                value={datos.termino_legal ?? ""}
                onChange={(e) =>
                  setDatos({ ...datos, termino_legal: (e.target.value || null) as TerminoLegal | null })
                }
              >
                <option value="">Sin indicar</option>
                {(Object.keys(ETIQUETA_TERMINO) as TerminoLegal[]).map((t) => (
                  <option key={t} value={t}>{ETIQUETA_TERMINO[t]}</option>
                ))}
              </select>
            </label>
          </>
        )}
        <label className="text-sm">
          Artículo
          <input className={campo} value={datos.articulo} onChange={(e) => setDatos({ ...datos, articulo: e.target.value })} />
        </label>
        <label className="text-sm md:col-span-2">
          Fuente
          <input
            className={campo}
            type="url"
            value={datos.fuente_url}
            onChange={(e) => setDatos({ ...datos, fuente_url: e.target.value })}
          />
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={datos.verificado}
            onChange={(e) => setDatos({ ...datos, verificado: e.target.checked })}
          />
          Verificado
        </label>
        {editable && (
          <div className="md:col-span-2">
            <button type="submit" className="rounded-lg bg-violet-500 px-3 py-2 text-sm font-semibold text-zinc-950">
              Guardar
            </button>
          </div>
        )}
      </fieldset>
    </form>
  );
}

function textoImpacto(impacto: Impacto | null): string {
  if (!impacto || impacto.plantillas_pendiente || impacto.organizaciones_pendiente) {
    return "El impacto en plantillas y organizaciones todavía no se puede medir. Las organizaciones verán los valores nuevos.";
  }
  return `Afecta a ${impacto.plantillas.length} plantillas y ${impacto.organizaciones ?? 0} organizaciones. Las organizaciones verán los valores nuevos.`;
}

export default function PaqueteDetallePage() {
  const { id } = useParams<{ id: string }>();
  const [detalle, setDetalle] = React.useState<DetallePaquete | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [aviso, setAviso] = React.useState<string | null>(null);
  const [denegado, setDenegado] = React.useState(false);
  const [confirmando, setConfirmando] = React.useState(false);
  const [nuevaVersion, setNuevaVersion] = React.useState("");
  const cancelarRef = React.useRef<HTMLButtonElement>(null);

  const manejar = (err: unknown) => {
    if (err instanceof ErrorPaquetes && err.status === 403) setDenegado(true);
    else setError(err instanceof Error ? err.message : "La operación no pudo completarse.");
  };

  const cargar = React.useCallback(async () => {
    setError(null);
    try {
      setDetalle(await paquetesApi.detalle(id));
    } catch (err) {
      manejar(err);
    }
  }, [id]);

  React.useEffect(() => {
    void cargar();
  }, [cargar]);

  React.useEffect(() => {
    if (confirmando) cancelarRef.current?.focus();
  }, [confirmando]);

  if (denegado) {
    return (
      <main className="min-h-screen bg-zinc-950 px-6 py-16 text-zinc-100">
        <section className="mx-auto max-w-xl rounded-2xl border border-red-900/60 bg-zinc-900 p-8 text-center">
          <ShieldAlert className="mx-auto h-10 w-10 text-red-400" aria-hidden="true" />
          <h1 className="mt-4 text-2xl font-semibold">Acceso denegado</h1>
          <p className="mt-2 text-sm text-zinc-400">Esta sección está reservada para operadores de la plataforma.</p>
        </section>
      </main>
    );
  }

  const paquete = detalle?.paquete;
  const borrador = paquete?.estado === "borrador";
  const sinVerificar = (detalle?.parametros ?? []).filter((p) => !p.verificado);
  const puedePublicar = borrador && sinVerificar.length === 0;

  async function guardar(clave: string, datos: ParametroEntrada) {
    setError(null);
    setAviso(null);
    try {
      await paquetesApi.fijarParametro(id, clave, datos);
      await cargar();
    } catch (err) {
      manejar(err);
    }
  }

  async function publicar() {
    setConfirmando(false);
    setError(null);
    try {
      const r = await paquetesApi.publicar(id);
      setAviso(`Versión ${r.paquete.version} publicada. ${textoImpacto(r.impacto)}`);
      await cargar();
    } catch (err) {
      manejar(err);
    }
  }

  async function crearVersion(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (!paquete) return;
    setError(null);
    try {
      const nuevo = await paquetesApi.crearVersion(paquete.codigo, nuevaVersion);
      window.location.assign(`/plataforma/paquetes/${encodeURIComponent(nuevo.id)}`);
    } catch (err) {
      manejar(err);
    }
  }

  return (
    <main className="min-h-screen bg-zinc-950 px-5 py-8 text-zinc-100">
      <div className="mx-auto max-w-4xl space-y-6">
        <Link href="/plataforma/paquetes" className="inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-100">
          <ArrowLeft className="h-4 w-4" aria-hidden="true" /> Paquetes normativos
        </Link>

        {paquete && (
          <header className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-violet-400">Paquete normativo</p>
              <h1 className="mt-2 text-3xl font-semibold">{paquete.nombre}</h1>
              <p className="mt-2 text-sm text-zinc-400">
                Versión {paquete.version} · {ETIQUETA_ESTADO[paquete.estado]}
              </p>
            </div>
            {borrador && (
              <div className="text-right">
                <button
                  type="button"
                  aria-disabled={!puedePublicar}
                  aria-describedby={sinVerificar.length ? "faltan-verificar" : undefined}
                  onClick={() => puedePublicar && setConfirmando(true)}
                  className="rounded-lg bg-emerald-400 px-4 py-2 text-sm font-semibold text-zinc-950 aria-disabled:cursor-not-allowed aria-disabled:opacity-50"
                >
                  Publicar
                </button>
              </div>
            )}
          </header>
        )}

        {borrador && sinVerificar.length > 0 && (
          <p id="faltan-verificar" className="rounded-lg border border-amber-800 bg-amber-950/30 px-4 py-3 text-sm text-amber-100">
            Faltan por verificar: {sinVerificar.map((p) => nombreParametro(p.clave)).join(", ")}
          </p>
        )}

        {error && (
          <p role="alert" className="rounded-lg border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-200">
            {error}
          </p>
        )}
        {aviso && (
          <p role="status" className="rounded-lg border border-emerald-900 bg-emerald-950/30 px-4 py-3 text-sm text-emerald-100">
            {aviso}
          </p>
        )}

        {confirmando && paquete && (
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="dialogo-titulo"
            aria-describedby="dialogo-texto"
            className="rounded-2xl border border-zinc-700 bg-zinc-900 p-5"
          >
            <h2 id="dialogo-titulo" className="text-lg font-semibold">
              ¿Publicar la versión {paquete.version} del paquete {paquete.nombre}?
            </h2>
            <p id="dialogo-texto" className="mt-2 text-sm text-zinc-300">{textoImpacto(null)}</p>
            <div className="mt-4 flex gap-3">
              <button
                ref={cancelarRef}
                type="button"
                onClick={() => setConfirmando(false)}
                className="rounded-lg border border-zinc-700 px-3 py-2 text-sm"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={() => void publicar()}
                className="rounded-lg bg-emerald-400 px-3 py-2 text-sm font-semibold text-zinc-950"
              >
                Publicar
              </button>
            </div>
          </div>
        )}

        {paquete && !borrador && (
          <form onSubmit={crearVersion} className="flex flex-wrap items-end gap-3 rounded-2xl border border-zinc-800 bg-zinc-900/70 p-5">
            <label className="text-sm">
              Nueva versión
              <input className={campo} value={nuevaVersion} required maxLength={16} onChange={(e) => setNuevaVersion(e.target.value)} />
            </label>
            <button type="submit" className="rounded-lg border border-zinc-700 px-3 py-2 text-sm">
              Crear versión en borrador
            </button>
          </form>
        )}

        <section aria-label="Parámetros" className="space-y-4">
          {(detalle?.parametros ?? []).map((p) => (
            <EditorParametro key={p.clave} parametro={p} editable={borrador} onGuardar={guardar} />
          ))}
        </section>
      </div>
    </main>
  );
}
