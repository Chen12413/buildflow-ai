from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_BAILIAN_CHAT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_BAILIAN_RESPONSES_BASE_URL = "https://dashscope.aliyuncs.com/api/v2/apps/protocols/compatible-mode/v1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "BuildFlow AI API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite+pysqlite:///./buildflow.db"
    cors_allow_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    llm_provider: str = "mock"
    llm_model: str = "mock-buildflow-v1"
    llm_api_mode: str = "auto"
    dashscope_api_key: str | None = Field(default=None, alias="DASHSCOPE_API_KEY")
    dashscope_chat_base_url: str = Field(default=DEFAULT_BAILIAN_CHAT_BASE_URL, alias="DASHSCOPE_CHAT_BASE_URL")
    dashscope_responses_base_url: str = Field(default=DEFAULT_BAILIAN_RESPONSES_BASE_URL, alias="DASHSCOPE_RESPONSES_BASE_URL")

    @field_validator("llm_provider")
    @classmethod
    def normalize_llm_provider(cls, value: str) -> str:
        cleaned = value.strip().lower().replace("-", "_")
        aliases = {
            "bailian": "aliyun_bailian",
            "dashscope": "aliyun_bailian",
            "aliyun": "aliyun_bailian",
            "aliyun_bailian": "aliyun_bailian",
            "mock": "mock",
        }
        return aliases.get(cleaned, cleaned)

    @field_validator("llm_model")
    @classmethod
    def normalize_llm_model(cls, value: str) -> str:
        return value.strip()

    @field_validator("llm_api_mode")
    @classmethod
    def normalize_llm_api_mode(cls, value: str) -> str:
        cleaned = value.strip().lower().replace("-", "_")
        aliases = {
            "auto": "auto",
            "response": "responses",
            "responses": "responses",
            "chat": "chat",
            "chat_completions": "chat",
            "chatcompletions": "chat",
        }
        return aliases.get(cleaned, cleaned)

    @field_validator("dashscope_api_key", "dashscope_chat_base_url", "dashscope_responses_base_url")
    @classmethod
    def normalize_optional_str(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


@lru_cache
def get_settings() -> Settings:
    return Settings()