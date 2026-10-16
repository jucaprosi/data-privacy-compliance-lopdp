/** Convierte la lista plana de áreas en un árbol ordenado, con su nivel de profundidad. */
import type { AreaItem } from "../../../../types/roadmap";

export interface NodoArea {
  area: AreaItem;
  nivel: number;
  hijos: NodoArea[];
}

/**
 * Las áreas cuyo padre no está en la lista (o que se señalan a sí mismas) se tratan como raíces:
 * una referencia rota no debe esconder un área ni provocar un ciclo.
 */
export function construirArbol(areas: AreaItem[]): NodoArea[] {
  const porId = new Map(areas.map((a) => [a.id, a]));
  const hijosDe = new Map<string, AreaItem[]>();
  const raices: AreaItem[] = [];

  for (const area of areas) {
    const padre = area.parent_area_id;
    if (padre && padre !== area.id && porId.has(padre)) {
      hijosDe.set(padre, [...(hijosDe.get(padre) ?? []), area]);
    } else {
      raices.push(area);
    }
  }

  const ordenar = (lista: AreaItem[]) => [...lista].sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));
  const visitadas = new Set<string>();

  function nodo(area: AreaItem, nivel: number): NodoArea {
    visitadas.add(area.id);
    const hijos = ordenar(hijosDe.get(area.id) ?? [])
      .filter((h) => !visitadas.has(h.id))
      .map((h) => nodo(h, nivel + 1));
    return { area, nivel, hijos };
  }

  return ordenar(raices).map((a) => nodo(a, 0));
}

/** Aplana el árbol en el orden en que se muestra, útil para listas de selección. */
export function aplanar(nodos: NodoArea[]): NodoArea[] {
  return nodos.flatMap((n) => [n, ...aplanar(n.hijos)]);
}
