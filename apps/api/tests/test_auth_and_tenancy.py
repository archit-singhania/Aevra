import uuid

from conftest import bearer, register_account
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from aevra_api.db.models import OrganizationMember, User, Workspace
from aevra_api.repositories.tenancy import TenancyRepository


def test_registration_is_atomic_and_returns_no_password_hash(client: TestClient) -> None:
    registration = register_account(
        client,
        email="alice@example.com",
        organization_name="Alice Labs",
        workspace_name="Launch team",
    )

    assert registration["user"]["email"] == "alice@example.com"  # type: ignore[index]
    assert "password_hash" not in registration["user"]  # type: ignore[operator]
    assert registration["organization"]["slug"] == "alice-labs"  # type: ignore[index]
    assert registration["workspace"]["slug"] == "launch-team"  # type: ignore[index]

    me = client.get("/api/v1/auth/me", headers=bearer(registration))
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"


def test_login_rejects_wrong_password_and_duplicate_registration(client: TestClient) -> None:
    register_account(
        client,
        email="alice@example.com",
        organization_name="Alice Labs",
        workspace_name="Core",
    )
    wrong_password = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "definitely-wrong"},
    )
    assert wrong_password.status_code == 401
    assert wrong_password.json()["error"]["code"] == "authentication_failed"

    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "email": "ALICE@example.com",
            "password": "AnotherStrongPassword!2026",
            "display_name": "Other Alice",
            "organization_name": "Other Labs",
            "workspace_name": "Core",
        },
    )
    assert duplicate.status_code == 409


def test_workspace_routes_hide_cross_tenant_resources(client: TestClient) -> None:
    alice = register_account(
        client,
        email="alice@example.com",
        organization_name="Alice Labs",
        workspace_name="Alice Core",
    )
    bob = register_account(
        client,
        email="bob@example.com",
        organization_name="Bob Labs",
        workspace_name="Bob Core",
    )
    alice_workspace_id = alice["workspace"]["id"]  # type: ignore[index]
    alice_organization_id = alice["organization"]["id"]  # type: ignore[index]

    alice_list = client.get("/api/v1/workspaces", headers=bearer(alice))
    assert alice_list.status_code == 200
    assert [item["id"] for item in alice_list.json()] == [alice_workspace_id]

    hidden = client.get(
        f"/api/v1/workspaces/{alice_workspace_id}",
        headers=bearer(bob),
    )
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "not_found"

    forbidden_create = client.post(
        f"/api/v1/organizations/{alice_organization_id}/workspaces",
        headers=bearer(bob),
        json={"name": "Intrusion", "timezone": "UTC"},
    )
    assert forbidden_create.status_code == 403


def test_owner_can_create_uniquely_sluggified_workspaces(client: TestClient) -> None:
    owner = register_account(
        client,
        email="owner@example.com",
        organization_name="Aevra Studio",
        workspace_name="Core",
    )
    organization_id = owner["organization"]["id"]  # type: ignore[index]
    headers = bearer(owner)

    first = client.post(
        f"/api/v1/organizations/{organization_id}/workspaces",
        headers=headers,
        json={"name": "Product Launch", "timezone": "UTC"},
    )
    second = client.post(
        f"/api/v1/organizations/{organization_id}/workspaces",
        headers=headers,
        json={"name": "Product Launch", "timezone": "UTC"},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["slug"] == "product-launch"
    assert second.json()["slug"] == "product-launch-2"


def test_repository_requires_user_scope_for_workspace_reads(
    client: TestClient,
    session: Session,
) -> None:
    alice = register_account(
        client,
        email="alice@example.com",
        organization_name="Alice Labs",
        workspace_name="Private",
    )
    register_account(
        client,
        email="bob@example.com",
        organization_name="Bob Labs",
        workspace_name="Private",
    )
    repository = TenancyRepository(session)
    alice_user = session.scalar(select(User).where(User.email == "alice@example.com"))
    bob_user = session.scalar(select(User).where(User.email == "bob@example.com"))
    assert alice_user is not None and bob_user is not None
    alice_workspace_id = uuid.UUID(str(alice["workspace"]["id"]))  # type: ignore[index]

    assert repository.get_workspace_for_user(alice_user.id, alice_workspace_id) is not None
    assert repository.get_workspace_for_user(bob_user.id, alice_workspace_id) is None

    memberships = session.scalars(select(OrganizationMember)).all()
    workspaces = session.scalars(select(Workspace)).all()
    assert len(memberships) == 2
    assert len(workspaces) == 2


def test_unauthenticated_workspace_access_is_rejected(client: TestClient) -> None:
    response = client.get(f"/api/v1/workspaces/{uuid.uuid4()}")
    assert response.status_code == 401
