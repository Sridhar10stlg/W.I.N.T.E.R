# pytest gives us raises() and parametrize.
import pytest

# The functions and constants under test, and Message to build sample conversations.
from winter.budget import (
    DEFAULT_REPLY_RESERVE_TOKENS,
    estimate_messages_tokens,
    estimate_tokens,
    prompt_budget,
)
from winter.providers.base import Message


# (characters, expected tokens): the rounding-up rule at the edges, with 3 chars per token.
@pytest.mark.parametrize(
    "chars, expected",
    [(0, 0), (1, 1), (3, 1), (4, 2), (6, 2), (7, 3)],
)
def test_estimate_rounds_up(chars, expected):
    # "x" * n makes a text of exactly n characters.
    assert estimate_tokens("x" * chars) == expected


def test_estimate_never_undercounts_the_measured_experiment():
    # Experiment (a), 2026-11-20: 27,640 characters came to 7,426 REAL tokens.
    # Our estimate must never be below the real count, or silent truncation could return.
    assert estimate_tokens("x" * 27_640) >= 7_426


def test_message_estimate_adds_up_each_messages_text():
    messages = [Message("user", "x" * 6), Message("assistant", "x" * 7)]
    # 6 chars -> 2 tokens, 7 chars -> 3 tokens.
    assert estimate_messages_tokens(messages) == 5


def test_message_estimate_of_nothing_is_zero():
    assert estimate_messages_tokens([]) == 0


def test_budget_leaves_room_for_the_reply():
    # 4096 window minus the default 512 reserve.
    assert prompt_budget(4096) == 4096 - DEFAULT_REPLY_RESERVE_TOKENS == 3584


def test_budget_accepts_a_custom_reserve():
    assert prompt_budget(8192, reply_reserve=1000) == 7192


def test_budget_refuses_a_reserve_as_big_as_the_window():
    # Nothing would be left for the conversation: refuse instead of returning 0 or less.
    with pytest.raises(ValueError, match="larger than the reply reserve"):
        prompt_budget(512)


def test_budget_refuses_a_negative_reserve():
    with pytest.raises(ValueError, match="cannot be negative"):
        prompt_budget(4096, reply_reserve=-1)
