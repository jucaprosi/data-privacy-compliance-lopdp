"use client";

// ¤¤frontend-architect
// ¤frontend-ide
import Image from "next/image";
import { ChevronRight, LogOut, Moon, Search, Sun } from "lucide-react";
import FileMenu from "@/components/layout/FileMenu";

interface DashboardHeaderProps {
  theme: "dark" | "light";
  isConfigured: boolean;
  workspaceTitle?: string;
  normativaLabel: string;
  sessionEmail?: string;
  onLogout: () => void;
  onToggleTheme: () => void;
  onCommandPalette: () => void;
}

// ¤frontend-ide
export default function DashboardHeader({
  theme, isConfigured, workspaceTitle, normativaLabel, sessionEmail,
  onLogout, onToggleTheme, onCommandPalette,
}: DashboardHeaderProps) {
  return (
    <header className="h-10 bg-[var(--ui-superficie)] border border-[#e8dcf5] dark:border-[var(--ui-borde)] rounded-lg px-3.5 flex items-center justify-between shrink-0 text-xs z-20 shadow-sm">
      <div className="flex items-center space-x-2.5">
        <Image
          src={theme === "light" ? "/brand/evydentia-principal.png" : "/brand/evydentia-negativo.png"}
          alt="EVYDENTIA by SMARTCIDI"
          width={1110}
          height={210}
          priority
          className="h-8 w-auto shrink-0"
          data-testid="evydentia-brand"
        />

        <FileMenu />

        <span className="text-[var(--ui-texto-suave)]">/</span>
        <span className="text-[var(--ui-texto-suave)] font-mono text-[11px]">Workspace</span>
        <ChevronRight className="w-3.5 h-3.5 text-[var(--ui-texto-suave)]" />
        <span className="text-white font-medium text-[11px] bg-[var(--ui-boton)] px-2 py-0.5 rounded border border-[var(--ui-borde)]">
          {workspaceTitle}
        </span>
      </div>

      {/* Indicadores de Entorno & Calibración + Botón Command Palette + Conmutador de Tema */}
      <div className="flex items-center space-x-3 text-[11px]">
        {sessionEmail && (
          <div className="flex items-center space-x-2" data-testid="sesion-activa">
            <span className="max-w-[180px] truncate text-[var(--ui-texto-suave)]" title={sessionEmail}>{sessionEmail}</span>
            <button
              type="button"
              onClick={onLogout}
              className="h-7 px-2 rounded-md bg-[var(--ui-campo)] hover:bg-[var(--ui-boton)] border border-[var(--ui-borde)] text-[var(--ui-texto-suave)] hover:text-white flex items-center space-x-1 transition cursor-pointer"
              title="Cerrar sesión"
            >
              <LogOut className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Cerrar sesión</span>
            </button>
          </div>
        )}
        {/* Conmutador Minimalista de Tema Dual Acromático (Módulo 8) */}
        <button
          type="button"
          onClick={onToggleTheme}
          className="h-7 w-7 rounded-md bg-[var(--ui-campo)] hover:bg-[var(--ui-boton)] border border-[var(--ui-borde)] text-[var(--ui-texto-suave)] hover:text-white flex items-center justify-center transition cursor-pointer"
          title={`Cambiar a tema ${theme === "dark" ? "claro" : "oscuro"}`}
        >
          {theme === "dark" ? (
            <Sun className="w-3.5 h-3.5 text-amber-400" />
          ) : (
            <Moon className="w-3.5 h-3.5 text-zinc-300" />
          )}
        </button>

        {/* Botón de Acceso Rápido Command Palette */}
        <button
          type="button"
          onClick={onCommandPalette}
          className="flex items-center space-x-2 px-2.5 py-1 rounded bg-[var(--ui-campo)] hover:bg-[var(--ui-boton)] border border-[var(--ui-borde)] hover:border-[#9a3bf1]/60 text-[var(--ui-texto-suave)] hover:text-white transition cursor-pointer shadow-xs"
          title="Abrir Command Palette (Ctrl + K)"
        >
          <Search className="w-3.5 h-3.5 text-[#9a3bf1]" />
          <span className="hidden md:inline">Buscar comando o artículo...</span>
          <kbd className="bg-[var(--ui-superficie)] px-1.5 py-0.5 rounded border border-[var(--ui-borde)] font-mono text-[10px] text-zinc-300">
            Ctrl + K
          </kbd>
        </button>

        <div className="flex items-center space-x-1.5 bg-[var(--ui-campo)] px-2.5 py-1 rounded border border-[var(--ui-borde)]">
          <span
            className={`w-2 h-2 rounded-full ${
              isConfigured
                ? "bg-[#00c853] shadow-[0_0_8px_rgba(0,200,83,0.8)]"
                : "bg-amber-500 animate-pulse"
            }`}
          />
          <span className="font-mono text-zinc-300">
            {isConfigured ? "Calibrado" : "Ficha Pendiente"}
          </span>
        </div>

        <div className="hidden sm:flex items-center space-x-1.5 text-[var(--ui-texto-suave)] font-mono">
          <span className="text-[var(--ui-texto-suave)]">Norma:</span>
          <span className="text-zinc-200 font-semibold">
            {normativaLabel}
          </span>
        </div>
      </div>
    </header>
  );
}
