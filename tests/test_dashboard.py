import pytest
from datetime import date, timedelta

async def add(c, **kw):
    p = {"tool_name":"T","category":"Other","price":10.0,"billing_cycle":"monthly",**kw}
    return (await c.post("/api/subscriptions", json=p)).json()

@pytest.mark.asyncio
async def test_empty(auth):
    c, _ = auth
    r = await c.get("/api/dashboard/summary")
    assert r.status_code == 200
    assert r.json()["total_monthly_spend"] == 0.0

@pytest.mark.asyncio
async def test_monthly_spend(auth):
    c, _ = auth
    await add(c, tool_name="A", price=10.0, billing_cycle="monthly")
    await add(c, tool_name="B", price=20.0, billing_cycle="monthly")
    await add(c, tool_name="C", price=120.0, billing_cycle="yearly")
    r = await c.get("/api/dashboard/summary")
    assert r.json()["total_monthly_spend"] == 40.0

@pytest.mark.asyncio
async def test_due_this_week(auth):
    c, _ = auth
    await add(c, tool_name="Soon",  renewal_date=(date.today()+timedelta(days=1)).isoformat())
    await add(c, tool_name="Later", renewal_date=(date.today()+timedelta(days=40)).isoformat())
    r = await c.get("/api/dashboard/summary")
    assert len(r.json()["due_this_week"]) == 1
    assert r.json()["due_this_week"][0]["tool_name"] == "Soon"

@pytest.mark.asyncio
async def test_renewals_window(auth):
    c, _ = auth
    await add(c, tool_name="A", renewal_date=(date.today()+timedelta(days=5)).isoformat())
    await add(c, tool_name="B", renewal_date=(date.today()+timedelta(days=45)).isoformat())
    assert len((await c.get("/api/dashboard/renewals?days=30")).json()) == 1
    assert len((await c.get("/api/dashboard/renewals?days=60")).json()) == 2
