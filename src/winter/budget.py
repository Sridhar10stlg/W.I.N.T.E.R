# Message is what the history is made of; we only read its .content here.
from winter.providers.base import Message

# Measured 2026-11-20 (ADR 0012): real text came to about 3.7 characters per token.
# We use 3 on purpose, so the estimate runs HIGH. Too high = we forget a little early.
# Too low = Ollama silently drops the start of the chat. High is the safe mistake.
CHARS_PER_TOKEN = 3

# Room kept free for the model's answer, because the window holds the question AND the reply.
# 512 tokens is roughly 380 words. Tunable later.
DEFAULT_REPLY_RESERVE_TOKENS = 512


def estimate_tokens(text: str) -> int:
    """Estimate how many tokens a piece of text uses, rounding UP (safe side)."""
    # Integer "round up" division: (n + d - 1) // d. No floats, so no rounding surprises.
    return (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN


def estimate_messages_tokens(messages: list[Message]) -> int:
    """Estimate the total tokens of a list of messages (message text only)."""
    # Add up the estimate of each message's text. An empty list gives 0.
    return sum(estimate_tokens(message.content) for message in messages)


def prompt_budget(
    context_tokens: int,                                   # the window size, e.g. 4096
    reply_reserve: int = DEFAULT_REPLY_RESERVE_TOKENS,     # space kept free for the answer
) -> int:
    """How many tokens the conversation (system prompt + history) may use."""
    # A negative reserve would make the budget bigger than the window: nonsense.
    if reply_reserve < 0:
        raise ValueError("The reply reserve cannot be negative.")
    # If the reserve eats the whole window, no conversation fits at all.
    if reply_reserve >= context_tokens:
        raise ValueError("The context window must be larger than the reply reserve.")
    # What is left after setting the answer's space aside.
    return context_tokens - reply_reserve


# When trimming triggers, cut down to this share of the budget, not just barely under it.
# Reason (ADR 0012, believed but not yet verified): Ollama reuses the already-read start of
# the conversation between turns, and every trim breaks that reuse. Trimming rarely and in
# chunks keeps most turns fast. Tunable later.
TRIM_TARGET_RATIO = 0.75


def trim_target(budget: int) -> int:
    """The size to trim DOWN to when the budget is exceeded (rounded down)."""
    # int() drops the fraction, which rounds down: the safe side again.
    return int(budget * TRIM_TARGET_RATIO)
