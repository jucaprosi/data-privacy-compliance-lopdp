"use client";
// ¤frontend-ide ¤seguridad
// Pantalla «Exportar datos» (ORG-20) en Configuración: una copia de los datos de la organización.
import React, { useCallback, useEffect, useRef, useState } from "react";
import { esExportacionEnCurso, fechaCorta, papeleraApi, puedeExportar, type Exportacion } from "./papelera";
import { useRolSedes } from "../sedes/useRolSedes";
import type { OrganizacionRole } from "@/types/roadmap";

const BOTON =
  "rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 py-1.5 text-sm font-medium text-[var(--ui-texto)] disabled:opacity-50";
const INTERVALO_MS = 3000;

export default function ExportarDatosPantalla() {
  const rol = useRolSedes();
  return (
    <div className="mx-auto max-w-3xl space-y-4 pb-10" data-testid="exportar-datos-organizacion">
      <header>
        <h2 className="text-lg font-semibold text-[var(--ui-texto)]">Exportar datos</h2>
        <p className="text-sm text-[var(--ui-texto-suave)]">Una copia de los datos de tu organización</p>
      </header>
      {rol.fase === "cargando" && <p role="status" className="text-sm">Cargando…</p>}
      {rol.fase === "sin_servidor" && <p className="text-sm">Inicia sesión para exportar los datos de tu organización.</p>}
      {(rol.fase === "sin_rol" || (rol.fase === "lista" && !puedeExportar(rol.rol))) && (
        <p className="text-sm">Solo la persona administradora de la organización puede exportar los datos.</p>
      )}
      {rol.fase === "error" && <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">{rol.mensaje}</p>}
      {rol.fase === "lista" && puedeExportar(rol.rol) && <Exportar rol={rol.rol} />}
    </div>
  );
}

function Exportar({ rol }: { rol: OrganizacionRole }) {
  const [exportacionId, setExportacionId] = useState<string | null>(null);
  const [estado, setEstado] = useState<Exportacion | null>(null);
  const [enCurso, setEnCurso] = useState(false);
  const [errorSolicitud, setErrorSolicitud] = useState(false);
  const [errorCarga, setErrorCarga] = useState(false);
  const [errorDescarga, setErrorDescarga] = useState(false);
  const temporizador = useRef<ReturnType<typeof setTimeout> | null>(null);

  const consultar = useCallback(
    async (id: string) => {
      try {
        const e = await papeleraApi.exportacion(id, rol);
        setEstado(e);
        setErrorCarga(false);
        if (e.estado === "pendiente") {
          temporizador.current = setTimeout(() => void consultar(id), INTERVALO_MS);
        }
      } catch {
        setErrorCarga(true);
      }
    },
    [rol],
  );

  useEffect(
    () => () => {
      if (temporizador.current) clearTimeout(temporizador.current);
    },
    [],
  );

  const solicitar = async () => {
    setErrorSolicitud(false);
    setEnCurso(false);
    setErrorDescarga(false);
    try {
      const { id } = await papeleraApi.solicitarExportacion(rol);
      setExportacionId(id);
      setEstado({ estado: "pendiente", completa: false });
      void consultar(id);
    } catch (err: unknown) {
      if (esExportacionEnCurso(err)) setEnCurso(true);
      else setErrorSolicitud(true);
    }
  };

  const descargar = async (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    if (!estado?.url || !exportacionId) return;
    try {
      const blob = await papeleraApi.descargar(estado.url, rol);
      const enlace = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = enlace;
      a.download = `exportacion-${exportacionId}.zip`;
      a.click();
      URL.revokeObjectURL(enlace);
      setErrorDescarga(false);
    } catch {
      setErrorDescarga(true);
    }
  };

  const pendiente = estado?.estado === "pendiente";
  return (
    <section aria-label="Exportar datos" className="space-y-3" aria-busy={pendiente || undefined}>
      <p className="text-sm">Preparamos un archivo con los datos de tu organización. Te avisamos aquí cuando esté listo.</p>
      <p role="note" className="rounded-md border border-[var(--ui-borde)] px-3 py-2 text-sm">
        El archivo incluye datos personales. Descárgalo solo en un equipo de confianza y guárdalo en un lugar seguro.
      </p>
      {errorSolicitud && (
        <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">
          No pudimos solicitar la exportación. Inténtalo de nuevo.
        </p>
      )}
      {enCurso && (
        <p role="status" className="text-sm">Ya hay una exportación en preparación. Te avisamos aquí cuando esté lista.</p>
      )}
      {errorCarga && (
        <div role="alert" className="badge-render-danger flex flex-wrap items-center gap-3 rounded-md px-3 py-2 text-sm">
          <span>No pudimos cargar tus exportaciones. Inténtalo de nuevo.</span>
          {exportacionId && (
            <button type="button" className={BOTON} onClick={() => void consultar(exportacionId)}>Volver a cargar</button>
          )}
        </div>
      )}
      {errorDescarga && (
        <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">
          No pudimos descargar la exportación. Inténtalo de nuevo.
        </p>
      )}
      {pendiente && (
        <p role="status" className="text-sm">
          <span aria-hidden="true">⏳ </span>En preparación
          <span className="sr-only">. Preparando tu exportación…</span>
        </p>
      )}
      {estado?.estado === "lista" && (
        <div className="space-y-1 text-sm">
          <p><span aria-hidden="true">✔ </span>Lista</p>
          <a href={estado.url} onClick={(e) => void descargar(e)} className="font-medium underline">
            Descargar la exportación
          </a>
          {estado.caduca_en && <p>{`Disponible hasta el ${fechaCorta(estado.caduca_en)}.`}</p>}
          {!estado.completa && (
            <p className="text-[var(--ui-texto-suave)]">
              Esta copia incluye los datos de la organización, el inventario y los roles. Aún no incluye los demás
              módulos; el archivo trae un manifiesto que lo detalla.
            </p>
          )}
        </div>
      )}
      {estado?.estado === "caducada" && (
        <p className="text-sm"><span aria-hidden="true">⚠ </span>El enlace caducó. Solicita una nueva exportación.</p>
      )}
      <div>
        <button type="button" className={BOTON} disabled={pendiente} onClick={() => void solicitar()}>
          {estado?.estado === "caducada" ? "Solicitar otra exportación" : "Solicitar exportación"}
        </button>
      </div>
    </section>
  );
}
