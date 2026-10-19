from winter.providers.base import Message, Provider, ProviderError

class MockProvider(Provider):
    """A fake model, used in tests and to run the CLI with nothing installed."""
    # Satisfies the "name" requirement from the Provider interface.
    name = "mock"
    
    def __init__(
        self,
        replies: list[str] | None = None,
        error: ProviderError | None = None,
    ) -> None:
        # replies: canned answers handed out one by one. None means "just echo the user".
        self._replies = list(replies) if replies else None

        # error: if set, every call fails with this error. Used to test failure handling.
        self._error = error

        # A log of every conversation we were asked about, so tests can inspect what
        # the CLI actually sent.
        self.calls: list[list[Message]] = []
        
        
    def generate(self, messages: list[Message]) -> str:
        # Save a COPY of the list. The CLI keeps changing its own list afterwards, and
        # tests need to see what it looked like at the moment of the call.
        self.calls.append(list(messages))
        
        # Simulate a failing model when the test asked for it.
        if self._error is not None:
            raise self._error
        
        # If canned replies were given, hand out the next one.
        if self._replies:
            return self._replies.pop(0)                            
        
        # Default behavior: find the most recent user message and echo it back.
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return f"[mock] you said: {last_user}"      
