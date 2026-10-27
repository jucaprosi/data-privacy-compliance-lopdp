/**
 * DIAG-03: paridad de los cuatro indicadores entre la pantalla y el servidor.
 *
 * Calcula, con el tablero de la pantalla (useAuditStore en modo «verificado»), los indicadores que
 * se sellan para cada caso de paridad.json y los compara con «esperado». La prueba del servidor
 * (tests/test_diagnostico_resultados.py) compara su propio cálculo con los mismos valores: si los
 * dos pasan, pantalla y servidor dan lo mismo.
 *
 * El respaldo con documentos y el riesgo que queda se derivan como lo hacía la pantalla al sellar
 * antes de DIAG-03 (promedio del nivel sellado sobre 3, y 100 menos la madurez).
 */
import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

import { BANCO_PREGUNTAS, PERFIL_VACIO } from "../../src/lib/bancoPreguntas";
import type { IndicadoresSellados } from "../../src/lib/diagnostico/indicadores";
import { respuestasSellables } from "../../src/lib/diagnostico/indicadores";
import { useAuditStore, type RespuestaItemStore } from "../../src/store/useAuditStore";

interface CasoParidad {
  nombre: string;
  tamano: string;
  perfil: Record<string, "si" | "no">;
  respuestas: { pregunta_id: number; estado: RespuestaItemStore["cumple"]; nivel_evidencia: number }[];
  controles_con_documento: number[];
  esperado: IndicadoresSellados;
}

const casos: CasoParidad[] = JSON.parse(
  fs.readFileSync(path.resolve(process.cwd(), "tests/diagnostico/paridad.json"), "utf8")
).casos;
const banco = new Map(BANCO_PREGUNTAS.map((p) => [p.id, p]));

for (const caso of casos) {
  test(`paridad con el servidor: ${caso.nombre}`, () => {
    const respuestas: RespuestaItemStore[] = caso.respuestas.map((r) => {
      const pregunta = banco.get(r.pregunta_id)!;
      return {
        preguntaId: r.pregunta_id,
        cumple: r.estado,
        evidenciaNivel: r.nivel_evidencia,
        esCritica: pregunta.criticidad >= 5,
        riesgoBase: 5,
        criticidad: pregunta.criticidad,
        control: pregunta.control,
        dimensionId: pregunta.dimensionId,
        esReferencia: false,
      };
    });
    const perfil = { ...PERFIL_VACIO, ...caso.perfil };
    useAuditStore.setState({
      normativaSeleccionada: "LOPDP",
      companyData: { ...useAuditStore.getState().companyData, tamano: caso.tamano, perfil },
      respuestas,
      evidencias: [
        {
          id: "evidencia-paridad",
          codigo: "EVD-0001",
          nombreArchivo: "respaldo.pdf",
          tamanoBytes: 1,
          tipoMime: "application/pdf",
          sha256: "0".repeat(64),
          normativa: "LOPDP",
          controlesVinculados: caso.controles_con_documento,
          registradaEn: "2026-10-28T00:00:00Z",
        },
      ],
    });

    const resultado = useAuditStore.getState().calcularResultadoAssessment("verificado");
    const evaluadas = respuestasSellables(respuestas, "LOPDP", caso.tamano, perfil).filter(
      (r) => r.cumple !== "Pendiente"
    );
    const conDocumento = new Set(caso.controles_con_documento);
    const sumaSellada = evaluadas.reduce((acc, r) => acc + (conDocumento.has(r.preguntaId) ? r.evidenciaNivel : 0), 0);
    const pantalla: IndicadoresSellados = {
      cumplimiento: resultado.brechasCriticas === 0,
      brechas_criticas: resultado.brechasCriticas,
      madurez: resultado.scorePonderado,
      nivel_madurez: resultado.nivelAjustado,
      respaldo_documental:
        evaluadas.length > 0 ? Math.round((sumaSellada / evaluadas.length / 3) * 1000) / 10 : 0,
      riesgo_residual: Math.round((100 - resultado.scorePonderado) * 10) / 10,
      preguntas_evaluadas: resultado.totalEvaluados,
      preguntas_aplicables: resultado.totalAplicables,
      cobertura: resultado.coberturaPorcentaje,
    };
    expect(pantalla).toEqual(caso.esperado);
  });
}
