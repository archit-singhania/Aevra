import pytest
from pydantic import ValidationError

from aevra_api.config import Settings


def test_production_rejects_default_secret() -> None:
    with pytest.raises(ValidationError, match="AEVRA_SECRET_KEY must be changed"):
        Settings(env="production")


def test_production_accepts_explicit_strong_secret() -> None:
    settings = Settings(
        env="production",
        secret_key="production-test-secret-with-at-least-thirty-two-characters",
    )
    assert settings.env == "production"
