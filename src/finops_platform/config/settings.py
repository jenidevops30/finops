from functools import lru_cache
import os

from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    """Validated application settings loaded from environment variables."""

    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    aws_region: str = Field(default="us-east-1")
    aws_read_only: bool = Field(default=True)
    required_tags: tuple[str, ...] = (
        "Environment",
        "Application",
        "Owner",
        "CostCenter",
        "Project",
    )

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        value = value.upper()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if value not in allowed:
            raise ValueError(f"Unsupported log level: {value}")
        return value

    @field_validator("required_tags", mode="before")
    @classmethod
    def parse_required_tags(cls, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            return tuple(tag.strip() for tag in value.split(",") if tag.strip())
        return tuple(value)

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            environment=os.getenv("FINOPS_ENV", "development"),
            log_level=os.getenv("FINOPS_LOG_LEVEL", "INFO"),
            aws_region=os.getenv("FINOPS_AWS_REGION", "us-east-1"),
            aws_read_only=os.getenv("FINOPS_AWS_READ_ONLY", "true").lower() == "true",
            required_tags=os.getenv(
                "FINOPS_REQUIRED_TAGS",
                "Environment,Application,Owner,CostCenter,Project",
            ),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_environment()
