"""Servicio determinista de roadmap; el adaptador LLM puede sustituirse sin tocar assessment."""
from datetime import date, timedelta
from uuid import uuid4
from app_core.schemas.roadmap_schema import RoadmapDocument, GenerateRoadmapRequest, TaskStatus

_roadmaps: dict[str, dict] = {}; _jobs: dict[str, dict] = {}; _task_index: dict[str, tuple[str, dict]] = {}

def generate_local(request: GenerateRoadmapRequest) -> RoadmapDocument:
    rid = str(uuid4()); today = date.today(); end = today + timedelta(days=request.variables.plazo_meses * 30)
    critical = [k for k, v in request.variables.evidencia_por_control.items() if not v][:6] or ["P1"]
    tasks = []
    for i, control in enumerate(critical):
        tid = str(uuid4()); task = {"id": tid, "control_ref": control, "dimension": f"D{(i % 10) + 1:02d}", "titulo": f"Cerrar brecha {control}", "descripcion": "Implementar y documentar la medida priorizada del assessment.", "responsable": request.variables.equipo[0], "prioridad": "critica" if i < 2 else "alta", "esfuerzo_estimado_horas": 8, "dependencias": [], "entregable": f"Evidencia verificable de {control}", "evidencia_requerida": ["procedimiento aprobado", "registro de ejecución"], "kpi": f"{control} verificado", "fecha_inicio": today.isoformat(), "fecha_fin": min(end, today + timedelta(days=14 + i * 7)).isoformat()}
        tasks.append(task); _task_index[tid] = (rid, task)
    doc = RoadmapDocument(roadmap_id=rid, resumen_ejecutivo="Hoja de ruta priorizada a partir de las brechas del assessment.", olas=[{"id":"ola-1","nombre":"Fundamentos críticos","plazo":"semanas 1-2","objetivo":"Cerrar brechas críticas","tareas":tasks}], kpis_globales={"criticos_totales":sum(t["prioridad"] == "critica" for t in tasks),"altos_totales":sum(t["prioridad"] == "alta" for t in tasks),"score_objetivo":80,"evidencia_verificada_objetivo":80})
    _roadmaps[rid] = {"document": doc.model_dump(mode="json"), "status": "generated", "tenant_id": ""}; return doc

def enqueue(request: GenerateRoadmapRequest) -> str:
    job = str(uuid4()); _jobs[job] = {"status":"completed", "roadmap":generate_local(request).model_dump(mode="json")}; return job
def job_status(job_id: str): return _jobs.get(job_id)
def get_roadmap(roadmap_id: str): return _roadmaps.get(roadmap_id)
def update_task(task_id: str, status: TaskStatus):
    item = _task_index.get(task_id)
    if not item: return None
    item[1]["status"] = status.value
    stored = _roadmaps.get(item[0])
    if stored:
        for wave in stored["document"]["olas"]:
            for task in wave["tareas"]:
                if str(task["id"]) == task_id: task["status"] = status.value; return task
    return item[1]
def kpis(roadmap_id: str):
    item = _roadmaps.get(roadmap_id); tasks = item["document"]["olas"][0]["tareas"] if item else []
    return {"total_tareas": len(tasks), "completadas": sum(t.get("status") == "completada" for t in tasks), "progreso_porcentaje": round(sum(t.get("status") == "completada" for t in tasks) * 100 / len(tasks), 1) if tasks else 0}
