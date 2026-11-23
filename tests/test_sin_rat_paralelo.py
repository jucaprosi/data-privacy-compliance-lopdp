# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤rat
# ¤arbitro
"""Prueba de comportamiento: RAT único y autoritativo en el backend."""
from __future__ import annotations

import pytest
from features.rat.domain.models import ActividadRAT, BaseLegitimacion, CategoriaTitular
from features.rat.domain.validaciones import evaluar_reglas
from features.rat import rat_service


def test_rat_unico_autoritativo_en_backend():
    """El RAT autoritativo evalúa reglas de dominio y expone sus operaciones solo por rat_service."""
    ficha = ActividadRAT(
        tenant_id="tenant-rat-unico",
        codigo="RAT-001",
        nombre="Gestión de Nómina",
        area_responsable="Talento Humano",
        finalidad="Pago de haberes",
        base_legal=BaseLegitimacion.CUMPLIMIENTO_CONTRATO,
        categorias_titulares=[CategoriaTitular.EMPLEADOS],
        categorias_datos=["Identificación", "Datos bancarios"],
        plazo_conservacion="7 años",
        medidas_seguridad=["Cifrado", "Control de acceso"],
    )
    reglas = evaluar_reglas(ficha)
    errores = [r for r in reglas if not r.cumple]
    assert not errores, f"Errores en RAT canónico: {errores}"

    assert callable(rat_service.registrar_actividad_rat)
    assert callable(rat_service.listar_actividades_rat)
    assert callable(rat_service.editar_actividad_rat)
    assert callable(rat_service.eliminar_actividad_rat)
