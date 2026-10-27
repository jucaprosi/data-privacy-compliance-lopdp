"use client";

import React, { useEffect, useState } from "react";

import { AdminPanel, type SeccionAdmin } from "@/components/modules/roadmap/admin";
import { setIdentitySession } from "@/lib/roadmap/cliente";
import { createInitialMockDatabase, createMockFetch } from "@/lib/roadmap/mockServer";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import type { OrganizacionRole } from "@/types/roadmap";

interface Props {
  rol: string;
  /**
   * "tamano", "sod", "duplicado": la primera asignación de rol responde con ese error de negocio;
   * "ultimo": la primera revocación responde que es el último administrador;
   * "carga": la primera carga de usuarios falla; "config": la primera carga de la configuración falla.
   */
  fallo: string;
  /** Tamaño con el que arranca la configuración; vacío = sin configurar. */
  tamano: string;
  seccion: string;
}

const ROLES: readonly OrganizacionRole[] = [
  "responsable_area",
  "coordinador",
  "dpo",
  "implementador",
  "admin_organizacion",
];
const SECCIONES: readonly SeccionAdmin[] = ["usuarios", "areas", "roles", "configuracion"];
const TAMANOS_VALIDOS = ["micro", "pequena", "mediana", "corporativo"];

function json(datos: unknown, estado = 200): Response {
  return new Response(JSON.stringify(datos), { status: estado, headers: { "Content-Type": "application/json" } });
}

function errorNegocio(estado: number, detalle: string, codigo: string, accion: string | null): Response {
  return json({ detail: detalle, code: codigo, action_required: accion }, estado);
}

export function HarnessAdmin({ rol, fallo, tamano, seccion }: Props) {
  const [listo, setListo] = useState(false);

  useEffect(() => {
    const original = window.fetch.bind(window);
    const db = createInitialMockDatabase();
    // Un área subordinada, para probar la jerarquía.
    db.areas.set("area-003", {
      id: "area-003",
      tenant_id: "tenant-corp-demo",
      nombre: "Seguridad de la Información",
      codigo: "SI-01",
      parent_area_id: "area-001",
      created_at: new Date().toISOString(),
    });
    const simulado = createMockFetch(db);
    const configuracion: { tamano: string | null; sector: string | null } = { tamano: tamano || null, sector: null };
    const yaFallo: Record<string, boolean> = {};
    const unaVez = (...claves: string[]) => {
      const clave = claves.find((c) => c === fallo);
      if (!clave || yaFallo[clave]) return false;
      yaFallo[clave] = true;
      return true;
    };

    window.fetch = async (entrada: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof entrada === "string" ? entrada : entrada instanceof URL ? entrada.href : entrada.url;
      if (!url.includes("/api/v1/")) return original(entrada, init);
      const metodo = (init?.method ?? "GET").toUpperCase();
      const ruta = new URL(url, "http://localhost").pathname.replace(/^\/api\/v1/, "");

      // Configuración de la organización: el backend (RM-15) aún no existe, la simula el harness.
      if (ruta === "/organizacion/configuracion") {
        if (metodo === "GET") {
          if (unaVez("config")) return errorNegocio(503, "No se pudo cargar la configuración.", "CONFIG_UNAVAILABLE", "retry_later");
          return json({ ...configuracion });
        }
        if (metodo === "PATCH") {
          const cuerpo = JSON.parse(String(init?.body ?? "{}")) as { tamano?: string | null; sector?: string | null };
          if (cuerpo.tamano != null && !TAMANOS_VALIDOS.includes(cuerpo.tamano)) {
            return errorNegocio(422, "Tamaño no válido.", "INVALID_TENANT_SIZE", null);
          }
          if (cuerpo.tamano !== undefined) configuracion.tamano = cuerpo.tamano;
          if (cuerpo.sector !== undefined) configuracion.sector = cuerpo.sector;
          return json({ ...configuracion });
        }
      }

      if (ruta === "/organizacion/usuarios" && metodo === "GET" && unaVez("carga")) {
        return errorNegocio(503, "No se pudo cargar la organización.", "ORG_UNAVAILABLE", "retry_later");
      }
      if (ruta === "/organizacion/roles" && metodo === "POST") {
        if (unaVez("tamano")) {
          return errorNegocio(409, "El tamaño de la organización no está configurado.", "TENANT_SIZE_NOT_CONFIGURED", "configure_tenant_size");
        }
        if (unaVez("sod")) return errorNegocio(409, "Violación de segregación de funciones (SoD).", "SOD_VIOLATION", null);
        if (unaVez("duplicado")) {
          return errorNegocio(409, "El usuario ya posee esta asignación en la organización.", "MEMBER_ALREADY_EXISTS", null);
        }
      }
      if (/^\/organizacion\/roles\/[^/]+$/.test(ruta) && metodo === "DELETE" && unaVez("ultimo")) {
        return errorNegocio(
          409,
          "No se puede revocar al último administrador de la organización.",
          "LAST_ADMIN_CANNOT_BE_REVOKED",
          null,
        );
      }
      return simulado(entrada, init);
    };

    const rolValido = (ROLES as readonly string[]).includes(rol) ? (rol as OrganizacionRole) : "admin_organizacion";
    setIdentitySession({ role: rolValido, userId: "user-admin-01" });
    useRoadmapStore.getState().setSession({ role: rolValido, userId: "user-admin-01" });
    setListo(true);

    return () => {
      window.fetch = original;
    };
  }, [rol, fallo, tamano]);

  const inicial = (SECCIONES as readonly string[]).includes(seccion) ? (seccion as SeccionAdmin) : "usuarios";

  return (
    <main className="h-screen overflow-auto bg-[var(--ui-campo)] p-6">
      <div className="mx-auto max-w-5xl">{listo ? <AdminPanel seccionInicial={inicial} /> : null}</div>
    </main>
  );
}
