"use client";

import { useEffect } from "react";
import { useAuditStore } from "@/store/useAuditStore";

export default function ThemeRootSync() {
  const theme = useAuditStore((state) => state.theme);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle("dark", theme === "dark");
    root.classList.toggle("theme-dark", theme === "dark");
    root.classList.toggle("theme-light", theme === "light");
  }, [theme]);

  return null;
}
