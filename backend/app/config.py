from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_DB_PASSWORD: str

    # DeepSeek (SiliconFlow)
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.siliconflow.cn/v1"

    # Jina Reader
    JINA_API_KEY: str

    # Search APIs
    TAVILY_API_KEY: Optional[str] = None
    SERPER_API_KEY: Optional[str] = None
    SEARCH_PROVIDER: str = "tavily"  # or "serper"

    # App Settings
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
