# main and run_chat are the two things under test, both from cli.py.
from winter.cli import main, run_chat

# Message is used to check exactly what was sent to the model.
# ProviderError lets us build a mock that fails the way a real provider would.
from winter.providers.base import Message, Reply, ProviderError, ProviderSetupError

# The conversation object that run_chat now uses (ADR 0012).
from winter.session import Session

# The fake model that stands in for a real one.
from winter.providers.mock import MockProvider


# ---- helpers: fake keyboard and screen --------------------------------------------

# Builds a stand-in for input() that returns scripted lines instead of reading the keyboard.
def fake_input(lines):
    """Feed scripted lines to the loop; when they run out, behave like Ctrl+Z (EOF)."""
    # iter() makes the list hand out its items one at a time.
    it = iter(lines)

    # This inner function has the same shape as input(): it takes a prompt, returns a string.
    def _input(prompt: str = "") -> str:
        # Try to hand out the next scripted line.
        try:
            return next(it)
        # No lines left: act like the user closed the input (end of file).
        except StopIteration:
            # "from None" hides the internal StopIteration from the error message.
            raise EOFError from None

    # Give the caller the finished fake input function.
    return _input

# Runs the chat loop with scripted input and returns everything it printed.
def run(provider, lines, session=None):
    """Run the loop with scripted input and return everything it printed."""
    # A plain list that collects each line the loop "prints".
    out: list[str] = []
    # out.append works as the fake print. With session=None, run_chat makes a bare Session.
    run_chat(provider, session, input_fn=fake_input(lines), output_fn=out.append)
    # Hand back the collected output for the test to inspect.
    return out



# ---- run_chat() behavior ------------------------------------------------------------

# Test 1: the model's reply is shown to the user.
def test_reply_is_printed():
    # One message, then quit.
    out = run(MockProvider(), ["hello", "/exit"])
    # The echo reply must appear with the "winter> " prefix.
    assert "winter> [mock] you said: hello" in out


# Test 2: each turn sends the whole conversation so far.
def test_history_grows_and_is_sent_each_turn():
    # A mock we can inspect afterwards.
    p = MockProvider()
    # Two user turns, then quit.
    run(p, ["one", "two", "/exit"])
    # Collect the roles in the second call's conversation.
    roles = [m.role for m in p.calls[1]]
    # It must hold: first user message, the reply to it, then the second user message.
    assert roles == ["user", "assistant", "user"]


# Test 3: a provider failure is shown, the session survives, and history is cleaned up.
def test_provider_error_is_shown_and_history_rolled_back():
    # A mock that always fails with a friendly message.
    p = MockProvider(error=ProviderError("Ollama is not running"))
    # Two attempts, then quit.
    out = run(p, ["hi", "again", "/exit"])
    # The error is displayed on one line instead of crashing.
    assert "[error] Ollama is not running" in out
    # The loop survived the first error and tried the second input: two calls were made.
    assert len(p.calls) == 2
    # The failed first message was removed, so the second call carried only ONE message.
    assert len(p.calls[1]) == 1


# Test 4: blank lines are ignored, not sent to the model.
def test_blank_input_is_ignored():
    # A mock to check afterwards.
    p = MockProvider()
    # An empty line, a spaces-only line, then quit.
    run(p, ["", "   ", "/exit"])
    # The model was never called.
    assert p.calls == []


# Test 5: /exit stops the loop before any later input is read.
def test_exit_command_stops_before_later_input():
    # A mock to check afterwards.
    p = MockProvider()
    # "/exit" comes first, so "never sent" must never reach the model.
    run(p, ["/exit", "never sent"])
    # No calls were made.
    assert p.calls == []


# Test 6: end-of-input (Ctrl+Z / Ctrl+D) exits cleanly.
def test_eof_exits_cleanly():
    # No scripted lines at all: the very first input() raises EOFError.
    out = run(MockProvider(), [])
    # The loop must still say goodbye as its last line, with no crash.
    assert out[-1] == "Goodbye."
 
# Test 6b: terminal control characters in a reply are removed from the screen, not from history.
def test_control_characters_removed_from_output_but_kept_in_history():
    # ESC (\x1b), a bidi override (\u202e) and a carriage return (\r) inside a reply.
    raw = "hi\x1b[31m red\u202e evil\r"
    p = MockProvider(replies=[raw, "ok"])
    out = run(p, ["a", "b", "/exit"])
    # The screen shows the reply without the control characters.
    assert "winter> hi[31m red evil" in out
    # The second call's history still holds the RAW reply: we clean output, not storage.
    assert p.calls[1][1].content == raw


# Test 6c: a reply that hit the length limit is flagged to the user.
def test_cut_off_reply_shows_note():
    p = MockProvider(replies=[Reply(text="Once upon a", stop_reason="length")])
    out = run(p, ["tell me a story", "/exit"])
    assert "[note] The reply was cut short because it hit the length limit." in out
   



# ---- main(): the wiring (settings -> provider -> loop) -------------------------------
# Each test below uses chdir(tmp_path) to move into an empty folder, so a real .env
# file in the repo can never leak into these tests.

# Test 7: a configuration error returns exit code 2 and shows no traceback.
def test_main_config_error_returns_2_without_traceback(monkeypatch, tmp_path, capsys):
    # Work from an empty folder.
    monkeypatch.chdir(tmp_path)
    # Choose OpenRouter...
    monkeypatch.setenv("LOCAL_AI_PROVIDER", "openrouter")
    # ...and make sure no API key is set (raising=False: fine if it was not set).
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    # main() must report a config problem with exit code 2.
    assert main() == 2
    # capsys captured what was printed; .err is the error stream.
    err = capsys.readouterr().err
    # The message names the missing setting...
    assert "OPENROUTER_API_KEY" in err
    # ...and is a short message, not a Python stack trace.
    assert "Traceback" not in err


def test_main_unimplemented_provider_returns_2(monkeypatch, tmp_path, capsys):
    # TEMPORARY: delete or change this test when the OpenRouter adapter exists (Month 2 to 3).
    # Work from an empty folder so no real .env file can leak in.
    monkeypatch.chdir(tmp_path)
    # OpenRouter is the provider that still has no adapter.
    monkeypatch.setenv("LOCAL_AI_PROVIDER", "openrouter")
    # It needs a key to be a VALID setting. This is a fake placeholder, never a real key.
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    # A setup problem must exit with code 2 (ADR 0009), the same stamp as a bad .env value.
    assert main() == 2
    # capsys.readouterr() collects what was printed; .err is the stderr part.
    err = capsys.readouterr().err
    # The friendly message must say what is wrong...
    assert "not implemented" in err
    # ...and must be prefixed so a person spots it as an error.
    assert err.startswith("[error]")


def test_main_bad_ollama_url_returns_2(monkeypatch, tmp_path, capsys):
    # A typo in LOCAL_OLLAMA_URL must stop the app at startup with the setup exit code.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LOCAL_AI_PROVIDER", "ollama")
    # Forgot the "http://": the classic mistake.
    monkeypatch.setenv("LOCAL_OLLAMA_URL", "localhost:11434")
    assert main() == 2
    # The message names the setting to fix.
    assert "LOCAL_OLLAMA_URL" in capsys.readouterr().err



# Test 9: with the mock provider, main() builds it and starts the chat loop.
def test_main_runs_with_mock_provider(monkeypatch, tmp_path):
    # Work from an empty folder.
    monkeypatch.chdir(tmp_path)
    # Choose the mock provider.
    monkeypatch.setenv("LOCAL_AI_PROVIDER", "mock")
    # A list that will record which provider main() hands to the loop.
    seen = []
    # Replace the real chat loop with a stub that just records the provider's name.
    # main() looks up run_chat in cli.py when it runs, so this swap takes effect.
    monkeypatch.setattr("winter.cli.run_chat", lambda provider, session: seen.append(provider.name))
    # main() must finish successfully with exit code 0...
    assert main() == 0
    # ...having passed a provider named "mock" into the loop.
    assert seen == ["mock"]
    
# ---- the Session in the loop (ADR 0012) ------------------------------------------------

# Builds one 10-token text: 30 characters ("x" padding) that start with a tag.
def ten_tokens(tag):
    return tag + "x" * (30 - len(tag))


def test_system_prompt_is_sent_first_to_the_model():
    session = Session("rules")
    p = MockProvider()
    run(p, ["hi", "/exit"], session)
    # The model sees the rules page first, then the user's message.
    assert p.calls[0] == [Message("system", "rules"), Message("user", "hi")]


def test_the_conversation_is_stored_in_the_session():
    session = Session()
    run(MockProvider(), ["hello", "/exit"], session)
    # The Session now owns the exchange (not a hidden list inside run_chat).
    assert session.messages_for_model() == [
        Message("user", "hello"),
        Message("assistant", "[mock] you said: hello"),
    ]


def test_a_failed_turn_is_crossed_out_of_the_session():
    session = Session("rules")
    run(MockProvider(error=ProviderError("down")), ["hi", "/exit"], session)
    # Only the rules remain: the unanswered question was removed.
    assert session.messages_for_model() == [Message("system", "rules")]


def test_dropped_messages_are_announced_to_the_user():
    # Budget 60 tokens, each message 10 tokens. After 3 turns the pad holds 60; the 4th user
    # message makes 70, so trim() drops exchanges 1 and 2 (4 messages) and keeps q0/r0 and q3.
    session = Session(budget_tokens=60)
    p = MockProvider(replies=[ten_tokens(f"r{i}") for i in range(4)])
    lines = [ten_tokens(f"q{i}") for i in range(4)] + ["/exit"]
    out = run(p, lines, session)
    note = "[note] The conversation got long, so 4 older messages were dropped from the model's memory."
    # The user was told, exactly once...
    assert out.count(note) == 1
    # ...and the model really received the trimmed conversation: q0, r0, q3.
    sent = p.calls[3]
    assert [m.content[:2] for m in sent] == ["q0", "r0", "q3"]


def test_no_note_is_shown_when_nothing_is_dropped():
    out = run(MockProvider(), ["hello", "/exit"], Session(budget_tokens=1000))
    assert not any(line.startswith("[note]") for line in out)


def test_a_message_too_long_for_the_window_is_refused_and_the_loop_continues():
    # Budget 5 tokens cannot hold a 10-token message.
    session = Session(budget_tokens=5)
    p = MockProvider()
    out = run(p, [ten_tokens("q0"), "/exit"], session)
    # The user is told what to do...
    assert "[error] That message is too long for the model's context window. Please send a shorter one." in out
    # ...the model was never called, the question was crossed out, and the loop said goodbye.
    assert p.calls == []
    assert session.messages_for_model() == []
    assert out[-1] == "Goodbye."


def test_main_builds_the_session_from_settings(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LOCAL_AI_PROVIDER", "mock")
    monkeypatch.setenv("LOCAL_AI_CONTEXT_TOKENS", "8192")
    captured = {}

    # A Session that records how main() created it, then behaves normally.
    class RecordingSession(Session):
        def __init__(self, system_prompt=None, budget_tokens=None):
            captured.update(system_prompt=system_prompt, budget_tokens=budget_tokens)
            super().__init__(system_prompt, budget_tokens)

    monkeypatch.setattr("winter.cli.Session", RecordingSession)
    # Stop before any real chat starts.
    monkeypatch.setattr("winter.cli.run_chat", lambda provider, session: None)
    assert main() == 0
    # The assistant's rules come from the prompt file...
    assert "W.I.N.T.E.R" in captured["system_prompt"]
    # ...and the budget is the 8192 window minus the 512-token reply reserve.
    assert captured["budget_tokens"] == 8192 - 512

