from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AICOACH_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./ai_coach.db"
    storage_root: Path = Path("storage")
    embedding_enabled: bool = True
    log_level: str = "INFO"

    llm_api_base: str | None = None
    llm_api_key: str | None = None


settings = Settings()
