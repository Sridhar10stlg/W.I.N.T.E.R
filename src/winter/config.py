from typing import Literal # Typing helper: Literal means "only these exact values are allowed".

'''
Field lets us say which environment variable name feeds each setting.
SecretStr is a string type that hides its value when printed or logged.
model_validator lets us write a check that looks at several settings together.
'''
from pydantic import Field, SecretStr, model_validator 

# pydantic-settings is the part of pydantic that reads environment variables and .env files.
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """All W.I.N.T.E.R configuration lives here, validated once at startup."""

    # env_file=".env": also read variables from a .env file in the folder you run from.
    # extra="ignore": if .env has variables we don't know about, skip them instead of erroring.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    # Which backend answers questions. Anything other than these two is rejected.
    # alias="..." is the exact variable name in .env / the environment.
    # The first argument is the default used when the variable is not set.
    provider: Literal["ollama", "openrouter"] = Field("ollama", alias="LOCAL_AI_PROVIDER")
    
    # Small model for low-RAM laptops and the bigger one for high spec laptops for better performance.
    model_low: str = Field("gemma3:1b", alias="LOCAL_AI_MODEL_LOW")
    model_high: str = Field("gemma3:4b", alias="LOCAL_AI_MODEL_HIGH")
    
    # Where the Ollama server listens. 11434 is Ollama's default port.
    ollama_url: str = Field("http://localhost:11434", alias="LOCAL_OLLAMA_URL")
    
    # The OpenRouter key. None means "not set". SecretStr stops it leaking into logs.
    openrouter_api_key: SecretStr | None = Field(None, alias="OPENROUTER_API_KEY")  # SecretStr hides the value
    
    # How much detail to log. Restricted to the standard Python logging levels.
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field("INFO", alias="LOG_LEVEL")

    # Runs after all fields are loaded, so it can compare provider and key together.
    @model_validator(mode="after")
    def _require_key_for_openrouter(self) -> "Settings":
        # If the user chose OpenRouter but left the key empty, fail now with a clear message.
        if self.provider == "openrouter" and not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is required when using the OpenRouter provider.")
        # A validator must return the object when everything is fine.
        return self
    
def load_settings() -> Settings:
    """Load settings from environment variables and .env file, returning a validated Settings object.
    Create the settings object. The rest of the app calls this, never os.environ."""
    
    return Settings()