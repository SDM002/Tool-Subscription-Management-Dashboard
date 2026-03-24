"""tests/conftest.py — shared fixtures using in-memory SQLite."""
import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import create_app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession  = async_sessionmaker(bind=test_engine, expire_on_commit=False, autoflush=False)


@pytest.fixture(scope="function")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db():
    import app.models  # noqa: F401
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSession() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db):
    application = create_app()
    async def override(): yield db
    application.dependency_overrides[get_db] = override
    async with AsyncClient(transport=ASGITransport(app=application), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def auth(client):
    r = await client.post("/api/auth/register", json={
        "email": "test@example.com", "full_name": "Test User", "password": "Test1234"
    })
    assert r.status_code == 201
    token = r.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client, token
