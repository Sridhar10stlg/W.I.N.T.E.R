# dataclasses gives us FrozenInstanceError, the error raised when you try to edit a frozen object.
import dataclasses

# pytest gives us raises(), the helper for "this code SHOULD fail".
import pytest

# The pieces under test: the message type, the abstract interface, and the error type.
from winter.providers.base import Message, Provider, ProviderError

# The fake model under test.
from winter.providers.mock import MockProvider


# Test 1: a Message must be read-only after creation.
def test_message_is_frozen():
    # Build one message.
    m = Message("user", "hi")
    # Editing a field of a frozen dataclass must raise FrozenInstanceError.
    with pytest.raises(dataclasses.FrozenInstanceError):
        # The comment tells type checkers "yes, I know this is illegal, that's the point".
        m.content = "changed"  # type: ignore[misc]


# Test 2: a provider that forgets `name` must fail when created (this checks Block A).
def test_provider_without_name_cannot_be_created():
    # Define a throwaway provider that implements generate() but NOT name.
    class NoName(Provider):
        # generate() is implemented, so only the missing name should block creation.
        def generate(self, messages: list[Message]) -> str:
            # Any reply will do; it is never called.
            return "x"

    # Python refuses to create a class that still has an abstract member: TypeError.
    with pytest.raises(TypeError):
        NoName()


# Test 3: with no canned replies, the mock echoes the latest user message.
def test_mock_echoes_last_user_message():
    # A mock with default settings = echo mode.
    p = MockProvider()
    # A short conversation; the LAST user message is "second".
    msgs = [Message("user", "first"), Message("assistant", "ok"), Message("user", "second")]
    # The echo must use "second", not "first".
    assert p.generate(msgs) == "[mock] you said: second"


# Test 4: canned replies come out in order, and running out is an error (checks Block B).
def test_mock_canned_replies_come_in_order_then_error():
    # Two canned replies.
    p = MockProvider(replies=["one", "two"])
    # One user message is enough to ask with.
    msgs = [Message("user", "hi")]
    # First call gets the first reply...
    assert p.generate(msgs) == "one"
    # ...second call gets the second.
    assert p.generate(msgs) == "two"
    # A third call has nothing left: it must fail loudly, not quietly fall back to echo.
    with pytest.raises(ProviderError):
        p.generate(msgs)


# Test 5: an empty list of replies is NOT the same as "no replies given" (checks Block B).
def test_mock_empty_replies_list_is_not_echo():
    # [] means canned mode with nothing in it. Before the fix this silently echoed.
    p = MockProvider(replies=[])
    # So the very first call must fail.
    with pytest.raises(ProviderError):
        p.generate([Message("user", "hi")])


# Test 6: an injected error is raised, with its message intact.
def test_mock_raises_injected_error():
    # Build a mock that always fails with this error.
    p = MockProvider(error=ProviderError("boom"))
    # match="boom" checks that the error message contains that text.
    with pytest.raises(ProviderError, match="boom"):
        p.generate([Message("user", "hi")])


# Test 7: the mock records what it was asked, as a snapshot taken at call time.
def test_mock_records_a_snapshot_of_each_call():
    # Default mock; we only care about its call log.
    p = MockProvider()
    # The caller's list, holding one message.
    msgs = [Message("user", "hi")]
    # Make one call.
    p.generate(msgs)
    # The caller keeps growing its own list afterwards, like the CLI does...
    msgs.append(Message("assistant", "later"))
    # ...but the recorded call must still show ONE message: the list as it was then.
    assert len(p.calls[0]) == 1
