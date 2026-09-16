import uuid

from fastapi import APIRouter, status

from aevra_api.api.dependencies import (
    CurrentUser,
    EmbeddingProviderDep,
    LLMProviderDep,
    SessionDep,
    SettingsDep,
)
from aevra_api.schemas.campaigns import (
    CampaignCreateRequest,
    CampaignDecisionRequest,
    CampaignGenerateRequest,
    CampaignGenerationResponse,
    CampaignResponse,
    CampaignRunResponse,
    CampaignStepResponse,
    ContentVariantResponse,
)
from aevra_api.services.campaigns import CampaignService, GenerationBundle

router = APIRouter(prefix="/workspaces/{workspace_id}/campaigns", tags=["campaigns"])


def service(
    session: SessionDep,
    settings: SettingsDep,
    embedding_provider: EmbeddingProviderDep,
    llm_provider: LLMProviderDep,
) -> CampaignService:
    return CampaignService(session, settings, embedding_provider, llm_provider)


def generation_response(
    bundle: GenerationBundle, campaign_service: CampaignService, user_id: uuid.UUID
) -> CampaignGenerationResponse:
    steps = campaign_service.steps(user_id, bundle.campaign.workspace_id, bundle.run.id)
    return CampaignGenerationResponse(
        campaign=CampaignResponse.model_validate(bundle.campaign),
        run=CampaignRunResponse.model_validate(bundle.run),
        plan=bundle.plan,
        variants=[ContentVariantResponse.model_validate(item) for item in bundle.variants],
        steps=[CampaignStepResponse.model_validate(item) for item in steps],
    )


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(
    workspace_id: uuid.UUID,
    request: CampaignCreateRequest,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    embedding_provider: EmbeddingProviderDep,
    llm_provider: LLMProviderDep,
) -> CampaignResponse:
    campaign = service(session, settings, embedding_provider, llm_provider).create(
        current_user.id, workspace_id, request
    )
    return CampaignResponse.model_validate(campaign)


@router.get("", response_model=list[CampaignResponse])
def list_campaigns(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    embedding_provider: EmbeddingProviderDep,
    llm_provider: LLMProviderDep,
) -> list[CampaignResponse]:
    campaigns = service(session, settings, embedding_provider, llm_provider).list_campaigns(
        current_user.id, workspace_id
    )
    return [CampaignResponse.model_validate(item) for item in campaigns]


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    workspace_id: uuid.UUID,
    campaign_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    embedding_provider: EmbeddingProviderDep,
    llm_provider: LLMProviderDep,
) -> CampaignResponse:
    campaign = service(session, settings, embedding_provider, llm_provider).get(
        current_user.id, workspace_id, campaign_id
    )
    return CampaignResponse.model_validate(campaign)


@router.post("/{campaign_id}/generate", response_model=CampaignGenerationResponse)
def generate_campaign(
    workspace_id: uuid.UUID,
    campaign_id: uuid.UUID,
    request: CampaignGenerateRequest,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    embedding_provider: EmbeddingProviderDep,
    llm_provider: LLMProviderDep,
) -> CampaignGenerationResponse:
    campaign_service = service(session, settings, embedding_provider, llm_provider)
    bundle = campaign_service.generate(current_user.id, workspace_id, campaign_id, request.feedback)
    return generation_response(bundle, campaign_service, current_user.id)


@router.post("/{campaign_id}/decision", response_model=CampaignGenerationResponse)
def decide_campaign(
    workspace_id: uuid.UUID,
    campaign_id: uuid.UUID,
    request: CampaignDecisionRequest,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    embedding_provider: EmbeddingProviderDep,
    llm_provider: LLMProviderDep,
) -> CampaignGenerationResponse:
    campaign_service = service(session, settings, embedding_provider, llm_provider)
    bundle = campaign_service.decide(
        current_user.id,
        workspace_id,
        campaign_id,
        request.decision,
        request.feedback,
    )
    return generation_response(bundle, campaign_service, current_user.id)


@router.get("/{campaign_id}/variants", response_model=list[ContentVariantResponse])
def list_variants(
    workspace_id: uuid.UUID,
    campaign_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    embedding_provider: EmbeddingProviderDep,
    llm_provider: LLMProviderDep,
) -> list[ContentVariantResponse]:
    variants = service(session, settings, embedding_provider, llm_provider).variants(
        current_user.id, workspace_id, campaign_id
    )
    return [ContentVariantResponse.model_validate(item) for item in variants]
