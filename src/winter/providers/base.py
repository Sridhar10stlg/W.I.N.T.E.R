# ABC = "Abstract Base Class". It lets us define a class that other classes MUST follow.
# abstractmethod marks a method that every subclass is required to implement.
from abc import ABC, abstractmethod

# dataclass writes boring boilerplate for us (__init__, __repr__, __eq__) for simple data holders.
from dataclasses import dataclass

# Literal restricts a value to a fixed set of allowed strings.
from typing import Literal 

# The three speakers in a chat. "system" sets the assistant's behavior, "user" is you,
# "assistant" is the model. Every major model API uses these same three role names.
Role = Literal["system", "user", "assistant"]

# frozen=True makes a Message read-only after creation, so it can't be changed by accident
# while it is stored in the conversation history.
@dataclass(frozen=True)
class Message:
    """One chat message: who said it, and what they said."""
    role: Role
    content: str
    
class ProviderError(Exception):
    """The ONLY error type the rest of the app needs to handle from a provider.

    Each real provider (Ollama, OpenRouter) will catch its own low-level problems
    (connection refused, timeout, bad key...) and re-raise them as ProviderError with a
    friendly message. That keeps provider-specific details out of the CLI.
    """
    
class Provider(ABC):
    """The narrow interface every model backend must follow."""

    # A short label shown in the CLI banner, e.g. "mock" or "ollama".
    name: str

    # Because this is abstract, Python refuses to create a Provider that forgets to implement generate(). 
    # The mistake shows up immediately, not mid-conversation.
    @abstractmethod
    def generate(self, messages: list[Message]) -> str:
        """Take the whole conversation so far and return the assistant's next reply.

        Must raise ProviderError on any failure.
        """
    
