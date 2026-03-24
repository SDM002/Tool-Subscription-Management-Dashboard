import pytest

@pytest.mark.asyncio
async def test_register(client):
    r = await client.post("/api/auth/register", json={"email":"a@b.com","full_name":"Alice","password":"Alice123"})
    assert r.status_code == 201
    assert "access_token" in r.json()

@pytest.mark.asyncio
async def test_duplicate_email(client):
    p = {"email":"dup@b.com","full_name":"Dup","password":"Dup12345"}
    await client.post("/api/auth/register", json=p)
    r = await client.post("/api/auth/register", json=p)
    assert r.status_code == 409

@pytest.mark.asyncio
async def test_weak_password(client):
    r = await client.post("/api/auth/register", json={"email":"w@b.com","full_name":"W","password":"short"})
    assert r.status_code == 422

@pytest.mark.asyncio
async def test_login(client):
    await client.post("/api/auth/register", json={"email":"l@b.com","full_name":"L","password":"Login123"})
    r = await client.post("/api/auth/login", json={"email":"l@b.com","password":"Login123"})
    assert r.status_code == 200
    assert "access_token" in r.json()

@pytest.mark.asyncio
async def test_wrong_password(client):
    await client.post("/api/auth/register", json={"email":"wp@b.com","full_name":"WP","password":"Good1234"})
    r = await client.post("/api/auth/login", json={"email":"wp@b.com","password":"wrongwrong1"})
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_me(auth):
    c, _ = auth
    r = await c.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
