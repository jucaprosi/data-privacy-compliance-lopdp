import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

import CommandPalette from "@/components/CommandPalette";
import { getServerTheme } from "@/app/actions/themeActions";

export const metadata: Metadata = {
  title: "JUBYS LOPDP 360",
  description: "Plataforma Integral de Cumplimiento LOPDP Ecuador",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const theme = await getServerTheme();
  const themeClass = theme === "dark" ? "dark theme-dark" : "theme-light";

  return (
    <html lang="es" className={`${inter.variable} ${themeClass}`}>
      <body className={`${inter.className} antialiased`}>
        {children}
        <CommandPalette />
      </body>
    </html>
  );
}
