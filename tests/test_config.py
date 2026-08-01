from app.core.config import Settings


def test_local_env_keeps_empty_root_path_by_default():
    settings = Settings(app_env="local")

    assert settings.is_local is True
    assert settings.is_prod is False
    assert settings.root_path == ""


def test_prod_env_sets_root_path_when_not_explicitly_configured():
    settings = Settings(app_env="prod")

    assert settings.is_prod is True
    assert settings.is_local is False
    assert settings.root_path == "/ai"


def test_explicit_root_path_overrides_prod_default():
    settings = Settings(app_env="prod", root_path="/custom")

    assert settings.is_prod is True
    assert settings.root_path == "/custom"
