import json
import uuid
from dataclasses import dataclass, field

from conftest import bearer, register_account
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aevra_api.ai.contracts import (
    GenerationRequest,
    GenerationResult,
    ProviderStatus,
)
from aevra_api.api.dependencies import get_llm_provider
from aevra_api.db.models import (
    CampaignRun,
    ContentVariant,
    OrganizationMember,
    User,
    Workspace,
)
from aevra_api.domain.errors import GenerationError
from aevra_api.generation.platforms import PLATFORM_SPECS, adapt_variant, validate_variant
from aevra_api.main import app


@dataclass
class CampaignLLMProvider:
    platforms: list[str]
    malformed: bool = False
    calls: list[GenerationRequest] = field(default_factory=list)

    @property
    def model_name(self) -> str:
        return "qwen-campaign-test"

    def status(self) -> ProviderStatus:
        return ProviderStatus(True, "fake-local", self.model_name, "Ready")

    def generate(self, request: GenerationRequest) -> GenerationResult:
        self.calls.append(request)
        if self.malformed:
            content = "not valid json"
        else:
            variants = []
            for platform in self.platforms:
                long_copy = (
                    "Evidence-led diagnostics help teams understand equipment signals. " * 8
                    if platform == "x"
                    else f"A distinct {platform} story grounded in verified product evidence."
                )
                variants.append(
                    {
                        "platform": platform,
                        "title": (
                            "Aevra evidence-led product launch for engineering teams"
                            if platform == "youtube"
                            else None
                        ),
                        "caption": long_copy,
                        "hashtags": ["#Aevra", "#AgenticAI", "#Evidence", "#Launch"],
                        "call_to_action": "Explore the evidence",
                    }
                )
            content = json.dumps(
                {
                    "master_plan": {
                        "objective": "Grounded launch",
                        "message_pillars": ["Evidence", "Clarity"],
                        "creative_direction": "Premium and precise",
                    },
                    "variants": variants,
                }
            )
        return GenerationResult(
            content=content,
            model=self.model_name,
            provider="fake-local",
            prompt_tokens=120,
            completion_tokens=80,
            metadata={"offline": True},
        )


def create_brand(client: TestClient, registration: dict[str, object]) -> dict[str, object]:
    workspace_id = registration["workspace"]["id"]  # type: ignore[index]
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/brands",
        headers=bearer(registration),
        json={
            "name": "Aevra",
            "description": "Evidence-grounded agentic content intelligence.",
            "tone_attributes": ["Precise", "Confident"],
            "target_audiences": ["Engineering leaders"],
            "preferred_ctas": ["Explore the evidence"],
            "preferred_hashtags": ["#Aevra", "#AgenticAI"],
            "status": "active",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def seed_knowledge(client: TestClient, registration: dict[str, object], brand_id: str) -> None:
    workspace_id = registration["workspace"]["id"]  # type: ignore[index]
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/knowledge/documents",
        headers=bearer(registration),
        json={
            "title": "Verified product brief",
            "source_type": "text",
            "brand_id": brand_id,
            "product": "Aevra Studio",
            "content": (
                "Aevra Studio grounds campaign content in tenant-specific evidence and "
                "preserves citations for review."
            ),
        },
    )
    assert response.status_code == 201, response.text


def create_campaign(
    client: TestClient,
    registration: dict[str, object],
    brand_id: str,
    platforms: list[str],
) -> dict[str, object]:
    workspace_id = registration["workspace"]["id"]  # type: ignore[index]
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/campaigns",
        headers=bearer(registration),
        json={
            "brand_id": brand_id,
            "name": "Evidence Launch",
            "goal": "Launch Aevra Studio with grounded product messaging",
            "product_service": "Aevra Studio",
            "audience": "Engineering and marketing leaders",
            "instructions": "Keep the campaign specific and evidence-led.",
            "platforms": platforms,
            "media_types": ["text"],
            "publishing_mode": "manual",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_every_platform_adapter_enforces_limits_and_quality_rules() -> None:
    raw = {
        "title": "A grounded campaign title " * 20,
        "caption": "Evidence-led platform copy " * 400,
        "hashtags": [f"#Tag{index}" for index in range(30)],
        "call_to_action": "Explore the evidence",
    }
    for platform, spec in PLATFORM_SPECS.items():
        adapted = adapt_variant({**raw, "platform": platform}, platform)
        assert len(str(adapted["caption"])) <= spec.caption_limit
        assert len(adapted["hashtags"]) <= spec.hashtag_limit  # type: ignore[arg-type]
        if spec.requires_title:
            assert adapted["title"] is not None
            assert len(str(adapted["title"])) <= int(spec.title_limit or 0)

    issues, score = validate_variant(
        {**adapt_variant({**raw, "platform": "linkedin"}, "linkedin"), "caption": "Never"},
        ['Never use the phrase "Never"'],
        has_citations=False,
    )
    assert any("No Brand Brain citations" in issue for issue in issues)
    assert any("Prohibited phrase" in issue for issue in issues)
    assert score < 100
    try:
        adapt_variant({"caption": "Missing title", "hashtags": []}, "youtube")
        raise AssertionError("YouTube variant without a title was accepted")
    except GenerationError:
        pass


def test_langgraph_generation_approval_and_revision_history(
    client: TestClient, session: Session
) -> None:
    owner = register_account(
        client,
        email="campaign-owner@example.com",
        organization_name="Campaign Labs",
        workspace_name="Core",
    )
    brand = create_brand(client, owner)
    seed_knowledge(client, owner, str(brand["id"]))
    platforms = ["linkedin", "x", "youtube"]
    provider = CampaignLLMProvider(platforms)
    app.dependency_overrides[get_llm_provider] = lambda: provider
    campaign = create_campaign(client, owner, str(brand["id"]), platforms)
    workspace_id = owner["workspace"]["id"]  # type: ignore[index]
    endpoint = f"/api/v1/workspaces/{workspace_id}/campaigns/{campaign['id']}"

    generated = client.post(f"{endpoint}/generate", headers=bearer(owner), json={"feedback": None})
    assert generated.status_code == 200, generated.text
    payload = generated.json()
    assert payload["campaign"]["status"] == "awaiting_approval"
    assert payload["campaign"]["current_revision"] == 1
    assert payload["run"]["status"] == "waiting_approval"
    assert payload["plan"]["objective"] == "Grounded launch"
    assert [step["node_name"] for step in payload["steps"]] == [
        "context_retrieval",
        "planning",
        "content_generation",
        "platform_adaptation",
        "validation",
        "approval_boundary",
    ]
    assert {item["platform"] for item in payload["variants"]} == set(platforms)
    assert all(item["citations"] for item in payload["variants"])
    x_variant = next(item for item in payload["variants"] if item["platform"] == "x")
    assert len(x_variant["caption"]) <= 280
    assert x_variant["generation_metadata"]["offline"] is True
    persisted_run = session.scalar(
        select(CampaignRun).where(CampaignRun.id == uuid.UUID(payload["run"]["id"]))
    )
    assert persisted_run is not None
    assert persisted_run.state_snapshot["status"] == "awaiting_approval"
    assert len(persisted_run.state_snapshot["validated_variants"]) == 3

    approved = client.post(
        f"{endpoint}/decision",
        headers=bearer(owner),
        json={"decision": "approve", "feedback": "Approved for scheduling"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["campaign"]["status"] == "approved"
    assert all(item["status"] == "approved" for item in approved.json()["variants"])

    regenerated = client.post(
        f"{endpoint}/generate",
        headers=bearer(owner),
        json={"feedback": "Make the opening more direct"},
    )
    assert regenerated.status_code == 200, regenerated.text
    assert regenerated.json()["campaign"]["current_revision"] == 2
    assert "Make the opening more direct" in provider.calls[-1].messages[-1].content

    rejected = client.post(
        f"{endpoint}/decision",
        headers=bearer(owner),
        json={"decision": "reject", "feedback": "Needs another concept"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["campaign"]["status"] == "draft"
    variants = client.get(f"{endpoint}/variants", headers=bearer(owner)).json()
    assert len(variants) == 6
    assert all(item["status"] == "approved" for item in variants if item["revision"] == 1)
    assert all(item["status"] == "rejected" for item in variants if item["revision"] == 2)


def test_campaigns_are_tenant_isolated(client: TestClient) -> None:
    alice = register_account(
        client,
        email="campaign-alice@example.com",
        organization_name="Alice Campaigns",
        workspace_name="Core",
    )
    bob = register_account(
        client,
        email="campaign-bob@example.com",
        organization_name="Bob Campaigns",
        workspace_name="Core",
    )
    brand = create_brand(client, alice)
    campaign = create_campaign(client, alice, str(brand["id"]), ["linkedin"])
    workspace_id = alice["workspace"]["id"]  # type: ignore[index]
    endpoint = f"/api/v1/workspaces/{workspace_id}/campaigns/{campaign['id']}"
    assert client.get(endpoint, headers=bearer(bob)).status_code == 404
    assert client.post(f"{endpoint}/generate", headers=bearer(bob), json={}).status_code == 404


def test_viewer_can_review_but_cannot_create_or_generate(
    client: TestClient, session: Session
) -> None:
    owner = register_account(
        client,
        email="campaign-editor@example.com",
        organization_name="Shared Campaigns",
        workspace_name="Core",
    )
    viewer = register_account(
        client,
        email="campaign-viewer@example.com",
        organization_name="Viewer Campaigns",
        workspace_name="Home",
    )
    workspace = session.get(Workspace, uuid.UUID(str(owner["workspace"]["id"])))  # type: ignore[index]
    viewer_user = session.scalar(select(User).where(User.email == "campaign-viewer@example.com"))
    assert workspace is not None and viewer_user is not None
    session.add(
        OrganizationMember(
            organization_id=workspace.organization_id,
            user_id=viewer_user.id,
            role="viewer",
        )
    )
    session.commit()
    brand = create_brand(client, owner)
    campaign = create_campaign(client, owner, str(brand["id"]), ["linkedin"])
    workspace_id = owner["workspace"]["id"]  # type: ignore[index]
    base = f"/api/v1/workspaces/{workspace_id}/campaigns"
    assert client.get(base, headers=bearer(viewer)).status_code == 200
    assert client.get(f"{base}/{campaign['id']}", headers=bearer(viewer)).status_code == 200
    blocked_create = client.post(
        base,
        headers=bearer(viewer),
        json={
            "brand_id": brand["id"],
            "name": "Blocked campaign",
            "goal": "Viewer must not create this campaign",
            "product_service": "Aevra",
            "audience": "Reviewers",
            "platforms": ["linkedin"],
        },
    )
    assert blocked_create.status_code == 403
    blocked_generate = client.post(
        f"{base}/{campaign['id']}/generate", headers=bearer(viewer), json={}
    )
    assert blocked_generate.status_code == 403


def test_malformed_generation_is_persisted_as_failed(client: TestClient) -> None:
    owner = register_account(
        client,
        email="campaign-failure@example.com",
        organization_name="Failure Campaigns",
        workspace_name="Core",
    )
    brand = create_brand(client, owner)
    provider = CampaignLLMProvider(["linkedin"], malformed=True)
    app.dependency_overrides[get_llm_provider] = lambda: provider
    campaign = create_campaign(client, owner, str(brand["id"]), ["linkedin"])
    workspace_id = owner["workspace"]["id"]  # type: ignore[index]
    endpoint = f"/api/v1/workspaces/{workspace_id}/campaigns/{campaign['id']}"
    generated = client.post(f"{endpoint}/generate", headers=bearer(owner), json={})
    assert generated.status_code == 502
    assert generated.json()["error"]["code"] == "generation_failed"
    campaign_state = client.get(endpoint, headers=bearer(owner))
    assert campaign_state.status_code == 200
    assert campaign_state.json()["status"] == "failed"
    assert campaign_state.json()["error_message"] == "The model returned malformed JSON"


def test_database_rejects_cross_workspace_variant(client: TestClient, session: Session) -> None:
    alice = register_account(
        client,
        email="variant-alice@example.com",
        organization_name="Variant Alice",
        workspace_name="Core",
    )
    bob = register_account(
        client,
        email="variant-bob@example.com",
        organization_name="Variant Bob",
        workspace_name="Core",
    )
    brand = create_brand(client, alice)
    campaign = create_campaign(client, alice, str(brand["id"]), ["linkedin"])
    session.add(
        ContentVariant(
            workspace_id=uuid.UUID(str(bob["workspace"]["id"])),  # type: ignore[index]
            campaign_id=uuid.UUID(str(campaign["id"])),
            revision=1,
            platform="linkedin",
            caption="Cross-tenant content must fail.",
            hashtags=[],
            status="draft",
            quality_score=80,
            validation_issues=[],
            citations=[],
            generated_by_model="test",
            generation_metadata={},
        )
    )
    try:
        session.commit()
        raise AssertionError("Cross-workspace content variant was accepted")
    except IntegrityError:
        session.rollback()
