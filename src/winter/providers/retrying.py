# Message and Reply are the data types the Provider interface speaks.
# Provider is the interface we implement: the wrapper must look like any other provider.
# ProviderTemporaryError is the ONLY failure kind this wrapper retries (ADR 0009 and 0010).
from winter.providers.base import Message, Provider, ProviderTemporaryError, Reply


# The wrapper IS a Provider (so the CLI can't tell the difference) and it HAS a Provider inside.
class RetryingProvider(Provider):
    """Wraps another provider and retries ONE time when the failure is temporary.

    This is the single place where retrying happens. Adapters and the CLI never retry,
    so one question can never turn into many calls (ADR 0010).
    """

    # inner is the real provider (Ollama, OpenRouter, mock...) that does the work.
    def __init__(self, inner: Provider) -> None:
        # Keep the wrapped provider. The leading underscore means "internal, don't touch".
        self._inner = inner

    # Satisfies the abstract `name` property: report the inner provider's name,
    # so the banner still says "ollama", not "retrying".
    @property
    def name(self) -> str:
        # Delegate: ask the provider we wrap.
        return self._inner.name

    # Same signature as Provider.generate, so it can replace any provider anywhere.
    def generate(self, messages: list[Message]) -> Reply:
        # First attempt.
        try:
            return self._inner.generate(messages)
        # Only a TEMPORARY failure (timeout, rate limit) is worth another try.
        # Setup and Unavailable errors are NOT caught here, so they pass straight through.
        except ProviderTemporaryError:
            # Second and last attempt. If it fails too, its error is NOT caught:
            # it travels up to run_chat, which shows it to the user.
            return self._inner.generate(messages)
