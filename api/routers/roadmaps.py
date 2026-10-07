from fastapi import APIRouter, HTTPException
from app_core.schemas.roadmap_schema import GenerateRoadmapRequest, TaskStatusUpdate
from app_core.services.roadmap_service import enqueue, job_status, get_roadmap, update_task, kpis

router = APIRouter(prefix="/roadmaps", tags=["Hoja de Ruta Inteligente"])
@router.post("/generate", status_code=202)
def generate(payload: GenerateRoadmapRequest): return {"job_id": enqueue(payload)}
@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    value = job_status(job_id)
    if not value: raise HTTPException(404, "Job no encontrado")
    return value
@router.get("/{roadmap_id}")
def get(roadmap_id: str):
    value = get_roadmap(roadmap_id)
    if not value: raise HTTPException(404, "Roadmap no encontrado")
    return value
@router.get("/{roadmap_id}/kpis")
def get_kpis(roadmap_id: str): return kpis(roadmap_id)
@router.patch("/tasks/{task_id}")
def patch_task(task_id: str, payload: TaskStatusUpdate):
    value = update_task(task_id, payload.status)
    if not value: raise HTTPException(404, "Tarea no encontrada")
    return value
