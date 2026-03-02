from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'enterprise-meeting-ai-brain'
    app_env: str = 'dev'
    log_level: str = 'INFO'

    openai_api_key: str = Field(..., alias='OPENAI_API_KEY')
    openai_model: str = Field(default='gpt-4o-mini', alias='OPENAI_MODEL')
    openai_base_url: str | None = Field(default=None, alias='OPENAI_BASE_URL')

    redis_url: str = Field(default='redis://redis:6379/0', alias='REDIS_URL')
    redis_ttl_seconds: int = Field(default=14400, alias='REDIS_TTL_SECONDS')

    n8n_base_url: str = Field(default='http://n8n:5678/webhook', alias='N8N_BASE_URL')
    tool_timeout_seconds: float = Field(default=15.0, alias='TOOL_TIMEOUT_SECONDS')


settings = Settings()
