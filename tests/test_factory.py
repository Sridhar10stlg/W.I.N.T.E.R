# pytest gives us raises() to say "this call should fail".
import pytest

# Settings builds a configuration object; _env_file=None ignores the real .env (see test_config.py).
from winter.config import Settings

# The things we expect build_provider to return or raise.
from winter.providers.base import Provider, ProviderSetupError
from winter.providers.factory import build_provider
from winter.providers.retrying import RetryingProvider


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


# Both providers that are valid settings but have no adapter yet.
@pytest.mark.parametrize("name", ["ollama"])
def test_provider_without_adapter_raises_setup_error(name):
    settings = Settings(_env_file=None, LOCAL_AI_PROVIDER=name)
    # A SETUP error (exit code 2 in main), not a crash or a silent fallback.
    with pytest.raises(ProviderSetupError, match="not implemented"):
        build_provider(settings)
