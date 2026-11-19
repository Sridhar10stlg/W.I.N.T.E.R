# pytest gives us raises() to say "this call should fail".
import pytest

# Settings builds a configuration object; _env_file=None ignores the real .env (see test_config.py).
from winter.config import Settings

# The things we expect build_provider to return or raise.
from winter.providers.base import Provider, ProviderSetupError
from winter.providers.factory import build_provider
from winter.providers.retrying import RetryingProvider

# A stand-in class for the real adapter in the "built from settings" test.
from winter.providers.mock import MockProvider



def test_mock_provider_comes_wrapped_in_retrying():
    # Ask the factory for the mock provider.
    provider = build_provider(Settings(_env_file=None, LOCAL_AI_PROVIDER="mock"))
    # The CLI must receive the wrapper, not the bare mock: this is the ADR 0010 promise.
    assert isinstance(provider, RetryingProvider)
    # And it is still a Provider, so the CLI accepts it.
    assert isinstance(provider, Provider)


def test_wrapped_provider_keeps_the_inner_name_and_still_answers():
    provider = build_provider(Settings(_env_file=None, LOCAL_AI_PROVIDER="mock"))
    # The banner must still say "mock", not "retrying".
    assert provider.name == "mock"
    # A call passes through the wrapper to the mock and comes back.
    from winter.providers.base import Message
    assert provider.generate([Message("user", "hi")]).text == "[mock] you said: hi"


def test_provider_without_adapter_raises_setup_error():
    # OpenRouter is valid but has no adapter yet; the key is a fake placeholder.
    settings = Settings(_env_file=None, LOCAL_AI_PROVIDER="openrouter", OPENROUTER_API_KEY="test-key-not-real")
    # A SETUP error (exit code 2 in main), not a crash or a silent fallback.
    with pytest.raises(ProviderSetupError, match="not implemented"):
        build_provider(settings)


def test_ollama_provider_is_built_from_settings_and_wrapped(monkeypatch):
    # Records what the factory passes to the adapter.
    captured = {}

    # A stand-in for OllamaProvider that remembers its arguments instead of connecting anywhere.
    class FakeOllama(MockProvider):
        def __init__(self, base_url, model, timeout_seconds):
            captured.update(base_url=base_url, model=model, timeout_seconds=timeout_seconds)
            super().__init__()

    # Swap the name the factory uses; monkeypatch undoes it after the test.
    monkeypatch.setattr("winter.providers.factory.OllamaProvider", FakeOllama)
    settings = Settings(
        _env_file=None,
        LOCAL_AI_PROVIDER="ollama",
        LOCAL_AI_MODEL_TIER="high",
        LOCAL_OLLAMA_URL="http://example:1234",
        LOCAL_AI_TIMEOUT_SECONDS=7,
    )
    provider = build_provider(settings)
    # The CLI receives the wrapper...
    assert isinstance(provider, RetryingProvider)
    # ...and the adapter got the address, the HIGH-tier model name, and the timeout from Settings.
    assert captured == {"base_url": "http://example:1234", "model": "gemma3:4b", "timeout_seconds": 7}


def test_bad_ollama_url_is_a_setup_error_at_build_time():
    # The real OllamaProvider validates its address when it is built.
    settings = Settings(_env_file=None, LOCAL_AI_PROVIDER="ollama", LOCAL_OLLAMA_URL="localhost:11434")
    with pytest.raises(ProviderSetupError, match="LOCAL_OLLAMA_URL"):
        build_provider(settings)

