# main and run_chat are the two things under test, both from cli.py.
from winter.cli import main, run_chat

# ProviderError lets us build a mock that fails the way a real provider would.
from winter.providers.base import Reply, ProviderError, ProviderSetupError

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
def run(provider, lines):
    """Run the loop with scripted input and return everything it printed."""
    # A plain list that collects each line the loop "prints".
    out: list[str] = []
    # out.append works as the fake print: each output line is added to the list.
    run_chat(provider, input_fn=fake_input(lines), output_fn=out.append)
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


# Renamed: the name must describe the promise, and the promise is now "exit code 2".
def test_main_unimplemented_provider_returns_2(monkeypatch, tmp_path, capsys):
    # TEMPORARY: delete or change this test in Week 3, when the Ollama adapter exists.
    # Work from an empty folder so no real .env file can leak in.
    monkeypatch.chdir(tmp_path)
    # Ask for the provider that has no adapter yet.
    monkeypatch.setenv("LOCAL_AI_PROVIDER", "ollama")
    # A setup problem must exit with code 2 (ADR 0009), the same stamp as a bad .env value.
    assert main() == 2
    # capsys.readouterr() collects what was printed; .err is the stderr part.
    err = capsys.readouterr().err
    # The friendly message must say what is wrong...
    assert "not implemented" in err
    # ...and must be prefixed so a person spots it as an error.
    assert err.startswith("[error]")



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
    monkeypatch.setattr("winter.cli.run_chat", lambda provider: seen.append(provider.name))
    # main() must finish successfully with exit code 0...
    assert main() == 0
    # ...having passed a provider named "mock" into the loop.
    assert seen == ["mock"]
