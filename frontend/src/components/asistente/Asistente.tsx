"use client";
// ¤asistente ¤frontend-ide
// Patrón único de asistente para los flujos guiados (FE-23, optimización O-6).
// Contrato y reglas R1-R5: governance/especificaciones/FE-23.md. No implementa ningún flujo:
// los pasos, su validación y el guardado los provee la sala dueña de los datos.
import React, { useEffect, useRef, useState } from "react";
import ListaPasos from "./ListaPasos";
import ResumenAsistente from "./ResumenAsistente";
import { AVISO_ERROR_GUARDAR, MAX_PASOS, type AsistenteProps, type EstadoPaso } from "./tipos";

function acotar(valor: number, minimo: number, maximo: number): number {
  return Math.min(maximo, Math.max(minimo, valor));
}

export default function Asistente({ pasos, guardar, alTerminar, pasoInicial = 0 }: AsistenteProps) {
  if (pasos.length < 1 || pasos.length > MAX_PASOS) {
    throw new Error(`El asistente admite entre 1 y ${MAX_PASOS} pasos; recibió ${pasos.length}.`);
  }
  const n = pasos.length;

  const [indice, setIndice] = useState(() => acotar(Math.trunc(pasoInicial), 0, n - 1));
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const [estados, setEstados] = useState<Record<string, EstadoPaso>>({});
  const [terminado, setTerminado] = useState(false);

  // El estado de React se publica en el siguiente render: el ref cierra la ventana en la que un
  // doble clic rápido podría lanzar dos guardados del mismo paso (R4).
  const ocupadoRef = useRef(false);
  const montado = useRef(true);
  const titulo = useRef<HTMLHeadingElement>(null);
  const primerRender = useRef(true);

  useEffect(() => {
    montado.current = true;
    return () => {
      montado.current = false;
    };
  }, []);

  // Foco al título del paso al cambiar (no al montar, para no robar el foco a la página).
  useEffect(() => {
    if (primerRender.current) {
      primerRender.current = false;
      return;
    }
    titulo.current?.focus();
  }, [indice, terminado]);

  const paso = pasos[indice];

  const dejarPaso = (estado: EstadoPaso) => {
    setEstados((previos) => ({ ...previos, [paso.id]: estado }));
    setMensaje(null);
    if (indice === n - 1) {
      setTerminado(true);
      alTerminar();
    } else {
      setIndice(indice + 1);
    }
  };

  // R1 · Siguiente / Terminar.
  const siguiente = async () => {
    if (ocupadoRef.current || terminado) return;
    const motivo = paso.validar();
    if (motivo !== null) {
      setMensaje(motivo);
      return;
    }
    ocupadoRef.current = true;
    setOcupado(true);
    try {
      await guardar(paso.id);
      if (montado.current) dejarPaso("completado");
    } catch {
      if (montado.current) setMensaje(AVISO_ERROR_GUARDAR);
    } finally {
      ocupadoRef.current = false;
      if (montado.current) setOcupado(false);
    }
  };

  // R2 · Saltar: solo en opcionales; no valida ni guarda.
  const saltar = () => {
    if (ocupadoRef.current || terminado || !paso.opcional) return;
    dejarPaso("saltado");
  };

  // R3 · Anterior: sin validar ni guardar.
  const anterior = () => {
    if (ocupadoRef.current || terminado || indice === 0) return;
    setMensaje(null);
    setIndice(indice - 1);
  };

  const idTitulo = `asistente-titulo-${paso.id}`;

  return (
    <section
      className="flex flex-col gap-4 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4 md:flex-row"
      aria-label="Asistente"
      aria-busy={ocupado}
    >
      <nav className="md:w-64" aria-label="Progreso del asistente">
        <p className="mb-2 text-sm text-[var(--ui-texto-suave)]" data-testid="asistente-progreso">
          {terminado ? `${n} de ${n} pasos` : `Paso ${indice + 1} de ${n}`}
        </p>
        <ListaPasos pasos={pasos} actual={indice} estados={estados} terminado={terminado} />
      </nav>

      {terminado ? (
        <ResumenAsistente ref={titulo} pasos={pasos} estados={estados} />
      ) : (
        <div className="flex flex-1 flex-col gap-4" role="group" aria-labelledby={idTitulo}>
          <h2 id={idTitulo} ref={titulo} tabIndex={-1} className="text-lg font-semibold outline-none">
            {paso.titulo}
          </h2>

          <div>{paso.contenido}</div>

          {mensaje !== null ? (
            <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">
              {mensaje}
            </p>
          ) : null}

          <div className="flex flex-wrap items-center justify-end gap-2">
            <button
              type="button"
              onClick={anterior}
              disabled={ocupado || indice === 0}
              className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 text-sm hover:bg-[var(--ui-boton-hover)] disabled:opacity-50"
            >
              Anterior
            </button>
            {paso.opcional ? (
              <button
                type="button"
                onClick={saltar}
                disabled={ocupado}
                className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 text-sm hover:bg-[var(--ui-boton-hover)] disabled:opacity-50"
              >
                Saltar
              </button>
            ) : null}
            <button
              type="button"
              onClick={() => void siguiente()}
              disabled={ocupado}
              className="rounded-md bg-[var(--ui-primario)] px-3 py-1.5 text-sm text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] disabled:opacity-50"
            >
              {indice === n - 1 ? "Terminar" : "Siguiente"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
