# Message is one chat turn (role + content). Session stores and hands out Messages.
from winter.providers.base import Message


# The notepad with rules. Interfaces (CLI now, voice later) use this instead of their own lists.
class Session:
    """Owns one conversation: the system prompt and the user/assistant history (ADR 0012).

    Invariant: the history is always whole exchanges, in order: user, assistant, user,
    assistant... (it may end on a user message while the model has not answered yet).
    Breaking the order is a bug in OUR code, so it raises ValueError (a traceback is the
    right outcome: fail loud), not a friendly provider-style error.
    """

    def __init__(self, system_prompt: str | None = None) -> None:
        # The system prompt is optional, but if given it must contain real text.
        # (A blank prompt would send the model an empty rule page and hide a config mistake.)
        if system_prompt is not None and not system_prompt.strip():
            raise ValueError("The system prompt cannot be empty.")
        # Page one: the standing rules. Kept apart from the history on purpose.
        self._system_prompt = system_prompt
        # The user/assistant messages only, oldest first. The leading underscore means
        # "private": outside code must use the methods below, which protect the order rule.
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
