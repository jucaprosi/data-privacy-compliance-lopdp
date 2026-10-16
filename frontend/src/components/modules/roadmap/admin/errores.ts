/**
 * Traduce los errores del backend a mensajes claros para la persona que administra.
 *
 * Los códigos son los del catálogo del backend (app_core/errors.py). Si llega uno desconocido,
 * se muestra el texto que envió el servidor: nunca un mensaje genérico que oculte la causa.
 */
import { ApiError } from "../../../../types/roadmap";

export interface ErrorDescrito {
  /** Explicación para la persona usuaria. */
  mensaje: string;
  /** Código de negocio, si el servidor lo envió. */
  codigo?: string;
  /** Acción que el servidor pide, si la envió. */
  accion?: string | null;
  /** Verdadero cuando la solución es configurar el tamaño de la organización. */
  irAConfiguracion: boolean;
}

const MENSAJES: Readonly<Record<string, string>> = {
  TENANT_SIZE_NOT_CONFIGURED:
    "Primero configura el tamaño de la organización. Sin él no se puede comprobar si una misma persona puede ser encargado y responsable de área.",
  SOD_VIOLATION:
    "Esta combinación de roles rompe la separación de funciones y no está permitida en una organización de este tamaño.",
  DPO_INDEPENDENCE_VIOLATED:
    "El delegado de protección de datos debe ser independiente: no puede tener a la vez un rol operativo, como implementador o encargado.",
  MEMBER_ALREADY_EXISTS: "Esa persona ya tiene esta asignación en la organización.",
  LAST_ADMIN_CANNOT_BE_REVOKED:
    "No se puede revocar al último administrador: la organización quedaría sin quien la gestione. Asigna primero ese rol a otra persona.",
};

export function describirError(err: unknown): ErrorDescrito {
  if (err instanceof ApiError) {
    const conocido = err.code ? MENSAJES[err.code] : undefined;
    return {
      mensaje: conocido ?? err.message,
      codigo: err.code,
      accion: err.action_required,
      irAConfiguracion: err.code === "TENANT_SIZE_NOT_CONFIGURED" || err.action_required === "configure_tenant_size",
    };
  }
  return { mensaje: "No se pudo completar la operación. Inténtalo de nuevo.", irAConfiguracion: false };
}
