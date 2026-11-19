# pytest gives us raises() to say "this call should fail".
import pytest

# The data types and the error family the wrapper cares about.
from winter.providers.base import (
    Message,
    Provider,
    ProviderError,
    ProviderSetupError,
    ProviderTemporaryError,
    ProviderUnavailableError,
    Reply,
)

# The class under test.
from winter.providers.retrying import RetryingProvider


# The "scripted phone": a fake provider that does exactly what the test tells it to.
class ScriptedProvider(Provider):
    # Satisfies the abstract `name` requirement.
    name = "scripted"

    # outcomes is the script: one item per call, each either a Reply to return
    # or an exception to raise.
    def __init__(self, outcomes: list[Reply | Exception]) -> None:
        # Copy the list so the test's own list is not changed.
        self._outcomes = list(outcomes)
        # Every conversation we were asked about; len(calls) = how many times we were "dialed".
        self.calls: list[list[Message]] = []

    def generate(self, messages: list[Message]) -> Reply:
        # Record this call (a copy, so later changes to the list can't rewrite history).
        self.calls.append(list(messages))
        # Take the next scripted outcome (pop(0) = the front of the queue).
        outcome = self._outcomes.pop(0)
        # If the script says "fail", raise the exception; otherwise return the reply.
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


# One tiny conversation reused by every test.
CONVERSATION = [Message("user", "hi")]


def test_success_on_first_try_makes_one_call():
    # Script: the first call works.
    inner = ScriptedProvider([Reply(text="ok")])
    # Wrap it and ask once.
    reply = RetryingProvider(inner).generate(CONVERSATION)
    # The answer arrives untouched...
    assert reply.text == "ok"
    # ...and the wrapper did not dial a second time for no reason.
    assert len(inner.calls) == 1


def test_temporary_error_is_retried_once_and_second_reply_is_returned():
    # Script: first call times out, second call works.
    inner = ScriptedProvider([ProviderTemporaryError("timeout"), Reply(text="ok")])
    reply = RetryingProvider(inner).generate(CONVERSATION)
    # The user gets the good answer and never sees the hiccup.
    assert reply.text == "ok"
    # Exactly two dials: the failure and the retry.
    assert len(inner.calls) == 2


def test_temporary_error_twice_is_raised_after_exactly_two_calls():
    # Script: both calls time out. A third script item proves we never reach a third call.
    inner = ScriptedProvider([
        ProviderTemporaryError("first"),
        ProviderTemporaryError("second"),
        Reply(text="should never be reached"),
    ])
    # The second failure must reach the caller (run_chat shows it to the user).
    with pytest.raises(ProviderTemporaryError, match="second"):
        RetryingProvider(inner).generate(CONVERSATION)
    # One retry only: 2 calls, not 3 (ADR 0010, bounded cost).
    assert len(inner.calls) == 2


# parametrize runs the test once per kind that must NEVER be retried.
# ProviderError itself (the plain parent) is included: unknown failures are not retried either.
@pytest.mark.parametrize(
    "error",
    [
        ProviderSetupError("bad config"),
        ProviderUnavailableError("server down"),
        ProviderError("something else"),
    ],
)
def test_non_temporary_errors_are_not_retried(error):
    # Script: a failure, then a reply that must stay unused.
    inner = ScriptedProvider([error, Reply(text="should never be reached")])
    # The ORIGINAL error comes straight out (the very same object).
    with pytest.raises(type(error)) as caught:
        RetryingProvider(inner).generate(CONVERSATION)
    assert caught.value is error
    # Only one call: no retry happened.
    assert len(inner.calls) == 1


def test_retry_sends_the_same_conversation_again():
    # Script: fail once, then succeed.
    inner = ScriptedProvider([ProviderTemporaryError("timeout"), Reply(text="ok")])
    RetryingProvider(inner).generate(CONVERSATION)
    # Asking again must repeat the SAME question, not a different or empty one.
    assert inner.calls[0] == inner.calls[1] == CONVERSATION


def test_name_comes_from_the_inner_provider():
    # The CLI banner must still say the real provider, not "retrying".
    assert RetryingProvider(ScriptedProvider([])).name == "scripted"


def test_wrapper_is_itself_a_provider():
    # Substitutability: anywhere a Provider is expected, the wrapper must fit.
    assert isinstance(RetryingProvider(ScriptedProvider([])), Provider)
