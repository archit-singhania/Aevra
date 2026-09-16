import hashlib
import json
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TypedDict, cast

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from aevra_api.ai.contracts import ChatMessage, GenerationRequest, LLMProvider
from aevra_api.db.models import BrandProfile, BrandRule, Campaign, CampaignRun, CampaignStep
from aevra_api.domain.errors import GenerationError
from aevra_api.generation.platforms import adapt_variant, validate_variant
from aevra_api.generation.prompts import build_campaign_prompt
from aevra_api.schemas.knowledge import RetrievalRequest
from aevra_api.services.knowledge import KnowledgeService


class CampaignState(TypedDict, total=False):
    campaign_id: str
    workspace_id: str
    revision: int
    feedback: str | None
    citations: list[dict[str, object]]
    context_text: str
    plan: dict[str, object]
    raw_variants: list[dict[str, object]]
    adapted_variants: list[dict[str, object]]
    validated_variants: list[dict[str, object]]
    provider_metadata: dict[str, object]
    status: str


Node = Callable[[CampaignState], CampaignState]


class CampaignWorkflow:
    def __init__(
        self,
        *,
        session: Session,
        actor_user_id: uuid.UUID,
        campaign: Campaign,
        run: CampaignRun,
        brand: BrandProfile,
        rules: list[BrandRule],
        knowledge_service: KnowledgeService,
        llm_provider: LLMProvider,
    ) -> None:
        self.session = session
        self.actor_user_id = actor_user_id
        self.campaign = campaign
        self.run = run
        self.brand = brand
        self.rules = rules
        self.knowledge_service = knowledge_service
        self.llm_provider = llm_provider
        self.sequence = 0

    def compile(self):  # type: ignore[no-untyped-def]
        builder = StateGraph(CampaignState)
        builder.add_node(
            "context_retrieval",
            self._tracked("context_retrieval", "context_retrieval", self._retrieve_context),
        )
        builder.add_node("planning", self._tracked("planning", "planning", self._plan))
        builder.add_node(
            "content_generation",
            self._tracked("content_generation", "content_generation", self._generate),
        )
        builder.add_node(
            "platform_adaptation",
            self._tracked("platform_adaptation", "platform_adaptation", self._adapt),
        )
        builder.add_node("validation", self._tracked("validation", "validation", self._validate))
        builder.add_node(
            "approval_boundary",
            self._tracked("approval_boundary", "awaiting_approval", self._await_approval),
        )
        builder.add_edge(START, "context_retrieval")
        builder.add_edge("context_retrieval", "planning")
        builder.add_edge("planning", "content_generation")
        builder.add_edge("content_generation", "platform_adaptation")
        builder.add_edge("platform_adaptation", "validation")
        builder.add_edge("validation", "approval_boundary")
        builder.add_edge("approval_boundary", END)
        return builder.compile()

    def _tracked(self, node_name: str, campaign_status: str, node: Node) -> Node:
        def execute(state: CampaignState) -> CampaignState:
            self.sequence += 1
            self.campaign.status = campaign_status
            self.run.current_node = node_name
            started = time.perf_counter()
            digest = hashlib.sha256(
                json.dumps(state, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()
            try:
                update = node(state)
                merged = cast(CampaignState, {**state, **update})
                duration_ms = round((time.perf_counter() - started) * 1000)
                provider_metadata = update.get("provider_metadata", {})
                self.session.add(
                    CampaignStep(
                        workspace_id=self.campaign.workspace_id,
                        campaign_id=self.campaign.id,
                        run_id=self.run.id,
                        sequence=self.sequence,
                        node_name=node_name,
                        status="completed",
                        input_digest=digest,
                        output_snapshot=self._safe_snapshot(update),
                        citations=merged.get("citations", []),
                        duration_ms=duration_ms,
                        provider_metadata=provider_metadata,
                    )
                )
                self.run.state_snapshot = self._safe_snapshot(merged)
                if provider_metadata:
                    self.run.provider_metadata = provider_metadata
                self.session.commit()
                return update
            except Exception as exc:
                duration_ms = round((time.perf_counter() - started) * 1000)
                safe_message = (
                    str(exc)[:1000]
                    if isinstance(exc, GenerationError)
                    else ("Campaign workflow failed")
                )
                self.session.add(
                    CampaignStep(
                        workspace_id=self.campaign.workspace_id,
                        campaign_id=self.campaign.id,
                        run_id=self.run.id,
                        sequence=self.sequence,
                        node_name=node_name,
                        status="failed",
                        input_digest=digest,
                        output_snapshot={},
                        citations=state.get("citations", []),
                        duration_ms=duration_ms,
                        provider_metadata={},
                        error_message=safe_message,
                    )
                )
                self.campaign.status = "failed"
                self.campaign.error_message = safe_message
                self.run.status = "failed"
                self.run.error_message = safe_message
                self.run.finished_at = datetime.now(UTC)
                self.session.commit()
                raise

        return execute

    @staticmethod
    def _safe_snapshot(value: CampaignState) -> dict[str, object]:
        return cast(dict[str, object], json.loads(json.dumps(value, default=str)))

    def _retrieve_context(self, _state: CampaignState) -> CampaignState:
        query = " ".join(
            [self.campaign.goal, self.campaign.product_service, self.campaign.audience]
        )
        result = self.knowledge_service.retrieve(
            self.actor_user_id,
            self.campaign.workspace_id,
            RetrievalRequest(query=query, limit=8, min_score=0, brand_id=self.campaign.brand_id),
        )
        citations = [citation.model_dump(mode="json") for citation in result.citations]
        return {
            "citations": citations,
            "context_text": "\n\n".join(item["excerpt"] for item in citations),
        }

    def _plan(self, state: CampaignState) -> CampaignState:
        return {
            "plan": {
                "objective": self.campaign.goal,
                "audience": self.campaign.audience,
                "product_service": self.campaign.product_service,
                "platforms": self.campaign.platforms,
                "evidence_count": len(state.get("citations", [])),
            }
        }

    def _generate(self, state: CampaignState) -> CampaignState:
        campaign_payload: dict[str, object] = {
            "name": self.campaign.name,
            "goal": self.campaign.goal,
            "product_service": self.campaign.product_service,
            "audience": self.campaign.audience,
            "instructions": self.campaign.instructions,
            "platforms": self.campaign.platforms,
            "media_types": self.campaign.media_types,
        }
        brand_payload: dict[str, object] = {
            "name": self.brand.name,
            "description": self.brand.description,
            "tone_attributes": self.brand.tone_attributes,
            "target_audiences": self.brand.target_audiences,
            "preferred_ctas": self.brand.preferred_ctas,
            "preferred_hashtags": self.brand.preferred_hashtags,
        }
        rule_payloads = [
            {
                "category": rule.category,
                "enforcement": rule.enforcement,
                "directive": rule.directive,
                "priority": rule.priority,
            }
            for rule in self.rules
            if rule.is_active
        ]
        prompt = build_campaign_prompt(
            campaign=campaign_payload,
            brand=brand_payload,
            rules=rule_payloads,
            citations=state.get("citations", []),
            feedback=state.get("feedback"),
        )
        result = self.llm_provider.generate(
            GenerationRequest(
                messages=[
                    ChatMessage(
                        role="system",
                        content=(
                            "You are Aevra's grounded campaign writer. Return JSON only and "
                            "obey brand, evidence, and platform constraints."
                        ),
                    ),
                    ChatMessage(role="user", content=prompt),
                ],
                temperature=0.35,
                max_tokens=5000,
                response_format="json",
            )
        )
        parsed = self._parse_json(result.content)
        variants = parsed.get("variants")
        plan = parsed.get("master_plan")
        if not isinstance(variants, list) or not all(isinstance(item, dict) for item in variants):
            raise GenerationError("The model returned an invalid variants collection")
        if not isinstance(plan, dict):
            raise GenerationError("The model returned an invalid campaign plan")
        return {
            "plan": cast(dict[str, object], plan),
            "raw_variants": cast(list[dict[str, object]], variants),
            "provider_metadata": {
                "provider": result.provider,
                "model": result.model,
                "prompt_tokens": result.prompt_tokens or 0,
                "completion_tokens": result.completion_tokens or 0,
                **result.metadata,
            },
        }

    def _adapt(self, state: CampaignState) -> CampaignState:
        raw_by_platform: dict[str, dict[str, object]] = {}
        for raw in state.get("raw_variants", []):
            platform = raw.get("platform")
            if isinstance(platform, str) and platform in self.campaign.platforms:
                if platform in raw_by_platform:
                    raise GenerationError(f"The model returned duplicate {platform} variants")
                raw_by_platform[platform] = raw
        missing = [item for item in self.campaign.platforms if item not in raw_by_platform]
        if missing:
            raise GenerationError(f"The model omitted platform variants: {', '.join(missing)}")
        return {
            "adapted_variants": [
                adapt_variant(raw_by_platform[platform], platform)
                for platform in self.campaign.platforms
            ]
        }

    def _validate(self, state: CampaignState) -> CampaignState:
        prohibited = [
            rule.directive
            for rule in self.rules
            if rule.is_active and rule.enforcement == "prohibited"
        ]
        validated: list[dict[str, object]] = []
        for variant in state.get("adapted_variants", []):
            issues, score = validate_variant(variant, prohibited, bool(state.get("citations")))
            validated.append({**variant, "validation_issues": issues, "quality_score": score})
        return {"validated_variants": validated}

    def _await_approval(self, _state: CampaignState) -> CampaignState:
        return {"status": "awaiting_approval"}

    @staticmethod
    def _parse_json(content: str) -> dict[str, object]:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```json").removeprefix("```")
            cleaned = cleaned.removesuffix("```").strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise GenerationError("The model returned malformed JSON") from exc
        if not isinstance(parsed, dict):
            raise GenerationError("The model response must be a JSON object")
        return cast(dict[str, object], parsed)
