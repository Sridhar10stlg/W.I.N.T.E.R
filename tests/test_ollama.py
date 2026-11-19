# httpx gives us MockTransport (the pretend road) and the exception classes to raise.
import httpx

# pytest gives us raises() and parametrize.
import pytest

# Our message type, the three error cards, and the Provider interface.
from winter.providers.base import (
    Message,
    Provider,
    ProviderSetupError,
    ProviderTemporaryError,
    ProviderUnavailableError,
    Usage,
)

# The class under test, and the wrapper for the end-to-end checks at the bottom.
from winter.providers.ollama import OllamaProvider
from winter.providers.retrying import RetryingProvider

# One tiny conversation reused by every test.
CONVO = [Message("user", "hi")]


# Build an OllamaProvider whose "network" is a function we control.
# handler(request) is called instead of any real HTTP call and returns (or raises) what we want.
def make_provider(handler, url="http://localhost:11434", model="gemma3:1b", timeout=5):
    # MockTransport routes every request to our handler; Client uses it instead of the network.
    client = httpx.Client(transport=httpx.MockTransport(handler))
    # client= is the injection point we left open in 3c.
    return OllamaProvider(url, model, timeout, client=client)


# A realistic Ollama answer (shape verified in step 3b). Tests override single fields.
def good_json(**overrides):
    body = {
        "message": {"role": "assistant", "content": "Hello!"},
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 15,
        "eval_count": 5,
    }
    # Replace or add the fields a test wants to change.
    body.update(overrides)
    return body


# --- the happy path ---------------------------------------------------------------

def test_good_answer_becomes_a_reply():
    # The pretend server always answers with a good reply.
    provider = make_provider(lambda request: httpx.Response(200, json=good_json()))
    reply = provider.generate(CONVO)
    # Text, our own stop word ("stop" became "complete"), and token counts all translated.
    assert reply.text == "Hello!"
    assert reply.stop_reason == "complete"
    assert reply.usage == Usage(input_tokens=15, output_tokens=5)


def test_request_has_the_shape_ollama_expects():
    # A list that the handler fills, so the test can inspect what the adapter sent.
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json=good_json())

    make_provider(handler, model="gemma3:4b").generate([Message("user", "hi"), Message("assistant", "yo")])
    # Exactly one request was made, to the right path, using POST.
    assert len(seen) == 1
    assert seen[0].method == "POST"
    assert seen[0].url.path == "/api/chat"
    # Parse the JSON body that was sent and check each promise.
    import json
    body = json.loads(seen[0].content)
    # The model comes from our settings...
    assert body["model"] == "gemma3:4b"
    # ...streaming is off (one complete answer)...
    assert body["stream"] is False
    # ...and our Message objects became plain role/content dicts, in order.
    assert body["messages"] == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "yo"},
    ]


def test_trailing_slash_in_url_does_not_double_the_slash():
    seen = []

    def handler(request):
        seen.append(request.url.path)
        return httpx.Response(200, json=good_json())

    # A URL ending with "/" is a very common typo in .env files.
    make_provider(handler, url="http://localhost:11434/").generate(CONVO)
    # The path must be /api/chat, not //api/chat.
    assert seen == ["/api/chat"]


def test_length_stop_reason_marks_the_reply_as_cut_off():
    provider = make_provider(lambda request: httpx.Response(200, json=good_json(done_reason="length")))
    reply = provider.generate(CONVO)
    assert reply.stop_reason == "length"
    # This is the property run_chat uses to print the "[note] cut short" line.
    assert reply.was_cut_off is True


# parametrize runs the test once per value: unknown word, missing word, wrong type.
@pytest.mark.parametrize("reason", ["weird_new_reason", None, ["x"]])
def test_unknown_stop_reason_becomes_other(reason):
    provider = make_provider(lambda request: httpx.Response(200, json=good_json(done_reason=reason)))
    # An odd stop word must never crash a chat.
    assert provider.generate(CONVO).stop_reason == "other"


# Bad token counts: missing (None), negative, or text instead of a number.
@pytest.mark.parametrize("bad", [None, -1, "5"])
def test_bad_token_counts_become_usage_none(bad):
    provider = make_provider(lambda request: httpx.Response(200, json=good_json(eval_count=bad)))
    reply = provider.generate(CONVO)
    # The ANSWER is still delivered; only the bookkeeping is "unknown".
    assert reply.text == "Hello!"
    assert reply.usage is None


# --- failures on the road (each one a different incident card) ------------------------

# Both timeout flavours are the same family and must give the same card.
@pytest.mark.parametrize("error", [httpx.ReadTimeout("slow"), httpx.ConnectTimeout("slow")])
def test_timeout_is_a_temporary_error(error):
    def handler(request):
        # raise instead of returning: the pretend network "times out".
        raise error

    with pytest.raises(ProviderTemporaryError, match="did not answer"):
        make_provider(handler, timeout=2.5).generate(CONVO)


def test_timeout_message_shows_the_configured_seconds():
    def handler(request):
        raise httpx.ReadTimeout("slow")

    # The user can only fix a timeout if the message says which number was used.
    with pytest.raises(ProviderTemporaryError, match="2.5 seconds"):
        make_provider(handler, timeout=2.5).generate(CONVO)


def test_connection_refused_is_an_unavailable_error():
    def handler(request):
        raise httpx.ConnectError("refused")

    with pytest.raises(ProviderUnavailableError, match="Cannot reach Ollama"):
        make_provider(handler).generate(CONVO)


def test_other_transport_failure_is_an_unavailable_error():
    def handler(request):
        # A dropped connection halfway: neither a timeout nor a refusal.
        raise httpx.RemoteProtocolError("dropped")

    with pytest.raises(ProviderUnavailableError, match="failed unexpectedly"):
        make_provider(handler).generate(CONVO)


def test_404_is_a_setup_error_naming_the_model_and_the_fix():
    # The body is a trap: it contains text that must NEVER reach the user.
    provider = make_provider(
        lambda request: httpx.Response(404, json={"error": "SERVER-WORDS"}),
        model="nope:1b",
    )
    with pytest.raises(ProviderSetupError) as caught:
        provider.generate(CONVO)
    message = str(caught.value)
    # Our own message names the model and the exact fix...
    assert "nope:1b" in message
    assert "ollama pull nope:1b" in message
    # ...and the server's raw words stay out (ADR 0009: replies are untrusted).
    assert "SERVER-WORDS" not in message


@pytest.mark.parametrize("status", [401, 500, 503])
def test_other_error_statuses_are_unavailable_and_show_the_number_only(status):
    provider = make_provider(lambda request: httpx.Response(status, text="SERVER-WORDS"))
    with pytest.raises(ProviderUnavailableError) as caught:
        provider.generate(CONVO)
    message = str(caught.value)
    # The status NUMBER helps the user; the body does not appear.
    assert str(status) in message
    assert "SERVER-WORDS" not in message


# Five ways a 200 answer can still be unusable, each given as the arguments for httpx.Response.
@pytest.mark.parametrize(
    "body",
    [
        {"text": "LEAK-ME this is not json"},          # not JSON at all
        {"json": ["a", "list", "not", "a", "dict"]},     # JSON, but the wrong shape
        {"json": {"unexpected": 1}},                     # no "message" key
        {"json": {"message": "just text"}},              # "message" is not a dict
        {"json": {"message": {"content": 123}}},         # content is a number, not text
    ],
)
def test_unusable_200_answers_are_an_unavailable_error(body):
    provider = make_provider(lambda request: httpx.Response(200, **body))
    with pytest.raises(ProviderUnavailableError, match="could not understand") as caught:
        provider.generate(CONVO)
    # Whatever the server sent, none of it is echoed back.
    assert "LEAK-ME" not in str(caught.value)


# --- secrets and addresses ---------------------------------------------------------------

def test_credentials_in_the_url_never_appear_in_error_messages():
    def handler(request):
        raise httpx.ConnectError("refused")

    provider = make_provider(handler, url="http://user:secret@localhost:9")
    with pytest.raises(ProviderUnavailableError) as caught:
        provider.generate(CONVO)
    message = str(caught.value)
    # The useful part (host and port) is shown...
    assert "http://localhost:9" in message
    # ...and neither the user name nor the password is.
    assert "secret" not in message
    assert "user" not in message


# Five kinds of broken address. Each must be refused when the adapter is BUILT.
@pytest.mark.parametrize(
    "bad_url",
    [
        "http://localhost:abc",   # port is not a number
        "localhost:11434",        # forgot the http://
        "ftp://localhost",        # not a web address
        "http://",                # no host name
        "",                       # empty
    ],
)
def test_bad_url_is_refused_at_startup_as_a_setup_error(bad_url):
    # No request is ever made: the problem is caught while building the provider.
    with pytest.raises(ProviderSetupError, match="LOCAL_OLLAMA_URL"):
        OllamaProvider(bad_url, "gemma3:1b", 5)


def test_bad_url_message_does_not_echo_the_address():
    # The address carries a canary password: it must not come back in the message.
    with pytest.raises(ProviderSetupError) as caught:
        OllamaProvider("ftp://user:secret@localhost", "gemma3:1b", 5)
    assert "secret" not in str(caught.value)


def test_https_address_without_a_port_is_accepted():
    # A valid address must still work (guards against a validator that is too strict).
    provider = OllamaProvider("https://ollama.example.com", "gemma3:1b", 5)
    assert provider.name == "ollama"



# --- the adapter as a citizen of the system -----------------------------------------------

def test_ollama_provider_is_a_provider_with_its_name():
    provider = make_provider(lambda request: httpx.Response(200, json=good_json()))
    # Substitutable anywhere the CLI expects a Provider.
    assert isinstance(provider, Provider)
    # The banner will read "W.I.N.T.E.R (ollama)".
    assert provider.name == "ollama"


def test_wrapper_retries_a_timeout_once_and_returns_the_second_answer():
    # Counts how many times the pretend server was "dialed".
    calls = []

    def handler(request):
        calls.append(1)
        # First call: too slow. Second call: fine.
        if len(calls) == 1:
            raise httpx.ReadTimeout("slow")
        return httpx.Response(200, json=good_json())

    # The real stack: RetryingProvider around OllamaProvider.
    reply = RetryingProvider(make_provider(handler)).generate(CONVO)
    assert reply.text == "Hello!"
    # Exactly two calls: the timeout and the retry.
    assert len(calls) == 2


def test_wrapper_does_not_retry_a_missing_model():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(404, json={"error": "missing"})

    with pytest.raises(ProviderSetupError):
        RetryingProvider(make_provider(handler)).generate(CONVO)
    # A setup problem is never retried (ADR 0010): one call only.
    assert len(calls) == 1
