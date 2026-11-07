"use client";

/**
 * Franja fija del entorno de pruebas y de la demo (EP-02, PRD §5.5 y §5.6.1.6). ¤entorno-pruebas
 *
 * Ante la duda no se pinta: si la llamada falla o el servidor responde `production`, no hay aviso.
 * `NEXT_PUBLIC_APP_ENV` solo da la primera pintura; manda `GET /api/v1/entorno`.
 */
import { useEffect, useState } from "react";
import { FlaskConical, Presentation } from "lucide-react";
import { type Entorno, debeConsultarEntorno, entornoCompilado, esEntornoDePruebas, normalizarEntorno } from "@/lib/entorno";
import { ranurasDe } from "@/lib/entorno/ranuras";

type Variante = "pruebas" | "demo";

const VARIANTES: Record<Variante, { texto: string; corto: string; clase: string; Icono: typeof FlaskConical }> = {
  pruebas: {
    texto: "Entorno de pruebas · datos ficticios",
    corto: "Pruebas · ficticio",
    clase: "bg-[#E8EEF7] text-[#1F3A64] [.theme-dark_&]:bg-[#16233A] [.theme-dark_&]:text-[#A9C2E8]",
    Icono: FlaskConical,
  },
  demo: {
    texto: "Demostración · datos ficticios",
    corto: "Demo · ficticio",
    clase: "bg-[#FFF4D6] text-[#7A5A00] [.theme-dark_&]:bg-[#3A2E10] [.theme-dark_&]:text-[#F5D27A]",
    Icono: Presentation,
  },
};

function varianteDe(entorno: Entorno | null): Variante | null {
  return entorno && esEntornoDePruebas(entorno) ? (entorno as Variante) : null;
}

export default function AvisoEntorno() {
  const [entorno, setEntorno] = useState<Entorno | null>(() => {
    const compilado = entornoCompilado();
    return esEntornoDePruebas(compilado) ? compilado : null;
  });

  useEffect(() => {
    if (!debeConsultarEntorno()) return;
    let vigente = true;
    fetch("/api/v1/entorno", { headers: { Accept: "application/json" }, cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((cuerpo) => {
        if (vigente) setEntorno(normalizarEntorno(cuerpo?.entorno));
      })
      .catch(() => {
        if (vigente) setEntorno(null);
      });
    return () => {
      vigente = false;
    };
  }, []);

  const variante = varianteDe(entorno);
  if (!variante || !entorno) return null;
  const { texto, corto, clase, Icono } = VARIANTES[variante];
  const organizacion = ranurasDe("organizacion").map((r, i) => <span key={i}>{r(entorno)}</span>);
  const acciones = ranurasDe("acciones").map((r, i) => <span key={i}>{r(entorno)}</span>);

  return (
    <div
      role="status"
      data-testid="aviso-entorno"
      data-entorno={variante}
      className={`sticky top-0 z-[60] flex h-8 w-full shrink-0 items-center gap-3 px-4 text-xs font-medium ${clase}`}
    >
      <Icono aria-hidden="true" className="h-4 w-4 shrink-0" />
      <span className="hidden sm:inline">{texto}</span>
      <span className="sm:hidden" aria-label={texto}>
        {corto}
      </span>
      <span data-slot="organizacion" className="hidden min-w-0 truncate md:inline">
        {organizacion}
      </span>
      <span data-slot="acciones" className="ml-auto flex items-center gap-2">
        {acciones}
      </span>
    </div>
  );
}
