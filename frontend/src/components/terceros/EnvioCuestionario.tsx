// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Send, CheckCircle2, Clock, AlertTriangle, XCircle, Copy, Check, FileText } from "lucide-react";
import {
  CuestionarioResumen,
  crearEnlaceCuestionario,
  listarCuestionariosTercero,
} from "@/lib/terceros/cuestionario";
import RevisionCuestionario from "./RevisionCuestionario";

interface Props {
  tercero: { id: string; nombre: string };
  permisos?: { gestionar?: boolean; evaluar?: boolean };
}

export default function EnvioCuestionario({ tercero, permisos = { gestionar: true, evaluar: true } }: Props) {
  const [cuestionarios, setCuestionarios] = useState<CuestionarioResumen[]>([]);
  const [dialogoAbierto, setDialogoAbierto] = useState(false);
  const [diasVigencia, setDiasVigencia] = useState(7);
  const [errorVigencia, setErrorVigencia] = useState<string | null>(null);
  const [enlaceCreado, setEnlaceCreado] = useState<string | null>(null);
  const [copiado, setCopiado] = useState(false);
  const [creando, setCreando] = useState(false);
  const [errorCreacion, setErrorCreacion] = useState<string | null>(null);

  // Modal de revisión
  const [revisionAbierta, setRevisionAbierta] = useState(false);
  const [mensajeRevision, setMensajeRevision] = useState<string | null>(null);

  const cancelarBtnRef = useRef<HTMLButtonElement | null>(null);

  const cargarCuestionarios = useCallback(async () => {
    try {
      const lista = await listarCuestionariosTercero(tercero.id);
      setCuestionarios(lista);
    } catch {
      setCuestionarios([]);
    }
  }, [tercero.id]);

  useEffect(() => {
    cargarCuestionarios();
  }, [cargarCuestionarios]);

  const ultimoCuestionario = cuestionarios[0] || null;

  const abrirDialogo = () => {
    setDiasVigencia(7);
    setErrorVigencia(null);
    setErrorCreacion(null);
    setEnlaceCreado(null);
    setCopiado(false);
    setDialogoAbierto(true);
    setTimeout(() => cancelarBtnRef.current?.focus(), 50);
  };

  const crearEnlace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (diasVigencia < 1 || diasVigencia > 30) {
      setErrorVigencia("Elige entre 1 y 30 días.");
      return;
    }

    setCreando(true);
    setErrorCreacion(null);
    try {
      const res = await crearEnlaceCuestionario(tercero.id, diasVigencia);
      const urlCompleta = `${window.location.origin}${res.url}`;
      setEnlaceCreado(urlCompleta);
      cargarCuestionarios();
    } catch {
      setErrorCreacion("No pudimos crear el enlace. Inténtalo de nuevo.");
    } finally {
      setCreando(false);
    }
  };

  const copiarEnlace = async () => {
    if (!enlaceCreado) return;
    try {
      await navigator.clipboard.writeText(enlaceCreado);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 3000);
    } catch {
      // Fallback
    }
  };

  const cerrarPasoEnlace = () => {
    setEnlaceCreado(null);
    setDialogoAbierto(false);
  };

  const handleRevisionGuardada = (resultado: { estado: string; informe_sha256?: string; url_nueva?: string }) => {
    setRevisionAbierta(false);
    cargarCuestionarios();
    if (resultado.estado === "conforme") {
      const huellaCorta = resultado.informe_sha256 ? resultado.informe_sha256.substring(0, 8) : "";
      setMensajeRevision(`Revisión guardada. El informe quedó guardado como evidencia. Huella de integridad: ${huellaCorta}`);
    } else if (resultado.estado === "correccion" && resultado.url_nueva) {
      const urlCompleta = `${window.location.origin}${resultado.url_nueva}`;
      setEnlaceCreado(urlCompleta);
      setDialogoAbierto(true);
    } else if (resultado.estado === "rechazado") {
      setMensajeRevision("Revisión guardada. Se registró un hallazgo en el plan de acción.");
    }
  };

  // Determinar texto e icono de estado
  let estadoTexto = "Sin cuestionario";
  let estadoIcono = <Clock className="w-3.5 h-3.5 text-[var(--ui-texto-suave)]" />;
  let badgeColor = "text-[var(--ui-texto-suave)] bg-[var(--ui-superficie-2)] border-[var(--ui-borde)]";

  if (ultimoCuestionario) {
    if (ultimoCuestionario.estado === "enviado") {
      estadoTexto = "Enviado";
      estadoIcono = <Send className="w-3.5 h-3.5 text-[var(--ui-aviso-texto)]" />;
      badgeColor = "text-[var(--ui-aviso-texto)] bg-[var(--ui-aviso-fondo)] border-[var(--ui-aviso-borde)]";
    } else if (ultimoCuestionario.estado === "respondido") {
      estadoTexto = "Respondido, por revisar";
      estadoIcono = <FileText className="w-3.5 h-3.5 text-[var(--ui-info-texto)]" />;
      badgeColor = "text-[var(--ui-info-texto)] bg-[var(--ui-info-fondo)] border-[var(--ui-info-borde)]";
    } else if (ultimoCuestionario.estado === "conforme") {
      estadoTexto = "Aceptado";
      estadoIcono = <CheckCircle2 className="w-3.5 h-3.5 text-[var(--ui-exito-texto)]" />;
      badgeColor = "text-[var(--ui-exito-texto)] bg-[var(--ui-exito-fondo)] border-[var(--ui-exito-borde)]";
    } else if (ultimoCuestionario.estado === "correccion") {
      estadoTexto = "Corrección pedida";
      estadoIcono = <AlertTriangle className="w-3.5 h-3.5 text-[var(--ui-aviso-texto)]" />;
      badgeColor = "text-[var(--ui-aviso-texto)] bg-[var(--ui-aviso-fondo)] border-[var(--ui-aviso-borde)]";
    } else if (ultimoCuestionario.estado === "rechazado") {
      estadoTexto = "Rechazado";
      estadoIcono = <XCircle className="w-3.5 h-3.5 text-[var(--ui-error-texto)]" />;
      badgeColor = "text-[var(--ui-error-texto)] bg-[var(--ui-error-fondo)] border-[var(--ui-error-borde)]";
    }
  }

  const estaEnviadoYVigente =
    ultimoCuestionario?.estado === "enviado" &&
    ultimoCuestionario.caduca_en &&
    new Date(ultimoCuestionario.caduca_en) > new Date();

  const fechaEnvio = ultimoCuestionario?.creado_en
    ? new Date(ultimoCuestionario.creado_en).toLocaleDateString("es-EC")
    : "";
  const fechaVence = ultimoCuestionario?.caduca_en
    ? new Date(ultimoCuestionario.caduca_en).toLocaleDateString("es-EC")
    : "";

  return (
    <div className="flex flex-col space-y-1.5 text-xs">
      <div className="flex items-center space-x-2">
        <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded border text-[11px] font-medium ${badgeColor}`}>
          {estadoIcono}
          <span>{estadoTexto}</span>
        </span>

        {/* Acciones para implementador y coordinador */}
        {permisos.gestionar && !estaEnviadoYVigente && (
          <button
            type="button"
            onClick={abrirDialogo}
            aria-label={`Enviar el cuestionario a ${tercero.nombre}`}
            className="px-2.5 py-1 bg-[var(--ui-primario)] hover:bg-[var(--ui-primario-hover)] text-[var(--ui-primario-texto)] rounded text-[11px] font-semibold transition"
          >
            Enviar cuestionario
          </button>
        )}

        {permisos.gestionar && ultimoCuestionario?.estado === "respondido" && (
          <button
            type="button"
            onClick={() => setRevisionAbierta(true)}
            aria-label={`Revisar las respuestas de ${tercero.nombre}`}
            className="px-2.5 py-1 bg-[var(--ui-primario)] hover:bg-[var(--ui-primario-hover)] text-[var(--ui-primario-texto)] rounded text-[11px] font-semibold transition"
          >
            Revisar respuestas
          </button>
        )}
      </div>

      {estaEnviadoYVigente && (
        <span className="text-[var(--ui-texto-suave)] text-[11px]">
          Enviado el {fechaEnvio} · el enlace vence el {fechaVence}
        </span>
      )}

      {mensajeRevision && (
        <p role="status" className="text-[var(--ui-exito-texto)] text-[11px] font-medium">
          {mensajeRevision}
        </p>
      )}

      {/* Diálogo Enviar cuestionario / Copia el enlace ahora */}
      {dialogoAbierto && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-[var(--ui-superficie)] border border-[var(--ui-borde)] rounded-xl p-5 max-w-md w-full text-[var(--foreground)] shadow-2xl">
            {!enlaceCreado ? (
              <div>
                <h3 className="text-sm font-bold text-[var(--ui-exito-texto)] mb-2">
                  Enviar cuestionario a {tercero.nombre}
                </h3>
                <p className="text-[var(--ui-texto-suave)] text-xs mb-3">
                  Creamos un enlace para que el proveedor responda sin crear una cuenta. El enlace funciona una sola vez y vence en los días que elijas.
                </p>

                <form onSubmit={crearEnlace} className="space-y-3">
                  <div>
                    <label htmlFor="vigencia-dias" className="block text-[var(--ui-texto-suave)] font-medium mb-1">
                      Vigencia del enlace (días)
                    </label>
                    <input
                      id="vigencia-dias"
                      type="number"
                      min={1}
                      max={30}
                      value={diasVigencia}
                      onChange={(e) => setDiasVigencia(parseInt(e.target.value) || 0)}
                      className="w-full bg-[var(--ui-campo)] border border-[var(--ui-borde-control)] rounded p-2 text-[var(--foreground)]"
                      required
                    />
                    {errorVigencia && (
                      <p role="alert" className="text-[var(--ui-error-texto)] text-xs mt-1">
                        {errorVigencia}
                      </p>
                    )}
                  </div>

                  {errorCreacion && (
                    <p role="alert" className="text-[var(--ui-error-texto)] text-xs">
                      {errorCreacion}
                    </p>
                  )}

                  <div className="flex justify-end space-x-2 pt-2 border-t border-[var(--ui-borde)]">
                    <button
                      ref={cancelarBtnRef}
                      type="button"
                      onClick={() => setDialogoAbierto(false)}
                      className="px-3.5 py-1.5 bg-[var(--ui-boton)] text-[var(--foreground)] rounded hover:bg-[var(--ui-boton-hover)] font-medium"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      disabled={creando}
                      className="px-4 py-1.5 bg-[var(--ui-primario)] text-[var(--ui-primario-texto)] rounded font-semibold hover:bg-[var(--ui-primario-hover)] disabled:opacity-50"
                    >
                      {creando ? "Creando enlace..." : "Crear enlace"}
                    </button>
                  </div>
                </form>
              </div>
            ) : (
              /* Paso: Copia el enlace ahora */
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-[var(--ui-exito-texto)]">Copia el enlace ahora</h3>
                <p className="text-[var(--ui-texto-suave)] text-xs">
                  Este enlace solo se muestra ahora. Envíalo al proveedor por el canal que usas habitualmente; la plataforma no lo envía.
                </p>

                <div>
                  <label htmlFor="enlace-cuestionario-readonly" className="block text-[var(--ui-texto-suave)] text-[11px] mb-1">
                    Enlace del cuestionario
                  </label>
                  <input
                    id="enlace-cuestionario-readonly"
                    type="text"
                    aria-label="Enlace del cuestionario"
                    readOnly
                    value={enlaceCreado}
                    className="w-full bg-[var(--ui-campo)] border border-[var(--ui-borde-control)] rounded p-2 text-[var(--foreground)] font-mono text-xs select-all"
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={copiarEnlace}
                    className="px-3 py-1.5 bg-[var(--ui-boton)] hover:bg-[var(--ui-boton-hover)] text-[var(--foreground)] rounded font-medium flex items-center space-x-1.5"
                  >
                    {copiado ? <Check className="w-3.5 h-3.5 text-[var(--ui-exito-texto)]" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiado ? "Enlace copiado." : "Copiar el enlace"}</span>
                  </button>
                  {copiado && (
                    <span role="status" className="text-[var(--ui-exito-texto)] text-xs">
                      Enlace copiado.
                    </span>
                  )}
                </div>

                <div className="flex justify-end pt-3 border-t border-[var(--ui-borde)]">
                  <button
                    type="button"
                    onClick={cerrarPasoEnlace}
                    className="px-4 py-1.5 bg-[var(--ui-primario)] hover:bg-[var(--ui-primario-hover)] text-[var(--ui-primario-texto)] rounded font-semibold"
                  >
                    Ya lo copié
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal de revisión */}
      {revisionAbierta && ultimoCuestionario && (
        <RevisionCuestionario
          cuestionario={ultimoCuestionario}
          terceroNombre={tercero.nombre}
          onCerrar={() => setRevisionAbierta(false)}
          onRevisionGuardada={handleRevisionGuardada}
        />
      )}
    </div>
  );
}
