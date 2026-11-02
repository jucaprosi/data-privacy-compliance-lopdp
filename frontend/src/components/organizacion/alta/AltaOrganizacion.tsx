"use client";
// ¤asistente ¤frontend-ide ¤alta-organizacion
// Alta de la organización en siete pasos (ORG-16) sobre el patrón único de asistente (FE-23).
// Cada paso se guarda en el servidor al terminarlo; el progreso sale de GET /organizacion/alta, no de
// ningún estado local. Contrato: governance/especificaciones/ORG-16.md.
import React, { useCallback, useEffect, useId, useState } from "react";
import { ClipboardList } from "lucide-react";
import { Asistente, type PasoAsistente } from "@/components/asistente";
import { organizacionApi } from "@/lib/roadmap/cliente";
import {
  ETIQUETA_NATURALEZA,
  ETIQUETA_ROL_DATOS,
  ETIQUETA_ROL_PERSONA,
  ETIQUETA_TAMANO,
  NATURALEZAS,
  PASOS_ALTA,
  PASOS_OBLIGATORIOS,
  ROLES_DATOS,
  ROLES_PERSONA,
  TAMANOS,
  TITULOS_PASO,
  altaApi,
  cuerposAlta,
  validarAreas,
  validarPerfil,
  validarPersonas,
  validarSedes,
  type BorradorArea,
  type BorradorPerfil,
  type BorradorPersona,
  type BorradorSedes,
  type EstadoAlta,
  type PasoAlta,
  type Sugerencias,
} from "@/lib/organizacion/alta";
import type { AreaItem, OrganizacionRole } from "@/types/roadmap";

type Estado =
  | { fase: "cargando" }
  | { fase: "lista"; estado: EstadoAlta }
  | { fase: "error"; mensaje: string };

interface Props {
  /** Rol con el que se consulta y, si puede escribir, se guarda. */
  rol: OrganizacionRole;
  /** Solo admin_organizacion e implementador inician el alta; los demás ven el estado sin botones. */
  puedeEditar: boolean;
  className?: string;
}

const CAMPO =
  "w-full rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-1.5 text-sm text-[var(--ui-texto)]";
const ETIQUETA = "mb-1 block text-xs font-semibold text-[var(--ui-texto-suave)]";

const PERFIL_VACIO: BorradorPerfil = {
  razonSocial: "",
  ruc: "",
  sector: "",
  tamano: "",
  naturaleza: "",
  rolDatos: "",
  actividadesRiesgo: "",
};
const SEDES_VACIAS: BorradorSedes = { domicilio: "", ciudad: "", provincia: "" };
const PERSONA_VACIA: BorradorPersona = { nombre: "", cargo: "", email: "", rol: "coordinador", areaId: "" };

/** Primer paso sin completar, para retomar el alta donde quedó. */
function pasoInicialDe(estado: EstadoAlta): number {
  const indice = estado.pasos.findIndex((p) => !p.completo && p.id !== "resumen");
  return indice === -1 ? PASOS_ALTA.length - 1 : indice;
}

export default function AltaOrganizacion({ rol, puedeEditar, className = "" }: Props) {
  const idBase = useId();
  const [estado, setEstado] = useState<Estado>({ fase: "cargando" });
  const [abierto, setAbierto] = useState(false);
  const [perfil, setPerfil] = useState<BorradorPerfil>(PERFIL_VACIO);
  const [sedes, setSedes] = useState<BorradorSedes>(SEDES_VACIAS);
  const [areas, setAreas] = useState<BorradorArea[]>([{ nombre: "", codigo: "" }]);
  const [aceptados, setAceptados] = useState<number[]>([]);
  const [personas, setPersonas] = useState<BorradorPersona[]>([]);
  const [sugerencias, setSugerencias] = useState<Sugerencias>({ tratamientos: [], terceros: [] });
  const [areasDelServidor, setAreasDelServidor] = useState<AreaItem[]>([]);

  const cargar = useCallback(async () => {
    try {
      setEstado({ fase: "lista", estado: await altaApi.estado(rol) });
    } catch (err: unknown) {
      setEstado({
        fase: "error",
        mensaje: err instanceof Error ? err.message : "No se pudo consultar el alta de la organización.",
      });
    }
  }, [rol]);

  useEffect(() => {
    setEstado({ fase: "cargando" });
    void cargar();
  }, [cargar]);

  const cargarApoyos = useCallback(async () => {
    const [sug, lista] = await Promise.allSettled([
      altaApi.sugerencias(rol),
      organizacionApi.listAreas({ headers: { "X-Role": rol } }),
    ]);
    if (sug.status === "fulfilled") setSugerencias(sug.value);
    if (lista.status === "fulfilled") setAreasDelServidor(lista.value);
  }, [rol]);

  useEffect(() => {
    if (abierto) void cargarApoyos();
  }, [abierto, cargarApoyos]);

  const alternarTratamiento = (indice: number) =>
    setAceptados((previos) => (previos.includes(indice) ? previos.filter((i) => i !== indice) : [...previos, indice]));

  const pasos: PasoAsistente[] = [
    {
      id: "perfil",
      titulo: TITULOS_PASO.perfil,
      opcional: false,
      validar: () => validarPerfil(perfil),
      contenido: (
        <div className="grid gap-3 md:grid-cols-2">
          <div className="md:col-span-2">
            <label htmlFor={`${idBase}-razon`} className={ETIQUETA}>Razón social</label>
            <input id={`${idBase}-razon`} className={CAMPO} value={perfil.razonSocial} maxLength={255}
              onChange={(e) => setPerfil({ ...perfil, razonSocial: e.target.value })} />
          </div>
          <div>
            <label htmlFor={`${idBase}-ruc`} className={ETIQUETA}>RUC</label>
            <input id={`${idBase}-ruc`} className={CAMPO} value={perfil.ruc} inputMode="numeric" maxLength={13}
              onChange={(e) => setPerfil({ ...perfil, ruc: e.target.value })} />
          </div>
          <div>
            <label htmlFor={`${idBase}-sector`} className={ETIQUETA}>Sector</label>
            <input id={`${idBase}-sector`} className={CAMPO} value={perfil.sector} maxLength={100}
              onChange={(e) => setPerfil({ ...perfil, sector: e.target.value })} />
          </div>
          <div>
            <label htmlFor={`${idBase}-tamano`} className={ETIQUETA}>Tamaño</label>
            <select id={`${idBase}-tamano`} className={CAMPO} value={perfil.tamano}
              onChange={(e) => setPerfil({ ...perfil, tamano: e.target.value })}>
              <option value="">Elige una opción</option>
              {TAMANOS.map((t) => <option key={t} value={t}>{ETIQUETA_TAMANO[t]}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor={`${idBase}-naturaleza`} className={ETIQUETA}>Naturaleza</label>
            <select id={`${idBase}-naturaleza`} className={CAMPO} value={perfil.naturaleza}
              onChange={(e) => setPerfil({ ...perfil, naturaleza: e.target.value })}>
              <option value="">Elige una opción</option>
              {NATURALEZAS.map((n) => <option key={n} value={n}>{ETIQUETA_NATURALEZA[n]}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor={`${idBase}-rol-datos`} className={ETIQUETA}>Rol frente a los datos</label>
            <select id={`${idBase}-rol-datos`} className={CAMPO} value={perfil.rolDatos}
              onChange={(e) => setPerfil({ ...perfil, rolDatos: e.target.value })}>
              <option value="">Elige una opción</option>
              {ROLES_DATOS.map((r) => <option key={r} value={r}>{ETIQUETA_ROL_DATOS[r]}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor={`${idBase}-riesgo`} className={ETIQUETA}>Actividades de riesgo (separadas por coma)</label>
            <input id={`${idBase}-riesgo`} className={CAMPO} value={perfil.actividadesRiesgo}
              onChange={(e) => setPerfil({ ...perfil, actividadesRiesgo: e.target.value })} />
          </div>
        </div>
      ),
    },
    {
      id: "sedes",
      titulo: TITULOS_PASO.sedes,
      opcional: true,
      validar: () => validarSedes(sedes),
      contenido: (
        <div className="grid gap-3 md:grid-cols-2">
          <div className="md:col-span-2">
            <label htmlFor={`${idBase}-domicilio`} className={ETIQUETA}>Domicilio principal</label>
            <input id={`${idBase}-domicilio`} className={CAMPO} value={sedes.domicilio} maxLength={300}
              onChange={(e) => setSedes({ ...sedes, domicilio: e.target.value })} />
          </div>
          <div>
            <label htmlFor={`${idBase}-ciudad`} className={ETIQUETA}>Ciudad</label>
            <input id={`${idBase}-ciudad`} className={CAMPO} value={sedes.ciudad} maxLength={120}
              onChange={(e) => setSedes({ ...sedes, ciudad: e.target.value })} />
          </div>
          <div>
            <label htmlFor={`${idBase}-provincia`} className={ETIQUETA}>Provincia</label>
            <input id={`${idBase}-provincia`} className={CAMPO} value={sedes.provincia} maxLength={120}
              onChange={(e) => setSedes({ ...sedes, provincia: e.target.value })} />
          </div>
        </div>
      ),
    },
    {
      id: "areas",
      titulo: TITULOS_PASO.areas,
      opcional: false,
      validar: () => validarAreas(areas),
      contenido: (
        <div className="flex flex-col gap-2">
          {areas.map((area, i) => (
            <div key={i} className="grid gap-2 md:grid-cols-[1fr_8rem_auto]">
              <input aria-label={`Nombre del área ${i + 1}`} className={CAMPO} value={area.nombre} maxLength={255}
                onChange={(e) => setAreas(areas.map((a, j) => (j === i ? { ...a, nombre: e.target.value } : a)))} />
              <input aria-label={`Código del área ${i + 1}`} placeholder="Código" className={CAMPO} value={area.codigo} maxLength={50}
                onChange={(e) => setAreas(areas.map((a, j) => (j === i ? { ...a, codigo: e.target.value } : a)))} />
              <button type="button" disabled={areas.length === 1}
                onClick={() => setAreas(areas.filter((_, j) => j !== i))}
                className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 text-sm hover:bg-[var(--ui-boton-hover)] disabled:opacity-50">
                Quitar
              </button>
            </div>
          ))}
          <button type="button" onClick={() => setAreas([...areas, { nombre: "", codigo: "" }])}
            className="self-start rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 text-sm hover:bg-[var(--ui-boton-hover)]">
            Agregar área
          </button>
        </div>
      ),
    },
    {
      id: "tratamientos",
      titulo: TITULOS_PASO.tratamientos,
      opcional: true,
      validar: () => (aceptados.length === 0 ? "Elige al menos un tratamiento o salta este paso." : null),
      contenido:
        sugerencias.tratamientos.length === 0 ? (
          <p className="text-sm text-[var(--ui-texto-suave)]">
            No hay sugerencias: completa el perfil con el sector de la organización o salta este paso.
          </p>
        ) : (
          <fieldset className="flex flex-col gap-2">
            <legend className="mb-1 text-xs text-[var(--ui-texto-suave)]">
              Son modelos de estructura del sector; los revisas luego en el registro de tratamientos.
            </legend>
            {sugerencias.tratamientos.map((t) => (
              <label key={t.indice} className="flex items-start gap-2 text-sm">
                <input type="checkbox" checked={aceptados.includes(t.indice)} onChange={() => alternarTratamiento(t.indice)} />
                <span><strong>{t.nombre}</strong> · {t.finalidad}</span>
              </label>
            ))}
          </fieldset>
        ),
    },
    {
      id: "terceros",
      titulo: TITULOS_PASO.terceros,
      opcional: true,
      // El servidor aún no guarda este paso (PASO_NO_DISPONIBLE): solo se puede saltar.
      validar: () => "Este paso aún no se guarda en el servidor; usa «Saltar».",
      contenido: (
        <div className="flex flex-col gap-2 text-sm">
          <p className="text-[var(--ui-texto-suave)]">
            Tipos de terceros frecuentes en el sector. Su registro se hará desde Encargados y terceros.
          </p>
          <ul className="list-disc pl-5">
            {sugerencias.terceros.map((t) => (
              <li key={t.indice}><strong>{t.tipo}</strong> · {t.descripcion}</li>
            ))}
          </ul>
        </div>
      ),
    },
    {
      id: "personas",
      titulo: TITULOS_PASO.personas,
      opcional: true,
      validar: () => validarPersonas(personas),
      contenido: (
        <div className="flex flex-col gap-3">
          <p className="text-xs text-[var(--ui-texto-suave)]">
            Solo nombre, cargo, área y correo. No se pide cédula ni otro dato de identificación.
          </p>
          {personas.map((p, i) => (
            <div key={i} className="grid gap-2 rounded-md border border-[var(--ui-borde)] p-2 md:grid-cols-2">
              <input aria-label={`Nombre de la persona ${i + 1}`} placeholder="Nombre" className={CAMPO} value={p.nombre} maxLength={200}
                onChange={(e) => setPersonas(personas.map((x, j) => (j === i ? { ...x, nombre: e.target.value } : x)))} />
              <input aria-label={`Cargo de la persona ${i + 1}`} placeholder="Cargo" className={CAMPO} value={p.cargo} maxLength={150}
                onChange={(e) => setPersonas(personas.map((x, j) => (j === i ? { ...x, cargo: e.target.value } : x)))} />
              <input aria-label={`Correo de la persona ${i + 1}`} placeholder="Correo" type="email" className={CAMPO} value={p.email} maxLength={254}
                onChange={(e) => setPersonas(personas.map((x, j) => (j === i ? { ...x, email: e.target.value } : x)))} />
              <select aria-label={`Rol propuesto de la persona ${i + 1}`} className={CAMPO} value={p.rol}
                onChange={(e) => setPersonas(personas.map((x, j) => (j === i ? { ...x, rol: e.target.value } : x)))}>
                {ROLES_PERSONA.map((r) => <option key={r} value={r}>{ETIQUETA_ROL_PERSONA[r]}</option>)}
              </select>
              <select aria-label={`Área de la persona ${i + 1}`} className={CAMPO} value={p.areaId}
                onChange={(e) => setPersonas(personas.map((x, j) => (j === i ? { ...x, areaId: e.target.value } : x)))}>
                <option value="">Sin área</option>
                {areasDelServidor.map((a) => <option key={a.id} value={a.id}>{a.nombre}</option>)}
              </select>
              <button type="button" onClick={() => setPersonas(personas.filter((_, j) => j !== i))}
                className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 text-sm hover:bg-[var(--ui-boton-hover)]">
                Quitar
              </button>
            </div>
          ))}
          <button type="button" onClick={() => setPersonas([...personas, { ...PERSONA_VACIA }])}
            className="self-start rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 text-sm hover:bg-[var(--ui-boton-hover)]">
            Agregar persona
          </button>
        </div>
      ),
    },
    {
      id: "resumen",
      titulo: TITULOS_PASO.resumen,
      opcional: false,
      validar: () => null,
      contenido: (
        <ul className="flex flex-col gap-1 text-sm">
          {estado.fase === "lista" &&
            estado.estado.pasos
              .filter((p) => p.id !== "resumen")
              .map((p) => (
                <li key={p.id}>
                  {TITULOS_PASO[p.id]}: {p.completo ? "completo" : PASOS_OBLIGATORIOS.has(p.id) ? "falta (obligatorio)" : "pendiente"}
                </li>
              ))}
        </ul>
      ),
    },
  ];

  const guardar = async (pasoId: string) => {
    const id = pasoId as PasoAlta;
    const cuerpos: Record<PasoAlta, object> = {
      perfil: cuerposAlta.perfil(perfil),
      sedes: cuerposAlta.sedes(sedes),
      areas: cuerposAlta.areas(areas),
      tratamientos: cuerposAlta.tratamientos(aceptados),
      terceros: {},
      personas: cuerposAlta.personas(personas),
      resumen: cuerposAlta.resumen(),
    };
    await altaApi.guardarPaso(id, cuerpos[id], rol);
    // El estado vuelve a leerse del servidor; el resumen y los apoyos dependen de lo ya guardado.
    await cargar();
    if (id === "perfil" || id === "areas") await cargarApoyos();
  };

  return (
    <section data-testid="alta-organizacion" aria-label="Alta de la organización"
      className={`rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4 ${className}`}>
      <header className="mb-3 flex items-center gap-2">
        <ClipboardList size={16} aria-hidden="true" />
        <h3 className="text-sm font-bold">Alta de la organización</h3>
      </header>

      {estado.fase === "cargando" && <p role="status" className="text-sm">Consultando el alta…</p>}
      {estado.fase === "error" && <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">{estado.mensaje}</p>}

      {estado.fase === "lista" && (
        <>
          <p data-testid="alta-estado" className="mb-2 text-sm">
            {estado.estado.completo
              ? "Alta completa: perfil y áreas registrados en el servidor."
              : "Alta pendiente: faltan el perfil o las áreas, que son obligatorios."}
          </p>
          <ul className="mb-3 grid gap-1 text-sm md:grid-cols-2">
            {estado.estado.pasos.filter((p) => p.id !== "resumen").map((p) => (
              <li key={p.id} data-testid={`alta-paso-${p.id}`} data-completo={p.completo}>
                {TITULOS_PASO[p.id]}: {p.completo ? "completo" : "pendiente"}
              </li>
            ))}
          </ul>

          {!puedeEditar && (
            <p className="text-xs text-[var(--ui-texto-suave)]">
              Tu rol consulta el estado del alta; la completan la administración de la organización o quien implementa.
            </p>
          )}
          {puedeEditar && !abierto && (
            <button type="button" onClick={() => setAbierto(true)}
              className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 text-sm hover:bg-[var(--ui-boton-hover)]">
              {estado.estado.pasos.some((p) => p.completo) ? "Continuar el alta" : "Iniciar el alta"}
            </button>
          )}
          {puedeEditar && abierto && (
            <Asistente
              pasos={pasos}
              guardar={guardar}
              pasoInicial={pasoInicialDe(estado.estado)}
              alTerminar={() => setAbierto(false)}
            />
          )}
        </>
      )}
    </section>
  );
}
