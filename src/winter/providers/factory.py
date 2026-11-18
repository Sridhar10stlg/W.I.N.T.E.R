# Settings is the validated configuration object (from config.py).
from winter.config import Settings

# Provider is the interface every backend follows.
# ProviderSetupError is the error for "your setup is wrong" (ADR 0009).
from winter.providers.base import Provider, ProviderSetupError

# The fake model, used when LOCAL_AI_PROVIDER=mock.
from winter.providers.mock import MockProvider


# The "waiter": it reads the order (settings.provider) and returns the right provider object.
def build_provider(settings: Settings) -> Provider:
    """Turn validated Settings into the one Provider object the CLI will use.

    This is the ONLY place that knows which class goes with which provider name,
    so the CLI never imports a concrete provider.

    Raises ProviderSetupError if the chosen provider has no adapter yet.
    """
    # If the order is "mock", the kitchen can cook it: build the fake model.
    if settings.provider == "mock":
        return MockProvider()

    # "ollama" and "openrouter" are on the menu (valid settings) but not cooked yet.
    # That is a SETUP problem, not a model failure, so we raise the setup error.
    # Week 3 replaces this line with real branches.
    raise ProviderSetupError(
        f"The '{settings.provider}' provider is not implemented yet. "
        "Set LOCAL_AI_PROVIDER=mock to run without a model."
    )
