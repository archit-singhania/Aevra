import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from aevra_api.ai.contracts import EmbeddingProvider, LLMProvider
from aevra_api.campaigns.workflow import CampaignState, CampaignWorkflow
from aevra_api.config import Settings
from aevra_api.db.models import BrandProfile, Campaign, CampaignRun, CampaignStep, ContentVariant
from aevra_api.domain.errors import ConflictError, ForbiddenError, NotFoundError
from aevra_api.repositories.brands import BrandRepository
from aevra_api.repositories.campaigns import CampaignRepository
from aevra_api.repositories.tenancy import TenancyRepository
from aevra_api.schemas.campaigns import CampaignCreateRequest
from aevra_api.services.brands import BrandService
from aevra_api.services.knowledge import KnowledgeService

CAMPAIGN_EDIT_ROLES = {"owner", "admin", "member"}


@dataclass(frozen=True)
class GenerationBundle:
    campaign: Campaign
    run: CampaignRun
    plan: dict[str, object]
    variants: list[ContentVariant]


class CampaignService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        embedding_provider: EmbeddingProvider,
        llm_provider: LLMProvider,
    ) -> None:
        self.session = session
        self.settings = settings
        self.embedding_provider = embedding_provider
        self.llm_provider = llm_provider
        self.repository = CampaignRepository(session)
        self.tenancy_repository = TenancyRepository(session)
        self.brand_repository = BrandRepository(session)

    def _require_access(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> str:
        access = self.tenancy_repository.get_workspace_access(user_id, workspace_id)
        if access is None:
            raise NotFoundError("Workspace not found")
        return access[1]

    def _require_editor(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> None:
        if self._require_access(user_id, workspace_id) not in CAMPAIGN_EDIT_ROLES:
            raise ForbiddenError("Campaign editor access is required")

    def create(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, request: CampaignCreateRequest
    ) -> Campaign:
        self._require_editor(user_id, workspace_id)
        brand = (
            BrandService(self.session).get_brand(user_id, workspace_id, request.brand_id)
            if request.brand_id
            else None
        )
        if brand is None:
            # Brand and retrieval policy are backend-owned. Existing tenant
            # brands remain valid, while new tenants can create campaigns
            # without first entering an internal configuration screen.
            existing_brands = self.brand_repository.list_brands_for_user(user_id, workspace_id)
            brand = existing_brands[0] if existing_brands else BrandProfile(
                workspace_id=workspace_id,
                name="VAE default",
                slug="vae-default",
                description="Default VAE campaign intelligence configuration.",
                industry="AI software",
                tone_attributes=["clear", "strategic", "evidence-led"],
                target_audiences=[],
                preferred_ctas=["Learn more"],
                preferred_hashtags=[],
                status="active",
            )
            if brand.id is None:
                self.brand_repository.add_brand(brand)
                self.session.flush()
        campaign = Campaign(
            workspace_id=workspace_id,
            brand_id=brand.id,
            created_by_user_id=user_id,
            name=request.name.strip(),
            goal=request.goal.strip(),
            product_service=request.product_service.strip(),
            audience=request.audience.strip(),
            instructions=request.instructions.strip(),
            platforms=request.platforms,
            media_types=request.media_types,
            start_at=request.start_at,
            publishing_mode=request.publishing_mode,
            status="draft",
        )
        self.repository.add_campaign(campaign)
        self.session.commit()
        return campaign

    def get(self, user_id: uuid.UUID, workspace_id: uuid.UUID, campaign_id: uuid.UUID) -> Campaign:
        campaign = self.repository.get_for_user(user_id, workspace_id, campaign_id)
        if campaign is None:
            raise NotFoundError("Campaign not found")
        return campaign

    def list_campaigns(self, user_id: uuid.UUID, workspace_id: uuid.UUID) -> list[Campaign]:
        self._require_access(user_id, workspace_id)
        return self.repository.list_for_user(user_id, workspace_id)

    def variants(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, campaign_id: uuid.UUID
    ) -> list[ContentVariant]:
        campaign = self.get(user_id, workspace_id, campaign_id)
        return self.repository.list_variants_for_user(user_id, workspace_id, campaign.id)

    def steps(
        self, user_id: uuid.UUID, workspace_id: uuid.UUID, run_id: uuid.UUID
    ) -> list[CampaignStep]:
        self._require_access(user_id, workspace_id)
        return self.repository.list_steps_for_user(user_id, workspace_id, run_id)

    def generate(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        campaign_id: uuid.UUID,
        feedback: str | None = None,
    ) -> GenerationBundle:
        self._require_editor(user_id, workspace_id)
        campaign = self.get(user_id, workspace_id, campaign_id)
        if campaign.status not in {"draft", "failed", "awaiting_approval", "approved"}:
            raise ConflictError("Campaign generation is already in progress")
        brand = BrandService(self.session).get_brand(user_id, workspace_id, campaign.brand_id)
        rules = self.brand_repository.list_rules_for_user(user_id, workspace_id, campaign.brand_id)
        self.repository.supersede_variants(campaign.id)
        campaign.current_revision += 1
        campaign.latest_feedback = feedback.strip() if feedback else None
        campaign.error_message = None
        run = CampaignRun(
            workspace_id=workspace_id,
            campaign_id=campaign.id,
            run_number=self.repository.next_run_number(campaign.id),
            revision=campaign.current_revision,
            status="running",
            started_at=datetime.now(UTC),
        )
        self.repository.add_run(run)
        self.session.commit()

        knowledge_service = KnowledgeService(self.session, self.settings, self.embedding_provider)
        workflow = CampaignWorkflow(
            session=self.session,
            actor_user_id=user_id,
            campaign=campaign,
            run=run,
            brand=brand,
            rules=rules or [],
            knowledge_service=knowledge_service,
            llm_provider=self.llm_provider,
        )
        initial_state = CampaignState(
            campaign_id=str(campaign.id),
            workspace_id=str(workspace_id),
            revision=campaign.current_revision,
            feedback=campaign.latest_feedback,
        )
        final_state = workflow.compile().invoke(initial_state)
        citation_payloads = final_state.get("citations", [])
        provider_metadata = final_state.get("provider_metadata", {})
        model = str(provider_metadata.get("model", self.llm_provider.model_name))
        variants = [
            ContentVariant(
                workspace_id=workspace_id,
                campaign_id=campaign.id,
                revision=campaign.current_revision,
                platform=str(item["platform"]),
                title=item.get("title") if isinstance(item.get("title"), str) else None,
                caption=str(item["caption"]),
                hashtags=[str(tag) for tag in item.get("hashtags", [])],
                call_to_action=(
                    item.get("call_to_action")
                    if isinstance(item.get("call_to_action"), str)
                    else None
                ),
                status="draft",
                quality_score=float(item["quality_score"]),
                validation_issues=[str(issue) for issue in item["validation_issues"]],
                citations=citation_payloads,
                generated_by_model=model,
                generation_metadata=provider_metadata,
            )
            for item in final_state.get("validated_variants", [])
        ]
        if len(variants) != len(campaign.platforms):
            raise ConflictError("Campaign workflow did not produce every platform variant")
        self.repository.add_variants(variants)
        campaign.status = "awaiting_approval"
        run.status = "waiting_approval"
        run.current_node = "approval_boundary"
        run.state_snapshot = dict(final_state)
        run.provider_metadata = provider_metadata
        self.session.commit()
        return GenerationBundle(campaign, run, final_state.get("plan", {}), variants)

    def decide(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        campaign_id: uuid.UUID,
        decision: str,
        feedback: str | None,
    ) -> GenerationBundle:
        self._require_editor(user_id, workspace_id)
        campaign = self.get(user_id, workspace_id, campaign_id)
        if campaign.status != "awaiting_approval":
            raise ConflictError("Campaign is not awaiting approval")
        run = self.repository.latest_run_for_user(user_id, workspace_id, campaign_id)
        if run is None or run.status != "waiting_approval":
            raise ConflictError("Campaign approval run is unavailable")
        variants = self.repository.list_variants_for_user(
            user_id, workspace_id, campaign_id, campaign.current_revision
        )
        now = datetime.now(UTC)
        if decision == "approve":
            for variant in variants:
                variant.status = "approved"
            campaign.status = "approved"
            run.status = "completed"
        else:
            for variant in variants:
                variant.status = "rejected"
            campaign.status = "draft"
            run.status = "cancelled"
        campaign.latest_feedback = feedback.strip() if feedback else None
        run.finished_at = now
        self.session.commit()
        plan = run.state_snapshot.get("plan", {})
        return GenerationBundle(
            campaign,
            run,
            plan if isinstance(plan, dict) else {},
            variants,
        )
