"use client";

/**
 * Playbook de incidentes y bitácora de la organización (INC-01).
 *
 * Lee y registra en el servidor (api/routers/incidentes.py). Registran el administrador, el
 * coordinador, los responsables de área y el implementador; el DPO consulta. Un incidente
 * registrado no se edita ni se borra. No se calcula ningún plazo legal: los plazos de notificación
 * siguen aplazados (LEG-02); solo se muestra el tiempo transcurrido desde la detección.
 */
import React, { useCallback, useEffect, useState } from "react";
import { AlertTriangle, Plus, RefreshCw, Search, ShieldCheck } from "lucide-react";
import { consultarBitacora, registrarIncidente } from "@/lib/incidentes/cliente";
import { ROLES_QUE_CONSULTAN, ROLES_QUE_REGISTRAN, rolEntre, rolesDelUsuario } from "@/lib/incidentes/roles";
import {
  SEVERIDADES_INCIDENTE,
  type BitacoraIncidentes,
  type Incidente,
  type SeveridadIncidente,
} from "@/types/incidente";

const CATEGORIAS_DATOS = [
  "Identificativos (Cédula / Nombres)",
  "Contacto (Email / Teléfono)",
  "Financieros / Bancarios",
  "Datos de Salud / Sensibles",
  "Biométricos",
  "Credenciales de Acceso",
] as const;

const CLASE_SEVERIDAD: Record<SeveridadIncidente, string> = {
  Baja: "border border-[var(--ui-borde)] bg-[var(--ui-boton)]",
  Media: "badge-render-warning",
  Alta: "badge-render-danger",
  Crítica: "badge-render-danger",
};

const CAMPO =
  "w-full px-3 py-2 text-xs bg-[var(--ui-campo)] border border-[var(--ui-borde)] rounded-lg focus:outline-none focus:border-[var(--ui-primario)]";

function ahoraLocal(): string {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}

function formatearFecha(iso: string): string {
  try {
    return new Intl.DateTimeFormat("es-EC", { dateStyle: "medium", timeStyle: "short" }).format(new Date(iso));
  } catch {
    return iso;
  }
}

/** Tiempo transcurrido desde la detección. No es un plazo legal. */
function transcurrido(desdeIso: string, ahora: number): string {
  const minutos = Math.max(0, Math.floor((ahora - new Date(desdeIso).getTime()) / 60000));
  const dias = Math.floor(minutos / 1440);
  const horas = Math.floor((minutos % 1440) / 60);
  const resto = minutos % 60;
  if (dias > 0) return `${dias} d ${horas} h`;
  if (horas > 0) return `${horas} h ${resto} min`;
  return `${resto} min`;
}

export default function IncidentPlaybook() {
  const [roles, setRoles] = useState<string[] | null>(null);
  const [bitacora, setBitacora] = useState<BitacoraIncidentes | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [busqueda, setBusqueda] = useState("");
  const [filtroSeveridad, setFiltroSeveridad] = useState<"TODAS" | SeveridadIncidente>("TODAS");
  const [ahora, setAhora] = useState(() => Date.now());

  const [fechaDeteccion, setFechaDeteccion] = useState(ahoraLocal);
  const [titulo, setTitulo] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [severidad, setSeveridad] = useState<SeveridadIncidente>("Alta");
  const [afectaDatos, setAfectaDatos] = useState(true);
  const [categorias, setCategorias] = useState<string[]>([]);
  const [medidas, setMedidas] = useState("");

  const rolConsulta = roles ? rolEntre(roles, ROLES_QUE_CONSULTAN) : null;
  const rolRegistro = roles ? rolEntre(roles, ROLES_QUE_REGISTRAN) : null;

  const cargar = useCallback(async (rol: string) => {
    setCargando(true);
    setError(null);
    try {
      setBitacora(await consultarBitacora(rol));
    } catch (err) {
      setBitacora(null);
      setError(err instanceof Error ? err.message : "No se pudo leer la bitácora de incidentes.");
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    let vigente = true;
    rolesDelUsuario().then((r) => {
      if (!vigente) return;
      setRoles(r);
      const rol = rolEntre(r, ROLES_QUE_CONSULTAN);
      if (rol) void cargar(rol);
    });
    return () => {
      vigente = false;
    };
  }, [cargar]);

  // El tiempo transcurrido se refresca cada minuto.
  useEffect(() => {
    const reloj = setInterval(() => setAhora(Date.now()), 60_000);
    return () => clearInterval(reloj);
  }, []);

  const alternarCategoria = (categoria: string) =>
    setCategorias((actuales) =>
      actuales.includes(categoria) ? actuales.filter((c) => c !== categoria) : [...actuales, categoria]
    );

  const registrar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rolRegistro) return;
    setEnviando(true);
    setError(null);
    setAviso(null);
    try {
      const registrado = await registrarIncidente(rolRegistro, {
        fecha_deteccion: new Date(fechaDeteccion).toISOString(),
        titulo: titulo.trim(),
        descripcion: descripcion.trim(),
        severidad,
        afecta_datos_personales: afectaDatos,
        categorias_datos: afectaDatos ? categorias : [],
        medidas_inmediatas: medidas.trim(),
      });
      setAviso(`Incidente n.º ${registrado.secuencia} registrado. Ya no se puede editar ni borrar.`);
      setTitulo("");
      setDescripcion("");
      setMedidas("");
      setCategorias([]);
      setFechaDeteccion(ahoraLocal());
      setMostrarFormulario(false);
      if (rolConsulta) await cargar(rolConsulta);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo registrar el incidente.");
    } finally {
      setEnviando(false);
    }
  };

  const incidentes = bitacora?.incidentes ?? [];
  const termino = busqueda.trim().toLowerCase();
  const filtrados = incidentes.filter(
    (i) =>
      (filtroSeveridad === "TODAS" || i.severidad === filtroSeveridad) &&
      (!termino || i.titulo.toLowerCase().includes(termino) || i.huella.includes(termino))
  );
  const alterado = bitacora && !bitacora.cadena_integra
    ? incidentes.find((i) => i.id === bitacora.primer_alterado)
    : undefined;

  return (
    <section aria-labelledby="incidentes-titulo" className="max-w-5xl mx-auto space-y-4 font-sans pb-12">
      <div className="p-5 rounded-xl bg-[var(--ui-superficie)] border border-[var(--ui-borde)] flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <h1 id="incidentes-titulo" className="text-base font-bold tracking-tight">
            Playbook de incidentes y bitácora
          </h1>
          <p className="text-xs text-[var(--ui-texto-suave)] mt-0.5">
            Registro de los incidentes de seguridad de la organización. Un incidente registrado no se puede editar ni
            borrar.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => rolConsulta && void cargar(rolConsulta)}
            disabled={cargando || !rolConsulta}
            aria-label="Actualizar la bitácora"
            className="p-2 rounded-lg bg-[var(--ui-boton)] hover:bg-[var(--ui-boton-hover)] border border-[var(--ui-borde)] cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${cargando ? "animate-spin" : ""}`} />
          </button>
          {rolRegistro && (
            <button
              type="button"
              onClick={() => setMostrarFormulario((v) => !v)}
              className="px-4 py-2 rounded-lg bg-[var(--ui-primario)] hover:bg-[var(--ui-primario-hover)] text-[var(--ui-primario-texto)] text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>{mostrarFormulario ? "Cerrar el reporte" : "Reportar vulneración"}</span>
            </button>
          )}
        </div>
      </div>

      <p role="note" className="p-3 rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] text-xs leading-relaxed">
        Los plazos de notificación a la Superintendencia y a los titulares todavía no se calculan en la plataforma: se
        incorporarán en una tarea propia. Esta bitácora solo muestra el tiempo transcurrido desde la detección.
      </p>

      {roles !== null && rolConsulta && !rolRegistro && (
        <p role="status" className="p-3 rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] text-xs">
          Modo lectura: su rol consulta la bitácora. Registran el administrador, el coordinador, los responsables de área
          y el implementador.
        </p>
      )}

      {roles !== null && !rolConsulta && (
        <p role="alert" className="badge-render-danger p-3 rounded-lg text-xs">
          Su rol no consulta la bitácora de incidentes de la organización.
        </p>
      )}

      {aviso && (
        <p role="status" className="badge-render-success p-3 rounded-lg text-xs flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 shrink-0" />
          <span>{aviso}</span>
        </p>
      )}

      {error && (
        <p role="alert" className="badge-render-danger p-3 rounded-lg text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </p>
      )}

      {mostrarFormulario && rolRegistro && (
        <form
          onSubmit={registrar}
          aria-label="Reportar vulneración"
          className="p-5 rounded-xl bg-[var(--ui-superficie)] border border-[var(--ui-borde)] space-y-4"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label htmlFor="incidente-titulo" className="text-xs font-semibold">
                Título del incidente
              </label>
              <input
                id="incidente-titulo"
                type="text"
                required
                maxLength={200}
                value={titulo}
                onChange={(e) => setTitulo(e.target.value)}
                className={CAMPO}
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="incidente-deteccion" className="text-xs font-semibold">
                Fecha y hora de detección
              </label>
              <input
                id="incidente-deteccion"
                type="datetime-local"
                required
                max={ahoraLocal()}
                value={fechaDeteccion}
                onChange={(e) => setFechaDeteccion(e.target.value)}
                className={CAMPO}
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="incidente-severidad" className="text-xs font-semibold">
                Severidad
              </label>
              <select
                id="incidente-severidad"
                value={severidad}
                onChange={(e) => setSeveridad(e.target.value as SeveridadIncidente)}
                className={CAMPO}
              >
                {SEVERIDADES_INCIDENTE.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2 pt-5">
              <input
                id="incidente-afecta-datos"
                type="checkbox"
                checked={afectaDatos}
                onChange={(e) => setAfectaDatos(e.target.checked)}
              />
              <label htmlFor="incidente-afecta-datos" className="text-xs font-semibold">
                Afecta datos personales
              </label>
            </div>
          </div>

          {afectaDatos && (
            <fieldset className="space-y-2">
              <legend className="text-xs font-semibold">Categorías de datos afectados</legend>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {CATEGORIAS_DATOS.map((categoria) => (
                  <label key={categoria} className="flex items-center gap-2 text-xs">
                    <input
                      type="checkbox"
                      checked={categorias.includes(categoria)}
                      onChange={() => alternarCategoria(categoria)}
                    />
                    <span>{categoria}</span>
                  </label>
                ))}
              </div>
            </fieldset>
          )}

          <div className="space-y-1.5">
            <label htmlFor="incidente-descripcion" className="text-xs font-semibold">
              Descripción
            </label>
            <textarea
              id="incidente-descripcion"
              rows={3}
              maxLength={4000}
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              className={CAMPO}
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor="incidente-medidas" className="text-xs font-semibold">
              Medidas inmediatas de contención
            </label>
            <textarea
              id="incidente-medidas"
              rows={2}
              maxLength={4000}
              value={medidas}
              onChange={(e) => setMedidas(e.target.value)}
              className={CAMPO}
            />
          </div>
          <p className="text-[11px] text-[var(--ui-texto-suave)]">
            Quién registra y la hora de registro los pone el servidor con su sesión.
          </p>
          <button
            type="submit"
            disabled={enviando}
            className="px-4 py-2 rounded-lg bg-[var(--ui-primario)] hover:bg-[var(--ui-primario-hover)] text-[var(--ui-primario-texto)] text-xs font-semibold cursor-pointer disabled:opacity-50"
          >
            {enviando ? "Registrando…" : "Registrar incidente"}
          </button>
        </form>
      )}

      {bitacora && !bitacora.cadena_integra && (
        <p role="alert" className="badge-render-danger p-3 rounded-lg text-xs">
          La cadena de huellas no cuadra{alterado ? ` desde el incidente n.º ${alterado.secuencia}` : ""}: un registro
          se modificó fuera de la plataforma.
        </p>
      )}

      {bitacora && (
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--ui-texto-suave)]" />
            <input
              type="search"
              aria-label="Buscar incidentes por título o código de verificación"
              placeholder="Buscar por título o código de verificación"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              className={`${CAMPO} pl-8`}
            />
          </div>
          <select
            aria-label="Filtrar por severidad"
            value={filtroSeveridad}
            onChange={(e) => setFiltroSeveridad(e.target.value as "TODAS" | SeveridadIncidente)}
            className={`${CAMPO} sm:w-48`}
          >
            <option value="TODAS">Todas las severidades</option>
            {SEVERIDADES_INCIDENTE.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
      )}

      {bitacora && incidentes.length === 0 && (
        <p className="p-4 rounded-lg bg-[var(--ui-campo)] border border-[var(--ui-borde)] text-xs text-[var(--ui-texto-suave)]">
          Todavía no hay incidentes registrados en esta organización.
        </p>
      )}

      {filtrados.length > 0 && (
        <ul aria-label="Bitácora de incidentes" className="space-y-2.5">
          {filtrados.map((i: Incidente) => (
            <li
              key={i.id}
              className="p-4 rounded-xl bg-[var(--ui-superficie)] border border-[var(--ui-borde)] space-y-2 text-xs"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <strong className="text-sm">
                  N.º {i.secuencia} · {i.titulo}
                </strong>
                <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${CLASE_SEVERIDAD[i.severidad]}`}>
                  {i.severidad}
                </span>
              </div>
              <p className="text-[var(--ui-texto-suave)]">
                Detectado el {formatearFecha(i.fecha_deteccion)} · hace {transcurrido(i.fecha_deteccion, ahora)} ·
                registrado el {formatearFecha(i.registrado_en)}
              </p>
              {i.afecta_datos_personales && (
                <p>
                  Afecta datos personales
                  {i.categorias_datos.length > 0 ? `: ${i.categorias_datos.join(", ")}` : ""}
                </p>
              )}
              {i.descripcion && <p>{i.descripcion}</p>}
              {i.medidas_inmediatas && <p>Medidas inmediatas: {i.medidas_inmediatas}</p>}
              <p className="font-mono text-[11px] text-[var(--ui-texto-suave)] break-all">
                Código de verificación: {i.huella}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
