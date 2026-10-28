/**
 * Cliente y validación de los datos de la organización para documentos (ORG-14).
 *
 * Forma de la respuesta, comprobada contra el servidor (`features/organizacion/services/
 * datos_documentales_engine.py`): GET y PATCH /organizacion/datos-documentales devuelven
 * `{tenant_id, <nueve campos>, faltantes}`. GET lo puede pedir cualquier rol activo; PATCH solo
 * `admin_organizacion`. La organización sale de la sesión: el cuerpo nunca la lleva.
 *
 * La validación de aquí es la misma que aplica el servidor, para avisar antes de enviar; el
 * servidor la repite y es quien decide (ErrorNegocio DATOS_DOCUMENTALES_INVALIDOS).
 */
import { requestJson } from "@/lib/roadmap/cliente";
import type { OrganizacionRole } from "@/types/roadmap";

export const CAMPOS_DOCUMENTALES = [
  "direccion",
  "ciudad",
  "telefono",
  "correo_contacto",
  "correo_privacidad",
  "sitio_web",
  "representante_legal_nombre",
  "representante_legal_identificacion",
  "representante_legal_cargo",
] as const;

export type CampoDocumental = (typeof CAMPOS_DOCUMENTALES)[number];

export type DatosDocumentales = Record<CampoDocumental, string | null> & {
  tenant_id: string;
  faltantes: CampoDocumental[];
};

export type CambiosDocumentales = Partial<Record<CampoDocumental, string | null>>;

export type TipoCampo = "texto" | "correo" | "telefono" | "url" | "identificacion";

export interface DefinicionCampo {
  campo: CampoDocumental;
  etiqueta: string;
  tipo: TipoCampo;
  maximo: number;
  grupo: "organizacion" | "representante";
  ayuda?: string;
}

export const DEFINICION_CAMPOS: ReadonlyArray<DefinicionCampo> = [
  { campo: "direccion", etiqueta: "Domicilio principal", tipo: "texto", maximo: 300, grupo: "organizacion" },
  { campo: "ciudad", etiqueta: "Ciudad", tipo: "texto", maximo: 120, grupo: "organizacion" },
  { campo: "telefono", etiqueta: "Teléfono de contacto", tipo: "telefono", maximo: 30, grupo: "organizacion" },
  { campo: "correo_contacto", etiqueta: "Correo general de contacto", tipo: "correo", maximo: 254, grupo: "organizacion" },
  {
    campo: "correo_privacidad",
    etiqueta: "Correo para solicitudes de titulares",
    tipo: "correo",
    maximo: 254,
    grupo: "organizacion",
    ayuda: "Canal por el que los titulares ejercen sus derechos.",
  },
  { campo: "sitio_web", etiqueta: "Sitio web", tipo: "url", maximo: 300, grupo: "organizacion", ayuda: "Dirección completa, p. ej. https://organizacion.ec" },
  { campo: "representante_legal_nombre", etiqueta: "Nombre del representante legal", tipo: "texto", maximo: 200, grupo: "representante" },
  {
    campo: "representante_legal_identificacion",
    etiqueta: "Cédula o RUC del representante legal",
    tipo: "identificacion",
    maximo: 13,
    grupo: "representante",
  },
  { campo: "representante_legal_cargo", etiqueta: "Cargo del representante legal", tipo: "texto", maximo: 150, grupo: "representante" },
];

const CORREO = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const TELEFONO = /^\+?[0-9 ()-]{7,30}$/;
const HOST = /^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/i;

/** Cédula ecuatoriana: provincia 01-24 o 30, tercer dígito < 6 y verificador módulo 10. */
export function esCedulaValida(cedula: string): boolean {
  if (!/^[0-9]{10}$/.test(cedula)) return false;
  const provincia = Number(cedula.slice(0, 2));
  if (!((provincia >= 1 && provincia <= 24) || provincia === 30) || Number(cedula[2]) >= 6) return false;
  let suma = 0;
  for (let i = 0; i < 9; i++) {
    const producto = Number(cedula[i]) * (i % 2 === 0 ? 2 : 1);
    suma += producto > 9 ? producto - 9 : producto;
  }
  return (10 - (suma % 10)) % 10 === Number(cedula[9]);
}

/** Cédula, o RUC de persona natural (cédula válida y establecimiento distinto de 000). */
export function esIdentificacionValida(valor: string): boolean {
  if (valor.length === 13) return esCedulaValida(valor.slice(0, 10)) && /^[0-9]{3}$/.test(valor.slice(10)) && valor.slice(10) !== "000";
  return esCedulaValida(valor);
}

function esUrlValida(valor: string): boolean {
  try {
    const url = new URL(valor);
    return (url.protocol === "http:" || url.protocol === "https:") && HOST.test(url.hostname);
  } catch {
    return false;
  }
}

/** Mensaje de error del valor, o null si es válido. El vacío siempre es válido: el campo es opcional. */
export function validarCampo(definicion: DefinicionCampo, valorCrudo: string): string | null {
  const valor = valorCrudo.trim();
  if (!valor) return null;
  if (valor.length > definicion.maximo) return `Admite hasta ${definicion.maximo} caracteres.`;
  switch (definicion.tipo) {
    case "correo":
      return CORREO.test(valor) ? null : "No es un correo electrónico válido.";
    case "url":
      return esUrlValida(valor) ? null : "Debe ser una dirección web completa, p. ej. https://organizacion.ec.";
    case "telefono":
      return TELEFONO.test(valor) && (valor.match(/[0-9]/g)?.length ?? 0) >= 7
        ? null
        : "Solo admite dígitos, espacios, guiones, paréntesis y un + inicial.";
    case "identificacion":
      return esIdentificacionValida(valor) ? null : "No es una cédula ni un RUC de persona natural válidos.";
    default:
      return null;
  }
}

/** Solo los campos que cambiaron respecto de lo guardado; el vacío se envía como null (borrar). */
export function cambiosRespectoDe(guardado: DatosDocumentales, borrador: Record<CampoDocumental, string>): CambiosDocumentales {
  const cambios: CambiosDocumentales = {};
  for (const campo of CAMPOS_DOCUMENTALES) {
    const nuevo = borrador[campo].trim() || null;
    if (nuevo !== (guardado[campo] ?? null)) cambios[campo] = nuevo;
  }
  return cambios;
}

function conRol(rol: OrganizacionRole): { headers: Record<string, string> } {
  return { headers: { "X-Role": rol } };
}

/** Toma de la respuesta solo campos de texto; lo demás cuenta como sin registrar. Recalcula los faltantes. */
export function normalizarRespuesta(crudo: unknown): DatosDocumentales {
  const objeto = crudo && typeof crudo === "object" && !Array.isArray(crudo) ? (crudo as Record<string, unknown>) : {};
  const texto = (v: unknown) => (typeof v === "string" && v.trim() ? v : null);
  const campos = Object.fromEntries(CAMPOS_DOCUMENTALES.map((c) => [c, texto(objeto[c])])) as Record<CampoDocumental, string | null>;
  return {
    ...campos,
    tenant_id: typeof objeto.tenant_id === "string" ? objeto.tenant_id : "",
    faltantes: CAMPOS_DOCUMENTALES.filter((c) => campos[c] === null),
  };
}

export const datosDocumentalesApi = {
  async obtener(rol: OrganizacionRole): Promise<DatosDocumentales> {
    return normalizarRespuesta(
      await requestJson<unknown>("/organizacion/datos-documentales", { method: "GET", ...conRol(rol) }),
    );
  },
  async guardar(cambios: CambiosDocumentales, rol: OrganizacionRole): Promise<DatosDocumentales> {
    return normalizarRespuesta(
      await requestJson<unknown>("/organizacion/datos-documentales", {
        method: "PATCH",
        body: JSON.stringify(cambios),
        ...conRol(rol),
      }),
    );
  },
};
