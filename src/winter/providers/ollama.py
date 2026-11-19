# urlsplit takes a web address apart, so we can print it WITHOUT any user:password part.
from urllib.parse import urlsplit

# httpx is the HTTP library we approved. It is imported in THIS file only,
# so no other part of W.I.N.T.E.R knows how we talk to Ollama.
import httpx

# Message is one chat turn; Provider is the interface we implement;
# Reply and Usage are our own result types; StopReason is our own list of stop words.
# The three Provider*Error types are the incident cards (ADR 0009).
from winter.providers.base import (
    Message,
    Provider,
    ProviderSetupError,
    ProviderTemporaryError,
    ProviderUnavailableError,
    Reply,
    StopReason,
    Usage,
)


# Translation table: Ollama's word for "why I stopped" -> OUR word (ADR 0008).
# Any word not in this table becomes "other" (see .get(..., "other") below).
_STOP_REASONS: dict[str, StopReason] = {
    # Ollama says "stop" when the model finished normally.
    "stop": "complete",
    # Ollama says "length" when the reply hit the token limit and was cut off.
    "length": "length",
}


# A small helper outside the class: it only turns Ollama's counters into a Usage.
def _usage_from(data: dict) -> Usage | None:
    """Return Usage when both token counts are sane numbers, otherwise None."""
    # prompt_eval_count = tokens the model READ (our input_tokens).
    input_tokens = data.get("prompt_eval_count")
    # eval_count = tokens the model WROTE (our output_tokens).
    output_tokens = data.get("eval_count")
    # Trust the numbers only if both are whole numbers that are not negative.
    # Bad or missing counts must not break a chat, so the answer is "unknown" (None).
    if (
        isinstance(input_tokens, int)
        and isinstance(output_tokens, int)
        and input_tokens >= 0
        and output_tokens >= 0
    ):
        # Both look fine: build our own Usage object.
        return Usage(input_tokens=input_tokens, output_tokens=output_tokens)
    # Anything else: say "not reported" rather than guess.
    return None

# One fixed message for every kind of bad address. It never echoes the value,
# because the value might contain a password (http://user:secret@host).
_BAD_URL_MESSAGE = (
    "LOCAL_OLLAMA_URL is not a valid address. "
    "It must look like http://localhost:11434"
)


# Checks the configured address and returns the version that is safe to print.
# Called once, from __init__, so a bad address fails at startup (exit code 2 in main()).
def _display_url(base_url: str) -> str:
    """Validate the Ollama address; return it without credentials or path.

    Raises ProviderSetupError if the address cannot be used.
    """
    try:
        # Take the address apart into scheme, host, port...
        parts = urlsplit(base_url)
        # Reading .port raises ValueError when the port is not a number (http://localhost:abc).
        port = parts.port
    except ValueError:
        # `from None`: the original error text could contain the address.
        raise ProviderSetupError(_BAD_URL_MESSAGE) from None

    # Only web addresses make sense here, and a host name is required.
    # This rejects "localhost:11434" (no http://), "ftp://...", "http://" and "".
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise ProviderSetupError(_BAD_URL_MESSAGE)

    # hostname never includes user:password, so credentials are dropped here.
    netloc = parts.hostname
    # Add the port when there is one.
    if port:
        netloc += f":{port}"
    # Put the safe pieces back together.
    return f"{parts.scheme}://{netloc}"




# The driver. It IS a Provider, so the CLI can use it exactly like the mock.
class OllamaProvider(Provider):
    """Talks to a local Ollama server through its /api/chat endpoint (no streaming)."""

    # Satisfies the abstract `name` property; the CLI banner shows this word.
    name = "ollama"

    def __init__(
        self,
        base_url: str,                              # where Ollama listens, e.g. http://localhost:11434
        model: str,                                 # which model to ask, e.g. gemma3:4b
        timeout_seconds: float,                     # how long to wait for an answer (from Settings)
        client: httpx.Client | None = None,         # a ready-made HTTP client; tests pass a fake one
    ) -> None:
        # Build the full address once. rstrip("/") avoids a double slash if the URL ends with "/".
        self._url = base_url.rstrip("/") + "/api/chat"
        # Remember which model to ask.
        self._model = model
        # Remember how long to wait.
        self._timeout = timeout_seconds
        # Use the client we were given, or make a real one. Reusing one client keeps the
        # connection open between questions instead of reconnecting every time.
        self._client = client if client is not None else httpx.Client()
        # The same address, cleaned for error messages.
        self._shown_url = _display_url(base_url)
   

    # Same signature as Provider.generate, so it can stand in for any provider.
    def generate(self, messages: list[Message]) -> Reply:
        # Step 1: pack the parcel (unchanged from 3c).
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }

        # Step 2: drive to Ollama. Each way the trip can fail gets its own card.
        # Order matters: specific first, general last (HTTPError is the parent of the others).
        # `from None` hides the original exception, whose text could contain the raw URL.
        try:
            response = self._client.post(self._url, json=payload, timeout=self._timeout)
        # No answer in time (connect or read timeout): may go away by itself, so "temporary".
        except httpx.TimeoutException:
            raise ProviderTemporaryError(
                f"Ollama did not answer within {self._timeout:g} seconds. "
                "A slow laptop may need a larger LOCAL_AI_TIMEOUT_SECONDS."
            ) from None
        # Connection refused: nothing is listening. Retrying won't start it, so "unavailable".
        except httpx.ConnectError:
            raise ProviderUnavailableError(
                f"Cannot reach Ollama at {self._shown_url}. "
                "Start it (open the Ollama app or run 'ollama serve') and try again."
            ) from None
        # Any other transport problem (connection dropped, protocol error...).
        except httpx.HTTPError:
            raise ProviderUnavailableError(
                f"The connection to Ollama at {self._shown_url} failed unexpectedly. "
                "Check that Ollama is running."
            ) from None

        # Step 3: check the status code BEFORE reading the body.
        # 404 = "no such model" (or an Ollama too old for /api/chat): a SETUP problem, never retried.
        if response.status_code == 404:
            raise ProviderSetupError(
                f"Ollama does not have the model '{self._model}'. "
                f"Run: ollama pull {self._model} (or check LOCAL_AI_MODEL_LOW / LOCAL_AI_MODEL_HIGH)."
            )
        # Any other non-success status: show the NUMBER only, never the server's own words.
        if not response.is_success:
            raise ProviderUnavailableError(
                f"Ollama answered with an error (HTTP {response.status_code}). "
                "Check that Ollama is healthy."
            )

        # Step 4: read the answer. The server's reply is untrusted: check its shape at every step.
        try:
            # Turn the reply text into dicts and lists (ValueError if it is not JSON).
            data = response.json()
            # Walk the tree: message -> content (KeyError / TypeError if the shape is wrong).
            text = data["message"]["content"]
            # The answer must be text; anything else is a broken reply.
            if not isinstance(text, str):
                raise TypeError("content is not text")
        # One card for every flavour of "the reply is not what we expected".
        except (ValueError, KeyError, TypeError):
            raise ProviderUnavailableError(
                "Ollama sent a reply W.I.N.T.E.R. could not understand. "
                "Check that your Ollama version supports /api/chat."
            ) from None

        # Step 5: translate into our own words. Guard the key: .get() needs a hashable value.
        reason = data.get("done_reason")
        stop_reason = _STOP_REASONS.get(reason, "other") if isinstance(reason, str) else "other"

        # Step 6: hand back the Reply.
        return Reply(text=text, stop_reason=stop_reason, usage=_usage_from(data))

