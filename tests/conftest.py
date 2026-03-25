"""
tests/conftest.py
Fixed fixture: creates a brand-new in-memory engine PER TEST FUNCTION,
so there is zero state bleed between tests.
"""
import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import create_app


@pytest.fixture(scope="function")
def event_loop():
    """Fresh event loop for every test."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db():
    """
    Fresh in-memory SQLite engine + session for every test.
    Engine is created here (not at module level) so each test
    gets a completely clean database with no connection pool sharing.
    """
    import app.models  # noqa — register all ORM models

    # New engine per test — guarantees complete isolation
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    session_factory = async_sessionmaker(
        bind=engine, expire_on_commit=False, autoflush=False
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    # Drop all tables and dispose engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db):
    """HTTP test client wired to the per-test DB session."""
    application = create_app()

    async def override_get_db():
        yield db

    application.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def auth(client):
    """Pre-registered and logged-in test user."""
    r = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "Test1234",
    })
    assert r.status_code == 201, f"Register failed: {r.json()}"
    token = r.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client, token
