# pytest gives us raises() ("this should fail") and parametrize (one test, many inputs).
import pytest

# estimate_messages_tokens and trim_target are what Session.trim() itself uses; the tests
# use them to check the final size against the same rules.
from winter.budget import estimate_messages_tokens, trim_target

# The class under test and its special error.
from winter.session import ConversationTooLongError, Session


# A text that our estimate counts as EXACTLY `tokens` tokens (3 characters each) and that
# starts with a short tag, so a test can see which message is which.
def words(tokens, tag):
    return tag + "x" * (3 * tokens - len(tag))


# Build a session of known size. With the defaults the size is:
#   system prompt 10 + 9 exchanges x 20 + one unanswered question 10 = 200 tokens.
# Tags: the system prompt is "SS", questions are q0, q1, ..., answers are a0, a1, ...
def make_session(budget, system_tokens=10, exchanges=9, per_message=10, unanswered=True):
    session = Session(words(system_tokens, "SS"), budget_tokens=budget)
    for i in range(exchanges):
        session.add_user(words(per_message, f"q{i}"))
        session.add_assistant(words(per_message, f"a{i}"))
    # The newest question, which the model has not answered yet (the usual moment to trim).
    if unanswered:
        session.add_user(words(per_message, f"q{exchanges}"))
    return session


# The two-letter tag of every message that would be sent, in order. Makes expectations readable.
def tags(session):
    return [message.content[:2] for message in session.messages_for_model()]


# The invariant after ANY trim: system prompt first, then strict user/assistant turns, and each
# kept answer belongs to the question just before it (same number in the tag).
def assert_valid(session):
    messages = session.messages_for_model()
    assert messages[0].role == "system"
    body = messages[1:]
    for position, message in enumerate(body):
        assert message.role == ("user" if position % 2 == 0 else "assistant")
        if message.role == "assistant":
            assert message.content[1:2] == body[position - 1].content[1:2]


# --- when NOT to trim -----------------------------------------------------------------------

def test_without_a_budget_nothing_is_ever_trimmed():
    session = make_session(budget=None, exchanges=50, unanswered=False)
    # 0 dropped, and all 100 messages plus the system prompt are still there.
    assert session.trim() == 0
    assert len(tags(session)) == 101


def test_a_conversation_that_fits_is_left_alone():
    session = make_session(budget=1000)
    before = tags(session)
    assert session.trim() == 0
    assert tags(session) == before


def test_exactly_at_the_budget_is_not_trimmed():
    # Total is 200 tokens (10 + 9 x 20 + 10). A budget of 200 is "full but allowed".
    assert make_session(budget=200).trim() == 0


# --- how trimming works ---------------------------------------------------------------------------

def test_one_token_over_the_budget_trims_and_stops_at_75_percent():
    # Budget 199, so the target is int(199 x 0.75) = 149.
    # Kept first: system 10 + newest question 10 = 20. Then the first exchange: 40.
    # Then recent exchanges, 20 each: 60, 80, 100, 120, 140. One more would be 160 > 149: stop.
    # Kept: q0/a0 (first), q4..q8 (recent), q9 (newest). Dropped: exchanges 1, 2, 3 = 6 messages.
    session = make_session(budget=199)
    assert session.trim() == 6
    assert tags(session) == ["SS", "q0", "a0", "q4", "a4", "q5", "a5", "q6", "a6", "q7", "a7", "q8", "a8", "q9"]


def test_trimming_keeps_the_system_prompt_first_exchange_recent_exchange_and_newest_question():
    # Budget 100, target 75. Used: 10 + 10 = 20, first exchange 40, q8/a8 60, next would be 80 > 75.
    session = make_session(budget=100)
    # 14 messages dropped (exchanges 1 to 7), in whole pairs from the middle.
    assert session.trim() == 14
    assert tags(session) == ["SS", "q0", "a0", "q8", "a8", "q9"]
    assert_valid(session)


def test_trimming_goes_down_to_the_target_not_just_under_the_budget():
    # Budget 45: the first exchange WOULD fit under the budget (20 + 20 = 40 <= 45) ...
    # ... but the target is int(45 x 0.75) = 33, and 40 > 33, so it is dropped.
    session = make_session(budget=45)
    session.trim()
    assert tags(session) == ["SS", "q9"]


def test_when_only_the_system_prompt_and_newest_question_fit_those_two_remain():
    # Budget 20 is exactly system (10) + newest question (10): the bare minimum.
    session = make_session(budget=20)
    assert session.trim() == 18
    assert tags(session) == ["SS", "q9"]


def test_the_newest_exchange_is_protected_even_when_it_is_already_answered():
    # No unanswered question this time: the newest exchange is q8/a8.
    # Budget 100, target 75: used 30 (system + q8/a8), first exchange 50, q7/a7 70, next 90 > 75.
    session = make_session(budget=100, unanswered=False)
    assert session.trim() == 12
    assert tags(session) == ["SS", "q0", "a0", "q7", "a7", "q8", "a8"]


def test_the_result_is_at_or_below_75_percent_of_the_budget():
    session = make_session(budget=100)
    session.trim()
    # Kept: 10 + 20 + 20 + 10 = 60 tokens, under trim_target(100) = 75.
    assert estimate_messages_tokens(session.messages_for_model()) <= trim_target(100)


def test_after_a_trim_there_is_headroom_so_the_next_turn_does_not_trim_again():
    session = make_session(budget=100)
    session.trim()                                   # leaves 60 tokens
    session.add_assistant(words(10, "a9"))           # 70
    session.add_user(words(10, "q10"))               # 80, still under the budget of 100
    assert session.trim() == 0


def test_trimming_twice_in_a_row_changes_nothing_the_second_time():
    session = make_session(budget=100)
    assert session.trim() == 14
    assert session.trim() == 0


# For many budgets from "bare minimum" to "almost everything fits", the conversation that is
# left must always be valid and within budget. (A loop over inputs finds edge cases by luck
# we would not have.)
@pytest.mark.parametrize("budget", [20, 25, 33, 45, 60, 99, 100, 150, 199])
def test_after_trimming_the_conversation_is_valid_and_within_budget(budget):
    session = make_session(budget=budget)
    session.trim()
    # System prompt first, strict turns, answers match their questions.
    assert_valid(session)
    # Never over budget.
    assert estimate_messages_tokens(session.messages_for_model()) <= budget
    # The system prompt and the newest question are always there.
    assert tags(session)[0] == "SS"
    assert tags(session)[-1] == "q9"


# --- when the message itself is too long ---------------------------------------------------------

# Budget 15 cannot hold even the system prompt (10) plus the newest question (10).
# With 0 earlier exchanges the question is alone; with 3 there is history behind it.
@pytest.mark.parametrize("exchanges", [0, 3])
def test_a_message_too_long_for_the_window_raises_a_friendly_error(exchanges):
    session = make_session(budget=15, exchanges=exchanges)
    with pytest.raises(ConversationTooLongError, match="too long"):
        session.trim()


def test_after_the_too_long_error_the_history_is_unchanged_and_can_be_rolled_back():
    session = make_session(budget=15, exchanges=3)
    before = tags(session)
    with pytest.raises(ConversationTooLongError):
        session.trim()
    # Nothing was dropped...
    assert tags(session) == before
    # ...and the interface can cross out the too-long question and carry on.
    session.discard_last_user()
    assert tags(session)[-1] == "a2"


# --- setup checks ---------------------------------------------------------------------------------

@pytest.mark.parametrize("bad", [0, -5])
def test_a_zero_or_negative_budget_is_refused(bad):
    with pytest.raises(ValueError, match="must be positive"):
        Session(budget_tokens=bad)


def test_no_budget_is_allowed():
    # None means "never trim"; it must not be confused with a bad budget.
    assert Session(budget_tokens=None).trim() == 0
