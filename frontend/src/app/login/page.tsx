"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Layers, ShieldCheck } from "lucide-react";

import {
  cargarGoogle,
  clientIdGoogle,
  guardarSesion,
  haCaducado,
  leerCredencial,
  modoAutenticacion,
  tenantConfigurado,
  useSesion,
} from "@/lib/auth";
import { duenoDe, reclamarDatosDeTrabajo } from "@/store/datosDeTrabajo";

const AVISOS: Record<string, string> = {
  expirada: "Tu sesión expiró. Vuelve a iniciar sesión para continuar.",
};

export default function LoginPage() {
  const router = useRouter();
  const { listo, sesion } = useSesion();
  const botonRef = React.useRef<HTMLDivElement>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [aviso, setAviso] = React.useState<string | null>(null);
  const [modo, setModo] = React.useState<"oidc" | "headers" | null>(null);

  // El modo depende del navegador (en desarrollo lo fijan las pruebas): se resuelve ya montado.
  React.useEffect(() => {
    setModo(modoAutenticacion());
    const motivo = new URLSearchParams(window.location.search).get("motivo");
    if (motivo && AVISOS[motivo]) setAviso(AVISOS[motivo]);
  }, []);

  React.useEffect(() => {
    if (listo && (modo === "headers" || sesion)) router.replace("/dashboard");
  }, [listo, modo, sesion, router]);

  const configuracionIncompleta =
    modo === "oidc" && (!clientIdGoogle() ? "NEXT_PUBLIC_GOOGLE_CLIENT_ID" : !tenantConfigurado() ? "NEXT_PUBLIC_TENANT_ID" : null);

  React.useEffect(() => {
    if (modo !== "oidc" || !listo || sesion || configuracionIncompleta) return;
    let cancelado = false;
    cargarGoogle()
      .then((google) => {
        if (cancelado || !botonRef.current) return;
        google.initialize({
          client_id: clientIdGoogle(),
          auto_select: false,
          cancel_on_tap_outside: true,
          callback: ({ credential }) => {
            // Antes de abrir la sesión, que es cuando se sincroniza con el servidor: los datos del
            // navegador que sean de otra persona u organización se vacían (FE-20).
            const credencial = credential ? leerCredencial(credential) : null;
            if (credencial && !haCaducado(credencial.exp)) {
              reclamarDatosDeTrabajo(duenoDe(credencial.email, tenantConfigurado()));
            }
            if (!credential || !guardarSesion(credential)) {
              setError("No se pudo iniciar sesión: Google devolvió una identificación no válida o ya caducada.");
            }
          },
        });
        google.renderButton(botonRef.current, { type: "standard", theme: "outline", size: "large", text: "signin_with", locale: "es", width: 280 });
      })
      .catch((err: unknown) => {
        if (!cancelado) setError(err instanceof Error ? err.message : "No se pudo cargar el inicio de sesión.");
      });
    return () => {
      cancelado = true;
    };
  }, [modo, listo, sesion, configuracionIncompleta]);

  return (
    <main className="flex min-h-screen w-screen items-center justify-center bg-white px-4 text-zinc-800">
      <section
        aria-labelledby="titulo-login"
        className="flex w-full max-w-sm flex-col items-center gap-5 rounded-xl border border-[#e8dcf5] p-8 shadow-sm"
      >
        <Layers className="h-8 w-8 text-[#9a3bf1]" aria-hidden="true" />
        <div className="text-center">
          <h1 id="titulo-login" className="text-lg font-semibold">Plataforma LOPDP 360</h1>
          <p className="mt-1 text-sm text-zinc-500">Inicia sesión con tu cuenta de Google para entrar al panel.</p>
        </div>

        {aviso && (
          <p role="status" data-testid="login-aviso" className="w-full rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
            {aviso}
          </p>
        )}

        {modo === "oidc" && configuracionIncompleta && (
          <p role="alert" data-testid="login-configuracion" className="w-full rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            Falta configurar {configuracionIncompleta} en el servidor. Avisa a quien administra la plataforma.
          </p>
        )}

        {modo === "oidc" && !configuracionIncompleta && (
          <div ref={botonRef} data-testid="login-boton-google" className="flex min-h-10 justify-center" />
        )}

        {error && (
          <p role="alert" data-testid="login-error" className="w-full rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <p className="flex items-center gap-1.5 text-xs text-zinc-400">
          <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
          Solo se usa tu correo verificado de Google para identificarte.
        </p>
      </section>
    </main>
  );
}
