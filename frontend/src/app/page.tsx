// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
import { redirect } from "next/navigation";

export const metadata = {
  title: "SMARTCIDI · Plataforma LOPDP 360",
  description: "Entorno unificado de gobernanza de privacidad y cumplimiento LOPDP Ecuador.",
};

export default function Home() {
  redirect("/dashboard");
}
