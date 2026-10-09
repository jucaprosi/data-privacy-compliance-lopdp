"""get_session fija el contexto RLS desde las cabeceras X-Tenant-ID / X-User-ID."""
import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.db.session import get_session

pytestmark = pytest.mark.asyncio

app = FastAPI()


@app.get("/ctx")
async def ctx(session: AsyncSession = Depends(get_session)) -> dict:
    row = (await session.execute(text(
        "SELECT current_setting('app.current_tenant_id', true), "
        "current_setting('app.current_user_id', true)"
    ))).one()
    return {"tenant": row[0] or None, "user": row[1] or None}


async def _get(**kwargs) -> dict:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/ctx", **kwargs)
    assert resp.status_code == 200
    return resp.json()


async def test_cabeceras_fijan_contexto():
    assert await _get(headers={"X-Tenant-ID": "t-hdr", "X-User-ID": "u-hdr"}) == {
        "tenant": "t-hdr", "user": "u-hdr",
    }


async def test_query_string_no_fija_contexto():
    assert await _get(params={"x_tenant_id": "t-qs", "x_user_id": "u-qs"}) == {
        "tenant": None, "user": None,
    }
