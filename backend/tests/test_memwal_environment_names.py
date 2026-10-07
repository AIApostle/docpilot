from client.config import ClientSettings


def test_memwal_environment_names_are_loaded_and_preferred(monkeypatch):
    monkeypatch.setenv("MEMWAL_PRIVATE_KEY", "live-private-key")
    monkeypatch.setenv("MEMWAL_ACCOUNT_ID", "live-account-id")
    monkeypatch.setenv("MEMWAL_SERVER_URL", "https://relayer.memory.walrus.xyz")
    monkeypatch.setenv("MEMWAL_VERIFY", "true")
    monkeypatch.setenv("WALRUS_DELEGATE_KEY", "legacy-private-key")
    monkeypatch.setenv("WALRUS_ACCOUNT_ID", "legacy-account-id")

    config = ClientSettings(_env_file=None)

    assert config.WALRUS_DELEGATE_KEY == "live-private-key"
    assert config.WALRUS_ACCOUNT_ID == "live-account-id"
    assert config.WALRUS_SERVER_URL == "https://relayer.memory.walrus.xyz"
    assert config.WALRUS_VERIFY is True


def test_production_relayer_url_selects_production_environment(monkeypatch):
    monkeypatch.setattr("client.config.settings.WALRUS_ENV", "dev")
    monkeypatch.setattr(
        "client.config.settings.WALRUS_SERVER_URL",
        "https://relayer.memory.walrus.xyz",
    )
    from client.walrus import _environment_for_server

    assert _environment_for_server(
        "https://relayer.memory.walrus.xyz",
        "dev",
    ) == "prod"