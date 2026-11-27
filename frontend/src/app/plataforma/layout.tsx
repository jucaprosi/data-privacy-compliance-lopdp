// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa
// ¤¤frontend-architect
"use client";
/** BIB-412 · Navegación de Plataforma: «Organizaciones» y «Biblioteca editorial». Muestra la activa con `aria-current`. */
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const ENTRADAS = [
  { href: "/plataforma", texto: "Organizaciones", activa: (p: string) => p === "/plataforma" || p.startsWith("/plataforma/paquetes") },
  { href: "/plataforma/biblioteca", texto: "Biblioteca editorial", activa: (p: string) => p.startsWith("/plataforma/biblioteca") },
] as const;

export default function PlataformaLayout({ children }: { children: ReactNode }) {
  const ruta = usePathname() ?? "";
  return (
    <>
      <nav aria-label="Plataforma" className="border-b border-[var(--ui-borde)] px-6 py-2">
        <ul className="flex flex-wrap gap-4">
          {ENTRADAS.map((e) => (
            <li key={e.href}>
              <Link href={e.href} aria-current={e.activa(ruta) ? "page" : undefined}
                className={e.activa(ruta) ? "font-semibold underline" : "hover:underline"}>{e.texto}</Link>
            </li>
          ))}
          {/* === BIB-414 === */}
          {/* === fin BIB-414 === */}
        </ul>
      </nav>
      {children}
    </>
  );
}
