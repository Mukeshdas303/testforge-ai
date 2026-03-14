from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Test Case Generation System"
    app_version: str = "1.0.0"
    debug: bool = False

    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "phi3"
    ollama_timeout: int = 120          # seconds — phi3 can be slow on first run

    # Generation settings
    max_test_cases_per_type: int = 5   # positive / negative / edge each

    class Config:
        env_file = ".env"

settings = Settings()