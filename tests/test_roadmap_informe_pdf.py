"""Árbitro RM-20: PDF por rol, tenant, alcance y huella de auditoría."""
import hashlib, os, uuid
from io import BytesIO
import pytest, pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pypdf import PdfReader
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from main import app
from app_core.db.session import get_session

pytestmark=pytest.mark.asyncio

def _url():
    u=os.environ.get("TEST_DATABASE_URL")
    if not u: pytest.skip("TEST_DATABASE_URL no configurada")
    return u.replace("postgresql://","postgresql+psycopg://",1)

@pytest_asyncio.fixture
async def escenario():
    engine=create_async_engine(_url()); factory=async_sessionmaker(engine,expire_on_commit=False,class_=AsyncSession)
    token=uuid.uuid4().hex[:8]; ta=f"rm20-a-{token}"; tb=f"rm20-b-{token}"; a1=f"a1-{token}"; a2=f"a2-{token}"; rid=f"rm-{token}"; ridb=f"rmb-{token}"; w=f"w-{token}"
    roles=["admin_organizacion","coordinador","dpo","implementador","responsable_area"]
    users={r:f"u-{r[:5]}-{token}" for r in roles}
    async with factory() as s:
        for t in (ta,tb): await s.execute(text("INSERT INTO tenants(id,nombre_comercial,razon_social,ruc_identificacion) VALUES(:i,:i,:i,:i)"),{"i":t})
        await s.execute(text("INSERT INTO areas(id,tenant_id,nombre,codigo) VALUES(:i,:t,'Legal','LEG'),(:j,:t,'TI','TI')"),{"i":a1,"j":a2,"t":ta})
        for rol,uid in users.items():
            await s.execute(text("INSERT INTO users(id,email,nombre) VALUES(:i,:e,:n)"),{"i":uid,"e":uid+"@test.local","n":rol})
            await s.execute(text("INSERT INTO user_tenant_roles(id,user_id,tenant_id,role,area_id) VALUES(:i,:u,:t,:r,:a)"),{"i":str(uuid.uuid4()),"u":uid,"t":ta,"r":rol,"a":a1 if rol=="responsable_area" else None})
        await s.execute(text("INSERT INTO roadmaps(id,tenant_id,status,variables_json) VALUES(:r,:t,'active','{}'),(:b,:tb,'active','{}')"),{"r":rid,"t":ta,"b":ridb,"tb":tb})
        await s.execute(text("INSERT INTO roadmap_waves(id,roadmap_id,tenant_id,name,sort_order) VALUES(:w,:r,:t,'Ola 1',1)"),{"w":w,"r":rid,"t":ta})
        await s.execute(text("INSERT INTO roadmap_tasks(id,wave_id,tenant_id,area_id,control_ref,dimension,title,description,priority,status) VALUES(:x,:w,:t,:a1,'P1','D01','Tarea Legal','x','alta','pendiente'),(:y,:w,:t,:a2,'P2','D01','Tarea Secreta TI','x','critica','pendiente')"),{"x":f"t1-{token}","y":f"t2-{token}","w":w,"t":ta,"a1":a1,"a2":a2})
        await s.commit()
    async def sesion():
        async with factory() as s: yield s
    app.dependency_overrides[get_session]=sesion
    async with AsyncClient(transport=ASGITransport(app=app),base_url="http://test") as client: yield client,ta,tb,rid,ridb,users
    app.dependency_overrides.clear()
    async with factory() as s:
        for sentencia in ("DELETE FROM audit_events WHERE tenant_id IN (:a,:b)","DELETE FROM roadmap_tasks WHERE tenant_id IN (:a,:b)","DELETE FROM roadmap_waves WHERE tenant_id IN (:a,:b)","DELETE FROM roadmaps WHERE tenant_id IN (:a,:b)","DELETE FROM user_tenant_roles WHERE tenant_id IN (:a,:b)","DELETE FROM areas WHERE tenant_id IN (:a,:b)"):
            await s.execute(text(sentencia),{"a":ta,"b":tb})
        await s.execute(text("DELETE FROM users WHERE id = ANY(:ids)"),{"ids":list(users.values())}); await s.execute(text("DELETE FROM tenants WHERE id IN (:a,:b)"),{"a":ta,"b":tb}); await s.commit()
    await engine.dispose()

def cab(tenant,user,role): return {"X-Tenant-ID":tenant,"X-User-ID":user,"X-Role":role}

@pytest.mark.parametrize("rol",["admin_organizacion","coordinador","dpo","implementador","responsable_area"])
async def test_cada_rol_recibe_pdf_y_alcance(escenario,rol):
    c,ta,_,rid,_,users=escenario; r=await c.get(f"/api/v1/roadmaps/{rid}/informe.pdf",headers=cab(ta,users[rol],rol)); assert r.status_code==200 and r.content.startswith(b"%PDF")
    texto="\n".join(p.extract_text() or "" for p in PdfReader(BytesIO(r.content)).pages)
    assert "Tarea Legal" in texto
    assert ("Tarea Secreta TI" not in texto) if rol=="responsable_area" else ("Tarea Secreta TI" in texto)
    # Constancia: quién, con qué rol, qué alcance (con nombres de área, no identificadores) e identificador.
    assert f"Rol: {rol}" in texto and "Identificador del informe" in texto and "Página 1 de" in texto
    assert ("Alcance: Áreas: Legal" in texto) if rol=="responsable_area" else ("Alcance: Organización completa" in texto)

async def test_otro_tenant_404_y_auditoria_hash(escenario):
    c,ta,tb,rid,ridb,users=escenario
    assert (await c.get(f"/api/v1/roadmaps/{ridb}/informe.pdf",headers=cab(ta,users["implementador"],"implementador"))).status_code==404
    r=await c.get(f"/api/v1/roadmaps/{rid}/informe.pdf",headers=cab(ta,users["implementador"],"implementador"))
    engine=create_async_engine(_url())
    async with engine.connect() as s:
        payload=(await s.execute(text("SELECT payload FROM audit_events WHERE tenant_id=:t AND action='roadmap_report_downloaded' ORDER BY timestamp DESC LIMIT 1"),{"t":ta})).scalar_one()
    await engine.dispose(); assert payload["sha256"]==hashlib.sha256(r.content).hexdigest()
