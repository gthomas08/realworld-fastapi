from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the application."""

    # Database configuration
    DATABASE_URL: str
    SECRET_KEY: str

    # OpenTelemetry configuration
    OTEL_EXPORTER_OTLP_ENDPOINT: str
    OTEL_SERVICE_NAME: str
    OTEL_TRACES_EXPORTER: str
    OTEL_METRICS_EXPORTER: str

    class Config:
        env_file = ".env"


settings = Settings()
