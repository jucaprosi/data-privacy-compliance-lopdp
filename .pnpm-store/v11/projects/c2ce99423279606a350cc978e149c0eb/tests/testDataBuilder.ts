/**
 * Test Data Builders - Patrón importado de PDA.
 * Facilita la construcción de datos de prueba complejos sin repetición.
 *
 * Uso:
 * ```typescript
 * import { ProjectBuilder, ControlBuilder } from "./testDataBuilder";
 *
 * const project = new ProjectBuilder()
 *   .withName("Mi Entidad")
 *   .withNormativa("LOPDP")
 *   .build();
 *
 * const control = new ControlBuilder()
 *   .withState("Conforme")
 *   .withEvidence()
 *   .build();
 * ```
 */

/**
 * Datos de configuración de proyecto.
 */
export interface ProjectData {
  name: string;
  normativa: "LOPDP" | "GDPR" | "ISO27001";
  industria?: string;
  description?: string;
}

/**
 * Datos de un control/pregunta en evaluación.
 */
export interface ControlData {
  id: string;
  nombre: string;
  estado: "Conforme" | "Parcial" | "No Conforme" | "No Aplica";
  evidencia?: {
    tipo: string;
    valor: string;
  };
  observaciones?: string;
}

/**
 * Datos de resultado de assessment.
 */
export interface AssessmentResultData {
  level: number;
  coverage: number;
  applicableControls: number;
  answeredControls: number;
  hasDiscrepancy: boolean;
  reason?: string;
}

/**
 * Builder para datos de proyecto.
 */
export class ProjectBuilder {
  private data: ProjectData = {
    name: "Entidad de Prueba S.A.",
    normativa: "LOPDP",
    industria: "Finance",
  };

  withName(name: string): ProjectBuilder {
    this.data.name = name;
    return this;
  }

  withNormativa(normativa: "LOPDP" | "GDPR" | "ISO27001"): ProjectBuilder {
    this.data.normativa = normativa;
    return this;
  }

  withIndustria(industria: string): ProjectBuilder {
    this.data.industria = industria;
    return this;
  }

  withDescription(description: string): ProjectBuilder {
    this.data.description = description;
    return this;
  }

  build(): ProjectData {
    return { ...this.data };
  }

  /**
   * Crea un builder por defecto para valores por defecto normalizados.
   */
  static default(): ProjectBuilder {
    return new ProjectBuilder();
  }

  /**
   * Crea un builder para entidad de prueba mínima.
   */
  static minimal(): ProjectBuilder {
    return new ProjectBuilder().withName("Test Corp");
  }

  /**
   * Crea un builder para entidad grande (simulación de caso complejo).
   */
  static large(): ProjectBuilder {
    return new ProjectBuilder()
      .withName("Corporación Global S.A.")
      .withIndustria("Manufacturing")
      .withDescription("Entidad con múltiples sedes y complejidad operativa");
  }
}

/**
 * Builder para datos de control.
 */
export class ControlBuilder {
  private data: ControlData = {
    id: `CTL-${Date.now()}`,
    nombre: "Control Genérico",
    estado: "Parcial",
  };

  withId(id: string): ControlBuilder {
    this.data.id = id;
    return this;
  }

  withNombre(nombre: string): ControlBuilder {
    this.data.nombre = nombre;
    return this;
  }

  withEstado(
    estado: "Conforme" | "Parcial" | "No Conforme" | "No Aplica"
  ): ControlBuilder {
    this.data.estado = estado;
    return this;
  }

  withEvidence(tipo = "Documento", valor = "evidencia.pdf"): ControlBuilder {
    this.data.evidencia = { tipo, valor };
    return this;
  }

  withObservaciones(obs: string): ControlBuilder {
    this.data.observaciones = obs;
    return this;
  }

  build(): ControlData {
    return { ...this.data };
  }

  /**
   * Control completamente conforme con evidencia.
   */
  static compliant(): ControlBuilder {
    return new ControlBuilder()
      .withEstado("Conforme")
      .withEvidence("Política", "politica-oficial.pdf");
  }

  /**
   * Control parcialmente implementado sin evidencia suficiente.
   */
  static partial(): ControlBuilder {
    return new ControlBuilder()
      .withEstado("Parcial")
      .withObservaciones("Implementación incompleta en una sucursal");
  }

  /**
   * Control no conforme sin evidencia.
   */
  static nonCompliant(): ControlBuilder {
    return new ControlBuilder()
      .withEstado("No Conforme")
      .withObservaciones("No implementado");
  }

  /**
   * Control no aplicable al alcance.
   */
  static notApplicable(): ControlBuilder {
    return new ControlBuilder()
      .withEstado("No Aplica")
      .withObservaciones("Fuera del alcance del proyecto");
  }
}

/**
 * Builder para resultados de assessment.
 */
export class AssessmentBuilder {
  private data: AssessmentResultData = {
    level: 0,
    coverage: 0,
    applicableControls: 0,
    answeredControls: 0,
    hasDiscrepancy: false,
  };

  withLevel(level: 0 | 1 | 2 | 3 | 4 | 5): AssessmentBuilder {
    this.data.level = level;
    return this;
  }

  withCoverage(coverage: number): AssessmentBuilder {
    this.data.coverage = Math.min(1, Math.max(0, coverage));
    return this;
  }

  withControls(
    applicable: number,
    answered: number
  ): AssessmentBuilder {
    this.data.applicableControls = applicable;
    this.data.answeredControls = answered;
    return this;
  }

  withDiscrepancy(reason: string): AssessmentBuilder {
    this.data.hasDiscrepancy = true;
    this.data.reason = reason;
    return this;
  }

  build(): AssessmentResultData {
    return { ...this.data };
  }

  /**
   * Assessment sin respuestas.
   */
  static unevaluated(): AssessmentBuilder {
    return new AssessmentBuilder()
      .withLevel(0)
      .withCoverage(0)
      .withControls(100, 0)
      .withDiscrepancy("Sin evaluación registrada");
  }

  /**
   * Assessment con cobertura insuficiente.
   */
  static insufficientCoverage(): AssessmentBuilder {
    return new AssessmentBuilder()
      .withLevel(0)
      .withCoverage(0.15)
      .withControls(100, 15)
      .withDiscrepancy("Cobertura por debajo del mínimo exigido");
  }

  /**
   * Assessment con nivel 1 válido.
   */
  static level1(): AssessmentBuilder {
    return new AssessmentBuilder()
      .withLevel(1)
      .withCoverage(0.65)
      .withControls(100, 65);
  }

  /**
   * Assessment con nivel 5 (máximo).
   */
  static level5(): AssessmentBuilder {
    return new AssessmentBuilder()
      .withLevel(5)
      .withCoverage(0.95)
      .withControls(100, 95);
  }
}

/**
 * Factory para crear conjuntos de controles típicos.
 */
export class ControlSetBuilder {
  /**
   * Retorna un conjunto de controles: N conformes, M parciales, rest no conformes.
   */
  static mixed(total: number, compliant: number, partial: number): ControlData[] {
    const controls: ControlData[] = [];

    // Agregar conformes
    for (let i = 0; i < compliant; i++) {
      controls.push(ControlBuilder.compliant().withId(`CTL-${i + 1}`).build());
    }

    // Agregar parciales
    for (let i = 0; i < partial; i++) {
      controls.push(
        ControlBuilder.partial()
          .withId(`CTL-${compliant + i + 1}`)
          .build()
      );
    }

    // Agregar no conformes
    for (let i = 0; i < total - compliant - partial; i++) {
      controls.push(
        ControlBuilder.nonCompliant()
          .withId(`CTL-${compliant + partial + i + 1}`)
          .build()
      );
    }

    return controls;
  }

  /**
   * Retorna todos conformes (caso ideal).
   */
  static allCompliant(count: number): ControlData[] {
    return Array.from({ length: count }, (_, i) =>
      ControlBuilder.compliant().withId(`CTL-${i + 1}`).build()
    );
  }

  /**
   * Retorna todos no conformes (peor caso).
   */
  static allNonCompliant(count: number): ControlData[] {
    return Array.from({ length: count }, (_, i) =>
      ControlBuilder.nonCompliant().withId(`CTL-${i + 1}`).build()
    );
  }
}

/**
 * Configuración de escenarios típicos de prueba.
 */
export class TestScenario {
  /**
   * Escenario: Empresa nueva sin evaluación.
   */
  static newCompany() {
    return {
      project: ProjectBuilder.default().build(),
      controls: [],
      expectedLevel: 0,
      expectedDiscrepancy: false,
    };
  }

  /**
   * Escenario: Empresa con evaluación incompleta.
   */
  static incompleteEvaluation() {
    const controls = ControlSetBuilder.mixed(20, 3, 2);
    return {
      project: ProjectBuilder.default().build(),
      controls,
      expectedLevel: 0,
      expectedDiscrepancy: true,
      expectedReason: "Cobertura insuficiente",
    };
  }

  /**
   * Escenario: Empresa con nivel 1 (madurez inicial).
   */
  static level1Maturity() {
    const controls = ControlSetBuilder.mixed(20, 13, 7);
    return {
      project: ProjectBuilder.default().build(),
      controls,
      expectedLevel: 1,
      expectedCoverage: 0.65,
    };
  }

  /**
   * Escenario: Empresa con nivel 5 (madurez máxima).
   */
  static level5Maturity() {
    const controls = ControlSetBuilder.allCompliant(20);
    return {
      project: ProjectBuilder.default().build(),
      controls,
      expectedLevel: 5,
      expectedCoverage: 1.0,
    };
  }
}
