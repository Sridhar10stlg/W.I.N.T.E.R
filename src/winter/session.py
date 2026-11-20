# estimate_* give sizes in tokens; trim_target says how far to cut when trimming.
from winter.budget import estimate_messages_tokens, estimate_tokens, trim_target

# Message is one chat turn (role + content). Session stores and hands out Messages.
from winter.providers.base import Message

# Raised when the system prompt plus the newest message alone do not fit the window.
# This is a situation the USER can fix (send something shorter), not a bug in our code,
# so it is its own type and NOT a ValueError. Interfaces catch it and tell the user.
class ConversationTooLongError(Exception):
    """The newest message is too long to fit the model's context window."""


# The notepad with rules. Interfaces (CLI now, voice later) use this instead of their own lists.
class Session:
    """Owns one conversation: the system prompt and the user/assistant history (ADR 0012).

    Invariant: the history is always whole exchanges, in order: user, assistant, user,
    assistant... (it may end on a user message while the model has not answered yet).
    Breaking the order is a bug in OUR code, so it raises ValueError (a traceback is the
    right outcome: fail loud), not a friendly provider-style error.
    """

    def __init__(
        self,
        system_prompt: str | None = None,         # the standing rules, or None for no rules
        budget_tokens: int | None = None,         # max size of system prompt + history; None = never trim
    ) -> None:
        # The system prompt is optional, but if given it must contain real text.
        # (A blank prompt would send the model an empty rule page and hide a config mistake.)
        if system_prompt is not None and not system_prompt.strip():
            raise ValueError("The system prompt cannot be empty.")
        # A zero or negative budget could never hold anything: a setup mistake.
        if budget_tokens is not None and budget_tokens <= 0:
            raise ValueError("The token budget must be positive.")
        # Page one: the standing rules. Kept apart from the history on purpose.
        self._system_prompt = system_prompt
        # How big the conversation may get before trim() cuts it down.
        self._budget_tokens = budget_tokens
        # The user/assistant messages only, oldest first. The leading underscore means
        # "private": outside code must use the methods, which protect the order rule.
        self._history: list[Message] = []


    def add_user(self, text: str) -> None:
        """Record what the user said. Only allowed at the start or after an assistant reply."""
        # Two user messages in a row would break the question-and-answer pairing.
        if self._history and self._history[-1].role == "user":
            raise ValueError("The last message is already a user message; wait for the reply.")
        # Messages are frozen (read-only), so storing one cannot be undone by accident.
        self._history.append(Message("user", text))

    def add_assistant(self, text: str) -> None:
        """Record the model's reply. Only allowed right after a user message."""
        # A reply needs a question: it cannot be first, and it cannot follow another reply.
        if not self._history or self._history[-1].role != "user":
            raise ValueError("An assistant reply must follow a user message.")
        self._history.append(Message("assistant", text))

    def discard_last_user(self) -> None:
        """Cross out the last user message because the model never answered it.

        Replaces the history.pop() that run_chat does today, with a safety check.
        """
        # Only an UNANSWERED user message may be removed; removing anything else would
        # tear a hole in the middle of the conversation.
        if not self._history or self._history[-1].role != "user":
            raise ValueError("There is no unanswered user message to discard.")
        # list.pop() removes the LAST item, exactly what we want.
        self._history.pop()

    def messages_for_model(self) -> list[Message]:
        """Return a fresh list to send to a provider: system prompt first, then the history."""
        # Start with an empty list so the caller always gets a NEW list (a photocopy).
        messages: list[Message] = []
        # Page one goes first, when there is one.
        if self._system_prompt is not None:
            messages.append(Message("system", self._system_prompt))
        # Then the conversation so far, oldest first. extend() copies the items across.
        messages.extend(self._history)
        # The caller may change this list freely; the session's own history is unaffected.
        return messages
    
    def trim(self) -> int:
        """Drop the oldest whole exchanges if the conversation is over budget (ADR 0012).

        Call it after add_user() and before messages_for_model(). Returns how many
        messages were dropped (0 = nothing), so the interface can tell the user.
        Raises ConversationTooLongError if even the system prompt plus the newest
        exchange do not fit; the history is left unchanged in that case.
        """
        # No budget configured: never trim.
        if self._budget_tokens is None:
            return 0

        # Cost of the standing rules, which always travel with every request.
        system_tokens = estimate_tokens(self._system_prompt) if self._system_prompt is not None else 0
        # Group the history into exchanges (user + assistant); the last one may be a lone,
        # unanswered user message. The turn-taking rule guarantees this pairing is valid.
        exchanges = [self._history[i:i + 2] for i in range(0, len(self._history), 2)]
        # The estimated size of each exchange, oldest first.
        sizes = [estimate_messages_tokens(exchange) for exchange in exchanges]

        # Everything fits already: nothing to do.
        if system_tokens + sum(sizes) <= self._budget_tokens:
            return 0

        # Priority 1 and 2: the system prompt and the newest exchange are never dropped.
        used = system_tokens + sizes[-1]
        # If even those do not fit, the user's message is too long: say so, change nothing.
        if used > self._budget_tokens:
            raise ConversationTooLongError(
                "That message is too long for the model's context window. Please send a shorter one."
            )

        # Trim DOWN to about 75% of the budget, not just under it (fewer trims overall).
        target = trim_target(self._budget_tokens)
        # The set of exchange positions we keep; the newest (last) one is already in.
        keep = {len(exchanges) - 1}

        # Priority 3: the first exchange, but only if there is room under the target.
        if len(exchanges) > 1 and used + sizes[0] <= target:
            keep.add(0)
            used += sizes[0]

        # Priority 4: recent exchanges, newest first, down to (not including) the first one.
        for i in range(len(exchanges) - 2, 0, -1):
            # Stop at the first one that does not fit: the kept block must stay contiguous.
            if used + sizes[i] > target:
                break
            keep.add(i)
            used += sizes[i]

        # Priority 5: everything else is dropped. Rebuild the history from the kept exchanges,
        # in their original order (this only changes the stored list AFTER all checks passed).
        kept = [message for i, exchange in enumerate(exchanges) if i in keep for message in exchange]
        dropped = len(self._history) - len(kept)
        self._history = kept
        # The caller uses this number to show a visible note.
        return dropped

