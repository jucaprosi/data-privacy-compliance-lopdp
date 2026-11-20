"use client";

// ¤api-integraciones ¤frontend-ide
/**
 * Panel de gestión de suscripciones a webhooks salientes (API-02b).
 *
 * Textos y requisitos de accesibilidad definidos en governance/especificaciones/API-02b.md (§4).
 * Solo visible para admin_organizacion; ante 403 no se renderiza.
 */
import React, { useCallback, useEffect, useId, useRef, useState } from "react";
import { CheckCircle2, XCircle } from "lucide-react";
import {
  EVENTOS_CON_EMISORA,
  ErrorWebhookApi,
  crearWebhook,
  desactivarWebhook,
  listarWebhooks,
  nombreEventoWebhook,
  obtenerTechosWebhooks,
  probarWebhook,
  rotarSecretoWebhook,
  type ResultadoPruebaWebhook,
  type WebhookSuscripcion,
} from "@/lib/integraciones/webhooks";

export interface WebhooksPanelProps {
  techoMaximo?: number | null;
  onCambioActivos?: () => void;
}

type ModalActivo =
  | { tipo: "ninguno" }
  | { tipo: "crear" }
  | { tipo: "secreto"; secreto: string }
  | { tipo: "rotar"; webhook: WebhookSuscripcion }
  | { tipo: "desactivar"; webhook: WebhookSuscripcion };

const SELECTOR_FOCALIZABLE =
  "button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])";

function formatearFechaCorta(iso: string | null): string {
  if (!iso) return "Sin cambios";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  return m ? `${m[3]}/${m[2]}/${m[1]}` : "Sin cambios";
}

function mensajeErrorFijo(err: unknown): { codigo: string | null; texto: string } {
  if (err instanceof ErrorWebhookApi) {
    if (err.status === 404 || err.code === "WEBHOOK_NO_ENCONTRADO") {
      return {
        codigo: "WEBHOOK_NO_ENCONTRADO",
        texto: "No encontramos este webhook. Actualizamos la lista.",
      };
    }
    if (err.status === 409 || err.code === "TECHO_WEBHOOKS_ALCANZADO") {
      return {
        codigo: "TECHO_WEBHOOKS_ALCANZADO",
        texto: "Alcanzaste el máximo de webhooks de tu plan. Desactiva uno para añadir otro.",
      };
    }
    if (err.code === "WEBHOOK_EVENTO_DESCONOCIDO") {
      return {
        codigo: "WEBHOOK_EVENTO_DESCONOCIDO",
        texto: "Uno de los eventos elegidos ya no existe. Vuelve a elegir los eventos.",
      };
    }
    if (err.status === 503 || err.code === "WEBHOOKS_CIFRADO_NO_CONFIGURADO") {
      return {
        codigo: "WEBHOOKS_CIFRADO_NO_CONFIGURADO",
        texto: "Los webhooks no están disponibles en este momento. Escribe al equipo de EVYDENTIA.",
      };
    }
    if (err.code === "WEBHOOK_URL_NO_PERMITIDA") {
      return {
        codigo: "WEBHOOK_URL_NO_PERMITIDA",
        texto: "Esta dirección no está permitida. Usa una dirección pública que empiece por https://.",
      };
    }
  }
  return {
    codigo: null,
    texto: "No pudimos completar la acción. El webhook sigue como estaba.",
  };
}

function DialogoModal({
  titulo,
  pasoKey,
  permitirEscape,
  permitirCerrarFondo,
  onCerrar,
  focoInicialRef,
  fallbackFocoRef,
  children,
}: {
  titulo: string;
  pasoKey: string;
  permitirEscape: boolean;
  permitirCerrarFondo: boolean;
  onCerrar: () => void;
  focoInicialRef?: React.RefObject<HTMLElement | null>;
  fallbackFocoRef?: React.RefObject<HTMLElement | null>;
  children: React.ReactNode;
}) {
  const idTitulo = useId();
  const cajaRef = useRef<HTMLDivElement | null>(null);
  const origenRef = useRef<HTMLElement | null>(
    typeof document !== "undefined" ? (document.activeElement as HTMLElement | null) : null,
  );
  const fallbackRef = useRef(fallbackFocoRef);
  fallbackRef.current = fallbackFocoRef;

  useEffect(() => {
    const destino = focoInicialRef?.current;
    if (destino) {
      destino.focus();
    } else if (cajaRef.current) {
      const primero = cajaRef.current.querySelector<HTMLElement>(SELECTOR_FOCALIZABLE);
      primero?.focus();
    }
  }, [pasoKey, focoInicialRef]);

  useEffect(() => {
    const retorno = origenRef.current;
    return () => {
      if (retorno && retorno.isConnected) {
        retorno.focus();
      } else {
        fallbackRef.current?.current?.focus();
      }
    };
  }, []);

  const manejarTecla = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      if (permitirEscape) {
        onCerrar();
      }
      return;
    }
    if (e.key !== "Tab" || !cajaRef.current) return;
    const focales = Array.from(cajaRef.current.querySelectorAll<HTMLElement>(SELECTOR_FOCALIZABLE));
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
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onKeyDown={manejarTecla}
      onMouseDown={(e) => {
        if (permitirCerrarFondo && e.target === e.currentTarget) {
          onCerrar();
        }
      }}
    >
      <div
        ref={cajaRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={idTitulo}
        className="w-full max-w-md space-y-4 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-5 shadow-lg"
      >
        <h3 id={idTitulo} className="text-base font-semibold">
          {titulo}
        </h3>
        {children}
      </div>
    </div>
  );
}

export default function WebhooksPanel({ techoMaximo = null, onCambioActivos }: WebhooksPanelProps) {
  const idTitulo = useId();
  const idUrl = useId();
  const idAyudaUrl = useId();
  const idErrorUrl = useId();
  const idSecreto = useId();

  const btnAnadirRef = useRef<HTMLButtonElement | null>(null);
  const cancelarCrearRef = useRef<HTMLButtonElement | null>(null);
  const cancelarRotarRef = useRef<HTMLButtonElement | null>(null);
  const cancelarDesactivarRef = useRef<HTMLButtonElement | null>(null);
  const copiarSecretoRef = useRef<HTMLButtonElement | null>(null);

  const [autorizado, setAutorizado] = useState<boolean | null>(null);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState(false);
  const [webhooks, setWebhooks] = useState<WebhookSuscripcion[]>([]);
  const [maximoTecho, setMaximoTecho] = useState<number | null>(techoMaximo);

  const [modal, setModal] = useState<ModalActivo>({ tipo: "ninguno" });
  const [procesando, setProcesando] = useState(false);

  // Estado formulario crear
  const [urlNueva, setUrlNueva] = useState("");
  const [eventosNuevos, setEventosNuevos] = useState<string[]>([]);
  const [errorUrlCampo, setErrorUrlCampo] = useState<string | null>(null);
  const [errorEventosCampo, setErrorEventosCampo] = useState<string | null>(null);

  // Estado paso secreto
  const [copiado, setCopiado] = useState(false);
  const [secretoGuardado, setSecretoGuardado] = useState(false);

  // Estado acciones y mensajes
  const [probandoId, setProbandoId] = useState<string | null>(null);
  const [estadoAviso, setEstadoAviso] = useState<string | null>(null);
  const [alertaAviso, setAlertaAviso] = useState<string | null>(null);
  const [eventosDisponibles, setEventosDisponibles] = useState<readonly string[]>(EVENTOS_CON_EMISORA);

  useEffect(() => {
    if (techoMaximo !== null && techoMaximo !== undefined) {
      setMaximoTecho((prev) => (prev === null ? techoMaximo : prev));
    }
  }, [techoMaximo]);

  const cargarDatos = useCallback(async () => {
    setCargando(true);
    setErrorCarga(false);
    try {
      const [lista, techos] = await Promise.all([listarWebhooks(), obtenerTechosWebhooks()]);
      setAutorizado(true);
      setWebhooks(lista);
      if (techos !== null) {
        setMaximoTecho(techos.maximo);
      }
    } catch (err) {
      if (err instanceof ErrorWebhookApi && err.status === 403) {
        setAutorizado(false);
        return;
      }
      setAutorizado(true);
      setErrorCarga(true);
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargarDatos();
  }, [cargarDatos]);

  if (autorizado === false) {
    return null;
  }

  const activos = webhooks.filter((w) => w.activo).length;
  const techoEfectivo = maximoTecho ?? techoMaximo ?? null;
  const techoAlcanzado = techoEfectivo !== null && activos >= techoEfectivo;

  const abrirCrear = () => {
    if (techoAlcanzado || procesando) return;
    setAlertaAviso(null);
    setEstadoAviso(null);
    setUrlNueva("");
    setEventosNuevos([]);
    setErrorUrlCampo(null);
    setErrorEventosCampo(null);
    setModal({ tipo: "crear" });
  };

  const cerrarModal = () => {
    setModal({ tipo: "ninguno" });
    setCopiado(false);
    setSecretoGuardado(false);
    setErrorUrlCampo(null);
    setErrorEventosCampo(null);
  };

  const cerrarPasoSecreto = () => {
    if (!secretoGuardado) return;
    setCopiado(false);
    setSecretoGuardado(false);
    setModal({ tipo: "ninguno" });
  };

  const manejarErrorAccion = async (err: unknown, cerrarSiEsModal = false) => {
    const { codigo, texto } = mensajeErrorFijo(err);
    if (codigo === "WEBHOOK_URL_NO_PERMITIDA") {
      setErrorUrlCampo(texto);
      return;
    }
    if (codigo === "WEBHOOK_EVENTO_DESCONOCIDO") {
      setErrorEventosCampo(texto);
      setEventosDisponibles([...EVENTOS_CON_EMISORA]);
      await cargarDatos();
      return;
    }
    if (cerrarSiEsModal) {
      cerrarModal();
    }
    setEstadoAviso(null);
    setAlertaAviso(texto);
    if (codigo === "WEBHOOK_NO_ENCONTRADO" || codigo === "TECHO_WEBHOOKS_ALCANZADO") {
      await cargarDatos();
    }
  };

  const enviarCrear = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorUrlCampo(null);
    setErrorEventosCampo(null);

    if (eventosNuevos.length === 0) {
      setErrorEventosCampo("Elige al menos un evento.");
      return;
    }

    setProcesando(true);
    setAlertaAviso(null);
    setEstadoAviso(null);
    try {
      const res = await crearWebhook(urlNueva.trim(), eventosNuevos);
      setCopiado(false);
      setSecretoGuardado(false);
      setUrlNueva("");
      setEventosNuevos([]);
      setModal({ tipo: "secreto", secreto: res.secreto_en_claro });
      await cargarDatos();
      onCambioActivos?.();
    } catch (err) {
      await manejarErrorAccion(err, true);
    } finally {
      setProcesando(false);
    }
  };

  const confirmarRotar = async (webhook: WebhookSuscripcion) => {
    setProcesando(true);
    setAlertaAviso(null);
    setEstadoAviso(null);
    try {
      const res = await rotarSecretoWebhook(webhook.id);
      setCopiado(false);
      setSecretoGuardado(false);
      setModal({ tipo: "secreto", secreto: res.secreto_en_claro });
      await cargarDatos();
    } catch (err) {
      await manejarErrorAccion(err, true);
    } finally {
      setProcesando(false);
    }
  };

  const confirmarDesactivar = async (webhook: WebhookSuscripcion) => {
    setProcesando(true);
    setAlertaAviso(null);
    setEstadoAviso(null);
    try {
      await desactivarWebhook(webhook.id);
      cerrarModal();
      setEstadoAviso("Webhook desactivado.");
      await cargarDatos();
      onCambioActivos?.();
    } catch (err) {
      await manejarErrorAccion(err, true);
    } finally {
      setProcesando(false);
    }
  };

  const ejecutarPrueba = async (webhook: WebhookSuscripcion) => {
    if (probandoId || procesando) return;
    setProbandoId(webhook.id);
    setAlertaAviso(null);
    setEstadoAviso("Enviando un aviso de prueba… puede tardar unos segundos.");
    try {
      const res: ResultadoPruebaWebhook = await probarWebhook(webhook.id);
      if (res.entregado) {
        const unidad = res.intentos === 1 ? "intento" : "intentos";
        setEstadoAviso(
          `El aviso de prueba llegó. Tu sistema respondió con el código ${res.estado_http ?? ""} tras ${res.intentos} ${unidad}.`,
        );
      } else {
        setEstadoAviso(null);
        const base = `El aviso de prueba no llegó tras ${res.intentos} intentos. Comprueba la dirección y que tu sistema responda.`;
        const extra =
          res.estado_http !== null && res.estado_http !== undefined
            ? ` Tu sistema respondió con el código ${res.estado_http}.`
            : "";
        setAlertaAviso(`${base}${extra}`);
      }
    } catch (err) {
      setEstadoAviso(null);
      await manejarErrorAccion(err, false);
    } finally {
      setProbandoId(null);
    }
  };

  const toggleEvento = (codigo: string) => {
    setErrorEventosCampo(null);
    setEventosNuevos((prev) =>
      prev.includes(codigo) ? prev.filter((item) => item !== codigo) : [...prev, codigo],
    );
  };

  const copiarSecreto = () => {
    if (modal.tipo !== "secreto") return;
    if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
      void navigator.clipboard.writeText(modal.secreto).catch(() => undefined);
    }
    setCopiado(true);
  };

  return (
    <section
      aria-labelledby={idTitulo}
      data-panel="webhooks"
      className="space-y-4 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-4 sm:p-5"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-1">
          <h2 id={idTitulo} className="text-lg font-semibold">
            Avisos automáticos (webhooks)
          </h2>
          <p className="text-sm text-[var(--ui-texto-suave)]">
            Envían un aviso a otro sistema cuando ocurre algo en la plataforma. Cada aviso va firmado para que ese
            sistema compruebe que viene de EVYDENTIA.
          </p>
          {!cargando && !errorCarga && (
            <p role="status" className="text-sm font-medium">
              {techoEfectivo !== null
                ? `${activos} de ${techoEfectivo} webhooks activos`
                : `${activos} webhooks activos`}
            </p>
          )}
        </div>

        <div className="flex flex-col items-start gap-1 sm:items-end">
          <button
            ref={btnAnadirRef}
            type="button"
            aria-disabled={techoAlcanzado ? "true" : undefined}
            onClick={abrirCrear}
            className={`rounded-md px-3.5 py-2 text-sm font-medium ${
              techoAlcanzado
                ? "cursor-not-allowed border border-[var(--ui-borde)] bg-[var(--ui-boton)] opacity-60"
                : "bg-[var(--ui-primario)] text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] cursor-pointer"
            }`}
          >
            Añadir webhook
          </button>
          {techoAlcanzado && (
            <p className="text-xs text-[var(--ui-texto-suave)] sm:text-right">
              Alcanzaste el máximo de webhooks de tu plan ({techoEfectivo}). Desactiva uno para añadir otro.
            </p>
          )}
        </div>
      </div>

      {estadoAviso && (
        <p
          role="status"
          className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie-2)] px-3 py-2 text-sm"
        >
          {estadoAviso}
        </p>
      )}

      {alertaAviso && (
        <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">
          {alertaAviso}
        </p>
      )}

      {cargando ? (
        <p role="status" className="py-4 text-sm text-[var(--ui-texto-suave)]">
          Cargando webhooks…
        </p>
      ) : errorCarga ? (
        <div className="flex flex-col items-start gap-2 py-2">
          <p role="alert" className="badge-render-danger rounded-md px-3 py-2 text-sm">
            No pudimos cargar los webhooks. Inténtalo de nuevo.
          </p>
          <button
            type="button"
            onClick={() => void cargarDatos()}
            className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 text-sm font-medium hover:bg-[var(--ui-boton-hover)] cursor-pointer"
          >
            Volver a cargar
          </button>
        </div>
      ) : webhooks.length === 0 ? (
        <p className="py-4 text-sm text-[var(--ui-texto-suave)]">
          Aún no hay webhooks. Añade uno para avisar a otro sistema.
        </p>
      ) : (
        <div className="w-full">
          <table role="table" aria-label="Webhooks" className="w-full text-left text-sm">
            <thead role="rowgroup" className="hidden border-b border-[var(--ui-borde)] text-[var(--ui-texto-suave)] md:table-header-group">
              <tr role="row">
                <th role="columnheader" className="py-2.5 pr-3 font-medium">
                  Dirección
                </th>
                <th role="columnheader" className="px-3 py-2.5 font-medium">
                  Eventos
                </th>
                <th role="columnheader" className="px-3 py-2.5 font-medium">
                  Estado
                </th>
                <th role="columnheader" className="px-3 py-2.5 font-medium">
                  Último cambio de secreto
                </th>
                <th role="columnheader" className="py-2.5 pl-3 text-right font-medium">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody role="rowgroup" className="block space-y-3 md:table-row-group md:space-y-0 md:divide-y md:divide-[var(--ui-borde)]">
              {webhooks.map((w) => {
                const estaProbando = probandoId === w.id;
                return (
                  <tr
                    key={w.id}
                    role="row"
                    className="block rounded-md border border-[var(--ui-borde)] bg-[var(--ui-superficie-2)] p-3 md:table-row md:rounded-none md:border-0 md:bg-transparent md:p-0"
                  >
                    <td role="cell" className="flex min-w-0 flex-col gap-1 py-1 md:table-cell md:py-3 md:pr-3">
                      <span className="text-xs font-medium text-[var(--ui-texto-suave)] md:hidden">Dirección</span>
                      <span
                        title={w.url}
                        aria-label={w.url}
                        className="block max-w-full truncate font-mono text-xs md:max-w-[260px]"
                      >
                        {w.url}
                      </span>
                    </td>
                    <td role="cell" className="flex flex-col gap-1 py-1 md:table-cell md:px-3 md:py-3">
                      <span className="text-xs font-medium text-[var(--ui-texto-suave)] md:hidden">Eventos</span>
                      <span className="text-sm">{w.eventos.map(nombreEventoWebhook).join(", ")}</span>
                    </td>
                    <td role="cell" className="flex flex-col gap-1 py-1 md:table-cell md:px-3 md:py-3">
                      <span className="text-xs font-medium text-[var(--ui-texto-suave)] md:hidden">Estado</span>
                      {w.activo ? (
                        <span className="badge-render-success inline-flex w-fit items-center gap-1 rounded px-2 py-0.5 text-xs font-medium">
                          <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
                          Activo
                        </span>
                      ) : (
                        <span className="inline-flex w-fit items-center gap-1 rounded border border-[var(--ui-borde)] px-2 py-0.5 text-xs font-medium text-[var(--ui-texto-suave)]">
                          <XCircle className="h-3.5 w-3.5" aria-hidden="true" />
                          Desactivado
                        </span>
                      )}
                    </td>
                    <td role="cell" className="flex flex-col gap-1 py-1 md:table-cell md:px-3 md:py-3">
                      <span className="text-xs font-medium text-[var(--ui-texto-suave)] md:hidden">
                        Último cambio de secreto
                      </span>
                      <span className="text-xs text-[var(--ui-texto-suave)]">
                        {formatearFechaCorta(w.rotada_en)}
                      </span>
                    </td>
                    <td role="cell" className="flex flex-wrap items-center gap-2 pt-2 md:table-cell md:py-3 md:pl-3 md:text-right">
                      {w.activo && (
                        <div className="flex flex-wrap justify-start gap-2 md:justify-end">
                          <button
                            type="button"
                            aria-label={`Probar el webhook ${w.url}`}
                            aria-busy={estaProbando ? "true" : undefined}
                            disabled={Boolean(probandoId) || procesando}
                            onClick={() => void ejecutarPrueba(w)}
                            className="rounded border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-2.5 py-1 text-xs font-medium hover:bg-[var(--ui-boton-hover)] disabled:opacity-50 cursor-pointer"
                          >
                            Probar
                          </button>
                          <button
                            type="button"
                            aria-label={`Rotar el secreto del webhook ${w.url}`}
                            disabled={Boolean(probandoId) || procesando}
                            onClick={() => {
                              setAlertaAviso(null);
                              setEstadoAviso(null);
                              setModal({ tipo: "rotar", webhook: w });
                            }}
                            className="rounded border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-2.5 py-1 text-xs font-medium hover:bg-[var(--ui-boton-hover)] disabled:opacity-50 cursor-pointer"
                          >
                            Rotar secreto
                          </button>
                          <button
                            type="button"
                            aria-label={`Desactivar el webhook ${w.url}`}
                            disabled={Boolean(probandoId) || procesando}
                            onClick={() => {
                              setAlertaAviso(null);
                              setEstadoAviso(null);
                              setModal({ tipo: "desactivar", webhook: w });
                            }}
                            className="badge-render-danger rounded px-2.5 py-1 text-xs font-medium disabled:opacity-50 cursor-pointer"
                          >
                            Desactivar
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {modal.tipo !== "ninguno" && (
        <DialogoModal
          pasoKey={modal.tipo}
          titulo={
            modal.tipo === "crear"
              ? "Añadir webhook"
              : modal.tipo === "secreto"
                ? "Copia el secreto ahora"
                : modal.tipo === "rotar"
                  ? "¿Rotar el secreto de este webhook?"
                  : "¿Desactivar este webhook?"
          }
          permitirEscape={modal.tipo !== "secreto"}
          permitirCerrarFondo={modal.tipo !== "secreto"}
          onCerrar={modal.tipo === "secreto" ? () => undefined : cerrarModal}
          focoInicialRef={
            modal.tipo === "crear"
              ? cancelarCrearRef
              : modal.tipo === "secreto"
                ? copiarSecretoRef
                : modal.tipo === "rotar"
                  ? cancelarRotarRef
                  : cancelarDesactivarRef
          }
          fallbackFocoRef={btnAnadirRef}
        >
          {modal.tipo === "crear" && (
            <form noValidate onSubmit={(e) => void enviarCrear(e)} className="space-y-4">
              <div className="space-y-1">
                <label htmlFor={idUrl} className="block text-sm font-medium">
                  Dirección del webhook
                </label>
                <input
                  id={idUrl}
                  type="text"
                  value={urlNueva}
                  onChange={(e) => {
                    setUrlNueva(e.target.value);
                    if (errorUrlCampo) setErrorUrlCampo(null);
                  }}
                  aria-invalid={errorUrlCampo ? "true" : undefined}
                  aria-describedby={errorUrlCampo ? `${idAyudaUrl} ${idErrorUrl}` : idAyudaUrl}
                  placeholder="https://sistema.ejemplo/avisos"
                  className="w-full rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-3 py-2 font-mono text-sm"
                />
                <p id={idAyudaUrl} className="text-xs text-[var(--ui-texto-suave)]">
                  Debe empezar por https:// y ser una dirección pública.
                </p>
                {errorUrlCampo && (
                  <p id={idErrorUrl} role="alert" className="badge-render-danger rounded px-2 py-1 text-xs">
                    {errorUrlCampo}
                  </p>
                )}
              </div>

              <fieldset className="space-y-2 rounded-md border border-[var(--ui-borde)] p-3">
                <legend className="px-1 text-sm font-medium">Eventos</legend>
                {eventosDisponibles.map((codigo) => (
                  <label key={codigo} className="flex cursor-pointer items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={eventosNuevos.includes(codigo)}
                      onChange={() => toggleEvento(codigo)}
                    />
                    <span>{nombreEventoWebhook(codigo)}</span>
                  </label>
                ))}
                {errorEventosCampo && (
                  <p role="alert" className="badge-render-danger rounded px-2 py-1 text-xs">
                    {errorEventosCampo}
                  </p>
                )}
              </fieldset>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  ref={cancelarCrearRef}
                  type="button"
                  onClick={cerrarModal}
                  className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 text-sm font-medium hover:bg-[var(--ui-boton-hover)] cursor-pointer"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={procesando}
                  className="rounded-md bg-[var(--ui-primario)] px-3 py-1.5 text-sm font-medium text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] disabled:opacity-50 cursor-pointer"
                >
                  Añadir webhook
                </button>
              </div>
            </form>
          )}

          {modal.tipo === "secreto" && (
            <div className="space-y-4">
              <p className="text-sm text-[var(--ui-texto-suave)]">
                Guárdalo ahora: no volverá a mostrarse. Tu sistema lo necesita para comprobar la firma de cada aviso.
              </p>
              <div className="space-y-1.5">
                <label htmlFor={idSecreto} className="block text-sm font-medium">
                  Secreto del webhook
                </label>
                <div className="flex flex-col gap-2 sm:flex-row">
                  <input
                    id={idSecreto}
                    type="text"
                    readOnly
                    value={modal.secreto}
                    className="min-w-0 flex-1 rounded-md border border-[var(--ui-borde)] bg-[var(--ui-campo)] px-3 py-2 font-mono text-xs"
                  />
                  <button
                    ref={copiarSecretoRef}
                    type="button"
                    onClick={copiarSecreto}
                    className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-2 text-xs font-medium hover:bg-[var(--ui-boton-hover)] cursor-pointer"
                  >
                    Copiar el secreto
                  </button>
                </div>
                {copiado && (
                  <p role="status" className="text-xs font-medium">
                    Secreto copiado.
                  </p>
                )}
              </div>

              <label className="flex cursor-pointer items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={secretoGuardado}
                  onChange={(e) => setSecretoGuardado(e.target.checked)}
                />
                <span>Guardé el secreto en un lugar seguro</span>
              </label>

              <div className="flex justify-end pt-1">
                <button
                  type="button"
                  disabled={!secretoGuardado}
                  onClick={cerrarPasoSecreto}
                  className="rounded-md bg-[var(--ui-primario)] px-3.5 py-1.5 text-sm font-medium text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer"
                >
                  Ya lo guardé
                </button>
              </div>
            </div>
          )}

          {modal.tipo === "rotar" && (
            <div className="space-y-4">
              <p className="text-sm text-[var(--ui-texto-suave)]">
                Se crea un secreto nuevo y los próximos avisos se firman con él. Actualiza tu sistema con el secreto
                nuevo; si no, rechazará los avisos.
              </p>
              <div className="flex justify-end gap-2">
                <button
                  ref={cancelarRotarRef}
                  type="button"
                  onClick={cerrarModal}
                  className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 text-sm font-medium hover:bg-[var(--ui-boton-hover)] cursor-pointer"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  disabled={procesando}
                  onClick={() => void confirmarRotar(modal.webhook)}
                  className="rounded-md bg-[var(--ui-primario)] px-3 py-1.5 text-sm font-medium text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] disabled:opacity-50 cursor-pointer"
                >
                  Rotar el secreto
                </button>
              </div>
            </div>
          )}

          {modal.tipo === "desactivar" && (
            <div className="space-y-4">
              <p className="text-sm text-[var(--ui-texto-suave)]">
                Deja de enviar avisos a {modal.webhook.url} de inmediato y libera un lugar de tu plan. No se puede
                volver a activar: si lo necesitas otra vez, añade uno nuevo.
              </p>
              <div className="flex justify-end gap-2">
                <button
                  ref={cancelarDesactivarRef}
                  type="button"
                  onClick={cerrarModal}
                  className="rounded-md border border-[var(--ui-borde)] bg-[var(--ui-boton)] px-3 py-1.5 text-sm font-medium hover:bg-[var(--ui-boton-hover)] cursor-pointer"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  disabled={procesando}
                  onClick={() => void confirmarDesactivar(modal.webhook)}
                  className="badge-render-danger rounded-md px-3 py-1.5 text-sm font-medium disabled:opacity-50 cursor-pointer"
                >
                  Desactivar el webhook
                </button>
              </div>
            </div>
          )}
        </DialogoModal>
      )}
    </section>
  );
}
