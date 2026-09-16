import uuid
from io import BytesIO

from conftest import bearer, register_account
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aevra_api.db.models import (
    KnowledgeChunk,
    KnowledgeDocument,
    OrganizationMember,
    User,
    Workspace,
)
from aevra_api.knowledge.normalization import chunk_text, normalize_text


def knowledge_url(registration: dict[str, object]) -> str:
    workspace_id = registration["workspace"]["id"]  # type: ignore[index]
    return f"/api/v1/workspaces/{workspace_id}/knowledge"


def test_normalization_removes_markup_and_chunking_preserves_offsets() -> None:
    markdown = normalize_text("# Voice\n\nUse **clear evidence**.", "markdown")
    website = normalize_text(
        "<main>Trusted facts</main><script>ignore me</script><style>x{}</style>", "website"
    )
    assert "#" not in markdown and "clear evidence" in markdown
    assert website == "Trusted facts"

    source = "First sentence. " * 80
    chunks = chunk_text(source, 240, 30)
    assert len(chunks) > 1
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))
    assert all(source[item.start_offset : item.end_offset] == item.content for item in chunks)


def test_ingest_deduplicate_filter_and_retrieve_citations(client: TestClient) -> None:
    owner = register_account(
        client,
        email="knowledge-owner@example.com",
        organization_name="Knowledge Labs",
        workspace_name="Core",
    )
    endpoint = knowledge_url(owner)
    payload = {
        "title": "Launch brief",
        "source_type": "markdown",
        "content": (
            "# Launch\n\nThe quantum pineapple campaign uses evidence-first product stories."
        ),
        "source_uri": "https://example.com/launch",
        "product": "Aevra Studio",
        "campaign": "Quantum",
    }
    created = client.post(f"{endpoint}/documents", headers=bearer(owner), json=payload)
    duplicate = client.post(f"{endpoint}/documents", headers=bearer(owner), json=payload)
    assert created.status_code == 201, created.text
    assert duplicate.status_code == 201, duplicate.text
    assert created.json()["deduplicated"] is False
    assert duplicate.json()["deduplicated"] is True
    assert duplicate.json()["document"]["id"] == created.json()["document"]["id"]

    search = client.post(
        f"{endpoint}/search",
        headers=bearer(owner),
        json={"query": "quantum pineapple", "campaign": "Quantum", "min_score": 0},
    )
    assert search.status_code == 200, search.text
    citation = search.json()["citations"][0]
    assert citation["document_title"] == "Launch brief"
    assert citation["source_uri"] == "https://example.com/launch"
    assert citation["metadata"]["product"] == "Aevra Studio"
    assert citation["start_offset"] < citation["end_offset"]

    excluded = client.post(
        f"{endpoint}/search",
        headers=bearer(owner),
        json={"query": "quantum pineapple", "campaign": "Another", "min_score": 0},
    )
    assert excluded.status_code == 200
    assert excluded.json()["citations"] == []


def test_pdf_upload_and_unsupported_file(client: TestClient) -> None:
    owner = register_account(
        client,
        email="pdf-owner@example.com",
        organization_name="PDF Labs",
        workspace_name="Library",
    )
    endpoint = knowledge_url(owner)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, "Aevra citations preserve evidence and provenance.")
    pdf.save()

    uploaded = client.post(
        f"{endpoint}/documents/upload",
        headers=bearer(owner),
        files={"file": ("evidence.pdf", buffer.getvalue(), "application/pdf")},
    )
    assert uploaded.status_code == 201, uploaded.text
    assert uploaded.json()["document"]["source_type"] == "pdf"
    assert uploaded.json()["chunks_created"] == 1

    unsupported = client.post(
        f"{endpoint}/documents/upload",
        headers=bearer(owner),
        files={"file": ("archive.zip", b"not a document", "application/zip")},
    )
    assert unsupported.status_code == 415
    assert unsupported.json()["error"]["code"] == "unsupported_content"


def test_knowledge_endpoints_are_tenant_isolated(client: TestClient) -> None:
    alice = register_account(
        client,
        email="knowledge-alice@example.com",
        organization_name="Alice Knowledge",
        workspace_name="Private",
    )
    bob = register_account(
        client,
        email="knowledge-bob@example.com",
        organization_name="Bob Knowledge",
        workspace_name="Private",
    )
    endpoint = knowledge_url(alice)
    created = client.post(
        f"{endpoint}/documents",
        headers=bearer(alice),
        json={"title": "Private", "source_type": "text", "content": "secret corpus"},
    )
    assert created.status_code == 201
    assert client.get(f"{endpoint}/documents", headers=bearer(bob)).status_code == 404
    assert (
        client.post(
            f"{endpoint}/search",
            headers=bearer(bob),
            json={"query": "secret corpus"},
        ).status_code
        == 404
    )


def test_viewer_can_retrieve_but_cannot_ingest(client: TestClient, session: Session) -> None:
    owner = register_account(
        client,
        email="knowledge-editor@example.com",
        organization_name="Shared Knowledge",
        workspace_name="Core",
    )
    viewer = register_account(
        client,
        email="knowledge-viewer@example.com",
        organization_name="Viewer Home",
        workspace_name="Home",
    )
    workspace = session.get(Workspace, uuid.UUID(str(owner["workspace"]["id"])))  # type: ignore[index]
    viewer_user = session.scalar(select(User).where(User.email == "knowledge-viewer@example.com"))
    assert workspace is not None and viewer_user is not None
    session.add(
        OrganizationMember(
            organization_id=workspace.organization_id,
            user_id=viewer_user.id,
            role="viewer",
        )
    )
    session.commit()
    endpoint = knowledge_url(owner)
    created = client.post(
        f"{endpoint}/documents",
        headers=bearer(owner),
        json={"title": "Readable", "source_type": "text", "content": "shared evidence"},
    )
    assert created.status_code == 201
    assert client.get(f"{endpoint}/documents", headers=bearer(viewer)).status_code == 200
    assert (
        client.post(
            f"{endpoint}/search",
            headers=bearer(viewer),
            json={"query": "shared evidence", "min_score": 0},
        ).status_code
        == 200
    )
    blocked = client.post(
        f"{endpoint}/documents",
        headers=bearer(viewer),
        json={"title": "Blocked", "source_type": "text", "content": "must not write"},
    )
    assert blocked.status_code == 403


def test_database_rejects_cross_workspace_knowledge_chunk(
    client: TestClient, session: Session
) -> None:
    alice = register_account(
        client,
        email="chunk-alice@example.com",
        organization_name="Chunk Alice",
        workspace_name="Core",
    )
    bob = register_account(
        client,
        email="chunk-bob@example.com",
        organization_name="Chunk Bob",
        workspace_name="Core",
    )
    endpoint = knowledge_url(alice)
    created = client.post(
        f"{endpoint}/documents",
        headers=bearer(alice),
        json={"title": "Scoped", "source_type": "text", "content": "tenant scoped evidence"},
    )
    document = session.get(KnowledgeDocument, uuid.UUID(created.json()["document"]["id"]))
    user = session.scalar(select(User).where(User.email == "chunk-alice@example.com"))
    assert document is not None and user is not None
    session.add(
        KnowledgeChunk(
            workspace_id=uuid.UUID(str(bob["workspace"]["id"])),  # type: ignore[index]
            document_id=document.id,
            chunk_index=99,
            content="must fail",
            start_offset=0,
            end_offset=9,
            token_count=2,
            embedding_model="test",
            embedding=[0.0] * 384,
        )
    )
    try:
        session.commit()
        raise AssertionError("Cross-workspace knowledge chunk was accepted")
    except IntegrityError:
        session.rollback()
