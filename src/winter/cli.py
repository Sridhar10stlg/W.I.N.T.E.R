# sys gives us sys.stderr, the "error" output stream (separate from normal output).
import sys

# Callable is a type hint meaning "something you can call like a function".
from collections.abc import Callable

# ValidationError is what pydantic raises when a setting in .env is invalid.
from pydantic import ValidationError

# load_settings() reads and validates all configuration.
from winter.config import load_settings

# Message is one chat turn; Provider is the interface any model backend follows;
# ProviderError is the single error type a provider is allowed to raise.
from winter.providers.base import Message, Provider, ProviderError

# build_provider() turns validated Settings into the one Provider object to use.
from winter.providers.factory import build_provider

# The words that end the session when the user types them.
# A set is used because "is this word in the group?" is a fast, simple check.
EXIT_COMMANDS = {"/exit", "/quit"}


# input_fn and output_fn default to the real keyboard (input) and screen (print).
# Tests will pass fake ones instead, so the loop never needs a real person or a real model.
def run_chat(
    provider: Provider,                                  # the model backend to talk to (mock, ollama, ...)
    input_fn: Callable[[str], str] = input,              # how we read a line from the user
    output_fn: Callable[[str], None] = print,            # how we show a line to the user
) -> None:                                               # returns nothing; it just runs until the user quits
    """The chat loop. Input and output are injected so tests need no keyboard or screen."""
    # The conversation so far, oldest message first. Starts empty.
    history: list[Message] = []

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

            # Record what the user said. Message("user", text) is role + content.
            history.append(Message("user", text))

            # Provider calls can fail, so we guard this one call.
            try:
                # Send the WHOLE history so the model sees earlier turns; get back one reply string.
                reply = provider.generate(history)
            # Catch only ProviderError: the expected, friendly kind of failure.
            except ProviderError as exc:
                # The model never answered, so remove the user message we just added.
                # Otherwise a retry would leave two "user" messages in a row.
                history.pop()
                # Show the problem on one line; str(exc) is the provider's friendly message.
                output_fn(f"[error] {exc}")
                # Go back to the prompt; the session stays alive.
                continue

            # The model answered, so store its reply in the history for the next turn.
            history.append(Message("assistant", reply))
            # Show the reply to the user.
            output_fn(f"winter> {reply}")
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
        # Exit code 2 = configuration problem.
        return 2

    # Step 2: turn the settings into a provider object (mock now, Ollama in Week 3).
    try:
        provider = build_provider(settings)
    # build_provider raises ProviderError for providers that aren't implemented yet.
    except ProviderError as exc:
        # Show the friendly message on stderr.
        print(f"[error] {exc}", file=sys.stderr)
        # Exit code 1 = provider problem.
        return 1

    # Step 3: hand the provider to the chat loop from F1. Runs until the user quits.
    run_chat(provider)
    # Exit code 0 = everything went fine.
    return 0

