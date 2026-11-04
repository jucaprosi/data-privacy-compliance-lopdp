// ¤adpa ¤rbac-tenant
import { httpBiblioteca } from "./http";

export type DecisionImpacto = "actualizar" | "no_aplica" | "pendiente";
export interface ImpactoOrganizacion {
  id: string; impacto_id: string; codigo: string; version: string;
  decision: DecisionImpacto; motivo: string | null; documentos_afectados: number;
  decidente_id: string | null; decidido_en: string | null;
}

const base = "/biblioteca/impactos";
export const listarImpactos = () => httpBiblioteca<ImpactoOrganizacion[]>(base);
export const decidirImpacto = (id: string, decision: DecisionImpacto, motivo: string) =>
  httpBiblioteca<ImpactoOrganizacion>(`${base}/${id}/decision`, {
    method: "PUT", body: JSON.stringify({ decision, motivo }),
  });
