from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    neo4j_uri: str = 'bolt://127.0.0.1:7687'
    neo4j_user: str | None = Field(default=None, repr=False)
    neo4j_password: str | None = Field(default=None, repr=False)
    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:5173"]
    database_url: str = Field(default="postgresql+psycopg://localhost/diabetes_mas", repr=False)

settings = Settings()
