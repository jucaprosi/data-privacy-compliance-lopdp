// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
"use client";

/**
 * Elegir o cambiar la organización con la que se trabaja (FE-21).
 *
 * Llega aquí quien pertenece a varias organizaciones, al iniciar sesión (con la credencial aún
 * pendiente) o desde «Cambiar organización» del encabezado (con la sesión abierta). Al elegir, los
 * datos del navegador se reclaman para esa organización y la página se recarga: todas las
 * peticiones llevan desde entonces la organización nueva.
 */
import * as React from "react";
import { useRouter } from "next/navigation";
import { Building2, Layers } from "lucide-react";
import {
  cerrarSesion,
  consultarMisOrganizaciones,
  guardarMisOrganizaciones,
  leerCredencial,
  leerCredencialPendiente,
  leerMisOrganizaciones,
  leerOrganizacionActiva,
  leerSesion,
  modoAutenticacion,
  olvidarCuentaDeGoogle,
  RUTA_LOGIN,
  type Organizacion,
} from "@/lib/auth";
// === FE-29 ===
import EstadoLogin, { type TipoAviso } from "@/components/login/EstadoLogin";
import { ErrorDeAcceso } from "@/lib/auth/organizacion";

const NOTA_LISTA_GUARDADA = "Lista guardada en este navegador; puede no estar al día.";
// === fin FE-29 ===
import { useAuditStore } from "@/store/useAuditStore";
import { cambiarDeOrganizacion, entrarEnOrganizacion, resolverCambiosSinGuardar } from "@/store/datosDeTrabajo";

const ETIQUETA_ROL: Record<string, string> = {
  admin_organizacion: "Administrador",
  coordinador: "Coordinador",
  dpo: "DPO",
  implementador: "Implementador",
  responsable_area: "Responsable de área",
};

interface Acceso {
  token: string;
  email: string;
  /** True si ya hay sesión (cambio); false si la credencial está pendiente (primer ingreso). */
  conSesion: boolean;
}

export default function OrganizacionesPage() {
  const router = useRouter();
  const [acceso, setAcceso] = React.useState<Acceso | null>(null);
  const [organizaciones, setOrganizaciones] = React.useState<Organizacion[] | null>(null);
  const [activa, setActiva] = React.useState<Organizacion | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  // FE-29: por qué no se pudieron consultar las organizaciones (§4), y si se está reintentando.
  const [fallo, setFallo] = React.useState<TipoAviso | null>(null);
  const [reintentando, setReintentando] = React.useState(false);
  const salirRef = React.useRef<HTMLButtonElement>(null);
  const [pendienteDeCambio, setPendienteDeCambio] = React.useState<Organizacion | null>(null);

  React.useEffect(() => {
    if (modoAutenticacion() !== "oidc") {
      router.replace("/dashboard");
      return;
    }
    const sesion = leerSesion();
    const pendiente = sesion ? null : leerCredencialPendiente();
    const token = sesion?.token ?? pendiente;
    const email = sesion?.email ?? (pendiente ? leerCredencial(pendiente)?.email : undefined);
    if (!token || !email) {
      router.replace(RUTA_LOGIN);
      return;
    }
    setAcceso({ token, email, conSesion: Boolean(sesion) });
    setActiva(sesion ? leerOrganizacionActiva() : null);
    let vigente = true;
    void consultar(token, () => vigente);
    return () => {
      vigente = false;
    };
  }, [router]);

  // === FE-29 ===
  /** Consulta las organizaciones; si no puede, el aviso de su tipo (R2) y la lista guardada debajo. */
  async function consultar(token: string, vigente: () => boolean = () => true): Promise<void> {
    try {
      const lista = await consultarMisOrganizaciones(token);
      if (!vigente()) return;
      guardarMisOrganizaciones(lista);
      setFallo(null);
      setOrganizaciones(lista);
    } catch (err: unknown) {
      if (!vigente()) return;
      setFallo(err instanceof ErrorDeAcceso ? err.tipo : "red");
      setOrganizaciones(leerMisOrganizaciones());
    }
  }

  const reintentar = async () => {
    if (!acceso) return;
    const credencial = leerCredencial(acceso.token);
    if (!credencial || credencial.exp * 1000 <= Date.now()) {
      setFallo("sesion");
      return;
    }
    setReintentando(true);
    try {
      await consultar(acceso.token);
    } finally {
      setReintentando(false);
    }
  };

  /** R5: olvida la cuenta elegida, la credencial pendiente y la sesión, y vuelve al botón de Google. */
  const usarOtraCuenta = () => {
    olvidarCuentaDeGoogle();
    cerrarSesion();
    router.replace(RUTA_LOGIN);
  };
  // === fin FE-29 ===

  const cambiar = (org: Organizacion) => {
    if (!acceso) return;
    cambiarDeOrganizacion(acceso.email, org);
    window.location.assign("/dashboard");
  };

  const elegir = (org: Organizacion) => {
    if (!acceso) return;
    if (!acceso.conSesion) {
      if (!entrarEnOrganizacion(acceso.token, acceso.email, org)) {
        setFallo("sesion");
        return;
      }
      window.location.assign("/dashboard");
      return;
    }
    if (activa?.tenant_id === org.tenant_id) {
      router.push("/dashboard");
      return;
    }
    if (useAuditStore.getState().cambiosSinGuardar) {
      setPendienteDeCambio(org);
      return;
    }
    cambiar(org);
  };

  const resolverYCambiar = (decision: "guardar" | "descartar") => {
    if (!pendienteDeCambio) return;
    if (!resolverCambiosSinGuardar(decision)) {
      setError("No se pudo guardar: el almacenamiento del navegador no está disponible.");
      setPendienteDeCambio(null);
      return;
    }
    cambiar(pendienteDeCambio);
  };

  return (
    <main className="flex min-h-screen w-full items-center justify-center bg-white px-4 text-zinc-800">
      <section
        aria-labelledby="titulo-organizaciones"
        className="flex w-full max-w-md flex-col gap-5 rounded-xl border border-[#e8dcf5] p-8 shadow-sm"
      >
        <div className="flex flex-col items-center text-center">
          <Layers className="h-8 w-8 text-[#9a3bf1]" aria-hidden="true" />
          <h1 id="titulo-organizaciones" className="mt-2 text-lg font-semibold">
            Elige con qué organización trabajar
          </h1>
          {acceso && <p className="mt-1 text-sm text-zinc-500">{acceso.email}</p>}
        </div>

        {error && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        {/* === FE-29 === */}
        {acceso && fallo && (
          <EstadoLogin
            tipo={fallo}
            correo={acceso.email}
            reintentando={reintentando}
            onOtraCuenta={usarOtraCuenta}
            onReintentar={() => void reintentar()}
            enfocarGoogle={() => salirRef.current?.focus()}
            testId="organizaciones-error"
          />
        )}

        {acceso && !fallo && organizaciones && organizaciones.length === 0 && (
          <EstadoLogin
            tipo="sin_organizaciones"
            correo={acceso.email}
            onOtraCuenta={usarOtraCuenta}
            testId="organizaciones-error"
          />
        )}

        {(fallo === "servidor" || fallo === "red") && organizaciones && organizaciones.length > 0 && (
          <p className="text-xs text-zinc-700">{NOTA_LISTA_GUARDADA}</p>
        )}
        {/* === fin FE-29 === */}

        {organizaciones && organizaciones.length > 0 && (!fallo || fallo === "servidor" || fallo === "red") && (
          <ul aria-label="Tus organizaciones" className="flex flex-col gap-2">
            {organizaciones.map((org) => {
              const esActiva = activa?.tenant_id === org.tenant_id;
              return (
                <li key={org.tenant_id}>
                  <button
                    type="button"
                    onClick={() => elegir(org)}
                    className="flex w-full items-center gap-3 rounded-lg border border-[#e8dcf5] px-4 py-3 text-left hover:bg-[#f7f1fd] cursor-pointer"
                  >
                    <Building2 className="h-5 w-5 shrink-0 text-[#9a3bf1]" aria-hidden="true" />
                    <span className="flex-1">
                      <span className="block text-sm font-semibold">{org.nombre_comercial}</span>
                      <span className="block text-xs text-zinc-500">
                        {org.roles.map((r) => ETIQUETA_ROL[r] ?? r).join(", ")}
                      </span>
                    </span>
                    {esActiva && <span className="text-xs font-semibold text-[#7a2bc4]">Organización activa</span>}
                  </button>
                </li>
              );
            })}
          </ul>
        )}

        <button
          ref={salirRef}
          type="button"
          onClick={() => {
            cerrarSesion();
            router.replace(RUTA_LOGIN);
          }}
          className="self-center text-xs text-zinc-500 underline cursor-pointer"
        >
          Salir y usar otra cuenta
        </button>
      </section>

      {pendienteDeCambio && (
        <div
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="titulo-cambios"
          className="fixed inset-0 flex items-center justify-center bg-zinc-900/40 px-4"
        >
          <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-lg">
            <h2 id="titulo-cambios" className="text-base font-semibold">
              Tienes cambios sin guardar
            </h2>
            <p className="mt-2 text-sm text-zinc-600">
              Son de {activa?.nombre_comercial ?? "la organización actual"} y no pasarán a {pendienteDeCambio.nombre_comercial}.
              ¿Qué hacemos con ellos antes de cambiar?
            </p>
            <div className="mt-4 flex flex-col gap-2">
              <button
                type="button"
                onClick={() => resolverYCambiar("guardar")}
                className="rounded-md bg-[#9a3bf1] px-3 py-2 text-sm font-semibold text-white cursor-pointer"
              >
                Guardar y cambiar
              </button>
              <button
                type="button"
                onClick={() => resolverYCambiar("descartar")}
                className="rounded-md border border-[#e8dcf5] px-3 py-2 text-sm cursor-pointer"
              >
                Descartar y cambiar
              </button>
              <button
                type="button"
                onClick={() => setPendienteDeCambio(null)}
                className="px-3 py-2 text-sm text-zinc-500 cursor-pointer"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
