import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

import CommandPalette from "@/components/CommandPalette";
import ThemeRootSync from "@/components/ThemeRootSync";
import AvisoEntorno from "@/components/entorno/AvisoEntorno";
import { entornoDelServidor, esProduccion } from "@/lib/entorno";

// EP-02: el entorno se lee en cada petición (APP_ENV), no al compilar; la imagen es la misma en todos.
export const dynamic = "force-dynamic";

export async function generateMetadata(): Promise<Metadata> {
  return {
    title: "EVYDENTIA · LOPDP 360",
    description: "Plataforma Integral de Cumplimiento LOPDP Ecuador",
    // Fuera de producción, o sin APP_ENV válido, ningún buscador indexa ni sigue enlaces.
    ...(esProduccion(entornoDelServidor()) ? {} : { robots: { index: false, follow: false } }),
  };
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className={`${inter.variable} theme-light`}>
      <body className={`${inter.className} antialiased`}>
        <ThemeRootSync />
        <AvisoEntorno entorno={entornoDelServidor()} />
        {children}
        <CommandPalette />
      </body>
    </html>
  );
}
