/**
 * DIAG-03: paridad de los cuatro indicadores entre la pantalla y el servidor.
 *
 * Calcula, con el tablero de la pantalla (useAuditStore en modo «verificado»), los indicadores que
 * se sellan para cada caso de paridad.json y los compara con «esperado». La prueba del servidor
 * (tests/test_diagnostico_resultados.py) compara su propio cálculo con los mismos valores: si los
 * dos pasan, pantalla y servidor dan lo mismo.
 *
 * Desde DIAG-09 los indicadores son por dimensión y sin cifra global: «esperado» sale del motor del
 * servidor (resultados_engine.py) y la pantalla debe dar el mismo nivel, puntaje, cobertura y brechas
 * en cada dimensión.
 */
import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

import { BANCO_PREGUNTAS, PERFIL_VACIO } from "../../src/lib/bancoPreguntas";
import { NIVEL_EVIDENCIA_MAXIMO, estadoDerivado } from "../../src/lib/diagnostico/escala";
import type { IndicadoresSellados } from "../../src/lib/diagnostico/indicadores";
import { respuestasSellables } from "../../src/lib/diagnostico/indicadores";
import { useAuditStore, type RespuestaItemStore } from "../../src/store/useAuditStore";

interface CasoParidad {
  nombre: string;
  tamano: string;
  perfil: Record<string, "si" | "no">;
  respuestas: { pregunta_id: number; nivel_asignado: number | null; nivel_evidencia: number }[];
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
        nivelAsignado: r.nivel_asignado,
        cumple: estadoDerivado(r.nivel_asignado),
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
      (r) => r.nivelAsignado != null
    );
    const conDocumento = new Set(caso.controles_con_documento);
    const sumaSellada = evaluadas.reduce((acc, r) => acc + (conDocumento.has(r.preguntaId) ? r.evidenciaNivel : 0), 0);
    const pantalla: IndicadoresSellados = {
      escala: "smartcidi_1_5",
      cumplimiento: resultado.brechasCriticas === 0,
      brechas_criticas: resultado.brechasCriticas,
      brechas_altas: resultado.brechasAltas,
      por_dimension: resultado.dimensiones
        .filter((d) => d.itemsAplicables > 0)
        .map((d) => ({
          dimension: d.id,
          nombre: d.nombre,
          nivel: d.nivel,
          etiqueta: d.nivelEtiqueta,
          score: d.score,
          cobertura: d.coberturaPorcentaje,
          brechas_criticas: d.brechasCriticas,
          brechas_altas: d.brechasAltas,
        })),
      respaldo_documental:
        evaluadas.length > 0 ? Math.round((sumaSellada / evaluadas.length / NIVEL_EVIDENCIA_MAXIMO) * 1000) / 10 : 0,
      preguntas_evaluadas: resultado.totalEvaluados,
      preguntas_aplicables: resultado.totalAplicables,
      cobertura: resultado.coberturaPorcentaje,
    };
    expect(pantalla).toEqual(caso.esperado);
  });
}
