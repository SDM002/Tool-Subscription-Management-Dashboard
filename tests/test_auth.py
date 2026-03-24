"""
tests/test_auth.py  [NEW]
Tests for user registration, login, and /me endpoint.
Run with: pytest tests/test_auth.py -v
"""

import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    res = await client.post("/api/auth/register", json={
        "email": "alice@example.com",
        "full_name": "Alice Smith",
        "password": "Alice1234",
    })
    assert res.status_code == 201
    body = res.json()
    assert "access_token" in body
    assert body["user"]["email"] == "alice@example.com"
    assert body["user"]["full_name"] == "Alice Smith"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "bob@example.com", "full_name": "Bob", "password": "Bob12345"}
    await client.post("/api/auth/register", json=payload)
    res = await client.post("/api/auth/register", json=payload)
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client):
    res = await client.post("/api/auth/register", json={
        "email": "weak@example.com",
        "full_name": "Weak",
        "password": "short",
    })
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/api/auth/register", json={
        "email": "carol@example.com",
        "full_name": "Carol",
        "password": "Carol123",
    })
    res = await client.post("/api/auth/login", json={
        "email": "carol@example.com",
        "password": "Carol123",
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/register", json={
        "email": "dave@example.com",
        "full_name": "Dave",
        "password": "Dave1234",
    })
    res = await client.post("/api/auth/login", json={
        "email": "dave@example.com",
        "password": "wrongpassword1",
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(auth_client):
    client, _ = auth_client
    res = await client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_me_unauthorized(client):
    res = await client.get("/api/auth/me")
    assert res.status_code == 403 or res.status_code == 401  # 401 from HTTPBearer


@pytest.mark.asyncio
async def test_health(client):
    res = await client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
