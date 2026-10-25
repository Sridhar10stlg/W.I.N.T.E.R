# main and run_chat are the two things under test, both from cli.py.
from winter.cli import main, run_chat

# ProviderError lets us build a mock that fails the way a real provider would.
from winter.providers.base import ProviderError

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


# Test 8: a provider with no adapter returns exit code 1.
def test_main_unimplemented_provider_returns_1(monkeypatch, tmp_path, capsys):
    # TEMPORARY: delete or change this test in Week 3, when the Ollama adapter exists.
    # Work from an empty folder.
    monkeypatch.chdir(tmp_path)
    # Ask for the provider that has no adapter yet.
    monkeypatch.setenv("LOCAL_AI_PROVIDER", "ollama")
    # main() must report a provider problem with exit code 1.
    assert main() == 1
    # The friendly message goes to the error stream.
    assert "not implemented" in capsys.readouterr().err


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
