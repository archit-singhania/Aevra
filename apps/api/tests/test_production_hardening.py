from conftest import bearer, register_account
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from aevra_api.config import Settings
from aevra_api.db.models import SocialAccount
from aevra_api.token_vault import LocalTokenVault


def test_browser_session_cookie_can_authenticate_and_logout(client: TestClient) -> None:
    registration = register_account(
        client,
        email="cookie@example.com",
        organization_name="Cookie Labs",
        workspace_name="Core",
    )
    assert client.get("/api/v1/auth/me").status_code == 200
    assert any(
        cookie.name == "aevra_session" and cookie.has_nonstandard_attr("HttpOnly")
        for cookie in client.cookies.jar
    )

    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    assert registration["user"]["email"] == "cookie@example.com"  # type: ignore[index]


def test_provider_token_is_encrypted_and_deletion_is_scheduled(
    client: TestClient, session: Session
) -> None:
    registration = register_account(
        client,
        email="secure@example.com",
        organization_name="Secure Labs",
        workspace_name="Core",
    )
    workspace_id = registration["workspace"]["id"]  # type: ignore[index]
    raw_token = "provider-token-123456"
    connected = client.post(
        f"/api/v1/workspaces/{workspace_id}/publishing/accounts",
        headers=bearer(registration),
        json={
            "platform": "linkedin",
            "external_account_id": "urn:li:organization:1",
            "display_name": "Secure page",
            "access_token_ref": raw_token,
            "capabilities": ["publish"],
        },
    )
    assert connected.status_code == 201
    stored = session.scalar(select(SocialAccount))
    assert stored is not None
    assert stored.access_token_ref != raw_token
    secret = Settings(
        secret_key="test-secret-key-that-is-at-least-thirty-two-characters"
    ).secret_key
    assert LocalTokenVault(secret).decrypt(stored.access_token_ref) == raw_token

    deletion = client.post(
        "/api/v1/auth/account-deletion",
        headers=bearer(registration),
        json={"confirmation_email": "secure@example.com"},
    )
    assert deletion.status_code == 202
    assert deletion.json()["status"] == "requested"
