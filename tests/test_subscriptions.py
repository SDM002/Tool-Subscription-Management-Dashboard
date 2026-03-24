"""
tests/test_subscriptions.py  [NEW]
Tests for subscription CRUD and user data isolation.
Run with: pytest tests/test_subscriptions.py -v
"""

import pytest
from datetime import date, timedelta


def sample_sub(**overrides):
    return {
        "tool_name": "TestTool",
        "category": "Productivity",
        "price": 10.00,
        "billing_cycle": "monthly",
        "renewal_date": (date.today() + timedelta(days=15)).isoformat(),
        **overrides,
    }


@pytest.mark.asyncio
async def test_create_subscription(auth_client):
    client, _ = auth_client
    res = await client.post("/api/subscriptions", json=sample_sub())
    assert res.status_code == 201
    body = res.json()
    assert body["tool_name"] == "TestTool"
    assert body["monthly_cost"] == 10.0
    assert body["yearly_cost"] == 120.0


@pytest.mark.asyncio
async def test_list_subscriptions(auth_client):
    client, _ = auth_client
    await client.post("/api/subscriptions", json=sample_sub(tool_name="A"))
    await client.post("/api/subscriptions", json=sample_sub(tool_name="B"))
    res = await client.get("/api/subscriptions")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2
    names = [s["tool_name"] for s in body["subscriptions"]]
    assert "A" in names and "B" in names


@pytest.mark.asyncio
async def test_get_single_subscription(auth_client):
    client, _ = auth_client
    create_res = await client.post("/api/subscriptions", json=sample_sub())
    sub_id = create_res.json()["id"]
    res = await client.get(f"/api/subscriptions/{sub_id}")
    assert res.status_code == 200
    assert res.json()["id"] == sub_id


@pytest.mark.asyncio
async def test_update_subscription(auth_client):
    client, _ = auth_client
    create_res = await client.post("/api/subscriptions", json=sample_sub())
    sub_id = create_res.json()["id"]
    res = await client.patch(f"/api/subscriptions/{sub_id}", json={"price": 25.0, "tool_name": "Updated"})
    assert res.status_code == 200
    body = res.json()
    assert body["price"] == 25.0
    assert body["tool_name"] == "Updated"
    assert body["monthly_cost"] == 25.0


@pytest.mark.asyncio
async def test_delete_subscription(auth_client):
    client, _ = auth_client
    create_res = await client.post("/api/subscriptions", json=sample_sub())
    sub_id = create_res.json()["id"]
    del_res = await client.delete(f"/api/subscriptions/{sub_id}")
    assert del_res.status_code == 204
    get_res = await client.get(f"/api/subscriptions/{sub_id}")
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_user_isolation(client):
    """User A cannot see or modify User B's subscriptions."""
    # Register User A
    res_a = await client.post("/api/auth/register", json={
        "email": "usera@example.com", "full_name": "User A", "password": "UserA123"
    })
    token_a = res_a.json()["access_token"]

    # Register User B
    res_b = await client.post("/api/auth/register", json={
        "email": "userb@example.com", "full_name": "User B", "password": "UserB123"
    })
    token_b = res_b.json()["access_token"]

    # User A creates a subscription
    res = await client.post("/api/subscriptions",
        json=sample_sub(tool_name="UserA-Secret"),
        headers={"Authorization": f"Bearer {token_a}"},
    )
    sub_id = res.json()["id"]

    # User B tries to access it — should get 404
    res_steal = await client.get(f"/api/subscriptions/{sub_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_steal.status_code == 404

    # User B tries to delete it — should get 404
    res_del = await client.delete(f"/api/subscriptions/{sub_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_del.status_code == 404


@pytest.mark.asyncio
async def test_billing_cycle_cost_calculation(auth_client):
    client, _ = auth_client
    # Yearly subscription: price=120, monthly_cost should be 10
    res = await client.post("/api/subscriptions", json=sample_sub(
        billing_cycle="yearly", price=120.0
    ))
    assert res.status_code == 201
    body = res.json()
    assert body["monthly_cost"] == 10.0
    assert body["yearly_cost"] == 120.0


@pytest.mark.asyncio
async def test_invalid_billing_cycle(auth_client):
    client, _ = auth_client
    res = await client.post("/api/subscriptions", json=sample_sub(billing_cycle="weekly"))
    assert res.status_code == 422
