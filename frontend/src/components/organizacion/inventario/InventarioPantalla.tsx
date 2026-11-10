"use client";
// ¤frontend-ide ¤inventario
// Pantalla del inventario (ORG-17) en el menú Inventario: sistemas, soportes y personas mínimas de la
// organización. Resuelve el rol con /organizacion/me/roles; todo se lee y se guarda en el servidor.
import React, { useCallback, useEffect, useId, useState } from "react";
import { useSesion } from "@/lib/auth";
import { organizacionApi } from "@/lib/roadmap/cliente";
import { ApiError } from "@/types/roadmap";
import type { AreaItem, OrganizacionRole } from "@/types/roadmap";
import {
  ETIQUETA_TIPO,
  cuerpoActivo,
  cuerpoPersona,
  inventarioApi,
  puedeEscribirInventario,
  validarActivo,
  validarPersona,
  type Activo,
  type BorradorActivo,
  type BorradorPersonaInventario,
  type PersonaInventario,
  type TipoActivo,
  type TratamientoVinculable,
} from "./inventario";

const CAMPO =
  "w-full rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-1.5 text-sm text-[var(--ui-texto)]";
const ETIQUETA = "mb-1 block text-xs font-semibold text-[var(--ui-texto-suave)]";
const BOTON =
  "rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-1.5 text-sm font-medium text-[var(--ui-texto)] disabled:opacity-50";

type Seccion = "sistema" | "soportes" | "personas";
const SECCIONES: ReadonlyArray<{ id: Seccion; nombre: string }> = [
  { id: "sistema", nombre: "Activos y sistemas" },
  { id: "soportes", nombre: "Soportes" },
  { id: "personas", nombre: "Personas" },
];

const ACTIVO_VACIO: BorradorActivo = { nombre: "", descripcion: "", ubicacion: "", areaId: "", responsableId: "" };
const PERSONA_VACIA: BorradorPersonaInventario = { nombre: "", cargo: "", email: "", areaId: "", cedula: "" };

type Carga =
  | { fase: "cargando" }
  | { fase: "sin_servidor" }
  | { fase: "sin_rol" }
  | { fase: "error"; mensaje: string }
  | { fase: "lista"; rol: OrganizacionRole };

const MENSAJE_CEDULA_NO_GUARDADA =
  "No pudimos guardar la cédula en este momento. No es un error tuyo; el resto de los datos se puede guardar sin ella. Inténtalo más tarde o avisa al equipo de EVYDENTIA.";

const mensajeDe = (err: unknown, defecto: string) => (err instanceof Error && err.message ? err.message : defecto);

export default function InventarioPantalla() {
  const { listo, requiereSesion, sesion } = useSesion();
  const [carga, setCarga] = useState<Carga>({ fase: "cargando" });

  useEffect(() => {
    if (!listo) return;
    if (!requiereSesion || !sesion) {
      setCarga({ fase: "sin_servidor" });
      return;
    }
    let cancelado = false;
    organizacionApi
      .getMyRoles()
      .then((roles) => {
        if (cancelado) return;
        const orden: OrganizacionRole[] = ["admin_organizacion", "implementador", "coordinador", "dpo"];
        const rol = orden.find((r) => roles.some((x) => x.role === r));
        setCarga(rol ? { fase: "lista", rol } : { fase: "sin_rol" });
      })
      .catch((err: unknown) => {
        if (!cancelado) setCarga({ fase: "error", mensaje: mensajeDe(err, "No pudimos comprobar tus permisos. Inténtalo de nuevo.") });
      });
    return () => {
      cancelado = true;
    };
  }, [listo, requiereSesion, sesion]);

  return (
    <div className="mx-auto max-w-5xl space-y-4 pb-10">
      <header>
        <h2 className="text-lg font-semibold text-[var(--ui-texto)]">Inventario de la organización</h2>
        <p className="text-sm text-[var(--ui-texto-suave)]">
          Sistemas, soportes y personas que intervienen en el tratamiento de datos personales.
        </p>
      </header>
      {carga.fase === "cargando" && <p role="status" className="text-sm">Cargando…</p>}
      {carga.fase === "sin_servidor" && (
        <p className="text-sm">Inicia sesión para ver el inventario de tu organización.</p>
      )}
      {carga.fase === "sin_rol" && <p className="text-sm">No tienes permiso para ver el inventario de esta organización.</p>}
      {carga.fase === "error" && <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">{carga.mensaje}</p>}
      {carga.fase === "lista" && <Inventario rol={carga.rol} puedeEditar={puedeEscribirInventario(carga.rol)} />}
    </div>
  );
}

function Inventario({ rol, puedeEditar }: { rol: OrganizacionRole; puedeEditar: boolean }) {
  const [seccion, setSeccion] = useState<Seccion>("sistema");
  const [activos, setActivos] = useState<Activo[]>([]);
  const [personas, setPersonas] = useState<PersonaInventario[]>([]);
  const [tratamientos, setTratamientos] = useState<TratamientoVinculable[]>([]);
  const [areas, setAreas] = useState<AreaItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [cargado, setCargado] = useState(false);

  const recargar = useCallback(async () => {
    try {
      const [a, p, t, ar] = await Promise.all([
        inventarioApi.activos(rol),
        inventarioApi.personas(rol),
        inventarioApi.tratamientos(rol),
        organizacionApi.listAreas().catch(() => [] as AreaItem[]),
      ]);
      setActivos(a);
      setPersonas(p);
      setTratamientos(t);
      setAreas(ar);
      setError(null);
    } catch (err: unknown) {
      setError(mensajeDe(err, "No pudimos leer el inventario. Inténtalo de nuevo."));
    } finally {
      setCargado(true);
    }
  }, [rol]);

  useEffect(() => {
    void recargar();
  }, [recargar]);

  const ejecutar = useCallback(
    async (accion: () => Promise<void>, manejarError?: (err: unknown) => boolean): Promise<boolean> => {
      try {
        await accion();
        await recargar();
        setError(null);
        return true;
      } catch (err: unknown) {
        if (!manejarError?.(err)) setError(mensajeDe(err, "No pudimos guardar los cambios. Inténtalo de nuevo."));
        return false;
      }
    },
    [recargar],
  );

  return (
    <div className="space-y-4">
      <div role="tablist" aria-label="Secciones del inventario" className="flex gap-2">
        {SECCIONES.map((s) => (
          <button
            key={s.id}
            type="button"
            role="tab"
            aria-selected={seccion === s.id}
            onClick={() => setSeccion(s.id)}
            className={`${BOTON} ${seccion === s.id ? "border-[var(--ui-acento)] font-semibold" : ""}`}
          >
            {s.nombre}
          </button>
        ))}
      </div>
      {error && <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">{error}</p>}
      {!puedeEditar && <p className="text-sm text-[var(--ui-texto-suave)]">Puedes consultar el inventario, pero no modificarlo.</p>}
      {!cargado && <p role="status" className="text-sm">Cargando…</p>}
      {cargado && seccion === "sistema" && (
        <SeccionActivos
          titulo="Activos y sistemas"
          tipos={["sistema"]}
          tipoNuevo="sistema"
          activos={activos}
          personas={personas}
          areas={areas}
          tratamientos={tratamientos}
          puedeEditar={puedeEditar}
          rol={rol}
          ejecutar={ejecutar}
        />
      )}
      {cargado && seccion === "soportes" && (
        <SeccionActivos
          titulo="Soportes"
          tipos={["soporte_fisico", "soporte_digital"]}
          tipoNuevo={null}
          activos={activos}
          personas={personas}
          areas={areas}
          tratamientos={tratamientos}
          puedeEditar={puedeEditar}
          rol={rol}
          ejecutar={ejecutar}
        />
      )}
      {cargado && seccion === "personas" && (
        <SeccionPersonas personas={personas} areas={areas} puedeEditar={puedeEditar} rol={rol} ejecutar={ejecutar} />
      )}
    </div>
  );
}

interface PropsActivos {
  titulo: string;
  tipos: TipoActivo[];
  /** Tipo fijo de lo que se crea aquí; null = se elige (soportes). */
  tipoNuevo: TipoActivo | null;
  activos: Activo[];
  personas: PersonaInventario[];
  areas: AreaItem[];
  tratamientos: TratamientoVinculable[];
  puedeEditar: boolean;
  rol: OrganizacionRole;
  ejecutar: (accion: () => Promise<void>, manejarError?: (err: unknown) => boolean) => Promise<boolean>;
}

function SeccionActivos(p: PropsActivos) {
  const id = useId();
  const [tipo, setTipo] = useState<TipoActivo>(p.tipoNuevo ?? p.tipos[0]);
  const [borrador, setBorrador] = useState<BorradorActivo>(ACTIVO_VACIO);
  const [motivo, setMotivo] = useState<string | null>(null);
  const [abierto, setAbierto] = useState<string | null>(null);
  const propios = p.activos.filter((a) => p.tipos.includes(a.tipo));
  const nombreArea = (areaId: string | null) => p.areas.find((a) => a.id === areaId)?.nombre ?? null;
  const nombrePersona = (personaId: string | null) => p.personas.find((x) => x.id === personaId)?.nombre ?? null;
  const campo = (k: keyof BorradorActivo, v: string) => setBorrador((b) => ({ ...b, [k]: v }));

  const crear = async () => {
    const m = validarActivo(borrador);
    setMotivo(m);
    if (m) return;
    if (await p.ejecutar(() => inventarioApi.crearActivo(cuerpoActivo(tipo, borrador), p.rol))) setBorrador(ACTIVO_VACIO);
  };

  return (
    <section aria-label={p.titulo} className="space-y-3">
      {propios.length === 0 ? (
        <p className="text-sm">Todavía no hay elementos en esta sección.{p.puedeEditar ? " Usa «Agregar activo» para crear el primero." : ""}</p>
      ) : (
        <ul className="space-y-2">
          {propios.map((a) => (
            <li key={a.id} className="rounded-md border border-[var(--ui-borde)] p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold">
                    {a.nombre} <span className="font-normal text-[var(--ui-texto-suave)]">· {ETIQUETA_TIPO[a.tipo]}</span>
                    {a.archivado && <span className="ml-2 text-xs">(archivado)</span>}
                  </p>
                  <p className="text-xs text-[var(--ui-texto-suave)]">
                    {[nombreArea(a.area_id), nombrePersona(a.responsable_id) && `Responsable: ${nombrePersona(a.responsable_id)}`, a.ubicacion]
                      .filter(Boolean)
                      .join(" · ") || "Sin área, responsable ni ubicación"}
                  </p>
                  <p className="text-xs">Tratamientos vinculados: {a.tratamiento_ids.length}</p>
                </div>
                <div className="flex gap-2">
                  <button type="button" className={BOTON} aria-expanded={abierto === a.id} onClick={() => setAbierto(abierto === a.id ? null : a.id)}>
                    {abierto === a.id ? "Cerrar" : "Vincular tratamientos"}
                  </button>
                  {p.puedeEditar && (
                    <button
                      type="button"
                      className={BOTON}
                      onClick={() => void p.ejecutar(() => inventarioApi.editarActivo(a.id, { archivado: !a.archivado }, p.rol))}
                    >
                      {a.archivado ? `Restaurar ${a.nombre}` : `Archivar ${a.nombre}`}
                    </button>
                  )}
                </div>
              </div>
              {abierto === a.id && (
                <VinculosTratamientos activo={a} tratamientos={p.tratamientos} puedeEditar={p.puedeEditar} rol={p.rol} ejecutar={p.ejecutar} />
              )}
            </li>
          ))}
        </ul>
      )}
      {p.puedeEditar && (
        <form
          noValidate
          aria-label={`Agregar a ${p.titulo}`}
          className="grid gap-3 rounded-md border border-[var(--ui-borde)] p-3 sm:grid-cols-2"
          onSubmit={(e) => {
            e.preventDefault();
            void crear();
          }}
        >
          {p.tipoNuevo === null && (
            <div>
              <label htmlFor={`${id}-tipo`} className={ETIQUETA}>Tipo de soporte</label>
              <select id={`${id}-tipo`} className={CAMPO} value={tipo} onChange={(e) => setTipo(e.target.value as TipoActivo)}>
                {p.tipos.map((t) => (
                  <option key={t} value={t}>{ETIQUETA_TIPO[t]}</option>
                ))}
              </select>
            </div>
          )}
          <div>
            <label htmlFor={`${id}-nombre`} className={ETIQUETA}>Nombre</label>
            <input id={`${id}-nombre`} className={CAMPO} value={borrador.nombre} onChange={(e) => campo("nombre", e.target.value)} maxLength={200} />
          </div>
          <div>
            <label htmlFor={`${id}-ubicacion`} className={ETIQUETA}>Ubicación</label>
            <input id={`${id}-ubicacion`} className={CAMPO} value={borrador.ubicacion} onChange={(e) => campo("ubicacion", e.target.value)} maxLength={200} />
          </div>
          <div>
            <label htmlFor={`${id}-area`} className={ETIQUETA}>Área</label>
            <select id={`${id}-area`} className={CAMPO} value={borrador.areaId} onChange={(e) => campo("areaId", e.target.value)}>
              <option value="">Sin área</option>
              {p.areas.map((a) => (
                <option key={a.id} value={a.id}>{a.nombre}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor={`${id}-resp`} className={ETIQUETA}>Responsable</label>
            <select id={`${id}-resp`} className={CAMPO} value={borrador.responsableId} onChange={(e) => campo("responsableId", e.target.value)}>
              <option value="">Sin responsable</option>
              {p.personas.filter((x) => !x.archivada).map((x) => (
                <option key={x.id} value={x.id}>{x.nombre}</option>
              ))}
            </select>
          </div>
          <div className="sm:col-span-2">
            <label htmlFor={`${id}-desc`} className={ETIQUETA}>Descripción</label>
            <textarea id={`${id}-desc`} className={CAMPO} rows={2} value={borrador.descripcion} onChange={(e) => campo("descripcion", e.target.value)} maxLength={1000} />
          </div>
          {motivo && <p role="alert" className="text-sm sm:col-span-2">{motivo}</p>}
          <div className="sm:col-span-2">
            <button type="submit" className={BOTON}>Agregar activo</button>
          </div>
        </form>
      )}
    </section>
  );
}

function VinculosTratamientos(p: {
  activo: Activo;
  tratamientos: TratamientoVinculable[];
  puedeEditar: boolean;
  rol: OrganizacionRole;
  ejecutar: (accion: () => Promise<void>, manejarError?: (err: unknown) => boolean) => Promise<boolean>;
}) {
  const [elegidos, setElegidos] = useState<string[]>(p.activo.tratamiento_ids);
  if (p.tratamientos.length === 0) return <p className="mt-2 text-sm">Todavía no hay tratamientos en el registro de tratamientos para vincular.</p>;
  const alternar = (id: string) => setElegidos((e) => (e.includes(id) ? e.filter((x) => x !== id) : [...e, id]));
  return (
    <fieldset className="mt-2 space-y-1" disabled={!p.puedeEditar}>
      <legend className="text-xs font-semibold">Tratamientos del registro que usan este elemento</legend>
      {p.tratamientos.map((t) => (
        <label key={t.id} className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={elegidos.includes(t.id)} onChange={() => alternar(t.id)} />
          {t.codigo} · {t.nombre}
        </label>
      ))}
      {p.puedeEditar && (
        <button type="button" className={BOTON} onClick={() => void p.ejecutar(() => inventarioApi.vincularTratamientos(p.activo.id, elegidos, p.rol))}>
          Guardar vínculos
        </button>
      )}
    </fieldset>
  );
}

function SeccionPersonas(p: {
  personas: PersonaInventario[];
  areas: AreaItem[];
  puedeEditar: boolean;
  rol: OrganizacionRole;
  ejecutar: (accion: () => Promise<void>, manejarError?: (err: unknown) => boolean) => Promise<boolean>;
}) {
  const id = useId();
  const [borrador, setBorrador] = useState<BorradorPersonaInventario>(PERSONA_VACIA);
  const [motivo, setMotivo] = useState<string | null>(null);
  const [errorCedula, setErrorCedula] = useState<string | null>(null);
  const campo = (k: keyof BorradorPersonaInventario, v: string) => setBorrador((b) => ({ ...b, [k]: v }));
  const nombreArea = (areaId: string | null) => p.areas.find((a) => a.id === areaId)?.nombre ?? null;

  const crear = async (sinCedula = false) => {
    const datos = sinCedula ? { ...borrador, cedula: "" } : borrador;
    if (sinCedula) campo("cedula", "");
    const m = validarPersona(datos);
    const cedulaMala = m === "La cédula debe tener 10 dígitos.";
    setMotivo(cedulaMala ? null : m);
    setErrorCedula(cedulaMala ? m : null);
    if (m) return;
    const guardada = await p.ejecutar(
      () => inventarioApi.crearPersona(cuerpoPersona(datos), p.rol),
      (err) => {
        if (err instanceof ApiError && err.code === "INVENTARIO_CIFRADO_NO_CONFIGURADO") {
          setErrorCedula(MENSAJE_CEDULA_NO_GUARDADA);
          return true;
        }
        return false;
      },
    );
    if (guardada) {
      setBorrador(PERSONA_VACIA);
      setErrorCedula(null);
    }
  };

  return (
    <section aria-label="Personas" className="space-y-3">
      {p.personas.length === 0 ? (
        <p className="text-sm">Todavía no hay personas registradas.</p>
      ) : (
        <ul className="space-y-2">
          {p.personas.map((x) => (
            <li key={x.id} className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-[var(--ui-borde)] p-3">
              <div>
                <p className="text-sm font-semibold">
                  {x.nombre} <span className="font-normal text-[var(--ui-texto-suave)]">· {x.cargo}</span>
                  {x.archivada && <span className="ml-2 text-xs">(archivada)</span>}
                </p>
                <p className="text-xs text-[var(--ui-texto-suave)]">
                  {[nombreArea(x.area_id), x.email, x.tiene_cedula ? "Cédula guardada" : null].filter(Boolean).join(" · ")}
                </p>
              </div>
              {p.puedeEditar && (
                <button
                  type="button"
                  className={BOTON}
                  onClick={() => void p.ejecutar(() => inventarioApi.editarPersona(x.id, { archivada: !x.archivada }, p.rol))}
                >
                  {x.archivada ? `Restaurar ${x.nombre}` : `Archivar ${x.nombre}`}
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
      {p.puedeEditar && (
        <form
          noValidate
          aria-label="Agregar persona"
          className="grid gap-3 rounded-md border border-[var(--ui-borde)] p-3 sm:grid-cols-2"
          onSubmit={(e) => {
            e.preventDefault();
            void crear();
          }}
        >
          <div>
            <label htmlFor={`${id}-nombre`} className={ETIQUETA}>Nombre</label>
            <input id={`${id}-nombre`} className={CAMPO} value={borrador.nombre} onChange={(e) => campo("nombre", e.target.value)} maxLength={200} />
          </div>
          <div>
            <label htmlFor={`${id}-cargo`} className={ETIQUETA}>Cargo</label>
            <input id={`${id}-cargo`} className={CAMPO} value={borrador.cargo} onChange={(e) => campo("cargo", e.target.value)} maxLength={150} />
          </div>
          <div>
            <label htmlFor={`${id}-correo`} className={ETIQUETA}>Correo</label>
            <input id={`${id}-correo`} type="email" className={CAMPO} value={borrador.email} onChange={(e) => campo("email", e.target.value)} maxLength={254} />
          </div>
          <div>
            <label htmlFor={`${id}-area`} className={ETIQUETA}>Área</label>
            <select id={`${id}-area`} className={CAMPO} value={borrador.areaId} onChange={(e) => campo("areaId", e.target.value)}>
              <option value="">Sin área</option>
              {p.areas.map((a) => (
                <option key={a.id} value={a.id}>{a.nombre}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor={`${id}-cedula`} className={ETIQUETA}>Cédula (solo si la firma la exige)</label>
            <input
              id={`${id}-cedula`}
              inputMode="numeric"
              pattern="[0-9]{10}"
              className={CAMPO}
              value={borrador.cedula}
              onChange={(e) => campo("cedula", e.target.value)}
              maxLength={10}
              autoComplete="off"
              aria-invalid={errorCedula ? true : undefined}
              aria-describedby={`${id}-cedula-ayuda${errorCedula ? ` ${id}-cedula-error` : ""}`}
            />
            <p id={`${id}-cedula-ayuda`} className="mt-1 text-xs text-[var(--ui-texto-suave)]">
              Se guarda cifrada y no se vuelve a mostrar. Solo se pide si la firma electrónica la exige.
            </p>
            {errorCedula && (
              <p id={`${id}-cedula-error`} role="alert" className="mt-1 text-sm">{errorCedula}</p>
            )}
          </div>
          {motivo && <p role="alert" className="text-sm sm:col-span-2">{motivo}</p>}
          <div className="sm:col-span-2">
            <button type="submit" className={BOTON}>Agregar persona</button>
            {errorCedula === MENSAJE_CEDULA_NO_GUARDADA && (
              <button type="button" className={`${BOTON} ml-2`} onClick={() => void crear(true)}>Guardar sin cédula</button>
            )}
          </div>
        </form>
      )}
    </section>
  );
}
