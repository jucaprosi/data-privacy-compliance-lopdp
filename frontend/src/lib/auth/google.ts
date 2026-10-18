/**
 * Google Identity Services: carga del script y tipos mínimos de lo que se usa.
 * https://developers.google.com/identity/gsi/web/reference/js-reference
 */
const URL_GIS = "https://accounts.google.com/gsi/client";

export interface RespuestaCredencial {
  /** Token de identidad (JWT) firmado por Google. */
  credential?: string;
}

export interface GoogleId {
  initialize(opciones: {
    client_id: string;
    callback: (respuesta: RespuestaCredencial) => void;
    auto_select?: boolean;
    cancel_on_tap_outside?: boolean;
  }): void;
  renderButton(
    elemento: HTMLElement,
    opciones: { type?: "standard"; theme?: string; size?: string; text?: string; locale?: string; width?: number },
  ): void;
  disableAutoSelect(): void;
}

declare global {
  interface Window {
    google?: { accounts: { id: GoogleId } };
  }
}

let carga: Promise<GoogleId> | null = null;

/** Carga el script de Google una sola vez. Rechaza con un mensaje legible si no se puede. */
export function cargarGoogle(): Promise<GoogleId> {
  if (window.google?.accounts?.id) return Promise.resolve(window.google.accounts.id);
  if (carga) return carga;
  carga = new Promise<GoogleId>((resolver, rechazar) => {
    const script = document.createElement("script");
    script.src = URL_GIS;
    script.async = true;
    script.defer = true;
    script.onload = () => {
      const id = window.google?.accounts?.id;
      if (id) resolver(id);
      else rechazar(new Error("El script de Google no expuso el servicio de identidad."));
    };
    script.onerror = () => {
      carga = null; // permite reintentar
      rechazar(new Error("No se pudo cargar el servicio de inicio de sesión de Google."));
    };
    document.head.appendChild(script);
  });
  return carga;
}

/** Evita que Google vuelva a elegir la cuenta solo tras cerrar sesión. */
export function olvidarCuentaDeGoogle(): void {
  window.google?.accounts?.id?.disableAutoSelect();
}
