"""Pruebas para el grafo de cumplimiento: interacciones entre RAT y Riesgos/EIPD."""
import pytest
from features.rat.domain.models import ActividadRAT, BaseLegitimacion, CategoriaTitular
from features.rat.rat_service import registrar_actividad_rat
from features.riesgos_mtge.domain.models import EntradaCalculoMTGE
from features.riesgos_mtge.riesgos_mtge_service import evaluar_gran_escala_mtge
# Asumiremos que creamos un servicio orquestador o añadimos lógica en rat_service para disparar esto
from features.rat.rat_service import eliminar_actividad_rat

# Simulación de un store de riesgos acoplado al RAT para el compliance graph
class RiesgosStoreMock:
    _riesgos = {}

    @classmethod
    def asociar_riesgo(cls, rat_id, eipd_requerido):
        cls._riesgos[rat_id] = {"eipd_requerido": eipd_requerido}

    @classmethod
    def obtener_riesgo(cls, rat_id):
        return cls._riesgos.get(rat_id)

    @classmethod
    def eliminar_riesgos_rat(cls, rat_id):
        if rat_id in cls._riesgos:
            del cls._riesgos[rat_id]

def modificar_tratamiento_rat(actividad: ActividadRAT, es_gran_escala: bool):
    """Orquesta la modificación de RAT y recálculo de riesgos."""
    actividad.es_gran_escala = es_gran_escala
    actividad.requiere_eipd = es_gran_escala
    guardada = registrar_actividad_rat(actividad)
    RiesgosStoreMock.asociar_riesgo(guardada.id, guardada.requiere_eipd)
    return guardada

def orquestar_eliminacion_rat(rat_id: str):
    """Elimina atómicamente un RAT y sus riesgos vinculados."""
    eliminar_actividad_rat(rat_id)
    RiesgosStoreMock.eliminar_riesgos_rat(rat_id)

def test_compliance_graph_recalculo_modificacion():
    """Al modificar un tratamiento a gran escala, las obligaciones de EIPD se recalculan."""
    actividad = ActividadRAT(
        tenant_id="tenant-cg-1",
        codigo="RAT-TEST-01",
        nombre="Tratamiento Test",
        area_responsable="IT",
        finalidad="Prueba",
    )
    guardada = registrar_actividad_rat(actividad)
    RiesgosStoreMock.asociar_riesgo(guardada.id, False)

    assert RiesgosStoreMock.obtener_riesgo(guardada.id)["eipd_requerido"] is False

    # Modificación que detona gran escala
    guardada_mod = modificar_tratamiento_rat(guardada, es_gran_escala=True)

    assert guardada_mod.requiere_eipd is True
    assert RiesgosStoreMock.obtener_riesgo(guardada_mod.id)["eipd_requerido"] is True

def test_compliance_graph_eliminacion_atomica():
    """Al eliminar un tratamiento en RAT, los riesgos vinculados se eliminan atómicamente."""
    actividad = ActividadRAT(
        tenant_id="tenant-cg-1",
        codigo="RAT-TEST-02",
        nombre="Tratamiento Test a eliminar",
        area_responsable="IT",
        finalidad="Prueba",
    )
    guardada = registrar_actividad_rat(actividad)
    RiesgosStoreMock.asociar_riesgo(guardada.id, True)
    
    assert RiesgosStoreMock.obtener_riesgo(guardada.id) is not None

    orquestar_eliminacion_rat(guardada.id)

    # Verificar eliminación atómica
    assert RiesgosStoreMock.obtener_riesgo(guardada.id) is None
