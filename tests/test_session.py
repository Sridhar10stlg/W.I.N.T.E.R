# pytest gives us raises() ("this should fail") and parametrize (one test, many inputs).
import pytest

# Message is what Session stores and returns; Session is the class under test.
from winter.providers.base import Message
from winter.session import Session


def test_new_session_without_a_prompt_has_nothing_to_send():
    # A fresh notepad with no house rules and no orders sends an empty list.
    assert Session().messages_for_model() == []


def test_system_prompt_comes_first_as_a_system_message():
    # Page one holds the rules, and it is sent as a "system" message.
    messages = Session("be careful").messages_for_model()
    assert messages == [Message("system", "be careful")]


def test_conversation_keeps_its_order_after_the_system_prompt():
    # Build one full exchange and the start of a second.
    session = Session("rules")
    session.add_user("hi")
    session.add_assistant("hello")
    session.add_user("2+2?")
    # System prompt first, then every message oldest to newest.
    assert session.messages_for_model() == [
        Message("system", "rules"),
        Message("user", "hi"),
        Message("assistant", "hello"),
        Message("user", "2+2?"),
    ]


# --- the turn-taking rule (the invariant) ---------------------------------------------

def test_two_user_messages_in_a_row_are_refused():
    session = Session()
    session.add_user("first")
    # The model has not answered yet, so a second question is a bug in our code.
    with pytest.raises(ValueError, match="already a user message"):
        session.add_user("second")


def test_an_assistant_reply_cannot_come_first():
    # A reply needs a question to answer.
    with pytest.raises(ValueError, match="must follow a user message"):
        Session().add_assistant("hello?")


def test_two_assistant_replies_in_a_row_are_refused():
    session = Session()
    session.add_user("hi")
    session.add_assistant("hello")
    # Only one reply per question.
    with pytest.raises(ValueError, match="must follow a user message"):
        session.add_assistant("hello again")


def test_a_refused_message_does_not_change_the_history():
    session = Session()
    session.add_user("first")
    # Try to break the rule and ignore the error...
    with pytest.raises(ValueError):
        session.add_user("second")
    # ...the stored conversation must be exactly as before, with no half-written entry.
    assert session.messages_for_model() == [Message("user", "first")]


# --- the rollback (replaces history.pop() in run_chat) ----------------------------------

def test_discarding_an_unanswered_question_allows_asking_again():
    session = Session()
    session.add_user("question the model never answered")
    # The provider failed, so cross the question out.
    session.discard_last_user()
    # The history is empty again, and a new question is accepted.
    assert session.messages_for_model() == []
    session.add_user("try again")
    assert session.messages_for_model() == [Message("user", "try again")]


def test_discard_keeps_the_earlier_exchanges_and_the_system_prompt():
    session = Session("rules")
    session.add_user("hi")
    session.add_assistant("hello")
    session.add_user("unanswered")
    session.discard_last_user()
    # Only the unanswered question disappears.
    assert session.messages_for_model() == [
        Message("system", "rules"),
        Message("user", "hi"),
        Message("assistant", "hello"),
    ]


def test_cannot_discard_an_answered_question():
    session = Session()
    session.add_user("hi")
    session.add_assistant("hello")
    # The last message is a reply; removing anything now would tear a hole in the middle.
    with pytest.raises(ValueError, match="no unanswered user message"):
        session.discard_last_user()


def test_cannot_discard_from_an_empty_session():
    # Nothing to cross out.
    with pytest.raises(ValueError, match="no unanswered user message"):
        Session().discard_last_user()


# --- the copy guarantee and the prompt check ----------------------------------------------

def test_changing_the_returned_list_does_not_change_the_session():
    session = Session("rules")
    session.add_user("hi")
    # Scribble on the photocopy: add a message and remove another.
    copy = session.messages_for_model()
    copy.append(Message("user", "SCRIBBLE"))
    copy.pop(0)
    # The real notepad is untouched.
    assert session.messages_for_model() == [Message("system", "rules"), Message("user", "hi")]


def test_each_call_returns_a_new_list():
    session = Session()
    # Two photocopies must be two different sheets, even when the content is the same.
    assert session.messages_for_model() is not session.messages_for_model()


# A prompt that is empty or only spaces is a config mistake: refuse it at startup.
@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_system_prompt_is_refused(blank):
    with pytest.raises(ValueError, match="cannot be empty"):
        Session(blank)
