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

export const metadata: Metadata = {
  title: "JUBYS LOPDP 360",
  description: "Plataforma Integral de Cumplimiento LOPDP Ecuador",
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
        {children}
        <CommandPalette />
      </body>
    </html>
  );
}
