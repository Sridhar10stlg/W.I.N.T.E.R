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