from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    model_name: str = Field(default="gemini-2.0-flash-001")
    temperature: float = Field(default=0.0)
    top_p: float = Field(default=0.0)
    top_k: int = Field(default=40)


def get_default_model_config() -> ModelConfig:
    """
    Returns the default model configuration.
    """
    return ModelConfig()
