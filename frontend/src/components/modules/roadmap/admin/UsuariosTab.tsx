"use client";

import React, { useId, useState } from "react";

import { organizacionApi } from "@/lib/roadmap/cliente";
import type { UserItem } from "@/types/roadmap";
import { describirError, type ErrorDescrito } from "./errores";
import { BOTON_PRIMARIO, BloqueError, CAMPO, ETIQUETA } from "./ui";

export interface UsuariosTabProps {
  usuarios: UserItem[];
  alCambiar: () => Promise<void>;
}

const PATRON_CORREO = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export function UsuariosTab({ usuarios, alCambiar }: UsuariosTabProps) {
  const id = useId();
  const [correo, setCorreo] = useState("");
  const [nombre, setNombre] = useState("");
  const [errores, setErrores] = useState<{ correo?: string; nombre?: string }>({});
  const [error, setError] = useState<ErrorDescrito | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const [creado, setCreado] = useState<string | null>(null);

  async function crear(evento: React.FormEvent) {
    evento.preventDefault();
    setError(null);
    setCreado(null);
    const nuevos: { correo?: string; nombre?: string } = {};
    if (!PATRON_CORREO.test(correo.trim())) nuevos.correo = "Escribe un correo electrónico válido, por ejemplo nombre@empresa.ec.";
    if (nombre.trim() === "") nuevos.nombre = "Indica el nombre de la persona.";
    setErrores(nuevos);
    if (Object.keys(nuevos).length > 0) return;

    setOcupado(true);
    try {
      const usuario = await organizacionApi.createUser({ email: correo.trim(), nombre: nombre.trim() });
      await alCambiar();
      setCreado(usuario.nombre);
      setCorreo("");
      setNombre("");
    } catch (err: unknown) {
      setError(describirError(err));
    } finally {
      setOcupado(false);
    }
  }

  return (
    <div className="space-y-5">
      <form onSubmit={crear} noValidate aria-label="Nuevo usuario" className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-start">
        <div>
          <label htmlFor={`${id}-correo`} className={ETIQUETA}>
            Correo electrónico
          </label>
          <input
            id={`${id}-correo`}
            type="email"
            className={CAMPO}
            value={correo}
            onChange={(e) => setCorreo(e.target.value)}
            aria-invalid={Boolean(errores.correo)}
            aria-describedby={errores.correo ? `${id}-correo-error` : undefined}
          />
          {errores.correo && (
            <p id={`${id}-correo-error`} role="alert" className="text-[11px] text-[#ff6b86] mt-1">
              {errores.correo}
            </p>
          )}
        </div>
        <div>
          <label htmlFor={`${id}-nombre`} className={ETIQUETA}>
            Nombre
          </label>
          <input
            id={`${id}-nombre`}
            className={CAMPO}
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            aria-invalid={Boolean(errores.nombre)}
            aria-describedby={errores.nombre ? `${id}-nombre-error` : undefined}
          />
          {errores.nombre && (
            <p id={`${id}-nombre-error`} role="alert" className="text-[11px] text-[#ff6b86] mt-1">
              {errores.nombre}
            </p>
          )}
        </div>
        <div className="sm:pt-[1.15rem]">
          <button type="submit" className={BOTON_PRIMARIO} disabled={ocupado}>
            {ocupado ? "Creando…" : "Crear usuario"}
          </button>
        </div>
      </form>

      {error && <BloqueError error={error} testId="error-usuarios" />}
      {creado && (
        <p role="status" data-testid="usuario-creado" className="text-xs text-[#5fe39a]">
          Se creó el usuario {creado}. Ahora puedes asignarle un rol en la pestaña de roles.
        </p>
      )}

      {usuarios.length === 0 ? (
        <p role="status" className="text-xs text-zinc-400">
          Todavía no hay usuarios en esta organización.
        </p>
      ) : (
        <table className="w-full text-left text-xs">
          <caption className="sr-only">Usuarios de la organización</caption>
          <thead>
            <tr className="text-[var(--ui-texto-suave)] border-b border-[var(--ui-borde)]">
              <th scope="col" className="py-2 pr-3 font-semibold">
                Nombre
              </th>
              <th scope="col" className="py-2 font-semibold">
                Correo electrónico
              </th>
            </tr>
          </thead>
          <tbody>
            {usuarios.map((u) => (
              <tr key={u.id} data-testid={`usuario-${u.id}`} className="border-b border-[var(--ui-borde)]">
                <td className="py-2 pr-3 text-zinc-100">{u.nombre}</td>
                <td className="py-2 text-zinc-300">{u.email}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
