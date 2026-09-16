import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status

from aevra_api.api.dependencies import (
    CurrentUser,
    EmbeddingProviderDep,
    SessionDep,
    SettingsDep,
)
from aevra_api.schemas.knowledge import (
    IngestionResponse,
    KnowledgeDocumentResponse,
    KnowledgeIngestRequest,
    RetrievalRequest,
    RetrievalResponse,
)
from aevra_api.services.knowledge import KnowledgeService

router = APIRouter(prefix="/workspaces/{workspace_id}/knowledge", tags=["knowledge"])


@router.post("/documents", response_model=IngestionResponse, status_code=status.HTTP_201_CREATED)
def ingest_document(
    workspace_id: uuid.UUID,
    request: KnowledgeIngestRequest,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    embedding_provider: EmbeddingProviderDep,
) -> IngestionResponse:
    result = KnowledgeService(session, settings, embedding_provider).ingest_text(
        user_id=current_user.id,
        workspace_id=workspace_id,
        title=request.title,
        source_type=request.source_type,
        content=request.content,
        source_uri=request.source_uri,
        brand_id=request.brand_id,
        metadata={"product": request.product or "", "campaign": request.campaign or ""},
    )
    return IngestionResponse(
        document=KnowledgeDocumentResponse.model_validate(result.document),
        chunks_created=result.chunks_created,
        deduplicated=result.deduplicated,
    )


@router.post(
    "/documents/upload",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    embedding_provider: EmbeddingProviderDep,
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form()] = None,
    source_uri: Annotated[str | None, Form()] = None,
    brand_id: Annotated[uuid.UUID | None, Form()] = None,
    product: Annotated[str | None, Form(max_length=160)] = None,
    campaign: Annotated[str | None, Form(max_length=160)] = None,
) -> IngestionResponse:
    content = await file.read(settings.max_document_bytes + 1)
    result = KnowledgeService(session, settings, embedding_provider).ingest_upload(
        user_id=current_user.id,
        workspace_id=workspace_id,
        filename=file.filename or "upload",
        content=content,
        title=title,
        source_uri=source_uri,
        brand_id=brand_id,
        metadata={"product": product or "", "campaign": campaign or ""},
    )
    return IngestionResponse(
        document=KnowledgeDocumentResponse.model_validate(result.document),
        chunks_created=result.chunks_created,
        deduplicated=result.deduplicated,
    )


@router.get("/documents", response_model=list[KnowledgeDocumentResponse])
def list_documents(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    embedding_provider: EmbeddingProviderDep,
) -> list[KnowledgeDocumentResponse]:
    documents = KnowledgeService(session, settings, embedding_provider).list_documents(
        current_user.id, workspace_id
    )
    return [KnowledgeDocumentResponse.model_validate(document) for document in documents]


@router.post("/search", response_model=RetrievalResponse)
def retrieve_knowledge(
    workspace_id: uuid.UUID,
    request: RetrievalRequest,
    current_user: CurrentUser,
    session: SessionDep,
    settings: SettingsDep,
    embedding_provider: EmbeddingProviderDep,
) -> RetrievalResponse:
    result = KnowledgeService(session, settings, embedding_provider).retrieve(
        current_user.id, workspace_id, request
    )
    return RetrievalResponse(
        query=request.query,
        citations=result.citations,
        embedding_model=result.embedding_model,
    )
