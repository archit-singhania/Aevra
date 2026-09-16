import pytest

from aevra_api.token_vault import LocalTokenVault, TokenVaultError


def test_local_token_vault_round_trip_and_tamper_detection() -> None:
    vault = LocalTokenVault("local-development-master-key-with-32-bytes")
    envelope = vault.encrypt("provider-secret")
    assert envelope != "provider-secret"
    assert vault.decrypt(envelope) == "provider-secret"
    with pytest.raises(TokenVaultError, match="authentication|envelope"):
        vault.decrypt(envelope[:-2] + "aa")
