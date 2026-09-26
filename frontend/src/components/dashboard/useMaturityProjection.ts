"use client";

import { useEffect, useState } from "react";

interface Observation {
  at: number;
  level: number;
  score: number;
}

const MONTH_MS = 30.44 * 24 * 60 * 60 * 1000;
const MIN_TREND_MS = 14 * 24 * 60 * 60 * 1000;
const HISTORY_MS = 365 * 24 * 60 * 60 * 1000;

function readHistory(key: string): Observation[] {
  try {
    const value = JSON.parse(localStorage.getItem(key) ?? "[]");
    if (!Array.isArray(value)) return [];
    return value.filter((item): item is Observation =>
      typeof item?.at === "number" && typeof item?.level === "number"
      && typeof item?.score === "number" && item.level >= 1 && item.level <= 5
    );
  } catch {
    return [];
  }
}

/** Registra cambios calculados; la tendencia solo se activa con observaciones separadas en el tiempo. */
export function useMaturityProjection(
  projectKey: string,
  level: number,
  score: number,
  isReference: boolean
) {
  const [history, setHistory] = useState<Observation[]>([]);

  useEffect(() => {
    if (isReference || level < 1 || !projectKey) return;
    const key = `lopdp-maturity-history:${projectKey}`;
    const now = Date.now();
    const previous = readHistory(key).filter((item) => now - item.at <= HISTORY_MS);
    const last = previous.at(-1);
    const next = last?.level === level && last.score === score
      ? previous
      : [...previous, { at: now, level, score }].slice(-60);
    try {
      localStorage.setItem(key, JSON.stringify(next));
    } catch {
      // La lectura del dashboard sigue disponible si el navegador bloquea el almacenamiento.
    }
    setHistory(next);
  }, [projectKey, level, score, isReference]);

  const first = history[0];
  const last = history.at(-1);
  const trendAvailable = !isReference && Boolean(first && last && last.at - first.at >= MIN_TREND_MS);
  const monthlyChange = trendAvailable && first && last
    ? (last.level - first.level) / ((last.at - first.at) / MONTH_MS)
    : 0;
  const projectedAt = (months: number) =>
    Math.min(5, Math.max(1, level + monthlyChange * months));
  const monthsToLevel3 = trendAvailable && monthlyChange > 0 && level < 3
    ? (3 - level) / monthlyChange
    : null;

  return { projectedAt, trendAvailable, monthsToLevel3 };
}
