from winter.config import Settings
from winter.providers.base import Message, Provider, ProviderError
from winter.providers.mock import MockProvider

def build_provider(settings: Settings) -> Provider:
    """
    Turn validated Settings into the one Provider object the CLI will use.

    This is the ONLY place that knows which class goes with which provider name,
    so the CLI never imports a concrete provider.

    Raises ValidationError if the settings are invalid.
    """
    if settings.provider == "mock":
        return MockProvider()
    
    # "ollama" and "openrouter" are valid settings but have no adapter yet.
    # Week 3 replaces this line with real branches.
    raise ProviderError(f"The '{settings.provider}' provider is not implemented yet.")