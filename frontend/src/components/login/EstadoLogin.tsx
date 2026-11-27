// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";

/**
 * Avisos del inicio de sesión (FE-29 §4): por qué una cuenta de Google no entra y qué puede hacer la
 * persona. Los textos son fijos (UX/UI, 2026-11-23): nunca llevan códigos, `err.message` ni el texto del
 * servidor, y el único dato personal es el correo de la credencial recién usada (R6).
 *
 * Cada aviso es `role="alert"` con `data-tipo`. Si tiene título, el foco va al h2; si no, a su acción, y
 * en `sesion` vuelve al botón de Google (`enfocarGoogle`).
 */
import * as React from "react";

import type { TipoErrorDeAcceso } from "@/lib/auth/organizacion";

export type TipoAviso = TipoErrorDeAcceso | "sin_organizaciones" | "google_no_carga";

export const AYUDA_OTRA_CUENTA =
  "Si Google vuelve a ofrecerte la misma cuenta, cierra sesión en Google o abre una ventana privada.";
export const CONSULTANDO = "Consultando tus organizaciones…";

interface PropsEstadoLogin {
  tipo: TipoAviso;
  /** Correo de la credencial que la persona acaba de usar (R6). */
  correo: string;
  reintentando?: boolean;
  onOtraCuenta?: () => void;
  onReintentar?: () => void;
  enfocarGoogle?: () => void;
  testId?: string;
}

interface Contenido {
  titulo?: string;
  mensaje: (correo: React.ReactNode) => React.ReactNode;
  accion: "otra_cuenta" | "reintentar" | "recargar" | "google";
}

const SIN_ACCESO: Contenido = {
  titulo: "Esta cuenta no tiene acceso",
  mensaje: (correo) => (
    <>
      La cuenta {correo} no está dada de alta en la plataforma. Pide a la persona que administra tu
      organización que te dé de alta con este correo, o entra con otra cuenta de Google.
    </>
  ),
  accion: "otra_cuenta",
};

const CONTENIDO: Record<TipoAviso, Contenido> = {
  no_registrado: SIN_ACCESO,
  sin_permiso: SIN_ACCESO,
  vinculada_otra: {
    titulo: "Este correo usa otra cuenta de Google",
    mensaje: (correo) => (
      <>
        El correo {correo} ya está vinculado a otra cuenta de Google. Entra con la cuenta con la que te
        diste de alta, o pide ayuda a la persona que administra tu organización.
      </>
    ),
    accion: "otra_cuenta",
  },
  sin_organizaciones: {
    titulo: "Aún no perteneces a ninguna organización",
    mensaje: (correo) => (
      <>
        Tu cuenta {correo} está dada de alta, pero no tiene ninguna organización asignada. Pide a la persona
        que administra tu organización que te añada.
      </>
    ),
    accion: "otra_cuenta",
  },
  sesion: {
    mensaje: () => "Tu inicio de sesión con Google caducó. Vuelve a pulsar el botón de Google.",
    accion: "google",
  },
  servidor: {
    mensaje: () => "La plataforma no pudo responder. Inténtalo de nuevo en unos minutos.",
    accion: "reintentar",
  },
  red: {
    mensaje: () => "No pudimos conectar con la plataforma. Revisa tu conexión e inténtalo de nuevo.",
    accion: "reintentar",
  },
  google_no_carga: {
    mensaje: () => "No pudimos cargar el inicio de sesión con Google. Revisa tu conexión y recarga la página.",
    accion: "recargar",
  },
};

const BOTON =
  "inline-flex min-h-10 w-full items-center justify-center rounded-md bg-[var(--ui-primario)] px-3 py-2 text-sm font-semibold text-[var(--ui-primario-texto)] cursor-pointer aria-disabled:cursor-wait aria-disabled:opacity-90";

export default function EstadoLogin({
  tipo,
  correo,
  reintentando = false,
  onOtraCuenta,
  onReintentar,
  enfocarGoogle,
  testId = "login-error",
}: PropsEstadoLogin) {
  const contenido = CONTENIDO[tipo];
  const tituloRef = React.useRef<HTMLHeadingElement>(null);
  const accionRef = React.useRef<HTMLButtonElement>(null);

  React.useEffect(() => {
    if (contenido.titulo) tituloRef.current?.focus();
    else if (contenido.accion === "google") enfocarGoogle?.();
    else accionRef.current?.focus();
    // Solo al cambiar de aviso: el foco no debe saltar mientras se reintenta.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tipo]);

  const destacado = <strong className="font-semibold break-all">{correo}</strong>;

  return (
    <div
      role="alert"
      data-tipo={tipo}
      data-testid={testId}
      className="flex w-full flex-col gap-3 rounded-md border border-[var(--ui-error-borde)] bg-[var(--ui-error-fondo)] px-3 py-3 text-sm text-[var(--ui-error-texto)]"
    >
      {contenido.titulo && (
        <h2 ref={tituloRef} tabIndex={-1} className="text-base font-semibold text-[var(--ui-error-texto)] outline-none">
          {contenido.titulo}
        </h2>
      )}
      <p className="break-words">{contenido.mensaje(destacado)}</p>

      {contenido.accion === "otra_cuenta" && (
        <>
          <button ref={accionRef} type="button" onClick={onOtraCuenta} className={BOTON}>
            Usar otra cuenta de Google
          </button>
          <p className="text-xs text-[var(--ui-texto-suave)]">{AYUDA_OTRA_CUENTA}</p>
        </>
      )}

      {contenido.accion === "reintentar" && (
        <>
          <button
            ref={accionRef}
            type="button"
            aria-disabled={reintentando || undefined}
            onClick={() => {
              if (!reintentando) onReintentar?.();
            }}
            className={BOTON}
          >
            {reintentando ? "Reintentando…" : "Reintentar"}
          </button>
          {reintentando && (
            <p role="status" className="text-xs text-[var(--ui-texto-suave)]">
              {CONSULTANDO}
            </p>
          )}
        </>
      )}

      {contenido.accion === "recargar" && (
        <button ref={accionRef} type="button" onClick={() => window.location.reload()} className={BOTON}>
          Recargar la página
        </button>
      )}
    </div>
  );
}
