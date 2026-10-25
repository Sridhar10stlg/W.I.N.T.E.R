import dataclasses

import pytest

from winter.providers.base import Message, Provider, ProviderError
from winter.providers.mock import MockProvider


def test_message_is_frozen():
    # frozen=True: assigning to a field must fail, so history can't be edited by accident.
    m = Message("user", "hi")
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.content = "changed"  # type: ignore[misc]


def test_provider_without_name_cannot_be_created():
    # A provider that forgets `name` must fail at construction, not mid-conversation.
    class NoName(Provider):
        def generate(self, messages: list[Message]) -> str:
            return "x"

    with pytest.raises(TypeError):
        NoName()


def test_mock_echoes_last_user_message():
    p = MockProvider()
    msgs = [Message("user", "first"), Message("assistant", "ok"), Message("user", "second")]
    assert p.generate(msgs) == "[mock] you said: second"


def test_mock_canned_replies_come_in_order_then_error():
    p = MockProvider(replies=["one", "two"])
    msgs = [Message("user", "hi")]
    assert p.generate(msgs) == "one"
    assert p.generate(msgs) == "two"
    # Out of replies: must fail loudly, not fall back to echo.
    with pytest.raises(ProviderError):
        p.generate(msgs)


def test_mock_empty_replies_list_is_not_echo():
    # Regression test for the replies=[] vs None bug.
    p = MockProvider(replies=[])
    with pytest.raises(ProviderError):
        p.generate([Message("user", "hi")])


def test_mock_raises_injected_error():
    p = MockProvider(error=ProviderError("boom"))
    with pytest.raises(ProviderError, match="boom"):
        p.generate([Message("user", "hi")])


def test_mock_records_a_snapshot_of_each_call():
    p = MockProvider()
    msgs = [Message("user", "hi")]
    p.generate(msgs)
    # The caller keeps growing its own list afterwards...
    msgs.append(Message("assistant", "later"))
    # ...but the recorded call must still show the list as it was at call time.
    assert len(p.calls[0]) == 1
