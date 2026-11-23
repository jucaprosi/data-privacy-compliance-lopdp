// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
export { AdminPanel } from "./AdminPanel";
export type { AdminPanelProps, SeccionAdmin } from "./AdminPanel";
export { construirArbol, aplanar } from "./arbolAreas";
export { describirError } from "./errores";
export { TAMANOS, configuracionApi } from "./configuracion";
export { estructuraApi, ETIQUETAS_NIVEL, ETIQUETAS_TIPO_CARGO } from "./estructura";
export type {
  AreaEstructuraNodo,
  CargoOrganico,
  InformeCoberturaResponse,
  NivelAreaEstructura,
  TipoCargoEstructura,
} from "./estructura";
export { EstructuraTab } from "./EstructuraTab";
export type { EstructuraTabProps } from "./EstructuraTab";
