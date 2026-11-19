# pytest gives us the raises() helper to say "this should fail".
import pytest

# ValidationError is what pydantic raises when a setting is invalid.
from pydantic import ValidationError

from winter.config import Settings

# _env_file=None in every test means "ignore my real .env". Tests must give the
# same result on every laptop and must never use real keys.

def test_defaults_use_ollama():
    # With no variables set, we should get the safe free defaults.
    s = Settings(_env_file=None)
    assert s.provider == "ollama"
    assert s.model_low == "gemma3:1b"
    assert s.openrouter_api_key is None
    
def test_env_variables_are_read(monkeypatch):
    # monkeypatch temporarily sets an environment variable, then undoes it after the test.
    monkeypatch.setenv("LOCAL_AI_MODEL_LOW", "some-model:1b")
    s = Settings(_env_file=None)
    # Proves the alias names in config.py really match what the environment provides.
    assert s.model_low == "some-model:1b"
    
def test_openrouter_requires_key():
    # Choosing OpenRouter without a key must be rejected at startup.
    with pytest.raises(ValidationError):
        Settings(_env_file=None, LOCAL_AI_PROVIDER="openrouter")

def test_openrouter_with_key_is_valid_and_secret_is_hidden():
    # With a key, settings are valid...
    s = Settings(_env_file=None, LOCAL_AI_PROVIDER="openrouter", OPENROUTER_API_KEY="abc123")
    # ...and printing the settings must not reveal the key.
    assert "abc123" not in repr(s)
    
def test_unknown_provider_rejected():
    # A typo in the provider name must fail, not silently fall back.
    with pytest.raises(ValidationError):
        Settings(_env_file=None, LOCAL_AI_PROVIDER="nope")

def test_mock_provider_is_allowed():
    # "mock" lets the CLI run with no model installed.
    s = Settings(_env_file=None, LOCAL_AI_PROVIDER="mock")
    assert s.provider == "mock"
    
# --- 2b-3: model tier and timeout ---------------------------------------------------

def test_default_tier_is_low_and_model_follows_it():
    # With nothing set, the safe choice is the small model (the user opts UP to high).
    s = Settings(_env_file=None)
    assert s.model_tier == "low"
    # The property must hand back the LOW name, not the high one.
    assert s.model == "gemma3:1b"


def test_high_tier_selects_the_high_model():
    # Flip the switch to "high"; the property must follow it.
    s = Settings(_env_file=None, LOCAL_AI_MODEL_TIER="high")
    assert s.model == "gemma3:4b"


def test_model_property_follows_custom_model_names(monkeypatch):
    # Rename both models through the environment, to prove the property reads the
    # configured names and does not have "gemma3" typed inside it.
    monkeypatch.setenv("LOCAL_AI_MODEL_LOW", "tiny:1b")
    monkeypatch.setenv("LOCAL_AI_MODEL_HIGH", "big:9b")
    # Same environment, two different switch positions, two different answers.
    assert Settings(_env_file=None, LOCAL_AI_MODEL_TIER="low").model == "tiny:1b"
    assert Settings(_env_file=None, LOCAL_AI_MODEL_TIER="high").model == "big:9b"


def test_unknown_tier_rejected():
    # A typo like "hgih" must fail at startup, not silently pick a model.
    with pytest.raises(ValidationError):
        Settings(_env_file=None, LOCAL_AI_MODEL_TIER="hgih")


def test_default_timeout_is_120_seconds():
    # The documented default: generous enough for a CPU-only first model load.
    assert Settings(_env_file=None).timeout_seconds == 120


def test_timeout_is_read_from_environment(monkeypatch):
    # The alias must match the name documented in .env.example.
    monkeypatch.setenv("LOCAL_AI_TIMEOUT_SECONDS", "2.5")
    # Environment values arrive as text; pydantic converts "2.5" to the float 2.5.
    assert Settings(_env_file=None).timeout_seconds == 2.5


# parametrize runs this one test once per bad value (zero, negative, over the cap).
@pytest.mark.parametrize("bad", [0, -1, 601])
def test_timeout_outside_allowed_range_rejected(bad):
    # Allowed range is 0 < seconds <= 600. Anything outside must fail at startup.
    with pytest.raises(ValidationError):
        Settings(_env_file=None, LOCAL_AI_TIMEOUT_SECONDS=bad)


# The edges of the range are the classic place for off-by-one bugs, so test them too.
@pytest.mark.parametrize("edge", [0.1, 600])
def test_timeout_edges_are_accepted(edge):
    # Just above 0 and exactly 600 are both legal (gt=0 excludes 0; le=600 includes 600).
    assert Settings(_env_file=None, LOCAL_AI_TIMEOUT_SECONDS=edge).timeout_seconds == edge
