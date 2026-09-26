"use client";

import React from "react";
import { BookOpen, ExternalLink } from "lucide-react";

interface CitationBadgeProps {
  citation: string;
  onClick?: () => void;
}

export default function CitationBadge({ citation, onClick }: CitationBadgeProps) {
  // Limpiar corchetes exteriores si vienen en formato [Art. 12 LOPDP]
  const cleanCitation = citation.replace(/^\[+|\]+$/g, "").trim();

  return (
    <span
      onClick={onClick}
      className="inline-flex items-center space-x-1 px-2 py-0.5 my-0.5 mx-1 rounded-md text-[11px] font-mono font-medium tracking-tight bg-[#3892f3]/15 text-[#2563eb] dark:text-[#60a5fa] border border-[#3892f3]/35 hover:bg-[#3892f3]/25 transition cursor-pointer shadow-2xs group"
      title={`Fundamento Normativo Oficial: ${cleanCitation} (Doctrina: Sin fuente no hay respuesta)`}
    >
      <BookOpen className="w-3 h-3 text-[#3892f3] shrink-0" />
      <span className="font-semibold">{cleanCitation}</span>
      <ExternalLink className="w-2.5 h-2.5 opacity-0 group-hover:opacity-100 transition-opacity text-[#3892f3]" />
    </span>
  );
}
