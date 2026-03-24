import pytest
from datetime import date, timedelta

def sub(**kw):
    return {"tool_name":"TestTool","category":"Productivity","price":10.0,
            "billing_cycle":"monthly","renewal_date":(date.today()+timedelta(days=15)).isoformat(),**kw}

@pytest.mark.asyncio
async def test_create(auth):
    c, _ = auth
    r = await c.post("/api/subscriptions", json=sub())
    assert r.status_code == 201
    assert r.json()["monthly_cost"] == 10.0
    assert r.json()["yearly_cost"]  == 120.0

@pytest.mark.asyncio
async def test_list(auth):
    c, _ = auth
    await c.post("/api/subscriptions", json=sub(tool_name="A"))
    await c.post("/api/subscriptions", json=sub(tool_name="B"))
    r = await c.get("/api/subscriptions")
    assert r.json()["total"] == 2

@pytest.mark.asyncio
async def test_update(auth):
    c, _ = auth
    id_ = (await c.post("/api/subscriptions", json=sub())).json()["id"]
    r   = await c.patch(f"/api/subscriptions/{id_}", json={"price":25.0})
    assert r.json()["price"] == 25.0

@pytest.mark.asyncio
async def test_delete(auth):
    c, _ = auth
    id_ = (await c.post("/api/subscriptions", json=sub())).json()["id"]
    assert (await c.delete(f"/api/subscriptions/{id_}")).status_code == 204
    assert (await c.get(f"/api/subscriptions/{id_}")).status_code == 404

@pytest.mark.asyncio
async def test_isolation(client):
    ra = await client.post("/api/auth/register", json={"email":"ua@x.com","full_name":"A","password":"UserA123"})
    rb = await client.post("/api/auth/register", json={"email":"ub@x.com","full_name":"B","password":"UserB123"})
    ta, tb = ra.json()["access_token"], rb.json()["access_token"]
    id_ = (await client.post("/api/subscriptions", json=sub(), headers={"Authorization":f"Bearer {ta}"})).json()["id"]
    assert (await client.get(f"/api/subscriptions/{id_}", headers={"Authorization":f"Bearer {tb}"})).status_code == 404

@pytest.mark.asyncio
async def test_yearly_cost(auth):
    c, _ = auth
    r = await c.post("/api/subscriptions", json=sub(billing_cycle="yearly", price=120.0))
    assert r.json()["monthly_cost"] == 10.0
    assert r.json()["yearly_cost"]  == 120.0

@pytest.mark.asyncio
async def test_invalid_cycle(auth):
    c, _ = auth
    r = await c.post("/api/subscriptions", json=sub(billing_cycle="weekly"))
    assert r.status_code == 422
