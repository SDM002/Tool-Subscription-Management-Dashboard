import pytest
from datetime import date, timedelta


def sub(**kw):
    return {
        "tool_name": "TestTool",
        "category": "Productivity",
        "price": 10.0,
        "billing_cycle": "monthly",
        "renewal_date": (date.today() + timedelta(days=15)).isoformat(),
        **kw,
    }


@pytest.mark.asyncio
async def test_create(auth):
    c, _ = auth
    r = await c.post("/api/subscriptions", json=sub())
    assert r.status_code == 201
    assert r.json()["monthly_cost"] == 10.0
    assert r.json()["yearly_cost"] == 120.0


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
    r = await c.patch(f"/api/subscriptions/{id_}", json={"price": 25.0})
    assert r.status_code == 200
    assert r.json()["price"] == 25.0


@pytest.mark.asyncio
async def test_delete(auth):
    c, _ = auth

    # Create a subscription
    create_r = await c.post("/api/subscriptions", json=sub())
    assert create_r.status_code == 201
    id_ = create_r.json()["id"]

    # Verify it exists
    get_before = await c.get(f"/api/subscriptions/{id_}")
    assert get_before.status_code == 200

    # Delete it
    del_r = await c.delete(f"/api/subscriptions/{id_}")
    assert del_r.status_code == 204

    # Flush the DB session so the delete is visible
    # We do this by expiring the session through a new request
    # The 404 should now be visible
    get_after = await c.get(f"/api/subscriptions/{id_}")
    assert get_after.status_code == 404, (
        f"Expected 404 after delete, got {get_after.status_code}: {get_after.json()}"
    )


@pytest.mark.asyncio
async def test_isolation(client):
    """User A cannot access User B's subscriptions."""
    # Register User A
    ra = await client.post("/api/auth/register", json={
        "email": "ua@x.com", "full_name": "UserA", "password": "UserA123"
    })
    assert ra.status_code == 201, f"User A register failed: {ra.json()}"
    ta = ra.json()["access_token"]

    # Register User B
    rb = await client.post("/api/auth/register", json={
        "email": "ub@x.com", "full_name": "UserB", "password": "UserB123"
    })
    assert rb.status_code == 201, f"User B register failed: {rb.json()}"
    tb = rb.json()["access_token"]

    # User A creates a subscription
    headers_a = {"Authorization": f"Bearer {ta}"}
    create_r = await client.post(
        "/api/subscriptions",
        json=sub(tool_name="UserA-Secret"),
        headers=headers_a,
    )
    assert create_r.status_code == 201
    sub_id = create_r.json()["id"]

    # User B tries to read it — must get 404
    headers_b = {"Authorization": f"Bearer {tb}"}
    steal_r = await client.get(f"/api/subscriptions/{sub_id}", headers=headers_b)
    assert steal_r.status_code == 404, (
        f"Isolation failed: User B got {steal_r.status_code}"
    )

    # User B tries to delete it — must get 404
    del_r = await client.delete(f"/api/subscriptions/{sub_id}", headers=headers_b)
    assert del_r.status_code == 404


@pytest.mark.asyncio
async def test_yearly_cost(auth):
    c, _ = auth
    r = await c.post("/api/subscriptions", json=sub(billing_cycle="yearly", price=120.0))
    assert r.status_code == 201
    assert r.json()["monthly_cost"] == 10.0
    assert r.json()["yearly_cost"] == 120.0


@pytest.mark.asyncio
async def test_invalid_cycle(auth):
    c, _ = auth
    r = await c.post("/api/subscriptions", json=sub(billing_cycle="weekly"))
    assert r.status_code == 422
