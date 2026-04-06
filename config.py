from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Base application settings
    project_name: str = "AI Pet Backend"
    version: str = "1.0.0"
    debug: bool = False
    
    # LLM Settings
    llm_api_key: str = ""
    llm_base_url: str = "https://api.siliconflow.cn/v1"
    llm_model_name: str = "Qwen/Qwen2.5-7B-Instruct"

    # Database Settings
    database_url: str = "sqlite+aiosqlite:///./pet_memory.db"
    redis_url: str = "redis://:147369szx@120.48.80.108:6379/0"
    celery_broker_url: str = "amqp://admin:147369szx@120.48.80.108:5672//"
    
    # This tells pydantic to load values from .env file
    # Priority: Environment Variables > .env file values > default values here
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
