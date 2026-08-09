from unittest.mock import Mock

from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.valkey_client import ValkeyClient


def test_connect_skips_when_host_is_not_configured(monkeypatch):
    monkeypatch.setattr("app.core.valkey_client.settings.valkey_host", None)
    redis_constructor = Mock()
    monkeypatch.setattr("app.core.valkey_client.Redis", redis_constructor)
    client = ValkeyClient()

    client.connect()

    redis_constructor.assert_not_called()
    assert client.client is None


def test_connect_uses_tls_configuration(monkeypatch):
    monkeypatch.setattr("app.core.valkey_client.settings.valkey_host", "valkey.example")
    monkeypatch.setattr("app.core.valkey_client.settings.app_env", "prod")
    redis = Mock()
    redis_constructor = Mock(return_value=redis)
    monkeypatch.setattr("app.core.valkey_client.Redis", redis_constructor)
    client = ValkeyClient()

    client.connect()

    redis.ping.assert_called_once_with()
    assert redis_constructor.call_args.kwargs["ssl"] is True
    assert redis_constructor.call_args.kwargs["ssl_ca_certs"] == (
        "/etc/ssl/certs/ca-certificates.crt"
    )
    assert client.client is redis


def test_connect_fails_open_when_valkey_is_unavailable(monkeypatch):
    monkeypatch.setattr("app.core.valkey_client.settings.valkey_host", "valkey.example")
    redis = Mock()
    redis.ping.side_effect = RedisConnectionError("unavailable")
    monkeypatch.setattr("app.core.valkey_client.Redis", Mock(return_value=redis))
    client = ValkeyClient()

    client.connect()

    redis.close.assert_called_once_with()
    assert client.client is None


def test_close_releases_connected_client(monkeypatch):
    monkeypatch.setattr("app.core.valkey_client.settings.valkey_host", "valkey.example")
    redis = Mock()
    monkeypatch.setattr("app.core.valkey_client.Redis", Mock(return_value=redis))
    client = ValkeyClient()
    client.connect()

    client.close()

    redis.close.assert_called_once_with()
    assert client.client is None
