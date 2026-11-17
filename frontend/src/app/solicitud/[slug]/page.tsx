"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";

interface PortalData {
  organizacion: string;
  derechos: string[];
  texto: string;
}

export default function SolicitudPublicaPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const resolvedParams = React.use(params);
  const slug = resolvedParams.slug;

  const [portal, setPortal] = useState<PortalData | null>(null);
  const [cargando, setCargando] = useState(true);
  const [errorPortal, setErrorPortal] = useState<string | null>(null);

  // Formulario
  const [derecho, setDerecho] = useState("ACCESO");
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [errorEnvio, setErrorEnvio] = useState<string | null>(null);
  const [codigoGenerado, setCodigoGenerado] = useState<string | null>(null);

  useEffect(() => {
    async function cargarPortal() {
      try {
        setCargando(true);
        setErrorPortal(null);
        const res = await fetch(`/api/v1/publico/solicitud/${encodeURIComponent(slug)}`);
        if (!res.ok) {
          if (res.status === 404) {
            setErrorPortal("El portal de privacidad solicitado no está disponible o no existe.");
          } else {
            setErrorPortal("Ocurrió un error al cargar la información del portal.");
          }
          return;
        }
        const data = await res.json();
        setPortal(data);
        if (data.derechos && data.derechos.length > 0) {
          setDerecho(data.derechos[0]);
        }
      } catch {
        setErrorPortal("No se pudo conectar con el servidor.");
      } finally {
        setCargando(false);
      }
    }
    cargarPortal();
  }, [slug]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nombre.trim() || !email.trim()) {
      setErrorEnvio("Por favor complete su nombre y correo electrónico.");
      return;
    }
    try {
      setEnviando(true);
      setErrorEnvio(null);
      const res = await fetch(`/api/v1/publico/solicitud/${encodeURIComponent(slug)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          derecho,
          nombre: nombre.trim(),
          email: email.trim(),
          descripcion: descripcion.trim(),
        }),
      });

      if (res.status === 429) {
        setErrorEnvio("Ha superado el límite de solicitudes permitidas por hora. Por favor intente más tarde.");
        return;
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        setErrorEnvio(errData.detail || "Error al procesar su solicitud. Revise los campos ingresados.");
        return;
      }

      const data = await res.json();
      setCodigoGenerado(data.codigo);
    } catch {
      setErrorEnvio("Error de conexión al enviar la solicitud.");
    } finally {
      setEnviando(false);
    }
  };

  if (cargando) {
    return (
      <main className="min-h-screen bg-[var(--color-bg-base)] text-[var(--color-text-primary)] flex items-center justify-center p-4">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-[var(--color-text-secondary)]">Cargando portal de solicitudes...</p>
        </div>
      </main>
    );
  }

  if (errorPortal || !portal) {
    return (
      <main className="min-h-screen bg-[var(--color-bg-base)] text-[var(--color-text-primary)] flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-[var(--color-bg-surface)] border border-[var(--color-border-subtle)] rounded-xl p-8 shadow-sm text-center">
          <div className="w-12 h-12 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4 font-bold text-lg">
            ✕
          </div>
          <h1 className="text-xl font-semibold mb-2">Portal no disponible</h1>
          <p className="text-sm text-[var(--color-text-secondary)] mb-6">{errorPortal}</p>
          <Link
            href="/solicitud/seguir"
            className="inline-block text-sm text-indigo-600 hover:text-indigo-700 font-medium underline"
          >
            Consultar estado de una solicitud existente
          </Link>
        </div>
      </main>
    );
  }

  if (codigoGenerado) {
    return (
      <main className="min-h-screen bg-[var(--color-bg-base)] text-[var(--color-text-primary)] flex items-center justify-center p-4">
        <div className="max-w-lg w-full bg-[var(--color-bg-surface)] border border-[var(--color-border-subtle)] rounded-xl p-8 shadow-sm text-center">
          <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4 font-bold text-lg">
            ✓
          </div>
          <h1 className="text-2xl font-bold mb-2">Solicitud Registrada</h1>
          <p className="text-sm text-[var(--color-text-secondary)] mb-6">
            Su solicitud ha sido recibida formalmente por <strong>{portal.organizacion}</strong>. Guarde el siguiente código para verificar el estado de su trámite.
          </p>

          <div className="bg-[var(--color-bg-subtle)] border border-[var(--color-border-strong)] rounded-lg p-4 mb-6 font-mono text-base font-semibold text-indigo-600 select-all tracking-wider break-all">
            {codigoGenerado}
          </div>

          <div className="flex flex-col gap-3">
            <Link
              href={`/solicitud/seguir/${encodeURIComponent(codigoGenerado)}`}
              className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg text-sm transition-colors text-center"
            >
              Consultar Seguimiento Ahora
            </Link>
            <button
              onClick={() => {
                setCodigoGenerado(null);
                setNombre("");
                setEmail("");
                setDescripcion("");
              }}
              className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] py-1.5"
            >
              Registrar otra solicitud
            </button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[var(--color-bg-base)] text-[var(--color-text-primary)] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <header className="text-center mb-8">
          <div className="inline-block px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full text-xs font-semibold tracking-wide uppercase mb-3">
            Portal de Derechos ARCO+ (LOPDP)
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
            {portal.organizacion}
          </h1>
          {portal.texto ? (
            <p className="mt-3 text-base text-[var(--color-text-secondary)]">
              {portal.texto}
            </p>
          ) : (
            <p className="mt-3 text-sm text-[var(--color-text-secondary)]">
              Complete el formulario para ejercer sus derechos de protección de datos personales.
            </p>
          )}
        </header>

        <div className="bg-[var(--color-bg-surface)] border border-[var(--color-border-subtle)] rounded-xl shadow-sm p-6 sm:p-8">
          {errorEnvio && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {errorEnvio}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="derecho" className="block text-sm font-medium mb-1.5">
                Derecho a Ejercer <span className="text-red-500">*</span>
              </label>
              <select
                id="derecho"
                value={derecho}
                onChange={(e) => setDerecho(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-[var(--color-bg-base)] border border-[var(--color-border-subtle)] rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              >
                {portal.derechos.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="nombre" className="block text-sm font-medium mb-1.5">
                Nombre y Apellidos del Titular <span className="text-red-500">*</span>
              </label>
              <input
                id="nombre"
                type="text"
                required
                maxLength={200}
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                placeholder="Ej. María Pérez López"
                className="w-full px-3.5 py-2.5 bg-[var(--color-bg-base)] border border-[var(--color-border-subtle)] rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium mb-1.5">
                Correo Electrónico de Notificación <span className="text-red-500">*</span>
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ejemplo@correo.com"
                className="w-full px-3.5 py-2.5 bg-[var(--color-bg-base)] border border-[var(--color-border-subtle)] rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
              <p className="mt-1 text-xs text-[var(--color-text-secondary)]">
                Utilizaremos este correo únicamente para notificarle la respuesta formal o solicitarle aclaraciones.
              </p>
            </div>

            <div>
              <label htmlFor="descripcion" className="block text-sm font-medium mb-1.5">
                Descripción o Motivo de la Solicitud
              </label>
              <textarea
                id="descripcion"
                rows={4}
                maxLength={4000}
                value={descripcion}
                onChange={(e) => setDescripcion(e.target.value)}
                placeholder="Detalle de forma clara qué datos o tratamiento requiere consultar, rectificar o eliminar..."
                className="w-full px-3.5 py-2.5 bg-[var(--color-bg-base)] border border-[var(--color-border-subtle)] rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
              <div className="flex justify-end mt-1 text-xs text-[var(--color-text-secondary)]">
                {descripcion.length} / 4000
              </div>
            </div>

            <button
              type="submit"
              disabled={enviando}
              className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold rounded-lg text-sm shadow transition-colors flex items-center justify-center gap-2"
            >
              {enviando ? "Enviando Solicitud..." : "Enviar Solicitud"}
            </button>
          </form>

          <footer className="mt-8 pt-6 border-t border-[var(--color-border-subtle)] text-center text-xs text-[var(--color-text-secondary)]">
            <Link
              href="/solicitud/seguir"
              className="text-indigo-600 hover:underline font-medium"
            >
              ¿Ya tiene un código de trámite? Consulte aquí el seguimiento
            </Link>
          </footer>
        </div>
      </div>
    </main>
  );
}
