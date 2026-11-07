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
import { esProduccion } from "@/lib/entorno";

export const metadata: Metadata = {
  title: "EVYDENTIA · LOPDP 360",
  description: "Plataforma Integral de Cumplimiento LOPDP Ecuador",
  // EP-02: fuera de producción, ningún buscador indexa ni sigue enlaces.
  ...(esProduccion() ? {} : { robots: { index: false, follow: false } }),
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className={`${inter.variable} theme-light`}>
      <body className={`${inter.className} antialiased`}>
        <ThemeRootSync />
        <AvisoEntorno />
        {children}
        <CommandPalette />
      </body>
    </html>
  );
}
