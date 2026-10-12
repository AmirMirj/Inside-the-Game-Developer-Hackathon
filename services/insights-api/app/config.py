"""Application settings (Azure OpenAI + explain mode)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-10-21"

    # auto | mock | azure — auto uses Azure when key+endpoint set
    explain_provider: str = "auto"

    def resolve_explain_provider(self) -> str:
        mode = (self.explain_provider or "auto").lower()
        if mode == "mock":
            return "mock"
        if mode == "azure":
            return "azure"
        if self.azure_openai_api_key and self.azure_openai_endpoint:
            return "azure"
        return "mock"


@lru_cache
def get_settings() -> Settings:
    return Settings()
