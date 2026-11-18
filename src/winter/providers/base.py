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

# Why the model stopped, in W.I.N.T.E.R's OWN words. Each adapter translates its vendor's
# names (Ollama, OpenRouter) into one of these, so vendor words never leak past the adapter.
# "complete" = finished normally, "length" = hit the length limit (reply is cut off),
# "other" = anything the adapter can't map.
StopReason = Literal["complete", "length", "other"]


# frozen=True makes a Message read-only after creation, so it can't be changed by accident
# while it is stored in the conversation history.
@dataclass(frozen=True)
class Message:
    """One chat message: who said it, and what they said."""
    role: Role
    content: str


@dataclass(frozen=True)
class Usage:
    """Token counts for one model call. Needed for cost tracking in Month 2."""
    # Tokens the model read (the conversation we sent).
    input_tokens: int
    # Tokens the model wrote (its reply).
    output_tokens: int

    # __post_init__ runs right after the generated __init__. We use it to validate.
    def __post_init__(self) -> None:
        # A negative count means an adapter bug; fail loudly instead of storing nonsense.
        if self.input_tokens < 0 or self.output_tokens < 0:
            raise ValueError("Token counts cannot be negative.")


@dataclass(frozen=True)
class Reply:
    """What a provider returns for one call (ADR 0008).

    It grows by ADDING optional fields (tool calls in Month 3), so code that uses it
    never breaks when a field is added.
    """
    # The model's answer. UNTRUSTED: it came from the model.
    text: str
    # Why the model stopped. None = the provider didn't say (the mock, for example).
    stop_reason: StopReason | None = None
    # Token counts. None = the provider didn't report them.
    usage: Usage | None = None

    # A property is read like a field (reply.was_cut_off) but computed on the fly.
    @property
    def was_cut_off(self) -> bool:
        """True when the reply stopped because it hit the length limit."""
        return self.stop_reason == "length"


# ProviderError is the PARENT of every provider failure. Code that only wants to know
# "did the provider fail?" catches this one type (run_chat does exactly that).
# The three subclasses below add WHAT THE CALLER SHOULD DO about it (ADR 0009).
class ProviderError(Exception):
    """Base class for every provider failure.

    Each real provider (Ollama, OpenRouter) catches its own low-level problems
    (connection refused, timeout, bad key...) and re-raises them as one of the three
    subclasses below, with a friendly message. That keeps provider-specific details
    out of the CLI.

    Message rules (every provider error): say what happened and how to fix it; never
    include a raw server response (untrusted data); never include any part of a secret,
    not even a prefix; strip credentials from URLs before printing them.
    """


# Caller action: "trying again may help". A bounded retry is allowed (ADR 0010).
class ProviderTemporaryError(ProviderError):
    """A failure that may go away on its own: a timeout or a rate limit."""


# Caller action: "tell the user to start or check something". Retrying won't help yet.
class ProviderUnavailableError(ProviderError):
    """The provider can't be reached right now: Ollama not running, no network."""


# Caller action: "tell the user to fix their configuration". NEVER retried.
class ProviderSetupError(ProviderError):
    """Something in the setup is wrong: model not found, missing or rejected key,
    or a provider that has no adapter yet."""



class Provider(ABC):
    """The narrow interface every model backend must follow."""

    # A short label shown in the CLI banner, e.g. "mock" or "ollama".
    # Declared as an abstract property so a subclass that forgets to define `name`
    # cannot even be created (TypeError at construction, not AttributeError mid-chat).
    # A subclass satisfies it with a plain class attribute: name = "mock".
    @property
    @abstractmethod
    def name(self) -> str:
        """Short label for this provider."""

    # Because this is abstract, Python refuses to create a Provider that forgets to implement generate().
    # The mistake shows up immediately, not mid-conversation.
    @abstractmethod
    def generate(self, messages: list[Message]) -> Reply:
        """Take the whole conversation so far and return the assistant's next Reply.

        Must raise ProviderError on any failure.
        """
