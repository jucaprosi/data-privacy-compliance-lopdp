// ¤api-integraciones
/**
 * Biblioteca de cliente para claves de integración y techos de paquete (API-02).
 */

export interface ClaveIntegracion {
  id: string;
  nombre: string;
  prefijo: string;
  alcances: string[];
  creada_en: string;
  rotada_en: string | null;
  revocada_en: string | null;
}

export interface TechosIntegracion {
  claves: {
    maximo: number | null;
    activas: number;
  };
  webhooks: {
    maximo: number | null;
    activos: number;
  };
}

export interface ClaveCreadaResponse {
  status: string;
  clave: ClaveIntegracion;
  clave_en_claro: string;
}

export async function obtenerTechos(): Promise<TechosIntegracion> {
  const res = await fetch("/api/v1/integraciones/techos", {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Error al consultar techos de integración: ${res.statusText}`);
  }
  return res.json();
}

export async function listarClaves(): Promise<ClaveIntegracion[]> {
  const res = await fetch("/api/v1/integraciones/claves", {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    throw new Error(`Error al listar claves de integración: ${res.statusText}`);
  }
  const data = await res.json();
  return data.claves || [];
}

export async function crearClave(
  nombre: string,
  alcances: string[]
): Promise<ClaveCreadaResponse> {
  const res = await fetch("/api/v1/integraciones/claves", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nombre, alcances }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Error al crear clave: ${res.statusText}`);
  }
  return res.json();
}

export async function rotarClave(id: string): Promise<ClaveCreadaResponse> {
  const res = await fetch(`/api/v1/integraciones/claves/${id}/rotar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Error al rotar clave: ${res.statusText}`);
  }
  return res.json();
}

export async function revocarClave(id: string): Promise<ClaveIntegracion> {
  const res = await fetch(`/api/v1/integraciones/claves/${id}/revocar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Error al revocar clave: ${res.statusText}`);
  }
  const data = await res.json();
  return data.clave;
}
