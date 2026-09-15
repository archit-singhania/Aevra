from aevra_api.config import get_settings
from aevra_api.db.session import SessionLocal
from aevra_api.repositories.brands import BrandRepository
from aevra_api.schemas.brands import BrandCreateRequest, BrandRuleCreateRequest
from aevra_api.schemas.tenancy import RegisterRequest
from aevra_api.services.brands import BrandService
from aevra_api.services.tenancy import TenancyService


def seed() -> None:
    settings = get_settings()
    with SessionLocal() as session:
        service = TenancyService(session)
        user = service.repository.get_user_by_email(settings.seed_email)
        if user is None:
            result = service.register(
                RegisterRequest(
                    email=settings.seed_email,
                    password=settings.seed_password,
                    display_name="Aevra Owner",
                    organization_name="Aevra Demo",
                    workspace_name="Core workspace",
                    timezone="Asia/Kolkata",
                )
            )
            user = result.user
            workspace = result.workspace
        else:
            workspaces = service.list_workspaces(user.id)
            if not workspaces:
                raise RuntimeError("Seed user exists without an accessible workspace")
            workspace = workspaces[0]

        brand_repository = BrandRepository(session)
        brand = brand_repository.get_brand_by_slug_for_user(user.id, workspace.id, "aevra")
        if brand is None:
            brand_service = BrandService(session)
            brand = brand_service.create_brand(
                user.id,
                workspace.id,
                BrandCreateRequest(
                    name="Aevra",
                    description="Agentic content intelligence grounded in brand evidence.",
                    industry="AI marketing infrastructure",
                    tone_attributes=["precise", "confident", "evidence-led"],
                    target_audiences=["marketing teams", "engineering leaders"],
                    preferred_ctas=["Explore the evidence"],
                    preferred_hashtags=["#AgenticAI", "#RAG", "#Aevra"],
                    status="active",
                ),
            )
            brand_service.create_rule(
                user.id,
                workspace.id,
                brand.id,
                BrandRuleCreateRequest(
                    category="claim",
                    enforcement="prohibited",
                    directive="Never present unverified performance claims as facts.",
                    priority=95,
                ),
            )

        print(f"Seed ready: {workspace.name} / {brand.name} for {user.email}")


if __name__ == "__main__":
    seed()
