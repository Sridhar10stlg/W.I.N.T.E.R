# pytest is needed for the fixture decorator.
import pytest

# Settings tells us every environment variable it reads (the "alias" of each field).
from winter.config import Settings

# Built FROM Settings, so a setting added later (like LOCAL_AI_CONTEXT_TOKENS) is covered
# automatically and nobody has to remember to update a second list.
_CONFIG_VARS = [field.alias for field in Settings.model_fields.values() if field.alias]


# autouse=True means "run this before EVERY test, without the test asking for it".
@pytest.fixture(autouse=True)
def _clean_config_environment(monkeypatch):
    # Start every test from a clean kitchen: remove each configuration variable
    # (raising=False = no complaint when it was not set anyway).
    for name in _CONFIG_VARS:
        monkeypatch.delenv(name, raising=False)
    # monkeypatch puts everything back after the test, so your real shell is not changed.
