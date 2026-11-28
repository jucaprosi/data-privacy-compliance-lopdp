// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";

import * as React from "react";
import { CheckCircle2, KeyRound, ShieldCheck } from "lucide-react";

import {
  cargarGoogle,
  clientIdGoogle,
  guardarSesion,
  modoAutenticacion,
  useSesion,
} from "@/lib/auth";
import { ErrorPlataforma, plataformaApi, type AceptacionInvitacion } from "@/lib/plataforma";

function mensajeAceptacion(error: unknown): string {
  if (!(error instanceof ErrorPlataforma)) return "No se pudo aceptar la invitación. Inténtalo nuevamente.";
  if (error.status === 403) return "Esta invitación pertenece a un correo distinto del que inició sesión.";
  if (error.status === 404) return "El código de invitación no es válido.";
  if (error.status === 400) {
    const detalle = error.message.toLowerCase();
    if (detalle.includes("caduc")) return "La invitación ha caducado. Solicita una nueva.";
    if (detalle.includes("revoc")) return "La invitación fue revocada. Solicita una nueva.";
    if (detalle.includes("usad") || detalle.includes("acept")) return "La invitación ya fue utilizada.";
  }
  return error.message;
}

export default function InvitacionPage() {
  const { listo, sesion } = useSesion();
  const botonGoogle = React.useRef<HTMLDivElement>(null);
  const [modo, setModo] = React.useState<"oidc" | "headers" | null>(null);
  const [codigo, setCodigo] = React.useState("");
  const [nombre, setNombre] = React.useState("");
  const [enviando, setEnviando] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [resultado, setResultado] = React.useState<AceptacionInvitacion | null>(null);

  React.useEffect(() => {
    setModo(modoAutenticacion());
    const url = new URL(window.location.href);
    const recibido = url.searchParams.get("codigo");
    if (recibido) {
      setCodigo(recibido);
      url.searchParams.delete("codigo");
      window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
    }
  }, []);

  React.useEffect(() => {
    if (modo !== "oidc" || !listo || sesion || !clientIdGoogle()) return;
    let cancelado = false;
    cargarGoogle().then((google) => {
      if (cancelado || !botonGoogle.current) return;
      google.initialize({
        client_id: clientIdGoogle(),
        auto_select: false,
        cancel_on_tap_outside: true,
        callback: ({ credential }) => {
          if (!credential || !guardarSesion(credential)) setError("No se pudo iniciar sesión con Google.");
        },
      });
      google.renderButton(botonGoogle.current, { type: "standard", theme: "outline", size: "large", text: "signin_with", locale: "es", width: 280 });
    }).catch(() => setError("No se pudo cargar el inicio de sesión con Google."));
    return () => { cancelado = true; };
  }, [listo, modo, sesion]);

  async function aceptar(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setEnviando(true);
    setError(null);
    try {
      setResultado(await plataformaApi.aceptar(codigo.trim(), nombre));
      setCodigo("");
    } catch (err) {
      setError(mensajeAceptacion(err));
    } finally {
      setEnviando(false);
    }
  }

  const autenticado = modo === "headers" || Boolean(sesion);

  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--background)] px-4 py-10 text-[var(--foreground)]">
      <section aria-labelledby="titulo-invitacion" className="w-full max-w-lg rounded-2xl border border-[var(--ui-borde)] bg-[var(--ui-superficie)] p-7 shadow-2xl">
        <KeyRound className="h-9 w-9 text-[var(--ui-exito-texto)]" aria-hidden="true" />
        <h1 id="titulo-invitacion" className="mt-4 text-2xl font-semibold">Aceptar invitación</h1>
        <p className="mt-2 text-sm text-[var(--ui-texto-suave)]">Inicia sesión con el correo invitado e introduce el código recibido.</p>

        {!autenticado && <div className="mt-6 rounded-xl border border-[var(--ui-borde-control)] bg-[var(--background)]/60 p-4"><p className="mb-3 text-sm">Primero, verifica tu identidad:</p><div ref={botonGoogle} data-testid="invitacion-google" /></div>}
        {autenticado && !resultado && (
          <form onSubmit={aceptar} aria-label="Aceptar invitación" className="mt-6 space-y-4">
            {sesion && <p className="flex items-center gap-2 rounded-lg bg-[var(--ui-exito-fondo)] px-3 py-2 text-sm text-[var(--ui-exito-texto)]"><ShieldCheck className="h-4 w-4" /> Sesión iniciada como {sesion.email}</p>}
            <label className="block text-sm text-[var(--ui-texto-suave)]">Código de invitación<input required minLength={10} autoComplete="off" value={codigo} onChange={(e) => setCodigo(e.target.value)} className="mt-1 w-full rounded-lg border border-[var(--ui-borde-control)] bg-[var(--background)] px-3 py-2 font-mono outline-none focus:border-[var(--ui-primario)]" /></label>
            <label className="block text-sm text-[var(--ui-texto-suave)]">Nombre para mostrar (opcional)<input value={nombre} onChange={(e) => setNombre(e.target.value)} className="mt-1 w-full rounded-lg border border-[var(--ui-borde-control)] bg-[var(--background)] px-3 py-2 outline-none focus:border-[var(--ui-primario)]" /></label>
            <button disabled={enviando} className="w-full rounded-lg bg-[var(--ui-primario)] px-4 py-2.5 text-sm font-semibold text-[var(--ui-primario-texto)] hover:bg-[var(--ui-primario-hover)] disabled:opacity-50">{enviando ? "Aceptando…" : "Aceptar e ingresar"}</button>
          </form>
        )}
        {error && <p role="alert" className="mt-4 rounded-lg border border-[var(--ui-error-borde)] bg-[var(--ui-error-fondo)] px-3 py-2 text-sm text-[var(--ui-error-texto)]">{error}</p>}
        {resultado && <div role="status" className="mt-6 rounded-xl border border-[var(--ui-exito-borde)] bg-[var(--ui-exito-fondo)] p-5 text-center"><CheckCircle2 className="mx-auto h-9 w-9 text-[var(--ui-exito-texto)]" /><h2 className="mt-3 text-lg font-semibold">Invitación aceptada</h2><p className="mt-1 text-sm text-[var(--ui-exito-texto)]">{resultado.mensaje}</p></div>}
      </section>
    </main>
  );
}
