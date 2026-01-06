from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR: Path = Path(__file__).parent.parent


class Settings(BaseSettings):
    vk_api_key: str
    openai_api_key_: str
    ai_model: str = "gpt-4o-mini"

    @property
    def openai_api_key(self) -> str:
        return f"sk-{self.openai_api_key_}"

    @property
    def openai_api_url(self) -> str:
        return "https://api.aiguoguo199.com/v1"

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env",),
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
