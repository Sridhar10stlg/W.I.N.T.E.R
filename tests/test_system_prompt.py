# inspect lets us look at a function's parameters (used by the "no free text" rule test).
import inspect

# date is the one value the loader accepts.
from datetime import date

# pytest gives us raises() ("this should fail").
import pytest

# _render is private (leading underscore) but holds all the filling logic, so we test it
# directly. load_system_prompt is the public function that reads the real file.
from winter.system_prompt import _render, load_system_prompt

# A fixed date makes the output predictable (no dependence on the real clock).
FIXED = date(2026, 11, 20)


# --- the real prompt file ---------------------------------------------------------------

def test_prompt_contains_the_date_we_supply():
    # The $date blank in system.txt must be filled with the date we pass in.
    assert "2026-11-20" in load_system_prompt(FIXED)


def test_no_blank_markers_are_left_in_the_prompt():
    # A leftover "$" would mean the model is sent a half-filled form letter.
    assert "$" not in load_system_prompt(FIXED)


def test_prompt_is_not_empty_and_has_no_stray_blank_lines():
    text = load_system_prompt(FIXED)
    # Something real was loaded...
    assert text
    # ...and the leading and trailing blank lines were removed.
    assert text == text.strip()


def test_default_date_is_today():
    # Ask for "today" without passing a date. Check the day before AND after the call,
    # so the test cannot fail just because midnight passed while it ran.
    before = date.today().isoformat()
    text = load_system_prompt()
    after = date.today().isoformat()
    assert before in text or after in text


def test_prompt_loads_from_any_working_folder(monkeypatch, tmp_path):
    # Start the program from an unrelated empty folder: a plain relative path to the
    # file would break here, but files("winter") must still find it.
    monkeypatch.chdir(tmp_path)
    assert "2026-11-20" in load_system_prompt(FIXED)


# --- the filling logic -----------------------------------------------------------------------

def test_render_fills_the_date_blank():
    assert _render("Today is $date.", FIXED) == "Today is 2026-11-20."


def test_render_with_no_blanks_returns_the_text_unchanged():
    # Boundary case: a template with nothing to fill (even an empty one) is fine.
    assert _render("No blanks here.", FIXED) == "No blanks here."
    assert _render("", FIXED) == ""


def test_render_refuses_a_blank_we_did_not_supply():
    # "$name" is not a value the loader provides. The error says which blank was
    # missing, so a typo in system.txt is found immediately.
    with pytest.raises(KeyError, match="name"):
        _render("Hello $name", FIXED)


def test_render_refuses_a_stray_dollar_sign():
    # A "$" followed by something that is not a blank name is a mistake in the file.
    with pytest.raises(ValueError):
        _render("The price is $5", FIXED)


def test_double_dollar_writes_a_literal_dollar():
    # "$$" is the way to write a real dollar sign in a template.
    assert _render("The price is $$5", FIXED) == "The price is $5"


# --- the trust rule --------------------------------------------------------------------------

def test_the_loader_accepts_a_date_and_nothing_else():
    # ADR 0012: conversation text, web pages and model output must never reach the template.
    # The safest way to guarantee it is a function that has NO parameter able to carry text.
    # If someone adds one later, this test fails and forces a conscious decision.
    assert list(inspect.signature(load_system_prompt).parameters) == ["today"]


def test_the_prompt_works_as_a_session_system_prompt():
    # The two new pieces fit together: Session accepts what the loader returns.
    from winter.session import Session

    session = Session(load_system_prompt(FIXED))
    first = session.messages_for_model()[0]
    # It becomes the first, "system" message.
    assert first.role == "system"
    assert "2026-11-20" in first.content
