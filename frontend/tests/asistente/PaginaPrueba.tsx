// ¤asistente
// Página de prueba del asistente, solo para Playwright (FE-23): no forma parte de la aplicación.
// La monta tests/asistente/montaje.ts en una página en blanco. El comportamiento de `guardar`
// se controla desde la prueba con window.__asistente.
import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { Asistente, type PasoAsistente } from "../../src/components/asistente";

type ModoGuardar = "resolver" | "rechazar" | "pendiente";

interface ControlAsistente {
  modo: ModoGuardar;
  llamadas: string[];
  terminado: number;
  resolverPendiente: (() => void) | null;
}

declare global {
  interface Window {
    __asistente: ControlAsistente;
  }
}

const control: ControlAsistente = { modo: "resolver", llamadas: [], terminado: 0, resolverPendiente: null };
window.__asistente = control;

function guardar(pasoId: string): Promise<void> {
  control.llamadas.push(pasoId);
  if (control.modo === "rechazar") return Promise.reject(new Error("fallo simulado"));
  if (control.modo === "pendiente") {
    return new Promise<void>((resolver) => {
      control.resolverPendiente = () => {
        control.resolverPendiente = null;
        resolver();
      };
    });
  }
  return Promise.resolve();
}

function Pagina() {
  const [nombre, setNombre] = useState("");
  const pasos: PasoAsistente[] = [
    {
      id: "datos",
      titulo: "Datos generales",
      opcional: false,
      validar: () => (nombre.trim() ? null : "Escribe el nombre de la organización."),
      contenido: (
        <label>
          Nombre
          <input value={nombre} onChange={(e) => setNombre(e.target.value)} />
        </label>
      ),
    },
    {
      id: "sedes",
      titulo: "Sedes",
      opcional: true,
      validar: () => null,
      contenido: <p>Sedes de la organización.</p>,
    },
    {
      id: "confirmacion",
      titulo: "Confirmación",
      opcional: false,
      validar: () => null,
      contenido: <p>Revisa y termina.</p>,
    },
  ];
  return (
    <main>
      <Asistente pasos={pasos} guardar={guardar} alTerminar={() => (control.terminado += 1)} />
    </main>
  );
}

const raiz = document.getElementById("raiz");
if (raiz) createRoot(raiz).render(<Pagina />);
