# unicodedata tells us what KIND of character something is (letter, control code, ...).
import unicodedata

# sys gives us sys.stderr, the "error" output stream (separate from normal output).
import sys

# Callable is a type hint meaning "something you can call like a function".
from collections.abc import Callable

# ValidationError is what pydantic raises when a setting in .env is invalid.
from pydantic import ValidationError

# load_settings() reads and validates all configuration.
from winter.config import load_settings

# Provider is the interface any model backend follows.
# ProviderError is the parent of every provider failure (run_chat catches this one).
# ProviderSetupError is the "your setup is wrong" kind, which main() turns into exit code 2.
from winter.providers.base import Provider, ProviderError, ProviderSetupError

# build_provider() turns validated Settings into the one Provider object to use.
from winter.providers.factory import build_provider

# prompt_budget turns the window size into "how many tokens the conversation may use".
from winter.budget import prompt_budget

# The Session owns the conversation (ADR 0012). ConversationTooLongError is what trim() raises
# when even the system prompt plus the newest message do not fit.
from winter.session import ConversationTooLongError, Session

# load_system_prompt() reads the assistant's standing rules from the prompt file.
from winter.system_prompt import load_system_prompt


# The words that end the session when the user types them.
# A set is used because "is this word in the group?" is a fast, simple check.
EXIT_COMMANDS = {"/exit", "/quit"}

# Bidirectional-text control characters. They make text DISPLAY in a different order
# than it really is, so a reply could look harmless while saying something else.
_BIDI_CONTROLS = set("\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")


def safe_for_terminal(text: str) -> str:
    """Remove characters that could control the terminal instead of being shown.

    Model output is untrusted (docs/design/diagrams/trust-boundaries.md). Control
    characters such as ESC (start of colour/cursor codes) or a carriage return
    (overwrites the line) could change what the terminal shows. Newlines and tabs are kept.
    """
    return "".join(
        ch for ch in text
        # Keep newline and tab: they are normal formatting.
        if ch in "\n\t"
        # "Cc" is Unicode's category for control characters; drop those and bidi controls.
        or (unicodedata.category(ch) != "Cc" and ch not in _BIDI_CONTROLS)
    )



# input_fn and output_fn default to the real keyboard (input) and screen (print).
# Tests pass fake ones instead, so the loop never needs a real person or a real model.
def run_chat(
    provider: Provider,                                  # the model backend to talk to (mock, ollama, ...)
    session: Session | None = None,                      # the conversation (messages + system prompt + size limit)
    input_fn: Callable[[str], str] = input,              # how we read a line from the user
    output_fn: Callable[[str], None] = print,            # how we show a line to the user
) -> None:                                               # returns nothing; it just runs until the user quits
    """The chat loop. The Session, input and output are injected so tests need no model or keyboard."""
    # main() passes a real Session (system prompt + budget). Without one, use a bare Session
    # with no rules and no size limit; that is only meant for simple tests.
    if session is None:
        session = Session()

    # Greet the user and show which provider is active (this is why Provider has a `name`).
    output_fn(f"W.I.N.T.E.R ({provider.name}). Type /exit to quit.")

    # try/except around the whole loop so Ctrl+C or end-of-input exits cleanly (see bottom).
    try:
        # Loop forever; we leave only through `break` (exit command) or the except below.
        while True:
            # Show the "you> " prompt, read a line, and strip spaces/newline from both ends.
            text = input_fn("you> ").strip()

            # If the line is empty (user just pressed Enter)...
            if not text:
                # ...skip back to the top of the loop instead of sending nothing to the model.
                continue

            # If the user typed an exit command (lower() so "/EXIT" works too)...
            if text.lower() in EXIT_COMMANDS:
                # ...leave the while loop.
                break

            # Record what the user said. The Session checks the turn-taking rule for us.
            session.add_user(text)

            # Make sure the conversation fits the model's window BEFORE sending it (ADR 0012).
            try:
                # trim() returns how many old messages it had to drop (0 = none).
                dropped = session.trim()
            # Even the system prompt plus this message alone do not fit: the user must shorten it.
            except ConversationTooLongError as exc:
                # The question was never answered, so cross it out of the conversation.
                session.discard_last_user()
                # Say so visibly, with the text cleaned like all output.
                output_fn(f"[error] {safe_for_terminal(str(exc))}")
                # Back to the prompt; the session stays alive.
                continue

            # Never forget silently: tell the user when old messages were dropped.
            if dropped:
                output_fn(
                    f"[note] The conversation got long, so {dropped} older messages "
                    "were dropped from the model's memory."
                )

            # Provider calls can fail, so we guard this one call.
            try:
                # Send the system prompt plus the conversation (a fresh list); get back a Reply.
                reply = provider.generate(session.messages_for_model())
            # Catch only ProviderError: the expected, friendly kind of failure.
            except ProviderError as exc:
                # The model never answered, so cross out the question we just added.
                # Otherwise a retry would leave two "user" messages in a row.
                session.discard_last_user()
                # Error text is output too: clean it before showing it.
                output_fn(f"[error] {safe_for_terminal(str(exc))}")

                # Go back to the prompt; the session stays alive.
                continue

            # The model answered, so store its reply for the next turn (raw text, not cleaned).
            session.add_assistant(reply.text)
            # Show the reply, cleaned for the terminal. The session keeps the raw text.
            output_fn(f"winter> {safe_for_terminal(reply.text)}")
            # Tell the user when the answer was cut short, instead of hiding it.
            if reply.was_cut_off:
                output_fn("[note] The reply was cut short because it hit the length limit.")

    # EOFError = input ended (Ctrl+Z then Enter on Windows, Ctrl+D elsewhere).
    # KeyboardInterrupt = the user pressed Ctrl+C.
    except (EOFError, KeyboardInterrupt):
        # Print an empty line so the shell prompt doesn't start on the same line as "you> ".
        output_fn("")

    # Reached after /exit, Ctrl+C, or end-of-input.
    output_fn("Goodbye.")


# main() is the program's front door. It returns a number: the "exit code" the
# operating system sees (0 = success, anything else = a problem).
def main() -> int:
    """Entry point: load config, pick a provider, run the chat. Returns a process exit code."""
    # Step 1: read and validate configuration. This can fail if .env has a bad value.
    try:
        # Reads environment variables / .env and checks every field.
        settings = load_settings()
    # A bad setting (typo in provider, missing key for OpenRouter, ...) lands here.
    except ValidationError as exc:
        # Printed to stderr so error text stays separate from normal program output.
        print("Configuration error:", file=sys.stderr)
        # exc.errors() is a list with one entry per problem. We loop over them.
        for err in exc.errors():
            # err["loc"] is the path to the bad field, e.g. ("provider",).
            # Join the parts with dots; fall back to "settings" if the path is empty.
            where = ".".join(str(part) for part in err["loc"]) or "settings"
            # Print ONLY the field name and the reason, never the bad value itself,
            # because a bad value could be a secret (like an API key) and must not be echoed.
            print(f"  - {where}: {err['msg']}", file=sys.stderr)
        # Exit code 2 = setup problem: fix your configuration.
        return 2

    # Step 2: turn the settings into a provider object (mock or Ollama).
    try:
        provider = build_provider(settings)
    # A SETUP problem: the chosen provider can't be built (no adapter yet; later, a missing
    # model or key). Only this kind is caught here. Anything else coming out of
    # build_provider() would be a bug, and we WANT its traceback (fail loud, ADR 0009).
    except ProviderSetupError as exc:
        # Show the friendly message on stderr, cleaned like all error text.
        print(f"[error] {safe_for_terminal(str(exc))}", file=sys.stderr)
        # Exit code 2 = "fix your setup" (the same stamp as a bad .env value).
        return 2


    # Step 3: build the conversation: the assistant's standing rules plus the size limit.
    # This is the one place that wires them together (the composition root).
    # The size limit is the window MINUS room for the reply, the same number Ollama is told.
    session = Session(
        load_system_prompt(),
        budget_tokens=prompt_budget(settings.context_tokens),
    )
    # Step 4: hand the provider and the session to the chat loop. Runs until the user quits.
    run_chat(provider, session)
    # Exit code 0 = everything went fine.
    return 0   


