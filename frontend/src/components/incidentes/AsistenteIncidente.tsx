"use client";
// ¤incidentes ¤asistente
// Asistente de ocho pasos de una vulneración (INC-02). Sigue las reglas del asistente de FE-23 (validar
// antes de avanzar, un guardado a la vez, Anterior sin guardar, foco al título) con los textos que cerró
// UX/UI para esta ficha. Ningún plazo se calcula ni se compara.
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ErrorAsistente,
  JUSTIFICACION_MINIMA,
  NOMBRES_PASOS,
  ROLES_DECISION,
  ROLES_PASOS_PREVIOS,
  TOTAL_PASOS,
  destinosDe,
  evidenciasCustodiadas,
  generarInforme,
  guardarSeccion,
  leerAsistente,
  registrarNotificacion,
  type Decision,
  type Destino,
  type EstadoAsistente,
  type EvidenciaCustodiada,
} from "@/lib/incidentes/asistente";
import { CamposDelPaso, cuerpoDe, faltantes, type Borrador } from "./campos";

const TEXTO_PLAZOS =
  "Los plazos legales no se calculan aquí. La ley fija términos para avisar a la Autoridad y a los titulares: consúltalos con tu DPO o tu asesor jurídico.";
const NOTA_DECISION =
  "Esta decisión es tuya como responsable. La plataforma la registra con su justificación; no sustituye el criterio de tu DPO ni de tu asesor jurídico.";
const SIN_PERMISO = "No tienes permiso para esta acción.";

const DECISIONES: { valor: Decision; texto: string; ayuda?: string }[] = [
  { valor: "spdp", texto: "Notificar a la Autoridad" },
  { valor: "titulares", texto: "Notificar a los titulares" },
  { valor: "ambos", texto: "Notificar a ambos" },
  { valor: "ninguno", texto: "No notificar", ayuda: "Documenta por qué esta vulneración no requiere aviso." },
];
const NOMBRE_INFORME: Record<Destino, { generar: string; abrir: string }> = {
  spdp: { generar: "Generar informe para la Autoridad", abrir: "Abrir el informe para la Autoridad" },
  titulares: { generar: "Generar comunicación a los titulares", abrir: "Abrir la comunicación a los titulares" },
};

const BOTON =
  "rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 text-sm hover:bg-[var(--ui-boton-hover)] aria-disabled:opacity-50 disabled:opacity-50";
const BOTON_PRIMARIO =
  "rounded-md bg-[var(--ui-primario)] px-3 py-1.5 text-sm text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] aria-disabled:opacity-50 disabled:opacity-50";

interface Aviso {
  texto: string;
  irAPaso?: number;
}

function pasoDeDetalle(detalle: string | null): number | null {
  const n = Number((detalle ?? "").match(/(\d)/)?.[1]);
  return n >= 1 && n <= TOTAL_PASOS ? n : null;
}

interface Props {
  incidenteId: string;
  titulo: string;
  rol: string;
  alVolver: () => void;
}

export default function AsistenteIncidente({ incidenteId, titulo, rol, alVolver }: Props) {
  const [estado, setEstado] = useState<EstadoAsistente | null>(null);
  const [errorCarga, setErrorCarga] = useState(false);
  const [paso, setPaso] = useState(1);
  const [borradores, setBorradores] = useState<Record<number, Borrador>>({});
  const [aviso, setAviso] = useState<Aviso | null>(null);
  const [exito, setExito] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const ocupadoRef = useRef(false);
  const tituloRef = useRef<HTMLHeadingElement>(null);
  const primerRender = useRef(true);

  const aplicar = useCallback((nuevo: EstadoAsistente) => {
    setEstado(nuevo);
    setBorradores((previos) => {
      const siguientes = { ...previos };
      for (const s of nuevo.secciones) if (s.datos && !siguientes[s.id]) siguientes[s.id] = { ...s.datos };
      return siguientes;
    });
  }, []);

  const cargar = useCallback(async () => {
    setErrorCarga(false);
    try {
      const nuevo = await leerAsistente(rol, incidenteId);
      aplicar(nuevo);
      setPaso(nuevo.seccion_actual);
    } catch {
      setErrorCarga(true);
    }
  }, [aplicar, incidenteId, rol]);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  useEffect(() => {
    if (primerRender.current) {
      primerRender.current = false;
      return;
    }
    tituloRef.current?.focus();
  }, [paso]);

  if (errorCarga) {
    return (
      <div className="flex flex-col gap-2">
        <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">
          No pudimos cargar el asistente. Inténtalo de nuevo.
        </p>
        <button type="button" className={BOTON + " self-start"} onClick={() => void cargar()}>
          Volver a cargar
        </button>
      </div>
    );
  }
  if (!estado) return <p role="status">Cargando el asistente…</p>;

  const borrador = borradores[paso] ?? {};
  const puedeEscribir = paso <= 6 ? (ROLES_PASOS_PREVIOS as readonly string[]).includes(rol) : (ROLES_DECISION as readonly string[]).includes(rol);
  const cambiar = (campo: string, valor: unknown) =>
    setBorradores((previos) => ({ ...previos, [paso]: { ...(previos[paso] ?? {}), [campo]: valor } }));

  const irA = (n: number) => {
    if (ocupadoRef.current) return;
    setAviso(null);
    setExito(null);
    setPaso(n);
  };

  const traducir = (e: unknown, porDefecto: string): Aviso => {
    if (e instanceof ErrorAsistente) {
      if (e.status === 403) return { texto: SIN_PERMISO };
      if (e.codigo === "DECISION_SIN_JUSTIFICACION") return { texto: "Explica tu decisión con al menos 20 caracteres." };
      if (e.codigo === "SECCION_ANTERIOR_INCOMPLETA") {
        const n = pasoDeDetalle(e.detalle);
        if (n) return { texto: `Antes de seguir, completa el paso ${n}: ${NOMBRES_PASOS[n - 1]}.`, irAPaso: n };
        return { texto: "Completa los pasos del 1 al 6 antes de generar los informes." };
      }
      if (e.codigo === "SECCION_INCOMPLETA") return { texto: "Completa este paso antes de continuar." };
    }
    return { texto: porDefecto };
  };

  const ejecutar = async (accion: () => Promise<void>, porDefecto: string) => {
    if (ocupadoRef.current) return;
    ocupadoRef.current = true;
    setOcupado(true);
    setAviso(null);
    setExito(null);
    try {
      await accion();
    } catch (e) {
      setAviso(traducir(e, porDefecto));
    } finally {
      ocupadoRef.current = false;
      setOcupado(false);
    }
  };

  const guardarYContinuar = () => {
    if (paso <= 6) {
      const faltan = faltantes(paso, borrador);
      if (faltan.length > 0) {
        setAviso({ texto: `Completa este paso antes de continuar: ${faltan.join(", ")}.` });
        return;
      }
    } else if (paso === 7) {
      const decision = borrador.decision as Decision | undefined;
      const justificacion = String(borrador.justificacion ?? "").trim();
      if (!decision || justificacion.length < JUSTIFICACION_MINIMA) {
        const faltan = [!decision ? "Decisión" : null, justificacion.length < JUSTIFICACION_MINIMA ? "Justificación" : null].filter(Boolean);
        setAviso({ texto: `Completa este paso antes de continuar: ${faltan.join(", ")}.` });
        return;
      }
    }
    void ejecutar(async () => {
      const cuerpo = paso <= 6 ? cuerpoDe(paso, borrador) : { decision: borrador.decision, justificacion: String(borrador.justificacion ?? "").trim() };
      const nuevo = await guardarSeccion(rol, incidenteId, paso, cuerpo);
      aplicar(nuevo);
      const lecciones = paso === 6 && Array.isArray(cuerpo.lecciones) && cuerpo.lecciones.length > 0;
      if (lecciones) setExito("Lección guardada como hallazgo.");
      setPaso(Math.min(paso + 1, TOTAL_PASOS));
    }, "No pudimos guardar este paso. Inténtalo de nuevo.");
  };

  const nombrePaso = NOMBRES_PASOS[paso - 1];
  const idTitulo = `asistente-vulneracion-paso-${paso}`;

  return (
    <section className="flex flex-col gap-4" aria-label={`Asistente de ${titulo}`} aria-busy={ocupado}>
      <button type="button" className={BOTON + " self-start"} onClick={alVolver}>
        Volver a la lista
      </button>
      <div className="flex flex-col gap-4 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4 md:flex-row">
        <nav className="md:w-72" aria-label="Progreso del asistente">
          <ol aria-label="Pasos del asistente" className="flex flex-col gap-1">
            {NOMBRES_PASOS.map((nombre, i) => {
              const n = i + 1;
              const completa = estado.secciones[i]?.completa ?? false;
              return (
                <li key={n} aria-current={n === paso ? "step" : undefined}>
                  <button
                    type="button"
                    onClick={() => irA(n)}
                    className={`w-full rounded-md px-2 py-1 text-left text-sm ${n === paso ? "bg-[var(--ui-boton-hover)] font-semibold" : ""}`}
                  >
                    <span>
                      Paso {n} de {TOTAL_PASOS}: {nombre}
                    </span>
                    <span className={`ml-2 rounded px-1.5 text-xs ${completa ? "badge-render-success" : "border border-[var(--ui-borde)]"}`}>
                      {completa ? "Completo" : "Pendiente"}
                    </span>
                  </button>
                </li>
              );
            })}
          </ol>
        </nav>

        <div className="flex min-w-0 flex-1 flex-col gap-4" role="group" aria-labelledby={idTitulo}>
          <h2 id={idTitulo} ref={tituloRef} tabIndex={-1} className="text-lg font-semibold outline-none">
            Paso {paso} de {TOTAL_PASOS}: {nombrePaso}
          </h2>

          {paso <= 6 ? (
            <CamposDelPaso paso={paso} borrador={borrador} cambiar={cambiar} soloLectura={!puedeEscribir} />
          ) : paso === 7 ? (
            <PasoDecision borrador={borrador} cambiar={cambiar} soloLectura={!puedeEscribir} />
          ) : (
            <PasoInformes
              incidenteId={incidenteId}
              rol={rol}
              estado={estado}
              puede={puedeEscribir}
              ejecutar={ejecutar}
              aplicar={aplicar}
              setExito={setExito}
            />
          )}

          {aviso ? (
            <div role="alert" className="badge-render-danger flex flex-wrap items-center gap-2 rounded-md px-3 py-2 text-sm">
              <span>{aviso.texto}</span>
              {aviso.irAPaso ? (
                <button type="button" className="underline" onClick={() => irA(aviso.irAPaso as number)}>
                  Ir al paso {aviso.irAPaso}
                </button>
              ) : null}
            </div>
          ) : null}
          {exito ? (
            <p role="status" className="badge-render-success rounded-md px-3 py-2 text-sm">
              {exito}
            </p>
          ) : null}

          <div className="flex flex-wrap items-center justify-end gap-2">
            <button type="button" className={BOTON} disabled={ocupado || paso === 1} onClick={() => irA(paso - 1)}>
              Anterior
            </button>
            {paso < TOTAL_PASOS && puedeEscribir ? (
              <button type="button" className={BOTON_PRIMARIO} disabled={ocupado} onClick={guardarYContinuar}>
                Guardar y continuar
              </button>
            ) : null}
            {paso < TOTAL_PASOS && !puedeEscribir ? (
              <button type="button" className={BOTON} disabled={ocupado} onClick={() => irA(paso + 1)}>
                Siguiente
              </button>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}

function PasoDecision({
  borrador,
  cambiar,
  soloLectura,
}: {
  borrador: Borrador;
  cambiar: (campo: string, valor: unknown) => void;
  soloLectura: boolean;
}) {
  const justificacion = String(borrador.justificacion ?? "");
  const n = justificacion.trim().length;
  return (
    <div className="flex flex-col gap-3">
      <div role="radiogroup" aria-label="Decisión" className="grid gap-2 sm:grid-cols-2">
        {DECISIONES.map((d) => (
          <label
            key={d.valor}
            className="flex items-start gap-2 rounded-md border border-[var(--ui-borde)] p-3 text-sm"
          >
            <input
              type="radio"
              name="decision-notificar"
              value={d.valor}
              checked={borrador.decision === d.valor}
              disabled={soloLectura}
              onChange={() => cambiar("decision", d.valor)}
            />
            <span className="flex flex-col">
              <span className="font-medium">{d.texto}</span>
              {d.ayuda ? <span className="text-xs text-[var(--ui-texto-suave)]">{d.ayuda}</span> : null}
            </span>
          </label>
        ))}
      </div>
      <div className="flex flex-col gap-1">
        <label htmlFor="decision-justificacion" className="text-sm font-medium">
          Justificación
        </label>
        <textarea
          id="decision-justificacion"
          rows={4}
          required
          aria-describedby="decision-contador"
          disabled={soloLectura}
          value={justificacion}
          onChange={(e) => cambiar("justificacion", e.target.value)}
          className="w-full rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-2 text-sm text-[var(--ui-texto)] disabled:opacity-60"
        />
        <p id="decision-contador" className="text-xs text-[var(--ui-texto-suave)]">
          {n} de {JUSTIFICACION_MINIMA} caracteres como mínimo
        </p>
      </div>
      <p className="text-sm">{NOTA_DECISION}</p>
      <div className="rounded-md border border-[var(--ui-borde)] p-3 text-sm">
        <p className="font-medium">Plazos</p>
        <p>{TEXTO_PLAZOS}</p>
      </div>
    </div>
  );
}

function PasoInformes({
  incidenteId,
  rol,
  estado,
  puede,
  ejecutar,
  aplicar,
  setExito,
}: {
  incidenteId: string;
  rol: string;
  estado: EstadoAsistente;
  puede: boolean;
  ejecutar: (accion: () => Promise<void>, porDefecto: string) => Promise<void>;
  aplicar: (e: EstadoAsistente) => void;
  setExito: (t: string | null) => void;
}) {
  const destinos = destinosDe(estado.decision);
  const [generados, setGenerados] = useState<Partial<Record<Destino, string>>>({});
  const [evidencias, setEvidencias] = useState<EvidenciaCustodiada[]>([]);
  const [fecha, setFecha] = useState("");
  const [evidencia, setEvidencia] = useState("");
  const [destinoNotificado, setDestinoNotificado] = useState<Destino | "">(destinos[0] ?? "");

  useEffect(() => {
    if (!puede || destinos.length === 0) return;
    evidenciasCustodiadas(rol).then(setEvidencias).catch(() => setEvidencias([]));
  }, [puede, rol, destinos.length]);

  if (!estado.decision) {
    return <p className="text-sm">Antes de seguir, completa el paso 7: Decisión de notificar.</p>;
  }
  if (destinos.length === 0) {
    return <p className="text-sm">Decidiste no notificar; no hay informes que generar.</p>;
  }

  const generar = (destino: Destino) => {
    if (!puede) return;
    void ejecutar(async () => {
      const salida = await generarInforme(rol, incidenteId, destino);
      setGenerados((previos) => ({ ...previos, [destino]: salida.evidencia_id }));
      aplicar({ ...estado, informes: Array.from(new Set([...estado.informes, destino])) });
      setExito("Informe generado y guardado como evidencia.");
    }, "No pudimos generar el informe. Inténtalo de nuevo.");
  };

  const registrar = () => {
    if (!puede || !destinoNotificado || !fecha || !evidencia) return;
    void ejecutar(async () => {
      const nuevo = await registrarNotificacion(rol, incidenteId, destinoNotificado, new Date(fecha).toISOString(), evidencia);
      aplicar(nuevo);
      setExito("Notificación registrada.");
    }, "No pudimos registrar la notificación. Inténtalo de nuevo.");
  };

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm">
        Revisa el contenido antes de usarlo. El informe se arma con lo que registraste en los pasos anteriores.
      </p>
      {!puede ? <p className="text-sm">Solo el DPO o el implementador generan los informes.</p> : null}
      <div className="flex flex-col gap-2">
        {destinos.map((destino) => (
          <div key={destino} className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              className={BOTON_PRIMARIO}
              aria-disabled={!puede}
              onClick={() => generar(destino)}
            >
              {NOMBRE_INFORME[destino].generar}
            </button>
            {generados[destino] ? (
              <a
                className="text-sm underline"
                href={`/api/v1/evidencias/documentos/${encodeURIComponent(generados[destino] as string)}/archivo`}
                target="_blank"
                rel="noreferrer"
              >
                {NOMBRE_INFORME[destino].abrir}
              </a>
            ) : null}
          </div>
        ))}
        {destinos.includes("spdp") ? (
          <p className="text-sm">Presenta el informe en el SISPDP (servicios.spdp.gob.ec).</p>
        ) : null}
      </div>

      {puede ? (
        <fieldset className="flex flex-col gap-3 rounded-md border border-[var(--ui-borde)] p-3">
          <legend className="px-1 text-sm font-medium">Registrar la notificación</legend>
          {destinos.length > 1 ? (
            <div className="flex flex-col gap-1">
              <label htmlFor="notificacion-destino" className="text-sm">
                A quién se notificó
              </label>
              <select
                id="notificacion-destino"
                value={destinoNotificado}
                onChange={(e) => setDestinoNotificado(e.target.value as Destino)}
                className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-2 text-sm"
              >
                <option value="spdp">La Autoridad</option>
                <option value="titulares">Los titulares</option>
              </select>
            </div>
          ) : null}
          <div className="flex flex-col gap-1">
            <label htmlFor="notificacion-fecha" className="text-sm">
              Fecha de notificación
            </label>
            <input
              id="notificacion-fecha"
              type="datetime-local"
              value={fecha}
              onChange={(e) => setFecha(e.target.value)}
              className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-2 text-sm"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="notificacion-evidencia" className="text-sm">
              Evidencia de la notificación
            </label>
            <select
              id="notificacion-evidencia"
              value={evidencia}
              onChange={(e) => setEvidencia(e.target.value)}
              className="min-w-0 rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-2 text-sm"
            >
              <option value="">Elige una evidencia custodiada</option>
              {evidencias.map((ev) => (
                <option key={ev.id} value={ev.sha256}>
                  {ev.codigo} · {ev.nombre}
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            className={BOTON_PRIMARIO + " self-start"}
            disabled={!destinoNotificado || !fecha || !evidencia}
            onClick={registrar}
          >
            Registrar notificación
          </button>
        </fieldset>
      ) : null}
    </div>
  );
}
