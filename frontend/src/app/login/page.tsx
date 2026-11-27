// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Layers, ShieldCheck } from "lucide-react";

import {
  cargarGoogle,
  cerrarSesion,
  clientIdGoogle,
  consultarMisOrganizaciones,
  guardarCredencialPendiente,
  guardarMisOrganizaciones,
  haCaducado,
  leerCredencial,
  leerSesion,
  modoAutenticacion,
  olvidarCuentaDeGoogle,
  RUTA_ORGANIZACIONES,
  useSesion,
} from "@/lib/auth";
import type { GoogleId } from "@/lib/auth/google";
import { entrarEnOrganizacion } from "@/store/datosDeTrabajo";
// === ORG-21 ===
import { guardarSesionDeOperador } from "@/lib/auth/sesion";
import { esOperadorDeLaPlataforma, ErrorPlataforma } from "@/lib/plataforma/cliente";
// === fin ORG-21 ===
// === DEMO-04 ===
import EntradaDemo, { type ReceptorDeCredencial } from "@/components/demo/EntradaDemo";
// === fin DEMO-04 ===
// === FE-29 ===
import EstadoLogin, { type TipoAviso } from "@/components/login/EstadoLogin";
import { ErrorDeAcceso, type TipoErrorDeAcceso } from "@/lib/auth/organizacion";
// === fin FE-29 ===

// === ORG-21 ===
/**
 * Quien no pertenece a ninguna organización pero es operador de la plataforma entra en
 * `/plataforma` (ORG-21): se guarda su sesión de operador, sin organización activa, y se recarga allí.
 * FE-29 R3: devuelve "entro" si navega, "no" si no es operador (403) y el tipo del fallo si la
 * comprobación no pudo hacerse (red, servidor o sesión). Esa sesión no despierta a esta pantalla.
 */
async function entrarComoOperador(credential: string): Promise<"entro" | "no" | TipoErrorDeAcceso> {
  let operador = false;
  try {
    operador = await esOperadorDeLaPlataforma(credential);
  } catch (err: unknown) {
    if (!(err instanceof ErrorPlataforma)) return "red";
    return err.status === 401 ? "sesion" : "servidor";
  }
  if (!operador) return "no";
  if (!guardarSesionDeOperador(credential)) return "sesion";
  window.location.assign("/plataforma");
  return "entro";
}
// === fin ORG-21 ===

// === BIB-412 ===
/**
 * Entrada del equipo editorial (demo): prueba la credencial como operador (igual que ORG-21) y, si lo es, abre su
 * sesión de operador y lleva a la biblioteca editorial de la plataforma. Devuelve lo mismo que `entrarComoOperador`.
 */
async function entrarComoEquipoEditorial(credential: string): Promise<"entro" | "no" | TipoErrorDeAcceso> {
  let operador = false;
  try {
    operador = await esOperadorDeLaPlataforma(credential);
  } catch (err: unknown) {
    if (!(err instanceof ErrorPlataforma)) return "red";
    return err.status === 401 ? "sesion" : "servidor";
  }
  if (!operador) return "no";
  if (!guardarSesionDeOperador(credential)) return "sesion";
  window.location.assign("/plataforma/biblioteca");
  return "entro";
}
// === fin BIB-412 ===

// === FE-29 ===
/**
 * R4: una sesión guardada lleva al panel. Si el panel la rechaza y vuelve aquí sin sesión, esta marca
 * (reciente) dice que no es una visita nueva: se muestra el aviso de sesión terminada, nunca /login a secas.
 */
const CLAVE_HACIA_PANEL = "lopdp-login-hacia-panel-v1";
const VIGENCIA_MARCA_MS = 60_000;

function marcarHaciaPanel(): void {
  try {
    window.sessionStorage.setItem(CLAVE_HACIA_PANEL, String(Date.now()));
  } catch {
    // sin almacenamiento: solo se pierde el aviso
  }
}

function volvioDelPanel(): boolean {
  try {
    const marca = Number(window.sessionStorage.getItem(CLAVE_HACIA_PANEL));
    window.sessionStorage.removeItem(CLAVE_HACIA_PANEL);
    return Number.isFinite(marca) && marca > 0 && Date.now() - marca < VIGENCIA_MARCA_MS;
  } catch {
    return false;
  }
}

/** Tipos tras los que se prueba si es operador de la plataforma (R3); los demás se muestran tal cual. */
const PRUEBA_OPERADOR: ReadonlySet<TipoErrorDeAcceso> = new Set(["no_registrado", "sin_permiso"]);
// === fin FE-29 ===

const AVISOS: Record<string, string> = {
  expirada: "Tu sesión terminó. Vuelve a iniciar sesión.",
};

interface Aviso {
  tipo: TipoAviso;
  correo: string;
}

export default function LoginPage() {
  const router = useRouter();
  const { listo, sesion } = useSesion();
  const botonRef = React.useRef<HTMLDivElement>(null);
  const googleRef = React.useRef<GoogleId | null>(null);
  const [estado, setEstado] = React.useState<Aviso | null>(null);
  const [reintentando, setReintentando] = React.useState(false);
  const [aviso, setAviso] = React.useState<string | null>(null);
  const [modo, setModo] = React.useState<"oidc" | "headers" | null>(null);
  // FE-29: la credencial recién usada, para «Reintentar» (se borra con «Usar otra cuenta de Google»).
  const credencialActual = React.useRef<string | null>(null);
  // === DEMO-04 ===
  // En `demo`, la credencial de Google va a la entrada de la demo y no a las organizaciones.
  const receptorDemo = React.useRef<ReceptorDeCredencial | null>(null);
  const registrarDemo = React.useCallback((r: ReceptorDeCredencial | null) => {
    receptorDemo.current = r;
  }, []);
  // === fin DEMO-04 ===
  // === BIB-412 ===
  // Entrada del equipo editorial (solo en la demo): su propio botón de Google y su propio destino.
  const botonEditorialRef = React.useRef<HTMLDivElement>(null);
  const [editorial, setEditorial] = React.useState(false);
  React.useEffect(() => {
    setEditorial(document.querySelector('[data-testid="aviso-entorno"][data-entorno="demo"]') !== null);
  }, []);
  // === fin BIB-412 ===

  // El modo depende del navegador (en desarrollo lo fijan las pruebas): se resuelve ya montado.
  React.useEffect(() => {
    const modoActual = modoAutenticacion();
    setModo(modoActual);
    const parametros = new URLSearchParams(window.location.search);
    const motivo = parametros.get("motivo");
    if (motivo && AVISOS[motivo]) {
      setAviso(AVISOS[motivo]);
    } else if (modoActual === "oidc" && !leerSesion() && volvioDelPanel()) {
      // R4: el panel rechazó la sesión guardada y volvió a /login a secas. Con sesión vigente la marca no
      // se consume: es la ida al panel (los efectos se repiten al montar en desarrollo).
      setAviso(AVISOS.expirada);
      router.replace("/login?motivo=expirada");
    }
  }, [router]);

  React.useEffect(() => {
    if (!listo) return;
    if (modo === "headers") router.replace("/dashboard");
    else if (modo === "oidc" && sesion) {
      marcarHaciaPanel();
      router.replace("/dashboard");
    }
  }, [listo, modo, sesion, router]);

  // La organización ya no se configura por despliegue (FE-21): se elige al iniciar sesión.
  const configuracionIncompleta = modo === "oidc" && !clientIdGoogle() ? "NEXT_PUBLIC_GOOGLE_CLIENT_ID" : null;

  const enfocarGoogle = React.useCallback(() => {
    botonRef.current?.focus();
  }, []);

  const pintarBotonGoogle = React.useCallback(() => {
    const google = googleRef.current;
    if (!google || !botonRef.current) return;
    botonRef.current.replaceChildren();
    google.renderButton(botonRef.current, { type: "standard", theme: "outline", size: "large", text: "signin_with", locale: "es", width: 280 });
    // === BIB-412 ===
    if (botonEditorialRef.current) {
      botonEditorialRef.current.replaceChildren();
      google.renderButton(botonEditorialRef.current, { type: "standard", theme: "outline", size: "large", text: "signin_with", locale: "es", width: 280 });
    }
    // === fin BIB-412 ===
  }, []);

  // === BIB-412 ===
  // Al aparecer la entrada editorial hay que pintar su botón (el de Google ya puede estar cargado).
  React.useEffect(() => {
    if (editorial && googleRef.current) pintarBotonGoogle();
  }, [editorial, pintarBotonGoogle]);
  // === fin BIB-412 ===

  /**
   * Con la credencial de Google se consultan las organizaciones de la persona ANTES de abrir la
   * sesión: los datos del navegador se reclaman para esa organización (FE-20 y FE-21) y solo
   * después empieza a hablarse con el servidor en su nombre. R4: cada camino navega o deja un aviso.
   */
  const consultar = React.useCallback(async (credential: string, correo: string) => {
    const mostrar = (tipo: TipoAviso) => setEstado({ tipo, correo });
    let organizaciones;
    try {
      organizaciones = await consultarMisOrganizaciones(credential);
    } catch (err: unknown) {
      const tipo: TipoErrorDeAcceso = err instanceof ErrorDeAcceso ? err.tipo : "red";
      if (!PRUEBA_OPERADOR.has(tipo)) return mostrar(tipo);
      // === ORG-21 ===
      const operador = await entrarComoOperador(credential);
      // === fin ORG-21 ===
      if (operador === "entro") return;
      return mostrar(operador === "no" ? tipo : operador);
    }
    if (organizaciones.length === 0) {
      // === ORG-21 ===
      const operador = await entrarComoOperador(credential);
      // === fin ORG-21 ===
      if (operador === "entro") return;
      return mostrar(operador === "no" ? "sin_organizaciones" : operador);
    }
    guardarMisOrganizaciones(organizaciones);
    if (organizaciones.length > 1) {
      guardarCredencialPendiente(credential);
      router.push(RUTA_ORGANIZACIONES);
      return;
    }
    if (!entrarEnOrganizacion(credential, correo, organizaciones[0])) return mostrar("sesion");
    // Recarga completa: los stores leen los datos de esta organización, no los de memoria.
    window.location.assign("/dashboard");
  }, [router]);

  const alRecibirCredencial = React.useCallback(async (credential: string | undefined) => {
    setEstado(null);
    const credencial = credential ? leerCredencial(credential) : null;
    if (!credential || !credencial || haCaducado(credencial.exp)) {
      credencialActual.current = null;
      setEstado({ tipo: "sesion", correo: credencial?.email ?? "" });
      return;
    }
    credencialActual.current = credential;
    // === BIB-412 ===
    // La credencial viene de la entrada editorial si el foco quedó en su botón (el de Google es un iframe).
    if (editorial && botonEditorialRef.current?.contains(document.activeElement)) {
      const resultado = await entrarComoEquipoEditorial(credential);
      if (resultado !== "entro") setEstado({ tipo: resultado === "no" ? "no_registrado" : resultado, correo: credencial.email });
      return;
    }
    // === fin BIB-412 ===
    // === DEMO-04 ===
    if (receptorDemo.current && (await receptorDemo.current(credential))) return;
    // === fin DEMO-04 ===
    await consultar(credential, credencial.email);
  }, [consultar, editorial]);

  // FE-29 · «Reintentar»: la misma consulta con la misma credencial; si caducó entretanto, `sesion`.
  const reintentar = React.useCallback(async () => {
    const credential = credencialActual.current;
    const credencial = credential ? leerCredencial(credential) : null;
    if (!credential || !credencial || haCaducado(credencial.exp)) {
      setEstado((previo) => ({ tipo: "sesion", correo: previo?.correo ?? "" }));
      return;
    }
    setReintentando(true);
    try {
      await consultar(credential, credencial.email);
    } finally {
      setReintentando(false);
    }
  }, [consultar]);

  // FE-29 R5 · «Usar otra cuenta de Google»: Google no deja cerrar su sesión desde la página.
  const usarOtraCuenta = React.useCallback(() => {
    olvidarCuentaDeGoogle();
    credencialActual.current = null;
    cerrarSesion(); // sesión, organizaciones y credencial pendiente del navegador
    setEstado(null);
    pintarBotonGoogle();
    enfocarGoogle();
  }, [pintarBotonGoogle, enfocarGoogle]);

  React.useEffect(() => {
    if (modo !== "oidc" || !listo || sesion || configuracionIncompleta) return;
    let cancelado = false;
    cargarGoogle()
      .then((google) => {
        if (cancelado || !botonRef.current) return;
        googleRef.current = google;
        google.initialize({
          client_id: clientIdGoogle(),
          auto_select: false,
          cancel_on_tap_outside: true,
          callback: ({ credential }) => {
            void alRecibirCredencial(credential);
          },
        });
        pintarBotonGoogle();
      })
      .catch(() => {
        if (!cancelado) setEstado({ tipo: "google_no_carga", correo: "" });
      });
    return () => {
      cancelado = true;
    };
  }, [modo, listo, sesion, configuracionIncompleta, alRecibirCredencial, pintarBotonGoogle]);

  return (
    <main className="flex min-h-screen w-full items-center justify-center bg-white px-4 text-zinc-800">
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

        {modo === "oidc" && !configuracionIncompleta && !editorial && (
          <div
            ref={botonRef}
            tabIndex={-1}
            data-testid="login-boton-google"
            className="flex min-h-10 justify-center outline-none"
          />
        )}

        {/* === DEMO-04 === */}
        <EntradaDemo registrar={registrarDemo} />
        {/* === fin DEMO-04 === */}

        {/* === BIB-412 === */}
        {editorial && modo === "oidc" && !configuracionIncompleta && (
          <>
            <div ref={botonRef} tabIndex={-1} data-testid="login-boton-google" className="flex min-h-10 justify-center outline-none" />
            <div role="group" aria-label="Entrar como equipo editorial" aria-describedby="ayuda-entrada-editorial"
              data-testid="entrada-editorial" className="flex w-full flex-col items-center gap-3">
              <div className="text-center">
                <h2 className="text-base font-semibold">Soy del equipo editorial</h2>
                <p id="ayuda-entrada-editorial" className="mt-1 text-sm text-zinc-500">
                  Para quienes mantienen el catálogo de plantillas de la plataforma. Entras con tu cuenta de Google de operador.
                </p>
              </div>
              <div ref={botonEditorialRef} tabIndex={-1} data-testid="login-boton-google-editorial" className="flex min-h-10 justify-center outline-none" />
            </div>
          </>
        )}
        {/* === fin BIB-412 === */}

        {/* === FE-29 === */}
        {estado && (
          <EstadoLogin
            tipo={estado.tipo}
            correo={estado.correo}
            reintentando={reintentando}
            onOtraCuenta={usarOtraCuenta}
            onReintentar={() => void reintentar()}
            enfocarGoogle={enfocarGoogle}
          />
        )}
        {/* === fin FE-29 === */}

        <p className="flex items-center gap-1.5 text-xs text-zinc-400">
          <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
          Solo se usa tu correo verificado de Google para identificarte.
        </p>
      </section>
    </main>
  );
}
