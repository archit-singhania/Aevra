import uuid

from conftest import bearer, register_account
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aevra_api.db.models import BrandRule, OrganizationMember, User, Workspace


def create_brand(
    client: TestClient,
    registration: dict[str, object],
    *,
    name: str = "Aevra",
) -> dict[str, object]:
    workspace_id = registration["workspace"]["id"]  # type: ignore[index]
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/brands",
        headers=bearer(registration),
        json={
            "name": name,
            "description": "Evidence-grounded content intelligence.",
            "website_url": "https://aevra.example",
            "industry": "Developer tools",
            "tone_attributes": ["Precise", "Confident", "Precise", "  "],
            "target_audiences": ["Engineering leaders", "Developers"],
            "preferred_ctas": ["Explore the evidence"],
            "preferred_hashtags": ["#AgenticAI", "#RAG"],
            "status": "active",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_brand_profile_crud_and_normalization(client: TestClient) -> None:
    owner = register_account(
        client,
        email="owner@example.com",
        organization_name="Aevra Labs",
        workspace_name="Core",
    )
    brand = create_brand(client, owner)
    workspace_id = owner["workspace"]["id"]  # type: ignore[index]

    assert brand["slug"] == "aevra"
    assert brand["tone_attributes"] == ["Precise", "Confident"]

    listed = client.get(
        f"/api/v1/workspaces/{workspace_id}/brands",
        headers=bearer(owner),
    )
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [brand["id"]]

    updated = client.patch(
        f"/api/v1/workspaces/{workspace_id}/brands/{brand['id']}",
        headers=bearer(owner),
        json={"industry": "AI infrastructure", "status": "active"},
    )
    assert updated.status_code == 200
    assert updated.json()["industry"] == "AI infrastructure"


def test_brand_and_rule_reads_are_tenant_isolated(client: TestClient) -> None:
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
    brand = create_brand(client, alice, name="Alice Private Brand")
    alice_workspace_id = alice["workspace"]["id"]  # type: ignore[index]

    hidden_brand = client.get(
        f"/api/v1/workspaces/{alice_workspace_id}/brands/{brand['id']}",
        headers=bearer(bob),
    )
    assert hidden_brand.status_code == 404

    hidden_list = client.get(
        f"/api/v1/workspaces/{alice_workspace_id}/brands",
        headers=bearer(bob),
    )
    assert hidden_list.status_code == 404

    hidden_rules = client.get(
        f"/api/v1/workspaces/{alice_workspace_id}/brands/{brand['id']}/rules",
        headers=bearer(bob),
    )
    assert hidden_rules.status_code == 404


def test_viewer_can_read_but_cannot_mutate_brand(
    client: TestClient,
    session: Session,
) -> None:
    owner = register_account(
        client,
        email="owner@example.com",
        organization_name="Shared Labs",
        workspace_name="Shared Core",
    )
    viewer = register_account(
        client,
        email="viewer@example.com",
        organization_name="Viewer Home",
        workspace_name="Viewer Core",
    )
    owner_workspace_id = uuid.UUID(str(owner["workspace"]["id"]))  # type: ignore[index]
    owner_workspace = session.get(Workspace, owner_workspace_id)
    viewer_user = session.scalar(select(User).where(User.email == "viewer@example.com"))
    assert owner_workspace is not None and viewer_user is not None
    session.add(
        OrganizationMember(
            organization_id=owner_workspace.organization_id,
            user_id=viewer_user.id,
            role="viewer",
        )
    )
    session.commit()
    brand = create_brand(client, owner)

    readable = client.get(
        f"/api/v1/workspaces/{owner_workspace_id}/brands/{brand['id']}",
        headers=bearer(viewer),
    )
    assert readable.status_code == 200

    blocked = client.patch(
        f"/api/v1/workspaces/{owner_workspace_id}/brands/{brand['id']}",
        headers=bearer(viewer),
        json={"description": "Unauthorized change"},
    )
    assert blocked.status_code == 403


def test_brand_rules_are_validated_and_ordered(client: TestClient) -> None:
    owner = register_account(
        client,
        email="owner@example.com",
        organization_name="Aevra Labs",
        workspace_name="Core",
    )
    brand = create_brand(client, owner)
    workspace_id = owner["workspace"]["id"]  # type: ignore[index]
    endpoint = f"/api/v1/workspaces/{workspace_id}/brands/{brand['id']}/rules"

    low = client.post(
        endpoint,
        headers=bearer(owner),
        json={
            "category": "cta",
            "enforcement": "preferred",
            "directive": "Use an evidence-oriented call to action.",
            "priority": 30,
        },
    )
    high = client.post(
        endpoint,
        headers=bearer(owner),
        json={
            "category": "claim",
            "enforcement": "prohibited",
            "directive": "Never claim guaranteed performance improvements.",
            "rationale": "Performance depends on the customer's environment.",
            "priority": 95,
        },
    )
    assert low.status_code == 201
    assert high.status_code == 201

    rules = client.get(endpoint, headers=bearer(owner))
    assert rules.status_code == 200
    assert [rule["priority"] for rule in rules.json()] == [95, 30]

    invalid = client.post(
        endpoint,
        headers=bearer(owner),
        json={
            "category": "anything",
            "enforcement": "optional",
            "directive": "Invalid enum values should be rejected.",
            "priority": 101,
        },
    )
    assert invalid.status_code == 422


def test_database_rejects_cross_workspace_brand_rule(
    client: TestClient,
    session: Session,
) -> None:
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
    brand = create_brand(client, alice)
    alice_user = session.scalar(select(User).where(User.email == "alice@example.com"))
    assert alice_user is not None

    session.add(
        BrandRule(
            workspace_id=uuid.UUID(str(bob["workspace"]["id"])),  # type: ignore[index]
            brand_id=uuid.UUID(str(brand["id"])),
            created_by_user_id=alice_user.id,
            category="voice",
            enforcement="required",
            directive="This mismatched tenant relation must fail.",
            priority=50,
        )
    )
    try:
        session.commit()
        raise AssertionError("Cross-workspace brand rule was accepted")
    except IntegrityError:
        session.rollback()
