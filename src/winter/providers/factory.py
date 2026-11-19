# Settings is the validated configuration object (from config.py).
from winter.config import Settings

# Provider is the interface every backend follows.
# ProviderSetupError is the error for "your setup is wrong" (ADR 0009).
from winter.providers.base import Provider, ProviderSetupError

# The fake model, used when LOCAL_AI_PROVIDER=mock.
from winter.providers.mock import MockProvider

# the wrapper that retries ONE temporary failure (ADR 0010).
from winter.providers.retrying import RetryingProvider


# The "waiter": it reads the order (settings.provider) and returns the right provider object.
def build_provider(settings: Settings) -> Provider:
    """Turn validated Settings into the one Provider object the CLI will use.

    This is the ONLY place that knows which class goes with which provider name,
    so the CLI never imports a concrete provider. It is also the only place that
    adds the retry wrapper, so no provider can reach the CLI without it (ADR 0010).

    Raises ProviderSetupError if the chosen provider has no adapter yet.
    """
    # If the order is "mock", the kitchen can cook it: build the fake model.
    # We store it in `inner` (the bare provider) instead of returning it straight away.
    if settings.provider == "mock":
        inner: Provider = MockProvider()

    # "ollama" and "openrouter" are on the menu (valid settings) but not cooked yet.
    # That is a SETUP problem, not a model failure, so we raise the setup error.
    # Week 3 replaces this branch with real adapters, each one also assigned to `inner`.
    else:
        raise ProviderSetupError(
            f"The '{settings.provider}' provider is not implemented yet. "
            "Set LOCAL_AI_PROVIDER=mock to run without a model."
        )
        
    # Wrap the inner provider with the retrying wrapper and return it.
    return RetryingProvider(inner)
