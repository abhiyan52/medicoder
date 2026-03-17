import json
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from app.utils.logger import logger

# Load .env file
load_dotenv()


def get_project_id_from_creds() -> str:
    """
    Attempt to find project_id from environment or the credentials JSON file.
    """
    env_project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if env_project:
        return env_project

    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        try:
            with open(creds_path) as f:
                data = json.load(f)
        except OSError as e:
            logger.error(
                "Failed to read credentials file", creds_path=creds_path, error=str(e)
            )
            return "medicoder-project"
        except json.JSONDecodeError as e:
            logger.error(
                "Invalid JSON in credentials file", creds_path=creds_path, error=str(e)
            )
            return "medicoder-project"

        project_id = data.get("project_id")
        if not project_id:
            logger.error("Credentials file missing 'project_id'", creds_path=creds_path)
            return "medicoder-project"
        return project_id

    return "medicoder-project"


def get_api_port() -> int:
    raw = os.getenv("API_PORT")
    if raw is None or raw == "":
        return 8000

    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid API_PORT value; falling back to default", raw_value=raw)
        return 8000


class AppConfig(BaseModel):
    # Essential Google Cloud Settings
    GOOGLE_APPLICATION_CREDENTIALS: str | None = Field(
        default_factory=lambda: os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    )
    PROJECT_ID: str = Field(default_factory=get_project_id_from_creds)
    LOCATION: str = Field(
        default_factory=lambda: os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    )

    # API server settings
    API_HOST: str = Field(default_factory=lambda: os.getenv("API_HOST", "127.0.0.1"))
    API_PORT: int = Field(default_factory=get_api_port)
    CORS_ORIGINS: str = Field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:5173")
    )

    # Storage
    OUTPUT_DIR: str = Field(
        default_factory=lambda: os.getenv("OUTPUT_DIR", "output")
    )


# Singleton instance
settings = AppConfig()
