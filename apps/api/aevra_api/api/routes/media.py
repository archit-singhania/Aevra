import uuid
from typing import Literal

from fastapi import APIRouter, Response, status

from aevra_api.api.dependencies import CurrentUser, SessionDep, SettingsDep
from aevra_api.schemas.media import (
    ImageGenerateRequest,
    MediaAssetResponse,
    MediaGenerationResponse,
    VideoComposeRequest,
)
from aevra_api.services.media import MediaService

router = APIRouter(prefix="/workspaces/{workspace_id}/media", tags=["media"])


def _response(asset: object, workspace_id: uuid.UUID) -> MediaAssetResponse:
    response = MediaAssetResponse.model_validate(asset)
    response.download_url = f"/api/v1/workspaces/{workspace_id}/media/assets/{response.id}/download"
    return response


@router.post(
    "/images/generate",
    response_model=MediaGenerationResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_images(
    workspace_id: uuid.UUID,
    request: ImageGenerateRequest,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
) -> MediaGenerationResponse:
    assets = MediaService(session, settings).generate_images(current_user.id, workspace_id, request)
    return MediaGenerationResponse(assets=[_response(asset, workspace_id) for asset in assets])


@router.post(
    "/videos/compose",
    response_model=MediaGenerationResponse,
    status_code=status.HTTP_201_CREATED,
)
def compose_videos(
    workspace_id: uuid.UUID,
    request: VideoComposeRequest,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
) -> MediaGenerationResponse:
    assets = MediaService(session, settings).compose_videos(current_user.id, workspace_id, request)
    return MediaGenerationResponse(assets=[_response(asset, workspace_id) for asset in assets])


@router.get("/assets", response_model=list[MediaAssetResponse])
def list_assets(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    campaign_id: uuid.UUID | None = None,
    media_type: Literal["image", "video"] | None = None,
) -> list[MediaAssetResponse]:
    assets = MediaService(session, settings).list_assets(
        current_user.id, workspace_id, campaign_id, media_type
    )
    return [_response(asset, workspace_id) for asset in assets]


@router.get("/assets/{asset_id}", response_model=MediaAssetResponse)
def get_asset(
    workspace_id: uuid.UUID,
    asset_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
) -> MediaAssetResponse:
    asset = MediaService(session, settings).get_asset(current_user.id, workspace_id, asset_id)
    return _response(asset, workspace_id)


@router.get("/assets/{asset_id}/download")
def download_asset(
    workspace_id: uuid.UUID,
    asset_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
) -> Response:
    asset, content = MediaService(session, settings).asset_bytes(
        current_user.id, workspace_id, asset_id
    )
    return Response(
        content=content,
        media_type=asset.mime_type,
        headers={"Content-Disposition": f'inline; filename="{asset.filename}"'},
    )
