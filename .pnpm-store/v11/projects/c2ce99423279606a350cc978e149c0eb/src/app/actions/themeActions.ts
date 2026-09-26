"use server";

import { cookies } from "next/headers";

export type ThemeMode = "dark" | "light";

export interface ServerThemeResponse {
  success: boolean;
  theme: ThemeMode;
}

/**
 * Server Action: Fija y persiste la preferencia de tema en la cookie de sesión
 * para evitar parpadeos visuales (FOUC) en el renderizado inicial del servidor.
 */
export async function setServerTheme(theme: ThemeMode): Promise<ServerThemeResponse> {
  try {
    const cookieStore = await cookies();
    cookieStore.set("jubys-theme", theme, {
      path: "/",
      maxAge: 60 * 60 * 24 * 365, // 1 año
      sameSite: "lax",
    });
    return { success: true, theme };
  } catch (error) {
    console.error("[SERVER_THEME_ACTION_ERROR]:", error);
    return { success: false, theme };
  }
}

/**
 * Server Action: Lee el tema actual configurado en las cookies.
 */
export async function getServerTheme(): Promise<ThemeMode> {
  try {
    const cookieStore = await cookies();
    const cookie = cookieStore.get("jubys-theme");
    return (cookie?.value as ThemeMode) || "dark";
  } catch {
    return "dark";
  }
}

