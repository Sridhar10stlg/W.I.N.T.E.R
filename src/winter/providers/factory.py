# Settings is the validated configuration object (from config.py).
from winter.config import Settings

# Provider is the interface every backend follows.
# ProviderSetupError is the error for "your setup is wrong" (ADR 0009).
from winter.providers.base import Provider, ProviderSetupError

# The fake model, used when LOCAL_AI_PROVIDER=mock.
from winter.providers.mock import MockProvider

# The real adapter for a local Ollama server.
from winter.providers.ollama import OllamaProvider

# the wrapper that retries ONE temporary failure (ADR 0010).
from winter.providers.retrying import RetryingProvider

# The "waiter": it reads the order (settings.provider) and returns the right provider object.
def build_provider(settings: Settings) -> Provider:
    """Turn validated Settings into the one Provider object the CLI will use.

    This is the ONLY place that knows which class goes with which provider name,
    so the CLI never imports a concrete provider. It is also the only place that
    adds the retry wrapper, so no provider can reach the CLI without it (ADR 0010).

    Raises ProviderSetupError if the chosen provider cannot be built: no adapter yet,
    or a bad address in LOCAL_OLLAMA_URL.
    """
    # The fake model: nothing to install, used for tests and demos.
    if settings.provider == "mock":
        inner: Provider = MockProvider()
    # The real local model. Everything it needs comes from validated Settings:
    # the address, the model chosen by LOCAL_AI_MODEL_TIER, and the timeout.
    # A bad address raises ProviderSetupError right here, at startup.
    elif settings.provider == "ollama":
        inner = OllamaProvider(
            base_url=settings.ollama_url,
            model=settings.model,
            timeout_seconds=settings.timeout_seconds,
        )
    # "openrouter" is a valid setting but has no adapter yet. That is a SETUP problem,
    # not a model failure, so we raise the setup error.
    else:
        raise ProviderSetupError(
            f"The '{settings.provider}' provider is not implemented yet. "
            "Set LOCAL_AI_PROVIDER=ollama (or mock to run without a model)."
        )

    # Every branch above ends here: put the bare provider in its "phone case" and hand it over.
    return RetryingProvider(inner)
