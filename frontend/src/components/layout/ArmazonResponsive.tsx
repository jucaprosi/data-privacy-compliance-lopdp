"use client";

// ¤¤frontend-architect
// ¤frontend-ide
/**
 * Armazón responsive del tablero (FE-27). Decide cuántos paneles se ven según el ancho:
 * - lg (≥ 1024 px): menú, centro y copiloto redimensionables, con sus tamaños guardados;
 * - md (768–1023 px): menú y centro; el copiloto va en un cajón derecho;
 * - menor de md: solo el centro; el menú y el copiloto van en cajones.
 * No sabe qué muestra cada zona: el contenido llega por props.
 */
import React from "react";
import { Group as PanelGroup, Panel, Separator as PanelResizeHandle } from "react-resizable-panels";
import { Bot, Menu as IconoMenu } from "lucide-react";
import CajonLateral from "./CajonLateral";

type Tamano = "lg" | "md" | "sm";

const calcular = (): Tamano => {
  if (typeof window === "undefined") return "lg";
  if (window.matchMedia("(min-width: 1024px)").matches) return "lg";
  if (window.matchMedia("(min-width: 768px)").matches) return "md";
  return "sm";
};

function useTamano(): Tamano {
  const [tamano, setTamano] = React.useState<Tamano>(calcular);
  React.useEffect(() => {
    const consultas = [window.matchMedia("(min-width: 1024px)"), window.matchMedia("(min-width: 768px)")];
    const alCambiar = () => setTamano(calcular());
    consultas.forEach((c) => c.addEventListener("change", alCambiar));
    alCambiar();
    return () => consultas.forEach((c) => c.removeEventListener("change", alCambiar));
  }, []);
  return tamano;
}

interface ArmazonResponsiveProps {
  /** Barra de los menús; va en la franja superior. */
  barraMenus: React.ReactNode;
  /** Contenido del menú lateral; recibe `alElegir` para cerrar el cajón al elegir un submenú. */
  menu: (alElegir: () => void) => React.ReactNode;
  centro: React.ReactNode;
  copiloto: React.ReactNode;
  claseFondo: string;
  panelLayout: {
    defaultLayout: React.ComponentProps<typeof PanelGroup>["defaultLayout"];
    onLayoutChanged: React.ComponentProps<typeof PanelGroup>["onLayoutChanged"];
  };
}

const CLASE_ZONA =
  "h-full bg-white dark:bg-[var(--ui-superficie)] border border-[#e8dcf5] dark:border-[var(--ui-borde)] rounded-lg flex flex-col justify-between overflow-hidden shadow-sm";
const CLASE_BOTON =
  "inline-flex min-h-10 min-w-10 shrink-0 items-center gap-1.5 rounded-lg border border-[var(--ui-borde)] bg-[var(--ui-superficie)] px-3 text-xs font-medium cursor-pointer hover:bg-[var(--ui-boton-hover)]";

export default function ArmazonResponsive({
  barraMenus,
  menu,
  centro,
  copiloto,
  claseFondo,
  panelLayout,
}: ArmazonResponsiveProps) {
  const tamano = useTamano();
  const [cajon, setCajon] = React.useState<"menu" | "copiloto" | null>(null);
  const cerrar = React.useCallback(() => setCajon(null), []);

  // Al ensanchar la ventana, el cajón que ya no aplica se cierra.
  React.useEffect(() => {
    if (tamano === "lg") setCajon(null);
    else if (tamano === "md" && cajon === "menu") setCajon(null);
  }, [tamano, cajon]);

  const conCopilotoEnCajon = tamano !== "lg";
  const conMenuEnCajon = tamano === "sm";

  return (
    <div data-testid="armazon-responsive" className="flex-1 min-h-0 min-w-0 flex flex-col overflow-hidden gap-0.5">
      <div className="flex shrink-0 items-center gap-1 min-w-0">
        {conMenuEnCajon && (
          <button
            type="button"
            className={CLASE_BOTON}
            aria-expanded={cajon === "menu"}
            aria-controls="cajon-menu"
            onClick={() => setCajon("menu")}
          >
            <IconoMenu className="h-4 w-4" aria-hidden="true" />
            <span>Menú</span>
          </button>
        )}
        <div className="min-w-0 flex-1">{barraMenus}</div>
        {conCopilotoEnCajon && (
          <button
            type="button"
            className={CLASE_BOTON}
            aria-expanded={cajon === "copiloto"}
            aria-controls="cajon-copiloto"
            onClick={() => setCajon("copiloto")}
          >
            <Bot className="h-4 w-4" aria-hidden="true" />
            <span>Copiloto</span>
          </button>
        )}
      </div>

      <div className={`flex-1 min-h-0 flex overflow-hidden ${claseFondo}`}>
        {tamano === "lg" ? (
          <PanelGroup
            id="dashboard-paneles-v1"
            orientation="horizontal"
            defaultLayout={panelLayout.defaultLayout}
            onLayoutChanged={panelLayout.onLayoutChanged}
            className="flex-1 flex overflow-hidden gap-0.5"
          >
            <Panel
              id="panel-dock-izquierdo"
              defaultSize="18%"
              minSize="14%"
              maxSize="25%"
              collapsible={true}
              collapsedSize="4%"
              className="h-full"
            >
              <aside className={CLASE_ZONA}>{menu(cerrar)}</aside>
            </Panel>
            <PanelResizeHandle
              className="w-0.5 bg-transparent cursor-col-resize select-none shrink-0"
              title="Arrastra para redimensionar el panel"
            />
            <Panel id="panel-lienzo-central" defaultSize="54%" minSize="40%" className="h-full">
              {centro}
            </Panel>
            <PanelResizeHandle
              className="w-0.5 bg-transparent cursor-col-resize select-none shrink-0"
              title="Arrastra para redimensionar el panel"
            />
            <Panel id="panel-copiloto-derecho" defaultSize="28%" minSize="20%" maxSize="45%" className="h-full">
              <aside className={CLASE_ZONA}>{copiloto}</aside>
            </Panel>
          </PanelGroup>
        ) : (
          <div className="flex-1 min-w-0 flex gap-0.5 overflow-hidden">
            {tamano === "md" && (
              <aside data-testid="panel-menu-md" className={`${CLASE_ZONA} w-56 shrink-0`}>
                {menu(cerrar)}
              </aside>
            )}
            <div className="flex-1 min-w-0 h-full">{centro}</div>
          </div>
        )}
      </div>

      <CajonLateral
        abierto={cajon === "menu" && conMenuEnCajon}
        onCerrar={cerrar}
        lado="izquierdo"
        nombre="Menú de navegación"
        nombreCerrar="Cerrar menú"
        anchoClase="w-[85vw] max-w-sm"
      >
        <div id="cajon-menu" className="flex-1 min-h-0 flex flex-col justify-between">
          {menu(cerrar)}
        </div>
      </CajonLateral>
      <CajonLateral
        abierto={cajon === "copiloto" && conCopilotoEnCajon}
        onCerrar={cerrar}
        lado="derecho"
        nombre="Copiloto"
        nombreCerrar="Cerrar copiloto"
        anchoClase="w-full max-w-none md:max-w-[400px]"
      >
        <div id="cajon-copiloto" className="flex-1 min-h-0 flex flex-col">
          {copiloto}
        </div>
      </CajonLateral>
    </div>
  );
}
