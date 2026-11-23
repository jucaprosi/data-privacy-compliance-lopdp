// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";
// ¤frontend-ide ¤conservacion
/**
 * Pantalla de CON-01: políticas de conservación por tratamiento. Solo CON-01 edita este archivo.
 * La plataforma REGISTRA la ejecución y guarda el acta como evidencia; la acción sobre los datos la hace la
 * organización en sus sistemas. Los errores se muestran con textos fijos por código, nunca con el del servidor.
 * Textos cerrados por UX/UI en governance/tareas/CON-01.md.
 */
import React, { useCallback, useEffect, useId, useRef, useState } from "react";
import { getActividadesRAT } from "@/lib/api";
import { requestJson } from "@/lib/roadmap/cliente";
import { ApiError } from "@/types/roadmap";
import type { OrganizacionRole } from "@/types/roadmap";
import { useRolSedes } from "@/components/organizacion/sedes/useRolSedes";
import type { RegistroPantallas } from "./base";

export type AccionVencimiento = "BLOQUEO" | "ANONIMIZACION" | "SUPRESION";
export type EstadoPolitica = "ACTIVA" | "BLOQUEADA" | "EJECUTADA";
export type Semaforo = "vigente" | "por_vencer" | "vencida";

export interface Politica {
  id: string;
  actividad_rat_id: string;
  plazo_meses: number;
  accion_vencimiento: AccionVencimiento;
  fecha_proxima_revision: string;
  estado: EstadoPolitica;
  acta_ejecucion_hash: string | null;
  /** Lo calcula el servidor (R3); nulo si la política ya se ejecutó. */
  semaforo: Semaforo | null;
}

/** Quien crea y registra la ejecución (ESTIMADO por UX/UI); el resto ve el listado sin botones. */
export const puedeEjecutar = (rol: OrganizacionRole) => rol === "admin_organizacion" || rol === "implementador";

const ACCION: Record<AccionVencimiento, { alVencer: string; articulo: string; nombre: string; pasado: string; registrada: string }> = {
  BLOQUEO: { alVencer: "Bloquear", articulo: "el", nombre: "bloqueo", pasado: "bloquearon", registrada: "Bloqueo registrado." },
  ANONIMIZACION: { alVencer: "Anonimizar", articulo: "la", nombre: "anonimización", pasado: "anonimizaron", registrada: "Anonimización registrada." },
  SUPRESION: { alVencer: "Suprimir", articulo: "la", nombre: "supresión", pasado: "suprimieron", registrada: "Supresión registrada." },
};
const ESTADO: Record<EstadoPolitica, string> = {
  ACTIVA: "Activa",
  BLOQUEADA: "Bloqueo registrado",
  EJECUTADA: "Ejecución registrada",
};

const TEXTO_ERROR_GENERAL = "No pudimos guardar los cambios. Inténtalo de nuevo.";
const ERROR_POR_CODIGO: Record<string, string> = {
  CONSERVACION_POLITICA_NO_ENCONTRADA: "No encontramos esta política. Actualizamos la lista.",
  CONSERVACION_PLAZO_INVALIDO: "El plazo debe ser de al menos 1 mes.",
  CONSERVACION_YA_EJECUTADA: "Esta política ya tiene la ejecución registrada. Actualizamos su estado.",
  CONSERVACION_ACTIVIDAD_NO_ENCONTRADA: "El tratamiento elegido ya no está en el inventario. Elige otro.",
};
const RECARGAN = new Set(["CONSERVACION_POLITICA_NO_ENCONTRADA", "CONSERVACION_YA_EJECUTADA"]);

export function textoDeError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.code && ERROR_POR_CODIGO[err.code]) return ERROR_POR_CODIGO[err.code];
    if (err.status === 403) return "No tienes permiso para esta acción.";
  }
  return TEXTO_ERROR_GENERAL;
}

/** dd/mm/aaaa a partir de una fecha ISO (aaaa-mm-dd); vacío si no se puede leer. */
export function fechaCorta(iso: string | undefined | null): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso ?? "");
  return m ? `${m[3]}/${m[2]}/${m[1]}` : "";
}

const ETIQUETA_SEMAFORO: Record<Semaforo, { texto: string; icono: string; clase: string }> = {
  vigente: { texto: "Vigente", icono: "✓", clase: "text-[var(--ui-texto)]" },
  por_vencer: { texto: "Por vencer", icono: "⚠", clase: "badge-render-warning" },
  vencida: { texto: "Vencida", icono: "✕", clase: "badge-render-danger" },
};

const conRol = (rol: OrganizacionRole) => ({ headers: { "X-Role": rol } });

export const conservacionApi = {
  listar: (rol: OrganizacionRole) => requestJson<Politica[]>("/conservacion/politicas", { method: "GET", ...conRol(rol) }),
  crear: (
    rol: OrganizacionRole,
    cuerpo: { actividad_rat_id: string; plazo_meses: number; accion_vencimiento: AccionVencimiento; fecha_proxima_revision?: string },
  ) => requestJson<Politica>("/conservacion/politicas", { method: "POST", body: JSON.stringify(cuerpo), ...conRol(rol) }),
  ejecutar: (rol: OrganizacionRole, id: string) =>
    requestJson<Politica>(`/conservacion/politicas/${encodeURIComponent(id)}/ejecutar`, { method: "POST", ...conRol(rol) }),
};

const CAMPO =
  "w-full rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-1.5 text-sm text-[var(--ui-texto)]";
const BOTON =
  "rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-1.5 text-sm font-medium text-[var(--ui-texto)] disabled:opacity-50";

interface Tratamiento {
  id: string;
  nombre: string;
}

export default function ConservacionPantalla() {
  const rol = useRolSedes();
  return (
    <main aria-label="Conservación de datos" className="mx-auto max-w-5xl space-y-4 pb-10" data-testid="conservacion-datos">
      <header>
        <h1 className="text-lg font-semibold text-[var(--ui-texto)]">Conservación de datos</h1>
        <p className="text-sm text-[var(--ui-texto-suave)]">Plazos de conservación por tratamiento</p>
        <p className="mt-1 text-sm text-[var(--ui-texto)]">
          Define cuánto tiempo se conservan los datos de cada tratamiento y qué hacer cuando se cumple el plazo.
        </p>
      </header>
      {rol.fase === "cargando" && <p role="status" className="text-sm">Cargando las políticas de conservación…</p>}
      {rol.fase === "sin_servidor" && <p className="text-sm">Inicia sesión para ver las políticas de conservación.</p>}
      {rol.fase === "sin_rol" && <p className="text-sm">No tienes permiso para esta acción.</p>}
      {rol.fase === "error" && <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">{rol.mensaje}</p>}
      {rol.fase === "lista" && <Listado rol={rol.rol} />}
      <p className="text-xs text-[var(--ui-texto-suave)]">LOPDP, art. 10, lit. i</p>
    </main>
  );
}

function Listado({ rol }: { rol: OrganizacionRole }) {
  const ejecuta = puedeEjecutar(rol);
  const [politicas, setPoliticas] = useState<Politica[] | null>(null);
  const [tratamientos, setTratamientos] = useState<Tratamiento[]>([]);
  const [fallo, setFallo] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [nueva, setNueva] = useState(false);
  const [aEjecutar, setAEjecutar] = useState<Politica | null>(null);

  const cargar = useCallback(async () => {
    try {
      setPoliticas(await conservacionApi.listar(rol));
      setFallo(false);
    } catch {
      setFallo(true);
    }
  }, [rol]);

  useEffect(() => {
    void cargar();
    getActividadesRAT()
      .then((a) => setTratamientos(a.map((x) => ({ id: x.id as string, nombre: (x as { nombre?: string }).nombre ?? String(x.id) }))))
      .catch(() => setTratamientos([]));
  }, [cargar]);

  const nombreDe = (id: string) => tratamientos.find((t) => t.id === id)?.nombre ?? id;

  const alFallar = async (err: unknown) => {
    setAviso(null);
    setError(textoDeError(err));
    if (err instanceof ApiError && err.code && RECARGAN.has(err.code)) await cargar();
  };

  return (
    <section aria-label="Políticas de conservación" className="space-y-3">
      {fallo && (
        <div role="alert" className="badge-render-danger flex flex-wrap items-center gap-3 rounded-md px-3 py-2 text-sm">
          <span>No pudimos cargar las políticas de conservación. Inténtalo de nuevo.</span>
          <button type="button" className={BOTON} onClick={() => void cargar()}>Volver a cargar</button>
        </div>
      )}
      {error && <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">{error}</p>}
      {aviso && <p role="status" className="text-sm">{aviso}</p>}
      {ejecuta ? (
        <button type="button" className={BOTON} onClick={() => { setError(null); setNueva(true); }}>Nueva política</button>
      ) : (
        <p className="text-sm text-[var(--ui-texto-suave)]">Registran la ejecución la persona administradora o el implementador.</p>
      )}
      {politicas && !fallo && politicas.length === 0 && (
        <p className="text-sm">Aún no hay políticas de conservación. Crea una para cada tratamiento del inventario.</p>
      )}
      {politicas && politicas.length > 0 && (
        <table className="w-full text-left text-sm max-sm:block">
          <caption className="sr-only">Políticas de conservación</caption>
          <thead className="max-sm:sr-only">
            <tr>
              <th scope="col">Tratamiento</th>
              <th scope="col">Plazo</th>
              <th scope="col">Al vencer</th>
              <th scope="col">Próxima revisión</th>
              <th scope="col">Estado</th>
              <th scope="col">Acción</th>
            </tr>
          </thead>
          <tbody className="max-sm:block">
            {politicas.map((p) => {
              const a = ACCION[p.accion_vencimiento];
              const s = p.semaforo ? ETIQUETA_SEMAFORO[p.semaforo] : null;
              return (
                <tr key={p.id} className="border-t border-[var(--ui-borde)] max-sm:mb-3 max-sm:block max-sm:rounded-md max-sm:border max-sm:p-3">
                  <td className="py-2 max-sm:block">{nombreDe(p.actividad_rat_id)}</td>
                  <td className="py-2 max-sm:block">{`${p.plazo_meses} meses`}</td>
                  <td className="py-2 max-sm:block">{a.alVencer}</td>
                  <td className="py-2 max-sm:block">
                    {fechaCorta(p.fecha_proxima_revision)}
                    {s && (
                      <span className={`ml-2 rounded px-1.5 py-0.5 text-xs font-medium ${s.clase}`}>
                        <span aria-hidden="true">{s.icono} </span>{s.texto}
                      </span>
                    )}
                  </td>
                  <td className="py-2 max-sm:block">{ESTADO[p.estado]}</td>
                  <td className="py-2 max-sm:block">
                    {ejecuta && p.estado === "ACTIVA" && (
                      <button
                        type="button"
                        className={BOTON}
                        aria-label={`Registrar ${a.nombre} de ${nombreDe(p.actividad_rat_id)}`}
                        onClick={() => { setError(null); setAEjecutar(p); }}
                      >
                        {`Registrar ${a.nombre}`}
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
      {nueva && (
        <DialogoNueva
          rol={rol}
          tratamientos={tratamientos}
          onCerrar={() => setNueva(false)}
          onCreada={async () => { setNueva(false); setAviso(null); await cargar(); }}
          onError={alFallar}
        />
      )}
      {aEjecutar && (
        <DialogoEjecutar
          rol={rol}
          politica={aEjecutar}
          tratamiento={nombreDe(aEjecutar.actividad_rat_id)}
          onCerrar={() => setAEjecutar(null)}
          onRegistrada={async (p) => {
            setAEjecutar(null);
            setAviso(`${ACCION[p.accion_vencimiento].registrada} El acta quedó guardada como evidencia. Huella de integridad: ${(p.acta_ejecucion_hash ?? "").slice(0, 8)}`);
            await cargar();
          }}
          onError={async (err) => { setAEjecutar(null); await alFallar(err); }}
        />
      )}
    </section>
  );
}

/** Diálogo modal: foco inicial en «Cancelar», foco atrapado, Escape cierra y el foco vuelve al origen. */
function Dialogo({ titulo, onCerrar, children }: { titulo: string; onCerrar: () => void; children: (cancelar: React.RefObject<HTMLButtonElement | null>) => React.ReactNode }) {
  const idTitulo = useId();
  const caja = useRef<HTMLDivElement | null>(null);
  const cancelar = useRef<HTMLButtonElement | null>(null);
  const origen = useRef<HTMLElement | null>(typeof document !== "undefined" ? (document.activeElement as HTMLElement | null) : null);

  useEffect(() => {
    cancelar.current?.focus();
    const retorno = origen.current;
    return () => retorno?.focus();
  }, []);

  const teclas = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Escape") {
      e.stopPropagation();
      onCerrar();
      return;
    }
    if (e.key !== "Tab" || !caja.current) return;
    const focales = Array.from(caja.current.querySelectorAll<HTMLElement>("button:not([disabled]), input:not([disabled]), select:not([disabled])"));
    if (focales.length === 0) return;
    const primero = focales[0];
    const ultimo = focales[focales.length - 1];
    if (e.shiftKey && document.activeElement === primero) {
      e.preventDefault();
      ultimo.focus();
    } else if (!e.shiftKey && document.activeElement === ultimo) {
      e.preventDefault();
      primero.focus();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onKeyDown={teclas}>
      <div
        ref={caja}
        role="dialog"
        aria-modal="true"
        aria-labelledby={idTitulo}
        className="w-full max-w-md space-y-3 rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4"
      >
        <h2 id={idTitulo} className="text-base font-semibold text-[var(--ui-texto)]">{titulo}</h2>
        {children(cancelar)}
      </div>
    </div>
  );
}

function DialogoNueva({ rol, tratamientos, onCerrar, onCreada, onError }: {
  rol: OrganizacionRole;
  tratamientos: Tratamiento[];
  onCerrar: () => void;
  onCreada: () => Promise<void>;
  onError: (err: unknown) => Promise<void>;
}) {
  const id = useId();
  const [actividad, setActividad] = useState("");
  const [plazo, setPlazo] = useState("");
  const [accion, setAccion] = useState<AccionVencimiento>("BLOQUEO");
  const [revision, setRevision] = useState("");
  const [errorPlazo, setErrorPlazo] = useState(false);
  const [enviando, setEnviando] = useState(false);

  const guardar = async () => {
    const meses = Number(plazo);
    if (!Number.isInteger(meses) || meses < 1) {
      setErrorPlazo(true);
      return;
    }
    setErrorPlazo(false);
    setEnviando(true);
    try {
      await conservacionApi.crear(rol, {
        actividad_rat_id: actividad,
        plazo_meses: meses,
        accion_vencimiento: accion,
        ...(revision ? { fecha_proxima_revision: revision } : {}),
      });
      await onCreada();
    } catch (err) {
      setEnviando(false);
      if (err instanceof ApiError && err.code === "CONSERVACION_PLAZO_INVALIDO") setErrorPlazo(true);
      else {
        onCerrar();
        await onError(err);
      }
    }
  };

  return (
    <Dialogo titulo="Nueva política" onCerrar={onCerrar}>
      {(cancelar) => (
        <>
          <div>
            <label htmlFor={`${id}-t`} className="mb-1 block text-xs font-semibold text-[var(--ui-texto-suave)]">Tratamiento</label>
            <select id={`${id}-t`} className={CAMPO} value={actividad} onChange={(e) => setActividad(e.target.value)}>
              <option value="" disabled>—</option>
              {tratamientos.map((t) => <option key={t.id} value={t.id}>{t.nombre}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor={`${id}-p`} className="mb-1 block text-xs font-semibold text-[var(--ui-texto-suave)]">Plazo de conservación (meses)</label>
            <input
              id={`${id}-p`}
              type="number"
              min={1}
              step={1}
              className={CAMPO}
              value={plazo}
              aria-invalid={errorPlazo}
              aria-describedby={errorPlazo ? `${id}-pe` : undefined}
              onChange={(e) => setPlazo(e.target.value)}
            />
            {errorPlazo && <p id={`${id}-pe`} role="alert" className="mt-1 text-xs">Escribe un plazo de al menos 1 mes.</p>}
          </div>
          <div>
            <label htmlFor={`${id}-a`} className="mb-1 block text-xs font-semibold text-[var(--ui-texto-suave)]">Al vencer</label>
            <select id={`${id}-a`} className={CAMPO} value={accion} onChange={(e) => setAccion(e.target.value as AccionVencimiento)}>
              {(Object.keys(ACCION) as AccionVencimiento[]).map((k) => <option key={k} value={k}>{ACCION[k].alVencer}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor={`${id}-r`} className="mb-1 block text-xs font-semibold text-[var(--ui-texto-suave)]">Próxima revisión</label>
            <input id={`${id}-r`} type="date" className={CAMPO} value={revision} onChange={(e) => setRevision(e.target.value)} />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" ref={cancelar} className={BOTON} onClick={onCerrar}>Cancelar</button>
            <button type="button" className={BOTON} disabled={enviando || !actividad || !plazo} onClick={() => void guardar()}>
              Guardar política
            </button>
          </div>
        </>
      )}
    </Dialogo>
  );
}

function DialogoEjecutar({ rol, politica, tratamiento, onCerrar, onRegistrada, onError }: {
  rol: OrganizacionRole;
  politica: Politica;
  tratamiento: string;
  onCerrar: () => void;
  onRegistrada: (p: Politica) => Promise<void>;
  onError: (err: unknown) => Promise<void>;
}) {
  const a = ACCION[politica.accion_vencimiento];
  const [confirmado, setConfirmado] = useState(false);
  const [enviando, setEnviando] = useState(false);

  const registrar = async () => {
    setEnviando(true);
    try {
      await onRegistrada(await conservacionApi.ejecutar(rol, politica.id));
    } catch (err) {
      await onError(err);
    }
  };

  return (
    <Dialogo titulo={`¿Registrar ${a.articulo} ${a.nombre} de los datos de ${tratamiento}?`} onCerrar={onCerrar}>
      {(cancelar) => (
        <>
          <p className="text-sm">
            {`Queda registrado que los datos de este tratamiento se ${a.pasado} al cumplirse el plazo de ${politica.plazo_meses} meses. La plataforma guarda el acta como evidencia; ${a.articulo} ${a.nombre} de los datos la hace tu organización en sus sistemas.`}
          </p>
          <p className="text-sm font-medium">Este registro no se puede deshacer.</p>
          <label className="flex items-start gap-2 text-sm">
            <input type="checkbox" checked={confirmado} onChange={(e) => setConfirmado(e.target.checked)} />
            <span>{`Confirmo que ${a.articulo} ${a.nombre} ya se hizo o se hará en los sistemas de la organización.`}</span>
          </label>
          <div className="flex justify-end gap-2">
            <button type="button" ref={cancelar} className={BOTON} onClick={onCerrar}>Cancelar</button>
            <button type="button" className={BOTON} disabled={!confirmado || enviando} onClick={() => void registrar()}>
              {`Registrar ${a.articulo} ${a.nombre}`}
            </button>
          </div>
        </>
      )}
    </Dialogo>
  );
}

export const PANTALLAS_CON_01: RegistroPantallas = {
  conservacion_datos: () => <ConservacionPantalla />,
};
