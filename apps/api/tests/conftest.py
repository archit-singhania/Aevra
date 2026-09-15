from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from aevra_api.config import Settings, get_settings
from aevra_api.db.base import Base
from aevra_api.db.session import get_session
from aevra_api.main import app


@pytest.fixture
def engine() -> Generator[Engine, None, None]:
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(test_engine, "connect")
    def enable_foreign_keys(dbapi_connection: object, _connection_record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    with session_factory() as database_session:
        yield database_session


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Generator[TestClient, None, None]:
    def override_session() -> Generator[Session, None, None]:
        with session_factory() as database_session:
            yield database_session

    def override_settings() -> Settings:
        return Settings(
            secret_key="test-secret-key-that-is-at-least-thirty-two-characters",
            database_url="sqlite://",
        )

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_settings] = override_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def register_account(
    client: TestClient,
    *,
    email: str,
    organization_name: str,
    workspace_name: str,
) -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "AevraTestPassword!2026",
            "display_name": email.split("@", 1)[0].title(),
            "organization_name": organization_name,
            "workspace_name": workspace_name,
            "timezone": "Asia/Kolkata",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def bearer(registration: dict[str, object]) -> dict[str, str]:
    token = registration["token"]
    assert isinstance(token, dict)
    return {"Authorization": f"Bearer {token['access_token']}"}
