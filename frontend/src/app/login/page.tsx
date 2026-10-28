"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Layers, ShieldCheck } from "lucide-react";

import {
  cargarGoogle,
  clientIdGoogle,
  consultarMisOrganizaciones,
  guardarCredencialPendiente,
  guardarMisOrganizaciones,
  haCaducado,
  leerCredencial,
  modoAutenticacion,
  RUTA_ORGANIZACIONES,
  useSesion,
} from "@/lib/auth";
import { entrarEnOrganizacion } from "@/store/datosDeTrabajo";

const SIN_ORGANIZACION = "Tu cuenta no pertenece a ninguna organización; pide una invitación.";

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

  // La organización ya no se configura por despliegue (FE-21): se elige al iniciar sesión.
  const configuracionIncompleta = modo === "oidc" && !clientIdGoogle() ? "NEXT_PUBLIC_GOOGLE_CLIENT_ID" : null;

  /**
   * Con la credencial de Google se consultan las organizaciones de la persona ANTES de abrir la
   * sesión: los datos del navegador se reclaman para esa organización (FE-20 y FE-21) y solo
   * después empieza a hablarse con el servidor en su nombre.
   */
  const alRecibirCredencial = React.useCallback(async (credential: string | undefined) => {
    setError(null);
    const credencial = credential ? leerCredencial(credential) : null;
    if (!credential || !credencial || haCaducado(credencial.exp)) {
      setError("No se pudo iniciar sesión: Google devolvió una identificación no válida o ya caducada.");
      return;
    }
    let organizaciones;
    try {
      organizaciones = await consultarMisOrganizaciones(credential);
    } catch (err: unknown) {
      setError(`No se pudieron consultar tus organizaciones: ${err instanceof Error ? err.message : "error de conexión"}.`);
      return;
    }
    if (organizaciones.length === 0) {
      setError(SIN_ORGANIZACION);
      return;
    }
    guardarMisOrganizaciones(organizaciones);
    if (organizaciones.length > 1) {
      guardarCredencialPendiente(credential);
      router.push(RUTA_ORGANIZACIONES);
      return;
    }
    if (!entrarEnOrganizacion(credential, credencial.email, organizaciones[0])) {
      setError("No se pudo iniciar sesión: Google devolvió una identificación no válida o ya caducada.");
      return;
    }
    // Recarga completa: los stores leen los datos de esta organización, no los de memoria.
    window.location.assign("/dashboard");
  }, [router]);

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
            void alRecibirCredencial(credential);
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
  }, [modo, listo, sesion, configuracionIncompleta, alRecibirCredencial]);

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
