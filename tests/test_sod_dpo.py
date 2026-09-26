"""Test de verificación de Segregación de Funciones (SoD) del DPO.
Invariante: INV_LOPDP_DPO_INDEPENDENCE.
"""
from app_core.security import (
    RolUsuario,
    AccionOperativa,
    UsuarioContexto,
    validar_permiso_sod,
)
from features.dpo_cockpit.dpo_cockpit_service import emitir_dictamen_dpo, firmar_acuse_recibo_dictamen
from features.dpo_cockpit.domain.models import DictamenDPO, TipoDictamenDPO
from features.auditoria_capa.auditoria_capa_service import (
    registrar_hallazgo_auditoria,
    cerrar_accion_correctiva_independiente,
)
from features.auditoria_capa.domain.models import TicketCAPA, SeveridadHallazgo
import pytest

def test_sod_bloquea_dpo_asignar_dueno_control():
    """El DPD/DPO no puede ser asignado como propietario de control ni aprobar políticas."""
    usuario_dpo = UsuarioContexto(
        usuario_id="dpo-001",
        tenant_id="tenant-123",
        email="dpo@empresa.com",
        rol=RolUsuario.DPD_DPO_INTERNO,
    )
    # Debe ser rechazado
    assert validar_permiso_sod(usuario_dpo, AccionOperativa.ASIGNAR_DUEÑO_CONTROL) is False
    assert validar_permiso_sod(usuario_dpo, AccionOperativa.APROBAR_FINALIDAD_RAT) is False
    assert validar_permiso_sod(usuario_dpo, AccionOperativa.EJECUTAR_REMEDIACION_CAPA) is False

    # Debe ser permitido
    assert validar_permiso_sod(usuario_dpo, AccionOperativa.EMITIR_DICTAMEN_DPO) is True
    assert validar_permiso_sod(usuario_dpo, AccionOperativa.SUPERVISAR_AUDITORIA) is True

def test_sod_bloquea_auto_verificacion_cierre_capa():
    """Un implementador no puede auditar y cerrar su propia acción correctiva."""
    ticket = TicketCAPA(
        tenant_id="tenant-123",
        control_id="CTRL-01",
        severidad=SeveridadHallazgo.NO_CONFORMIDAD_MENOR,
        descripcion_hallazgo="Falta cláusula contractual en proveedor de hosting",
        responsable_implementacion_id="usuario_implementador_99",
    )
    creado = registrar_hallazgo_auditoria(ticket)
    
    # Intento de auto-cierre con el mismo ID de usuario
    with pytest.raises(PermissionError, match="Violación SoD"):
        cerrar_accion_correctiva_independiente(
            ticket_id=creado.id,
            auditor_id="usuario_implementador_99", # MISMO USUARIO
            evidencia_id="EVD-001",
        )

    # Cierre con auditor independiente: Permitido
    cerrado = cerrar_accion_correctiva_independiente(
        ticket_id=creado.id,
        auditor_id="auditor_independiente_77", # USUARIO DISTINTO
        evidencia_id="EVD-001",
    )
    assert cerrado.estado.value == "CERRADO_VERIFICADO"

def test_dpo_bitacora_inviolable():
    """Los dictámenes del DPO se emiten como no vinculantes y registran acuse de recibo."""
    dictamen = DictamenDPO(
        tenant_id="tenant-123",
        dpo_id="dpo-001",
        tipo=TipoDictamenDPO.OPINION_CONSULTIVA,
        asunto="Revisión de base legal para campaña de marketing",
        referencia_normativa="Art. 7 LOPDP",
        cuerpo="Se recomienda exigir consentimiento explícito...",
    )
    emitido = emitir_dictamen_dpo(dictamen)
    assert emitido.es_vinculante is False
    assert emitido.acuse_recibo_alta_direccion is False

    con_acuse = firmar_acuse_recibo_dictamen(emitido.id)
    assert con_acuse.acuse_recibo_alta_direccion is True
    assert con_acuse.fecha_acuse is not None

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_api_sod_dpo_mutate_rat_forbidden():
    """El DPO no puede mutar el RAT a través del API Gateway (403 Forbidden)."""
    headers = {
        "X-Tenant-ID": "tenant-test-sod",
        "X-Role": "DPD_DPO_INTERNO",
        "X-User-ID": "dpo-001"
    }
    payload = {
        "codigo": "RAT-TEST-002",
        "nombre": "Test RAT por DPO",
        "area_responsable": "Legal",
        "finalidad": "Prueba",
        "base_legal": "CONSENTIMIENTO",
        "categorias_titulares": ["EMPLEADOS"],
        "datos_sensibles": False,
        "volumen_titulares_estimado": 10,
        "transferencia_internacional": False,
        "requiere_eipd": False,
        "es_gran_escala": False
    }
    resp = client.post("/api/v1/rat/actividades", json=payload, headers=headers)
    assert resp.status_code == 403
    assert "Violación SoD" in resp.json()["detail"]

def test_api_sod_dpo_cerrar_capa_forbidden():
    """El DPO no puede cerrar una acción correctiva a través del API Gateway (403 Forbidden)."""
    headers = {
        "X-Tenant-ID": "tenant-test-sod",
        "X-Role": "DPD_DPO_INTERNO",
        "X-User-ID": "dpo-001"
    }
    
    # Intento de cierre directo con token DPO
    close_payload = {
        "auditor_id": "dpo-001",
        "evidencia_id": "evd-test-01"
    }
    resp = client.post("/api/v1/capa/tickets/TICKET-999/cerrar", json=close_payload, headers=headers)
    assert resp.status_code == 403
    assert "Violación SoD" in resp.json()["detail"]
