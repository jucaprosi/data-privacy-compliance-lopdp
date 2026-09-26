export interface FundamentoCopiloto {
  articulo: string;
  titulo: string;
  url: string;
  version: string;
  resumen: string;
}

export interface BrechaCopiloto {
  pregunta_id: number;
  control: string;
  dimension_id: string;
  severidad: string;
}

export interface PlanCopiloto {
  pregunta_id: number;
  control: string;
  severidad: string;
  pasos: string[];
  responsable_sugerido: string;
  evidencias: string[];
  criterio_cierre: string;
  seguimiento: string;
  fundamento: FundamentoCopiloto[];
}

export interface ConsultaCopiloto {
  pregunta: string;
  brechas: BrechaCopiloto[];
  historial: { rol: "usuario" | "asistente"; contenido: string }[];
  brecha_id?: number;
  estado: "Por iniciar" | "Implementación" | "Seguimiento";
}

export interface RespuestaCopiloto {
  pregunta: string;
  respuesta: string;
  modo: "local" | "deepseek" | "sin_fuente";
  fundamentos: FundamentoCopiloto[];
  planes: PlanCopiloto[];
  advertencias: string[];
  corpus_version: string;
  dlp_aplicado: boolean;
}

export interface EstadoCopiloto {
  proveedor_configurado: boolean;
  proveedor: string;
  modo: string;
  corpus_version: string;
  dlp_activo: boolean;
  inferencia_externa_habilitada?: boolean;
  datos_enviados?: string[];
  datos_excluidos?: string[];
}

export interface TurnoCopiloto {
  id: string;
  pregunta: string;
  respuesta: RespuestaCopiloto;
  creado: string;
}
