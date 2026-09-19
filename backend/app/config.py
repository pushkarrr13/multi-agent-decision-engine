from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)


class Settings(BaseSettings):

    app_name: str = (
        "Multi-Agent Business Decision Engine"
    )

    app_version: str = "0.1.0"

    environment: str = "development"

    database_url: str = (
        "postgresql+psycopg2://"
        "mabde:mabde_password@postgres:5432/"
        "decision_engine"
    )

    gemini_api_key: str = ""

    gemini_model: str = (
        "gemini-3.5-flash-lite"
    )

    model_config = SettingsConfigDict(

        env_file=".env",

        extra="ignore"
    )


settings = Settings()